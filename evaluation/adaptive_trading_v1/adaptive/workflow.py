"""Reproducible staged native experiments, immutable freeze, and final audit artifacts."""

import argparse
import gzip
import json
import platform
import subprocess
import sys
import time

import pandas as pd

from .common import ROOT, assert_frozen, config, digest, ns, source_hashes, write_json
from .data import download, load
from .evidence import EvidenceProvider
from .features import aggregate, build_features
from .native import EdgeStrategy, run
from .performance import daily_statistics, trade_metrics
from .profiles import BASE, library
from .runtime import factory, native_candidate

PRE = ("research", "validation", "wf1", "wf2")
COSTED = [p.id for p in BASE] + ["TB48_SHORT", "TB48_FUNDING"]


def save_run(result):
    directory = ROOT / "results" / "runs" / result["period"] / result["scenario"]
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / (result["candidate"] + "__" + result["symbol"] + ".json.gz")
    with gzip.GzipFile(filename=str(path), mode="wb", mtime=0) as f:
        f.write(json.dumps(result, sort_keys=True, allow_nan=False).encode())


def run_path(profile, symbol, period, scenario):
    return (
        ROOT
        / "results"
        / "runs"
        / period
        / scenario
        / (profile + "__" + symbol + ".json.gz")
    )


def read_runs(periods):
    result = []
    for period in periods:
        for path in sorted((ROOT / "results" / "runs" / period).glob("*/*.json.gz")):
            with gzip.open(path, "rt") as f:
                result.append(json.load(f))
    return result


def inputs(period):
    raw, rates = {}, {}
    for symbol in config()["symbols"]:
        raw[symbol], rates[symbol] = load(symbol, period, 5)
    frames = build_features(raw, rates)
    result = {}
    for symbol, raw_frame in raw.items():
        features = {
            int(row["available_ns"]): row for row in frames[symbol].to_dict("records")
        }
        result[symbol] = (aggregate(raw_frame, 15), rates[symbol], features)
    return result


def static(periods):
    for period in periods:
        data = inputs(period)
        for profile in library().values():
            if profile.id == "NO_TRADE":
                continue
            scenarios = (
                list(config()["scenarios"]) if profile.id in COSTED else ["base"]
            )
            for scenario in scenarios:
                for symbol, (bars, rates, features) in data.items():
                    path = run_path(profile.id, symbol, period, scenario)
                    if path.exists():
                        continue
                    started = time.monotonic()
                    out = run(
                        native_candidate(profile.id),
                        symbol,
                        period,
                        bars,
                        rates,
                        scenario,
                        strategy_factory=factory(features, fixed=profile.id),
                    )
                    save_run(out)
                    print(
                        f"static {period} {profile.id} {scenario} {symbol}: {len(out['trades'])} trades ({time.monotonic() - started:.1f}s)",
                        flush=True,
                    )


def combined(runs):
    trades = sorted([t for r in runs for t in r["trades"]], key=lambda t: t["exit_ns"])
    symbols = {r["symbol"] for r in runs}
    capital = 10000 * len(symbols)
    result = trade_metrics(trades, capital or 30000)
    if not runs:
        return result
    points = []
    wealth = float(capital)
    for period in sorted(
        {r["period"] for r in runs}, key=lambda p: ns(config()["periods"][p][0])
    ):
        per = [r for r in runs if r["period"] == period]
        changes = []
        for r in per:
            series = pd.Series({int(t): float(e) for t, e in r["daily"]}).sort_index()
            changes.append(series.diff().fillna(0))
        changes = pd.concat(changes).groupby(level=0).sum().sort_index()
        curve = wealth + changes.cumsum()
        points += [(int(t), float(e)) for t, e in curve.items()]
        wealth = float(curve.iloc[-1])
    result.update(daily_statistics(points, capital))
    result["daily_equity"] = points
    result["capital"] = capital
    result["reconciled"] = all(
        abs(float(r["reconciliation_difference"])) < 0.00001 for r in runs
    )
    result["switch_count"] = sum(len(r["switches"]) for r in runs)
    result["research_event_count"] = sum(len(r["research"]) for r in runs)
    result["return_method"] = (
        "fixed-risk sleeves, nominal PnL carried across separately flattened periods"
    )
    return result


def choose_static(runs):
    ranks = []
    for profile in COSTED:
        m = combined(
            [
                r
                for r in runs
                if r["candidate"] == profile
                and r["scenario"] == "base"
                and r["period"] != "research"
            ]
        )
        ranks.append({"profile": profile, "metrics": m})
    ranks.sort(
        key=lambda x: (
            -(x["metrics"].get("sharpe") or -100),
            -x["metrics"]["net_pnl"],
            x["profile"],
        )
    )
    return {
        "selected": ranks[0]["profile"],
        "ranking": ranks,
        "selection_periods": ["validation", "wf1", "wf2"],
        "caveat": "Developmental selection; only future sealed comparison is independent",
    }


class BuyHold(EdgeStrategy):
    def on_bar(self, bar):
        if self.start <= bar.ts_event < self.end:
            self.previous_volume = bar.volume.as_decimal() * 10000
            if not self.active:
                self.pending = {
                    "action": "entry",
                    "side": 1,
                    "distance": float(bar.close) * 0.0025 / 0.9,
                    "signal_ns": bar.ts_event,
                    "regime": "REFERENCE",
                }
            if (bar.ts_event + 10**6) % (86400 * 10**9) == 0:
                from .native import USDT, VENUE, D

                balance = (
                    self.cache.account_for_venue(VENUE).balance_total(USDT).as_decimal()
                )
                unrealized = (
                    self.signed_qty
                    * (bar.close.as_decimal() - self.active["entry_price"])
                    if self.active
                    else D(0)
                )
                self.daily[bar.ts_event + 10**6] = float(balance + unrealized)


def adaptive(periods, historical_runs, scenarios=None):
    provider = EvidenceProvider(
        [r for r in historical_runs if r["candidate"] in library()]
    )
    for period in periods:
        data = inputs(period)
        for scenario in scenarios or config()["scenarios"]:
            for symbol, (bars, rates, features) in data.items():
                for label in ("ADAPTIVE", "BUY_HOLD", "NO_TRADE"):
                    path = run_path(label, symbol, period, scenario)
                    if path.exists():
                        continue
                    candidate = native_candidate("TB48")
                    candidate["id"] = label
                    previous_state = None
                    ordered = list(config()["periods"])
                    index = ordered.index(period)
                    if label == "ADAPTIVE" and index > 0:
                        previous = run_path(label, symbol, ordered[index - 1], scenario)
                        if previous.exists():
                            with gzip.open(previous, "rt") as f:
                                previous_state = json.load(f).get("adaptive_state")
                            if previous_state is None:
                                raise RuntimeError(
                                    "Previous adaptive state missing; rebuild preholdout"
                                )
                    sf = (
                        factory(
                            features,
                            evidence_provider=provider,
                            resume_state=previous_state,
                        )
                        if label == "ADAPTIVE"
                        else BuyHold
                        if label == "BUY_HOLD"
                        else factory(features, fixed="NO_TRADE")
                    )
                    out = run(
                        candidate,
                        symbol,
                        period,
                        bars,
                        rates,
                        scenario,
                        strategy_factory=sf,
                    )
                    save_run(out)
                    print(
                        f"{label} {period} {scenario} {symbol}: {len(out['trades'])} trades, {len(out['research'])} research events",
                        flush=True,
                    )


def preholdout():
    static(PRE)
    runs = read_runs(PRE)
    write_json(ROOT / "results" / "static_selection.json", choose_static(runs))
    adaptive(PRE, runs)
    provider = EvidenceProvider(runs)
    final = {p: provider(p, ns("2026-07-01")) for p in library() if p != "NO_TRADE"}
    write_json(ROOT / "results" / "preholdout_evidence.json", final)


def test_suite():
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", str(ROOT / "tests")],
        capture_output=True,
        text=True,
        check=False,
    )
    path = ROOT / "results" / "tests.txt"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(result.stdout + result.stderr)
    write_json(
        ROOT / "results" / "tests.json",
        {
            "exit_code": result.returncode,
            "source_hashes": source_hashes(),
            "output_sha256": digest(path),
            "command": "python -m pytest -q tests",
        },
    )
    print(result.stdout + result.stderr)
    if result.returncode:
        raise RuntimeError("Integrity test suite failed")


def freeze():
    freeze_path = ROOT / "results" / "freeze.json"
    if freeze_path.exists():
        assert_frozen()
        return
    required = [
        ROOT / "results" / "static_selection.json",
        ROOT / "results" / "preholdout_evidence.json",
        ROOT / "results" / "tests.txt",
    ]
    if any(not p.exists() for p in required):
        raise RuntimeError("Preholdout evidence and tests required before freeze")
    test_record = ROOT / "results" / "tests.json"
    if not test_record.exists():
        raise RuntimeError("Run workflow tests to record test provenance before freeze")
    test_status = json.loads(test_record.read_text())
    if test_status["exit_code"] != 0 or test_status["source_hashes"] != source_hashes():
        raise RuntimeError("Tests failed or tested source changed")
    if digest(ROOT / "results" / "tests.txt") != test_status["output_sha256"]:
        raise RuntimeError("Test evidence changed")
    required.append(test_record)
    for period in PRE:
        for scenario in config()["scenarios"]:
            for symbol in config()["symbols"]:
                path = run_path("ADAPTIVE", symbol, period, scenario)
                if not path.exists():
                    raise RuntimeError("Missing adaptive comparison")
                with gzip.open(path, "rt") as f:
                    result = json.load(f)
                if result.get("adaptive_state") is None:
                    raise RuntimeError("State-continuation evidence missing")
    required += sorted((ROOT / "results" / "runs").glob("*/*/*.json.gz"))
    required += sorted((ROOT / "data").glob("preholdout*.json"))
    import nautilus_trader

    write_json(
        freeze_path,
        {
            "frozen_at": pd.Timestamp.now(tz="UTC").isoformat(),
            "source_hashes": source_hashes(),
            "evidence_hashes": {str(p.relative_to(ROOT)): digest(p) for p in required},
            "baseline": config()["baseline_commit"],
            "prior": config()["prior_commit"],
            "runtime": {
                "python": platform.python_version(),
                "nautilus": nautilus_trader.__version__,
            },
            "static_choice": json.loads(required[0].read_text())["selected"],
            "sealed_period": config()["periods"]["holdout"],
        },
    )


def holdout():
    assert_frozen()
    opened = ROOT / "results" / "holdout_opened.json"
    if not opened.exists():
        write_json(
            opened,
            {
                "opened_at": pd.Timestamp.now(tz="UTC").isoformat(),
                "freeze_sha256": digest(ROOT / "results" / "freeze.json"),
            },
        )
    download(holdout=True)
    frozen_choice = assert_frozen()["static_choice"]
    data = inputs("holdout")
    for profile in COSTED:
        for scenario in config()["scenarios"]:
            for symbol, (bars, rates, features) in data.items():
                if run_path(profile, symbol, "holdout", scenario).exists():
                    continue
                out = run(
                    native_candidate(profile),
                    symbol,
                    "holdout",
                    bars,
                    rates,
                    scenario,
                    strategy_factory=factory(features, fixed=profile),
                )
                save_run(out)
                print(f"sealed static {profile} {scenario} {symbol}", flush=True)
    # Provider deliberately excludes all holdout static outcomes
    adaptive(("holdout",), read_runs(PRE))
    assert frozen_choice == assert_frozen()["static_choice"]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "stage",
        choices=[
            "download",
            "preholdout",
            "tests",
            "freeze",
            "holdout",
            "report",
            "verify",
        ],
    )
    args = parser.parse_args()
    if args.stage == "download":
        download()
    elif args.stage == "preholdout":
        preholdout()
    elif args.stage == "tests":
        test_suite()
    elif args.stage == "freeze":
        freeze()
    elif args.stage == "holdout":
        holdout()
    elif args.stage == "report":
        from .report import report

        report()
    elif args.stage == "verify":
        from .report import verify

        verify()


if __name__ == "__main__":
    main()

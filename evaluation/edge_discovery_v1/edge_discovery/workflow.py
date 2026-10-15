"""Auditable chronological selection and single-use holdout admission."""

import argparse
import concurrent.futures
import datetime
import gzip
import json
import platform
import subprocess
import sys

import nautilus_trader
import numpy
import pandas

from .common import ROOT, assert_frozen, candidates, config, digest, source_hashes, write_json
from .data import download, load
from .engine import run
from .metrics import metrics


def run_path(candidate, symbol, period, scenario):
    return ROOT / "results" / "runs" / period / scenario / f"{candidate['id']}__{symbol}.json.gz"


def evaluate(candidate, symbol, period, scenario="base"):
    path = run_path(candidate, symbol, period, scenario)
    signature = source_hashes()
    if path.exists():
        with gzip.open(path, "rt") as f:
            result = json.load(f)
        execution_files = [
            "config.json",
            "edge_discovery/common.py",
            "edge_discovery/data.py",
            "edge_discovery/engine.py",
            "edge_discovery/__init__.py",
        ]
        if any(result["source_hashes"].get(p) != signature[p] for p in execution_files):
            raise RuntimeError(
                f"Stale execution must be explicitly removed before recompute: {path}"
            )
        return result
    bars, rates = load(symbol, period, candidate["minutes"])
    result = run(candidate, symbol, period, bars, rates, scenario)
    result["source_hashes"] = signature
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp")
    with gzip.open(temporary, "wt") as f:
        json.dump(result, f, allow_nan=False, sort_keys=True)
    temporary.replace(path)
    print(
        f"{period} {scenario} {candidate['id']} {symbol}: {len(result['trades'])} trades, balance {result['native_balance']}",
        flush=True,
    )
    return result


def collect(candidate, periods, scenario="base"):
    return [evaluate(candidate, s, p, scenario) for p in periods for s in config()["symbols"]]


def rank(family, periods):
    ranked = []
    for c in candidates():
        if c["family"] != family:
            continue
        m = metrics(collect(c, periods))
        ranked.append((c, m))
    ranked.sort(
        key=lambda pair: (
            -(pair[1]["sharpe"] if pair[1]["sharpe"] is not None else -1e9),
            -pair[1]["net_pnl"],
            pair[0]["id"],
        )
    )
    return ranked


def neighbors(candidate):
    keys = list(config()["grids"][candidate["family"]])
    return [
        c
        for c in candidates()
        if c["family"] == candidate["family"]
        and c["minutes"] == candidate["minutes"]
        and sum(c[k] != candidate[k] for k in keys) == 1
    ]


def preholdout():
    if (ROOT / "results" / "holdout_opened.json").exists():
        raise RuntimeError("Holdout already opened: preholdout work is locked")
    if (ROOT / "results" / "freeze.json").exists():
        raise RuntimeError("Selection already frozen")
    grid = candidates()
    with concurrent.futures.ProcessPoolExecutor(max_workers=3) as pool:
        for offset in range(0, len(grid), 3):
            list(pool.map(evaluate_grid_candidate, grid[offset : offset + 3]))
    decisions = {}
    selection = config()["selection"]
    for family in config()["grids"]:
        choices = {}
        for target, history in (
            ("validation", ["research"]),
            ("wf1", ["research", "validation"]),
            ("wf2", ["research", "validation", "wf1"]),
            ("final", ["research", "validation", "wf1", "wf2"]),
        ):
            ranked = rank(family, history)
            choices[target] = {
                "candidate": ranked[0][0],
                "history": history,
                "ranking": [
                    {"id": c["id"], "sharpe": m["sharpe"], "net_pnl": m["net_pnl"]}
                    for c, m in ranked
                ],
            }
        final = choices["final"]["candidate"]
        oos_runs = [
            r for p in ("validation", "wf1", "wf2") for r in collect(choices[p]["candidate"], [p])
        ]
        oos = metrics(oos_runs)
        fixed = metrics(collect(final, ["validation", "wf1", "wf2"]))
        folds = {
            p: metrics(collect(choices[p]["candidate"], [p])) for p in ("validation", "wf1", "wf2")
        }
        neighborhood = {
            c["id"]: metrics(collect(c, ["validation", "wf1", "wf2"]))["net_pnl"]
            for c in neighbors(final)
        }
        positive_neighbor_fraction = sum(v > 0 for v in neighborhood.values()) / len(neighborhood)
        stresses = {}
        fixed_stresses = {}
        for scenario in ("slip2", "slip3", "cost2x"):
            stresses[scenario] = metrics(
                [
                    r
                    for p in ("validation", "wf1", "wf2")
                    for r in collect(choices[p]["candidate"], [p], scenario)
                ]
            )
            fixed_stresses[scenario] = metrics(
                collect(final, ["validation", "wf1", "wf2"], scenario)
            )
        gates = {
            "integrity": oos["reconciled"] and fixed["reconciled"],
            "validation_positive": folds["validation"]["net_pnl"] > 0,
            "both_walkforward_folds_positive": all(folds[p]["net_pnl"] > 0 for p in ("wf1", "wf2")),
            "oos_trades": oos["total_trades"] >= selection["minimum_trades"],
            "symbol_samples": all(
                m["total_trades"] >= selection["minimum_symbol_trades"]
                for m in oos["by_symbol"].values()
            ),
            "symbol_transfer": sum(m["net_pnl"] > 0 for m in oos["by_symbol"].values())
            >= selection["minimum_positive_symbols"],
            "profit_factor": (oos["profit_factor"] or 0) >= selection["minimum_profit_factor"],
            "drawdown": oos["maximum_drawdown"] <= selection["maximum_drawdown"],
            "fixed_representative_positive": fixed["net_pnl"] > 0,
            "parameter_neighborhood": positive_neighbor_fraction
            >= selection["minimum_positive_neighbor_fraction"],
            "cost_stress": all(m["net_pnl"] > 0 for m in stresses.values())
            and all(m["net_pnl"] > 0 for m in fixed_stresses.values()),
            "both_sides_positive": all(m["net_pnl"] > 0 for m in oos["by_side"].values()),
            "trade_concentration": oos["net_excluding_best_trade"] > 0
            and (oos["best_trade_positive_profit_share"] or 1)
            <= selection["maximum_best_trade_profit_share"],
            "month_concentration": oos["net_excluding_best_month"] > 0
            and (oos["best_month_positive_profit_share"] or 1)
            <= selection["maximum_best_month_profit_share"],
        }
        decisions[family] = {
            "choices": choices,
            "oos": oos,
            "fixed_preholdout": fixed,
            "folds": folds,
            "neighbors": neighborhood,
            "positive_neighbor_fraction": positive_neighbor_fraction,
            "stresses": stresses,
            "fixed_stresses": fixed_stresses,
            "gates": gates,
            "eligible": all(gates.values()),
        }
    write_json(ROOT / "results" / "selection.json", decisions)
    summaries = []
    for c in candidates():
        for period in ("research", "validation", "wf1", "wf2"):
            summaries.append(
                {"candidate": c, "period": period, "metrics": metrics(collect(c, [period]))}
            )
    write_json(ROOT / "results" / "grid_summary.json", summaries)


def evaluate_grid_candidate(candidate):
    collect(candidate, ["research", "validation", "wf1", "wf2"])


def freeze():
    if (ROOT / "results" / "freeze.json").exists():
        raise RuntimeError("Freeze exists and cannot be overwritten")
    if not (ROOT / "results" / "integrity.json").exists():
        raise RuntimeError("Run integrity checks before freezing")
    integrity = json.loads((ROOT / "results" / "integrity.json").read_text())
    if not integrity["passed"] or integrity["source_hashes"] != source_hashes():
        raise RuntimeError("Integrity checks missing, failed, or stale")
    decisions = json.loads((ROOT / "results" / "selection.json").read_text())
    evidence = [
        ROOT / "results" / "selection.json",
        ROOT / "results" / "grid_summary.json",
        ROOT / "results" / "integrity.json",
        ROOT / "results" / "tests.txt",
        ROOT / "data" / "preholdout_manifest.json",
        ROOT / "data" / "preholdout_repairs.json",
    ]
    evidence += sorted((ROOT / "results" / "runs").rglob("*.json.gz"))
    evidence += sorted((ROOT / "data" / "audits").glob("*.json"))
    evidence += sorted(ROOT.glob("*.py"))
    evidence += [ROOT / "READING_NOTES.md", ROOT / "REPRODUCTION.md"]
    evidence += sorted((ROOT / "upstream_locks").glob("*"))
    evidence += [
        ROOT / "results" / "engineering_notes.json",
        ROOT / "results" / "runtime_provenance.json",
    ]
    frozen = {
        "frozen_at_utc": datetime.datetime.now(datetime.UTC).isoformat(),
        "source_hashes": source_hashes(),
        "evidence_hashes": {str(p.relative_to(ROOT)): digest(p) for p in evidence},
        "representatives": {f: d["choices"]["final"]["candidate"] for f, d in decisions.items()},
        "eligible": {f: d["eligible"] for f, d in decisions.items()},
        "tested_candidates": len(candidates()),
        "git_head": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        "runtime": {
            "python": sys.version,
            "platform": platform.platform(),
            "nautilus_trader": nautilus_trader.__version__,
            "numpy": numpy.__version__,
            "pandas": pandas.__version__,
        },
    }
    write_json(ROOT / "results" / "freeze.json", frozen)
    print("Selection frozen; holdout can now be opened once", flush=True)


def holdout():
    frozen = assert_frozen()
    marker = ROOT / "results" / "holdout_opened.json"
    with marker.open("x") as f:
        json.dump(
            {
                "opened_at_utc": datetime.datetime.now(datetime.UTC).isoformat(),
                "freeze_sha256": digest(ROOT / "results" / "freeze.json"),
            },
            f,
            indent=2,
        )
    download(holdout=True)
    final = {}
    selections = json.loads((ROOT / "results" / "selection.json").read_text())
    for family, candidate in frozen["representatives"].items():
        scenarios = {s: metrics(collect(candidate, ["holdout"], s)) for s in config()["scenarios"]}
        base = scenarios["base"]
        oos = selections[family]["oos"]
        label = "NO_EDGE"
        if base["net_pnl"] > 0 and oos["net_pnl"] > 0:
            label = "WEAK_EDGE"
            if (
                frozen["eligible"][family]
                and base["total_trades"] >= 30
                and (base["profit_factor"] or 0) >= 1.05
                and all(m["net_pnl"] > 0 for m in scenarios.values())
            ):
                label = "EDGE_CANDIDATE"
        final[family] = {
            "classification": label,
            "candidate": candidate,
            "preholdout_eligible": frozen["eligible"][family],
            "scenarios": scenarios,
            "robust_label_blocked_by": [
                "No historical filter snapshots",
                "Bar-derived execution quotes",
                "Funding mark proxies where archives have gaps",
            ],
        }
    write_json(ROOT / "results" / "final.json", final)
    print({f: d["classification"] for f, d in final.items()}, flush=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "stage", choices=["download", "preholdout", "freeze", "holdout", "report", "integrity"]
    )
    args = parser.parse_args()
    if args.stage == "download":
        download()
    elif args.stage == "integrity":
        from .checks import check

        check()
    elif args.stage == "report":
        from .report import report

        report()
    else:
        globals()[args.stage]()


if __name__ == "__main__":
    main()

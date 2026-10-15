"""Independent evidence, native-ledger and causal-prefix checks."""

import hashlib
import json
import subprocess
from decimal import Decimal as D

import pandas as pd

from .common import ROOT, config, digest, ns, write_json


def reference_audit():
    expected = json.loads((ROOT / "results/reference_audit.json").read_text())
    prefixes = {
        "edge_v1": "evaluation/edge_discovery_v1",
        "adaptive_v1": "evaluation/adaptive_trading_v1",
        "adaptive_v2": "evaluation/adaptive_trading_v2",
    }
    rows = {}
    for key, record in expected.items():
        tree = subprocess.check_output(
            ["git", "ls-tree", "-r", record["commit"], prefixes[key]], text=True
        )
        actual = hashlib.sha256(tree.encode()).hexdigest()
        assert actual == record["tree_listing_sha256"]
        merge_base = subprocess.run(
            ["git", "merge-base", "--is-ancestor", record["commit"], "HEAD"],
            capture_output=True,
            check=False,
        )
        assert merge_base.returncode == 1, (
            "Reference evidence was merged into work branch"
        )
        rows[key] = {**record, "unchanged": True, "merged": False}
    assert (
        subprocess.check_output(["git", "branch", "--show-current"], text=True).strip()
        == "evaluation/alpha-discovery-v3"
    )
    # Validate the V2 prospective freeze directly against immutable git blobs
    sha = config()["reference_commits"]["adaptive_v2"]
    prefix = prefixes["adaptive_v2"]
    frozen = json.loads(
        subprocess.check_output(
            ["git", "show", f"{sha}:{prefix}/prospective_freeze.json"]
        )
    )
    for path, expected_digest in frozen["files"].items():
        data = subprocess.check_output(["git", "show", f"{sha}:{prefix}/{path}"])
        assert hashlib.sha256(data).hexdigest() == expected_digest
    rows["v2_prospective_freeze"] = {
        "verified_files": len(frozen["files"]),
        "eligible": frozen["initial_shadow_eligible_profiles"],
        "status": frozen["prospective_status"],
    }
    return rows


def causal_history_audit():
    from .features import build
    from .ml import attach
    from .native import run
    from .profiles import library
    from .strategy import factory

    raw = {
        s: pd.read_parquet(ROOT / f"data/cache/{s}_bars.parquet")
        for s in config()["symbols"]
    }
    rates = {
        s: pd.read_parquet(ROOT / f"data/cache/{s}_rates.parquet")
        for s in config()["symbols"]
    }
    cutoff = ns("2025-04-17")
    # Prefix recomputation never reads later bars or settlements
    prefix_raw = {s: f[f.t < cutoff].copy() for s, f in raw.items()}
    prefix_rates = {
        s: f[f.original_ms * 10**6 < cutoff].copy() for s, f in rates.items()
    }
    prefix, _models = attach(build(prefix_raw, prefix_rates))
    full = {s: pd.read_parquet(ROOT / f"data/cache/{s}_features.parquet") for s in raw}
    for s, f in full.items():
        a = f[f.available_ns < cutoff].reset_index(drop=True)
        pd.testing.assert_frame_equal(a, prefix[s], check_exact=True)
    mutated = {s: f.copy() for s, f in raw.items()}
    for f in mutated.values():
        f.loc[f.t >= cutoff, ["open", "high", "low", "close"]] *= 3
        f.loc[f.t >= cutoff, "taker_buy"] *= 0.1
    changed, _ = attach(build(mutated, rates))
    for s, f in full.items():
        pd.testing.assert_frame_equal(
            f[f.available_ns < cutoff].reset_index(drop=True),
            changed[s][changed[s].available_ns < cutoff].reset_index(drop=True),
            check_exact=True,
        )
    # Actual consumed-history native prefix, no artificial liquidation at prefix end
    from .features import aggregate

    symbol = "BTCUSDT"
    features = {int(r["available_ns"]): r for r in full[symbol].to_dict("records")}
    p = library()["RAW_LONG"]
    common = {
        "candidate": {**p.definition(), "liquidate": False},
        "symbol": symbol,
        "period": "retrospective",
        "start_ns": ns("2025-01-01"),
        "strategy_factory": factory(features),
    }
    short = run(
        **common,
        bars=aggregate(prefix_raw[symbol], 15),
        rates=prefix_rates[symbol],
        end_ns=cutoff,
    )
    later = ns("2025-05-01")
    long = run(
        **common,
        bars=aggregate(raw[symbol][raw[symbol].t < later], 15),
        rates=rates[symbol][rates[symbol].t < later],
        end_ns=later,
    )
    assert short["fills"] == [f for f in long["fills"] if f["ts_ns"] < cutoff]
    result = {
        "passed": True,
        "cutoff_ns": cutoff,
        "feature_prefix_symbols": list(raw),
        "future_tail_mutation": "all earlier features and ML scores unchanged",
        "actual_history_native_prefix_fills": len(short["fills"]),
        "fixture_is_performance_evidence": False,
    }
    write_json(ROOT / "results/causality_audit.json", result)
    return result


def native_audit(runs):
    from .workflow import fingerprint

    assert len(runs) == config()["research_budget"]["maximum_native_runs"]
    stamp = fingerprint()
    trades = fills = 0
    for r in runs.values():
        assert r["fingerprint"] == stamp
        assert abs(D(r["reconciliation_difference"])) <= D("0.00001")
        net = D(0)
        for t in r["trades"]:
            e = t["exact_financials"]
            value = (
                D(e["gross_pnl"]) - D(e["fees"]) - D(e["slippage"]) + D(e["funding"])
            )
            assert abs(value - D(e["net_pnl"])) <= D("0.00000001")
            net += D(e["net_pnl"])
            assert t["entry_ns"] < t["exit_ns"]
        assert abs(
            D(r["native_balance"]) - D(config()["capital_per_symbol"]) - net
        ) <= D("0.00001")
        assert all(
            f["signal_ns"] < f["ts_ns"] and D(f["fee"]) >= 0 and D(f["slippage"]) >= 0
            for f in r["fills"]
        )
        assert len(r["fills"]) == 2 * len(r["trades"])
        assert r["open_position"] is None
        trades += len(r["trades"])
        fills += len(r["fills"])
    return {
        "passed": True,
        "runs": len(runs),
        "closed_trades": trades,
        "fills": fills,
        "decimal_account_tolerance": "0.00001 USDT",
        "chronology": "every signal before fill",
    }


def verify():
    from .workflow import load_runs, verify_freeze

    verify_freeze()
    references = reference_audit()
    native = native_audit(load_runs())
    frozen = json.loads((ROOT / "prospective_freeze.json").read_text())
    for path, expected in frozen["files"].items():
        assert digest(ROOT / path) == expected, path
    artifacts = json.loads((ROOT / "artifact_checksums.json").read_text())
    for path, expected in artifacts.items():
        assert digest(ROOT / path) == expected, path
    result = {
        "references": references,
        "native": native,
        "prospective_freeze_verified": True,
        "artifact_files_verified": len(artifacts),
        "real_money_enabled": False,
    }
    write_json(ROOT / "results/final_verification.json", result)
    print(
        json.dumps(
            {
                "verified": True,
                "native_runs": native["runs"],
                "artifact_files": len(artifacts),
            }
        )
    )

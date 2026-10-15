"""Independent reconciliation of published tables, contracts and promotion claims."""

import json
from collections import Counter
from decimal import Decimal as D

import pandas as pd
from alpha.common import DAY, ROOT, config, write_json
from alpha.profiles import library
from alpha.workflow import load_runs, verify_freeze


def main():
    verify_freeze()
    runs = load_runs()
    profiles = library()
    expected = {
        (p, s, c)
        for p in profiles
        for s in config()["symbols"]
        for c in config()["scenarios"]
    }
    assert set(runs) == expected
    totals = pd.read_csv(ROOT / "results/profile_results.csv")
    symbols = pd.read_csv(ROOT / "results/per_symbol_results.csv")
    quarters = pd.read_csv(ROOT / "results/walk_forward_quarterly.csv")
    months = pd.read_csv(ROOT / "results/monthly_contributions.csv")
    assert len(totals) == 44 * 3 and len(symbols) == 396 and len(quarters) == 44 * 3 * 7
    assert len(months) == 44 * 3 * 21
    errors = []
    for row in totals.itertuples(index=False):
        sm = symbols[(symbols.profile == row.profile) & (symbols.cost == row.cost)]
        qm = quarters[(quarters.profile == row.profile) & (quarters.cost == row.cost)]
        mm = months[(months.profile == row.profile) & (months.cost == row.cost)]
        assert set(sm.symbol) == set(config()["symbols"])
        assert len(qm) == 7 and len(mm) == 21
        assert int(sm.trades.sum()) == row.trades
        errors.extend(
            [
                abs(sm.net_pnl.sum() - row.net_pnl),
                abs(qm.marked_net.sum() - row.net_pnl),
                abs(mm.marked_net.sum() - row.net_pnl),
            ]
        )
    assert max(errors) < 1e-6
    precision_fills = 0
    for r in runs.values():
        spec = config()["instrument_specs"][r["symbol"]]
        for f in r["fills"]:
            price = D(f["price"]) / D(spec["tick"])
            qty = D(f["quantity"]) / D(spec["step"])
            assert price == price.to_integral_value() and qty == qty.to_integral_value()
            assert (
                f["signal_ns"] < f["ts_ns"]
                and D(f["fee"]) >= 0
                and D(f["slippage"]) >= 0
            )
            precision_fills += 1
    for s in config()["symbols"]:
        f = pd.read_parquet(ROOT / f"data/cache/{s}_features.parquet")
        available = f.funding_available_ns.notna()
        assert (
            f.loc[available, "funding_available_ns"] <= f.loc[available, "available_ns"]
        ).all()
    models = json.loads((ROOT / "results/ml_training.json").read_text())
    for m in models:
        if m["latest_label_end_ns"] is not None:
            assert (
                m["latest_label_end_ns"]
                < m["training_cutoff_ns"]
                <= m["decision_ns"] - DAY
            )
    experiments = json.loads((ROOT / "results/experiments.json").read_text())
    required = {
        "hypothesis_id",
        "strategy_family",
        "features",
        "parameters",
        "symbols",
        "timeframes",
        "entry_logic",
        "exit_logic",
        "risk_model",
        "cost_model",
        "date_range",
        "result",
        "reason",
    }
    assert len(experiments) == 44 and {r["hypothesis_id"] for r in experiments} == set(
        profiles
    )
    for row in experiments:
        assert required <= set(row) and isinstance(row["features"], dict)
    evidence = json.loads((ROOT / "results/profile_evidence.json").read_text())
    validated = {
        p for p, e in evidence.items() if e["classification"] == "VALIDATED_PROFILE"
    }
    for p in validated:
        assert all(evidence[p]["gates"].values())
    output = json.loads((ROOT / "profile_library.json").read_text())
    conclusion = json.loads((ROOT / "results/conclusions.json").read_text())
    assert {p["profile_id"] for p in output["profiles"]} == validated
    assert set(conclusion["validated_profiles"]) == validated
    assert (
        not conclusion["real_money_enabled"]
        and not conclusion["prospective_performance_observed"]
    )
    if conclusion["classification"] == "ALPHA_DISCOVERY_VALIDATED_LIBRARY":
        assert len(validated) >= 2 and any(
            p["materially_different"] for p in conclusion["material_difference_checks"]
        )
    required_files = [
        "REPORT.md",
        "PROTOCOL.md",
        "GATES.md",
        "FEATURES.md",
        "AUTOPSY.md",
        "DELIVERABLES.md",
        "README.md",
        "PROVENANCE.md",
        "CONFIGURATION_NOTES.md",
        "SHADOW.md",
        "RESEARCH_INTERPRETATION.md",
        "prospective_freeze.json",
        "profile_library.json",
        "results/experiments.json",
        "results/research_loop.json",
        "results/monthly_eligibility.json",
        "results/primary_daily_correlations.csv",
        "results/neighbor_path_changes.csv",
    ]
    assert all((ROOT / p).is_file() for p in required_files)
    write_json(
        ROOT / "results/delivery_audit.json",
        {
            "status": "PASS",
            "matrix_runs": len(runs),
            "paths": 44,
            "central_economic_hypotheses": 12,
            "primary_treatments_including_controls": 16,
            "precision_and_fill_chronology_checks": precision_fills,
            "maximum_table_sum_error_USDT": max(errors),
            "profile_classification_counts": dict(
                Counter(e["classification"] for e in evidence.values())
            ),
            "all_path_classification_counts": dict(
                Counter(e["classification"] for e in experiments)
            ),
            "validated_profile_ids": sorted(validated),
            "required_artifacts_checked": len(required_files),
            "prospective_performance_claimed": False,
            "real_money_enabled": False,
            "note": "Costs, symbol runs, neighbors and engineering replays are not independent market samples.",
        },
    )
    print(
        json.dumps(
            {
                "delivery_audit": "PASS",
                "matrix_runs": len(runs),
                "maximum_sum_error": max(errors),
            }
        )
    )


if __name__ == "__main__":
    main()

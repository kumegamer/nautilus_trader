"""Independently verify saved evidence without executing or selecting strategies."""

import gzip
import json
from decimal import Decimal

from edge_discovery.common import ROOT, assert_frozen, candidates, config, digest, ns, write_json
from edge_discovery.metrics import metrics

EXECUTION_FILES = [
    "config.json",
    "edge_discovery/common.py",
    "edge_discovery/data.py",
    "edge_discovery/engine.py",
    "edge_discovery/__init__.py",
]


def verify():
    frozen = assert_frozen()
    cfg = config()
    signatures = frozen["source_hashes"]
    allowed = {c["id"] for c in candidates()}
    saved = {}
    original_signature_sets = set()
    for path in sorted((ROOT / "results/runs").rglob("*.json.gz")):
        with gzip.open(path, "rt") as f:
            run = json.load(f)
        assert run["candidate"] in allowed
        assert all(run["source_hashes"][p] == signatures[p] for p in EXECUTION_FILES)
        original_signature_sets.add(json.dumps(run["source_hashes"], sort_keys=True))
        total = sum(t["net_pnl"] for t in run["trades"])
        assert abs(float(run["native_balance"]) - cfg["capital_per_symbol"] - total) < 0.00001
        assert abs(float(run["reconciliation_difference"])) < 0.00001
        begin, end = map(ns, cfg["periods"][run["period"]])
        for fill in run["fills"]:
            assert begin <= fill["ts_ns"] < end
            assert fill["signal_ns"] < fill["ts_ns"]
            price, quantity = Decimal(fill["price"]), Decimal(fill["quantity"])
            spec = cfg["instrument_specs"][run["symbol"]]
            assert price % Decimal(spec["tick"]) == 0
            assert quantity % Decimal(spec["step"]) == 0
            assert Decimal(fill["slippage"]) >= 0
            fee_rate = (
                Decimal(cfg["taker_fee"]) * cfg["scenarios"][run["scenario"]]["fee_multiplier"]
            )
            assert abs(Decimal(fill["fee"]) - price * quantity * fee_rate) <= Decimal("0.00000001")
        for trade in run["trades"]:
            expected = trade["gross_pnl"] - trade["slippage"] - trade["fees"] + trade["funding"]
            assert abs(expected - trade["net_pnl"]) < 0.000001
        saved[(run["candidate"], run["symbol"], run["period"], run["scenario"])] = run
    selection = json.loads((ROOT / "results/selection.json").read_text())
    for family, decision in selection.items():
        for target in ["validation", "wf1", "wf2"]:
            for previous in decision["choices"][target]["history"]:
                assert ns(cfg["periods"][previous][1]) <= ns(cfg["periods"][target][0])
        assert all("holdout" not in c["history"] for c in decision["choices"].values())
    final = json.loads((ROOT / "results/final.json").read_text())
    assert set(final) == set(cfg["grids"])
    for family, item in final.items():
        assert item["candidate"] == frozen["representatives"][family]
        for scenario, expected in item["scenarios"].items():
            runs = [
                saved[(item["candidate"]["id"], s, "holdout", scenario)] for s in cfg["symbols"]
            ]
            assert metrics(runs) == expected
    archives = 0
    for name in [
        "preholdout_manifest.json",
        "preholdout_repairs.json",
        "holdout_manifest.json",
        "holdout_repairs.json",
    ]:
        for row in json.loads((ROOT / "data" / name).read_text()):
            assert digest(ROOT / row["path"]) == row["sha256"] == row["publisher_sha256"]
            archives += 1
    opened = json.loads((ROOT / "results/holdout_opened.json").read_text())
    assert opened["freeze_sha256"] == digest(ROOT / "results/freeze.json")
    assert opened["opened_at_utc"] >= frozen["frozen_at_utc"]
    provenance = json.loads((ROOT / "results/runtime_provenance.json").read_text())
    assert digest(provenance["native_extension"]) == provenance["native_extension_sha256"]
    result = {
        "passed": True,
        "saved_runs": len(saved),
        "verified_archives": archives,
        "original_full_execution_signature_sets": len(original_signature_sets),
        "execution_sources_all_match_freeze": True,
        "native_accounts_reconciled": True,
        "fill_precision_fees_slippage_and_causality_passed": True,
        "selection_histories_are_chronological": True,
        "final_representatives_equal_frozen_decisions": True,
        "final_metrics_recomputed_from_saved_native_runs": True,
        "publisher_checksums_verified": True,
        "native_extension_unchanged": True,
    }
    write_json(ROOT / "results/verification.json", result)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    verify()

"""Independent read-only artifact reconciliation; never runs trading simulations."""

import csv
import hashlib
import json
import math
import unittest
from collections import Counter
from decimal import Decimal
from pathlib import Path

OUT = Path(__file__).resolve().parent
BASE = OUT.parent
ROOT = BASE.parents[1]


def read(name, folder=OUT):
    return json.loads((folder / name).read_text())


def rows(name):
    with (OUT / name).open() as f:
        return list(csv.DictReader(f))


class ArtifactReconciliation(unittest.TestCase):
    def test_original_files_and_frozen_artifacts_unchanged(self):
        inputs = read("input_checksums.json")
        self.assertEqual(len(inputs), 686)
        for path, expected in inputs.items():
            self.assertEqual(
                hashlib.sha256((ROOT / path).read_bytes()).hexdigest(), expected, path
            )
        original = read("results/artifact_checksums.json", BASE)
        self.assertEqual(len(original), 685)
        for path, expected in original.items():
            self.assertEqual(
                hashlib.sha256((BASE / path).read_bytes()).hexdigest(), expected, path
            )

    def test_gate_decisions_exactly_preserve_frozen_evidence(self):
        evidence = read("results/preholdout_evidence.json", BASE)
        gates = rows("gate_decisions.csv")
        self.assertEqual(len(evidence), 14)
        self.assertEqual(len(gates), 168)
        self.assertEqual(len({(g["profile"], g["gate"]) for g in gates}), 168)
        for g in gates:
            expected = evidence[g["profile"]]["gates"][g["gate"]]
            self.assertEqual(g["frozen_result"], "PASS" if expected else "FAIL")
            self.assertEqual(g["status"] == "PASS", expected)
            self.assertTrue(json.loads(g["threshold"]))
        near = [g for g in gates if g["status"] == "NEAR_MISS"]
        self.assertEqual({g["profile"] for g in near}, {"VB48", "VB48_STOP"})
        self.assertTrue(all(g["gate"] == "profit_factor" for g in near))
        counted = Counter(g["gate"] for g in gates if g["frozen_result"] == "FAIL")
        self.assertEqual(
            dict(counted), read("preholdout_diagnosis.json")["gate_failure_counts"]
        )

    def test_outer_metrics_reconcile_to_saved_native_results(self):
        saved = read("results/all_static_results.json", BASE)
        profiles = read("preholdout_profiles.json")
        for p, d in profiles.items():
            for period, m in d["outer"].items():
                original = saved[p][period + "/base"]
                for key in (
                    "number_of_trades",
                    "net_pnl",
                    "sharpe",
                    "sortino",
                    "maximum_drawdown",
                    "fees",
                    "slippage",
                    "funding",
                ):
                    if m[key] is None or original[key] is None:
                        self.assertEqual(m[key], original[key], (p, period, key))
                    else:
                        self.assertTrue(
                            math.isclose(
                                m[key], original[key], rel_tol=1e-8, abs_tol=1e-7
                            ),
                            (p, period, key),
                        )
                self.assertAlmostEqual(
                    m["gross_pnl"] - m["fees"] - m["slippage"] + m["funding"],
                    m["net_pnl"],
                    places=6,
                )

    def test_gate_attribution_and_concentration(self):
        profiles = read("preholdout_profiles.json")
        ratio_fail, exclusion_fail = 0, 0
        for p, d in profiles.items():
            m = d["actual_gate"]
            for axis in ("symbol", "side", "regime"):
                groups = d["groups"][axis].values()
                self.assertEqual(
                    sum(g["number_of_trades"] for g in groups),
                    m["number_of_trades"],
                    (p, axis),
                )
                self.assertAlmostEqual(
                    sum(g["net_pnl"] for g in groups), m["net_pnl"], places=6
                )
            self.assertAlmostEqual(
                m["long_net"] + m["short_net"], m["net_pnl"], places=6
            )
            self.assertAlmostEqual(
                m["top10_profit"] + m["net_excluding_top10"], m["net_pnl"], places=6
            )
            ratio_fail += (
                m["top10_positive_profit_share"] is None
                or m["top10_positive_profit_share"] > 0.5
            )
            exclusion_fail += m["net_excluding_top10"] <= 0
        self.assertEqual((ratio_fail, exclusion_fail), (5, 14))

    def test_missing_evidence_is_not_invented(self):
        profiles = read("preholdout_profiles.json")
        untested = {p for p, d in profiles.items() if not d["assessed_costs"]}
        self.assertEqual(len(untested), 8)
        sealed = rows("sealed_completed_evaluation_only.csv")
        self.assertEqual(len(sealed), 42)
        for g in sealed:
            self.assertEqual(bool(g["net_pnl"]), g["profile"] not in untested)
        self.assertEqual(len([g for g in sealed if g["net_pnl"]]), 18)

    def test_actual_control_and_near_miss_only_eligibility(self):
        c = read("control_audit.json")
        self.assertEqual((c["actual_trades"], c["actual_profile_switches"]), (0, 0))
        self.assertEqual(c["actual_changes_one_market_path"], 4186)
        self.assertEqual(c["logged_records_one_cost"], 4189)
        self.assertEqual(c["actual_changes_all_three_cost_repetitions"], 12558)
        self.assertEqual(sum(c["degradation_states_base"].values()), 4107)
        self.assertEqual(set(c["degradation_states_base"]), {"INSUFFICIENT_DATA"})
        p = c["near_miss_only_diagnostic"]
        eligibility = rows("near_miss_eligibility.csv")
        self.assertEqual(len(eligibility), p["records_checked"])
        self.assertEqual(p["additional_hypothetical_switches"], 0)
        self.assertEqual(p["incremental_subsequent_net_pnl"], 0)
        self.assertEqual(p["eligible_profiles_at_final_freeze"], [])
        self.assertEqual(p["eligible_profiles_at_recorded_preholdout_requests"], [])
        self.assertEqual(p["arbitrary_fail_waivers"], 0)
        self.assertFalse(p["holdout_used_for_eligibility"])
        self.assertFalse(p["thresholds_changed"])
        for row in eligibility:
            self.assertEqual(row["eligible"], "False")
            self.assertTrue(json.loads(row["true_fail_gates"]))
            statuses = json.loads(row["gate_statuses"])
            for gate, status in statuses.items():
                if status == "NEAR_MISS":
                    self.assertEqual(gate, "profit_factor")
                    self.assertTrue(1 < float(row["profit_factor"]) < 1.05)
            self.assertLessEqual(int(row["timestamp"]), 1782864000000000000)

    def test_buy_hold_accounting_and_same_period_exposure(self):
        d = read("diagnosis_summary.json")
        t = {k: Decimal(v) for k, v in d["buy_hold_totals"].items()}
        self.assertEqual(
            t["gross"] - t["fees"] - t["slippage"] + t["funding"], t["net"]
        )
        self.assertEqual(t["net"], Decimal("15155.29048807"))
        self.assertEqual(sum(b["capital"] for b in d["buy_hold"]), 30000)
        exp = d["completed_holdout_exposure"]
        self.assertEqual(exp["TB48_SHORT"]["trades"], 6)
        self.assertEqual(exp["BUY_HOLD"]["trades"], 3)
        self.assertAlmostEqual(
            exp["TB48_SHORT"]["duration_weighted_entry_notional_to_initial_capital"],
            0.001360955183423913,
        )
        self.assertAlmostEqual(
            exp["BUY_HOLD"]["duration_weighted_entry_notional_to_initial_capital"],
            0.8987567234265549,
        )
        self.assertFalse(d["sealed_used_to_select_profile_or_parameters"])
        self.assertEqual(d["v2_proposals"], [])

    def test_autopsy_manifest(self):
        manifest = read("autopsy_checksums.json")
        for path, expected in manifest.items():
            self.assertEqual(
                hashlib.sha256((OUT / path).read_bytes()).hexdigest(), expected, path
            )
        self.assertIn("analyze.py", manifest)
        self.assertIn("explain.py", manifest)
        self.assertIn("verify.py", manifest)


if __name__ == "__main__":
    unittest.main(verbosity=2)

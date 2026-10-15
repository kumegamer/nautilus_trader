"""Render frozen results with auditable metadata-only reporting corrections.

The frozen experiment and report module remain byte-for-byte unchanged. This adapter
supplies the run's already-known symbol to reference trades before report aggregation.
No PnL, fill, order, feature, decision, research gate or promotion evidence is changed.
"""

import json
import shutil
from collections import Counter

from adaptive import report as reporting
from adaptive.common import ROOT, assert_frozen, digest, write_json
from adaptive.workflow import PRE, read_runs


def enriched_runs(periods):
    runs = read_runs(periods)
    for run in runs:
        for trade in run["trades"]:
            trade.setdefault("symbol", run["symbol"])
            trade.setdefault("profile", run["candidate"])
            trade.setdefault(
                "strategy",
                "reference" if run["candidate"] == "BUY_HOLD" else run["family"],
            )
    return runs


def main():
    assert_frozen()
    original = ROOT / "results/reporting_superseded"
    if not original.exists():
        original.mkdir()
        for name in (
            "REPORT.md",
            "results/details.json",
            "results/final.json",
            "results/profiles.json",
        ):
            path = ROOT / name
            if path.exists():
                shutil.copyfile(path, original / path.name)
    reporting.read_runs = enriched_runs
    reporting.report()
    details = json.loads((ROOT / "results/details.json").read_text())
    for system in details.values():
        for period in system.values():
            for scenario in period.values():
                groups = scenario["breakdown"]["symbol"]
                assert (
                    sum(v["number_of_trades"] for v in groups.values())
                    == scenario["metrics"]["number_of_trades"]
                )
                assert (
                    abs(
                        sum(v["net_pnl"] for v in groups.values())
                        - scenario["metrics"]["net_pnl"]
                    )
                    < 0.00001
                )
    states = Counter(
        e["new_state"]
        for run in read_runs((*PRE, "holdout"))
        if run["candidate"] == "ADAPTIVE"
        for e in run["promotions"]
    )
    final_path = ROOT / "results/final.json"
    final = json.loads(final_path.read_text())
    final["promotion_transitions_by_state"] = dict(states)
    final["successful_shadow_promotions"] = states["SHADOW"]
    write_json(final_path, final)
    profiles_path = ROOT / "results/profiles.json"
    profiles = json.loads(profiles_path.read_text())
    profiles["NO_TRADE"]["expected_trades_per_symbol_month"] = [0, 0]
    profiles["NO_TRADE"]["expected_net_r_band"] = [0, 0]
    profiles["NO_TRADE"]["expected_range_status"] = (
        "zero exposure by construction; no expectancy claim"
    )
    write_json(profiles_path, profiles)
    write_json(
        ROOT / "results/reporting_corrections.json",
        {
            "scope": "derived descriptive metadata only; experiment remains frozen and unchanged",
            "frozen_manifest_sha256": digest(ROOT / "results/freeze.json"),
            "corrections": [
                "Reference trades inherit symbol/profile/strategy from their immutable run before grouping.",
                "Assert per-symbol counts and PnL sum exactly to each system/scenario total.",
                "Distinguish CANDIDATE/REJECTED state events from successful SHADOW promotions.",
                "NO_TRADE descriptive expected frequency and R band are zero; generic frozen defaults did not affect execution.",
            ],
            "original_reports": "results/reporting_superseded",
            "runtime_source_changed": False,
            "economic_results_changed": False,
            "successful_shadow_promotions": states["SHADOW"],
        },
    )
    text = (ROOT / "REPORT.md").read_text()
    text += (
        "\n## Reporting audit correction\n\n"
        "Reference trade grouping inherits symbol/profile/strategy from each immutable run. "
        "The original generated tables are retained in results/reporting_superseded. "
        "Every per-symbol count and PnL sum is independently checked against system totals. "
        "NO_TRADE expected frequency and R band are zero by construction; generic frozen "
        "descriptive defaults never affected its zero-exposure logic. "
        f"Promotion state events comprise {dict(states)}; successful SHADOW promotions: {states['SHADOW']}. "
        "No experimental source, strategy parameters, fills, performance or decision logs changed. "
        "Exact correction scope is in results/reporting_corrections.json.\n"
    )
    (ROOT / "REPORT.md").write_text(text)
    artifacts = [
        p
        for p in ROOT.rglob("*")
        if p.is_file()
        and "__pycache__" not in p.parts
        and ".pytest_cache" not in p.parts
        and p.name != "artifact_checksums.json"
        and "raw" not in p.parts
    ]
    write_json(
        ROOT / "results/artifact_checksums.json",
        {str(p.relative_to(ROOT)): digest(p) for p in sorted(artifacts)},
    )
    reporting.verify()


if __name__ == "__main__":
    main()

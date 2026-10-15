"""Independent native ledgers, chronological decisions and frozen-reference checks."""

import gzip
import hashlib
import json
import subprocess
from decimal import Decimal

from .common import ROOT, assert_specification, config, digest, write_json
from .workflow import execution_hash


def reference_audit():
    repo = ROOT.parents[1]
    references = config()["reference_commits"]
    result = {}
    for name, commit in references.items():
        directory = (
            "adaptive_trading_v1" if name == "adaptive_v1" else "edge_discovery_v1"
        )
        paths = subprocess.check_output(
            ["git", "ls-tree", "-r", "--name-only", commit, f"evaluation/{directory}"],
            cwd=repo,
            text=True,
        ).splitlines()
        checksums = {}
        for path in paths:
            copy = repo / "work/references" / path
            content = copy.read_bytes()
            git_blob = hashlib.sha1(
                b"blob " + str(len(content)).encode() + b"\0" + content
            ).hexdigest()
            expected = subprocess.check_output(
                ["git", "rev-parse", f"{commit}:{path}"], cwd=repo, text=True
            ).strip()
            if git_blob != expected:
                raise RuntimeError(f"Read-only reference changed: {path}")
            checksums[path] = hashlib.sha256(content).hexdigest()
        tree = subprocess.check_output(
            ["git", "rev-parse", f"{commit}^{{tree}}"], cwd=repo, text=True
        ).strip()
        result[name] = {
            "commit": commit,
            "tree": tree,
            "files_verified": len(paths),
            "checksums_manifest_sha256": hashlib.sha256(
                json.dumps(checksums, sort_keys=True).encode()
            ).hexdigest(),
            "unchanged": True,
        }
    write_json(ROOT / "results/reference_audit.json", result)
    return result


def audit_runs():
    assert_specification()
    fingerprint = execution_hash()
    checked, trades, fills, switches, decisions = 0, 0, 0, 0, 0
    worst = Decimal(0)
    for path in sorted((ROOT / "results/runs").glob("*.json.gz")):
        run = json.loads(gzip.decompress(path.read_bytes()))
        if run["execution_hash"] != fingerprint:
            raise RuntimeError(f"Stale execution fingerprint: {path.name}")
        discrepancy = abs(Decimal(run["reconciliation_difference"]))
        worst = max(worst, discrepancy)
        if discrepancy > Decimal("0.00001") or run["open_position"] is not None:
            raise RuntimeError(
                f"Native account/open-position reconciliation failed: {path.name}"
            )
        nominal = sum((Decimal(str(t["net_pnl"])) for t in run["trades"]), Decimal(0))
        native = Decimal(run["native_balance"]) - Decimal(
            config()["capital_per_symbol"]
        )
        if abs(nominal - native) > Decimal("0.00001"):
            raise RuntimeError(f"Trade sum/native account disagreement: {path.name}")
        for fill in run["fills"]:
            if fill["signal_ns"] >= fill["ts_ns"]:
                raise RuntimeError("Signal must be strictly before fill")
            if (
                Decimal(fill["quantity"]) <= 0
                or Decimal(fill["fee"]) < 0
                or Decimal(fill["slippage"]) < 0
            ):
                raise RuntimeError("Invalid fill quantity or costs")
        for decision in run["decisions"]:
            end = decision.get("evidence_end_ns")
            if end is not None and end >= decision["timestamp"]:
                raise RuntimeError("Future validation evidence in controller decision")
        for t in run["trades"]:
            net = (
                Decimal(str(t["gross_pnl"]))
                - Decimal(str(t["fees"]))
                - Decimal(str(t["slippage"]))
                + Decimal(str(t["funding"]))
            )
            if abs(net - Decimal(str(t["net_pnl"]))) > Decimal("0.00001"):
                raise RuntimeError("Trade accounting identity failed")
            if t["entry_ns"] >= t["exit_ns"] or not t["exit_reasons"]:
                raise RuntimeError("Invalid trade chronology or exit attribution")
        checked += 1
        trades += len(run["trades"])
        fills += len(run["fills"])
        switches += len(run["switches"])
        decisions += len(run["decisions"])
    if checked != 351:
        raise RuntimeError(
            f"Incomplete matrix: expected 351 symbol/scenario runs, found {checked}"
        )
    eligibility = json.loads((ROOT / "results/eligibility.json").read_text())
    for e in eligibility:
        if e["end_ns"] >= e["timestamp"] or e["eligible"] != all(e["gates"].values()):
            raise RuntimeError("Invalid eligibility availability or gate reduction")
    result = {
        "runs": checked,
        "trades_including_repeated_scenarios": trades,
        "fills_including_repeated_scenarios": fills,
        "decisions": decisions,
        "switches_including_repeated_scenarios": switches,
        "maximum_native_reconciliation_difference": str(worst),
        "chronology_checks": "PASS",
        "execution_hash": fingerprint,
        "historical_status": "ALL_CONSUMED_RETROSPECTIVE_EVIDENCE",
        "live_orders": 0,
    }
    write_json(ROOT / "results/native_integrity.json", result)
    return result


def verify_manifest():
    manifest = json.loads((ROOT / "artifact_checksums.json").read_text())
    for name, expected in manifest.items():
        if digest(ROOT / name) != expected:
            raise RuntimeError(f"Artifact changed: {name}")
    return len(manifest)


if __name__ == "__main__":
    print(json.dumps(audit_runs(), indent=2))

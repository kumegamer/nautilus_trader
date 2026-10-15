"""One-time prospective bundle freeze and complete reproducibility manifest."""

import argparse
import importlib.metadata
import json
import platform
from datetime import datetime, timezone

from .common import ROOT, config, digest, specification_hashes, write_json


def freeze():
    target = ROOT / "prospective_freeze.json"
    if target.exists():
        raise RuntimeError(
            "Prospective freeze already exists; verify it or create a new version"
        )
    from nautilus_trader import _libnautilus

    versions = {
        name: importlib.metadata.version(name)
        for name in ("numpy", "pandas", "pyarrow", "pytest", "ruff", "plotly")
    }
    runtime = {
        "python": platform.python_version(),
        "platform": platform.platform(),
        "packages": versions,
        "nautilus_source_commit": config()["baseline_commit"],
        "nautilus_native_binary_sha256": digest(_libnautilus.__file__),
    }
    write_json(ROOT / "runtime_snapshot.json", runtime)
    (ROOT / "runtime-requirements.txt").write_text(
        "# Build Nautilus from baseline commit; these are the observed Python runtime pins\n"
        + "\n".join(f"{n}=={v}" for n, v in versions.items())
        + "\n"
    )
    conclusion = json.loads((ROOT / "results/conclusions.json").read_text())
    paths = sorted((ROOT / "ats").glob("*.py"))
    paths += [
        ROOT / n
        for n in (
            "config.json",
            "PROTOCOL.md",
            "GATES.md",
            "SHADOW.md",
            "ARCHITECTURE.md",
            "runtime_snapshot.json",
            "runtime-requirements.txt",
            "results/profiles.json",
            "results/eligibility.json",
            "results/predeclaration.json",
            "results/static_selection.json",
            "results/static_full_grid_selection.json",
            "data/historical_manifest.json",
            "data/historical_repairs.json",
            "data/feature_cache_manifest.json",
        )
    ]
    files = {p.relative_to(ROOT).as_posix(): digest(p) for p in paths}
    value = {
        "version": "adaptive-trading-v2",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "source_branch": "evaluation/adaptive-trading-v2",
        "baseline_commit": config()["baseline_commit"],
        "references_read_only": config()["reference_commits"],
        "files": files,
        "specification_hashes": specification_hashes(),
        "initial_shadow_eligible_profiles": conclusion[
            "prospective_shadow_eligible_profiles"
        ],
        "historical_data_status": "CONSUMED_THROUGH_2026_09",
        "prospective_status": "NOT_STARTED_NO_FORWARD_PERFORMANCE_CLAIM",
        "automatic_parameter_activation": False,
        "real_money_execution": False,
        "monthly_revalidation": "Frozen evaluator may generate new evidence for frozen profiles; availability at actual completion; proposals inert",
        "version_rule": "Any rule/profile/threshold/code modification after prospective observation requires a new version",
    }
    write_json(target, value)
    artifact_manifest()
    return value


def artifact_manifest():
    paths = [
        p
        for p in ROOT.rglob("*")
        if p.is_file()
        and p.name != "artifact_checksums.json"
        and "__pycache__" not in p.parts
        and ".pytest_cache" not in p.parts
        and not p.name.endswith(".tmp")
        and not any(
            part in ("raw", "cache", "shadow_state")
            for part in p.relative_to(ROOT).parts
        )
    ]
    manifest = {p.relative_to(ROOT).as_posix(): digest(p) for p in sorted(paths)}
    write_json(ROOT / "artifact_checksums.json", manifest)
    return manifest


def verify():
    from .audit import verify_manifest
    from .shadow import assert_freeze

    assert_freeze()
    print(f"Verified prospective freeze and {verify_manifest()} artifact checksums")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("create", "verify"))
    args = parser.parse_args()
    if args.action == "create":
        value = freeze()
        print(
            json.dumps(
                {
                    k: value[k]
                    for k in (
                        "version",
                        "created_utc",
                        "initial_shadow_eligible_profiles",
                    )
                },
                indent=2,
            )
        )
    else:
        verify()

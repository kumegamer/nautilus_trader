"""Bind the delivered evidence and future protocol to the actual tested runtime."""

import argparse
import importlib.metadata
import json
import platform
import subprocess
from datetime import datetime, timezone

from alpha.common import ROOT, digest, write_json
from alpha.workflow import verify_freeze


def verify_runtime():
    from nautilus_trader import _libnautilus

    runtime = json.loads((ROOT / "results/runtime_snapshot.json").read_text())
    assert platform.python_version() == runtime["python"], "Python runtime drift"
    for package, version in runtime["packages"].items():
        assert importlib.metadata.version(package) == version, (
            f"Dependency drift: {package}"
        )
    assert digest(_libnautilus.__file__) == runtime["native_binary_sha256"], (
        "Native engine binary drift"
    )
    core_changes = subprocess.check_output(
        [
            "git",
            "diff",
            "--name-only",
            runtime["baseline_commit"],
            "--",
            ".",
            ":(exclude)evaluation/**",
            ":(exclude)work/**",
        ],
        text=True,
    ).strip()
    assert not core_changes, "Core source drift from the tested baseline"
    return runtime


def freeze_confirmation():
    verify_freeze()
    runtime = verify_runtime()
    prior = json.loads((ROOT / "prospective_freeze.json").read_text())
    files = dict(prior["files"])
    for name in (
        "prospective_freeze.json",
        "SHADOW.md",
        "results/runtime_snapshot.json",
        "data/historical_repairs.json",
        "results/predeclaration.json",
        "reporting/verify_delivery.py",
        "reporting/diagnostics.py",
        "results/experiments.json",
        "CONFIGURATION_NOTES.md",
    ):
        files[name] = digest(ROOT / name)
    write_json(
        ROOT / "prospective_confirmation_freeze.json",
        {
            "created_utc": datetime.now(timezone.utc).isoformat(),
            "files": files,
            "runtime": runtime,
            "initial_eligible_profiles": prior["initial_eligible_profiles"],
            "historical_evidence": "CONSUMED_RETROSPECTIVE_ONLY",
            "prospective_status": "NOT_STARTED",
            "real_money_enabled": False,
            "automatic_activation": False,
            "purpose": "Add explicit future-protocol and runtime bindings; no profile or gate change",
        },
    )


def verify():
    verify_freeze()
    runtime = verify_runtime()
    frozen = json.loads((ROOT / "prospective_confirmation_freeze.json").read_text())
    for path, expected in frozen["files"].items():
        assert digest(ROOT / path) == expected, f"Confirmation freeze changed: {path}"
    assert runtime == frozen["runtime"]
    files = json.loads((ROOT / "artifact_checksums.json").read_text())
    for path, expected in files.items():
        assert digest(ROOT / path) == expected, f"Delivery artifact changed: {path}"
    print(
        json.dumps(
            {
                "runtime_verified": True,
                "confirmation_freeze_files": len(frozen["files"]),
                "delivery_artifacts": len(files),
                "real_money_enabled": False,
            }
        )
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--freeze-confirmation", action="store_true")
    args = parser.parse_args()
    if args.freeze_confirmation:
        freeze_confirmation()
    else:
        verify()

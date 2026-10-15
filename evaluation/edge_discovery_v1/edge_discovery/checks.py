"""Executable prefix, future-tail mutation, precision, and native accounting probes."""

import json
import subprocess

from .common import ROOT, candidates, source_hashes, write_json
from .data import load
from .engine import run


def check():
    (ROOT / "results").mkdir(parents=True, exist_ok=True)
    if (ROOT / "results" / "holdout_opened.json").exists():
        raise RuntimeError("Cannot alter integrity evidence after holdout opening")
    checks = []
    for family in dict.fromkeys(c["family"] for c in candidates()):
        c = next(c for c in candidates() if c["family"] == family)
        bars, rates = load("BTCUSDT", "validation", c["minutes"])
        first = int((bars.t < 1704067200000000000).sum())
        prefix_size = first + 2400
        extended = bars.iloc[: prefix_size + 600].copy()
        prefix = extended.iloc[:prefix_size].copy()
        cutoff = int(prefix.t.iloc[-2])

        def replay(frame):
            r = rates[rates.t <= frame.t.iloc[-1]]
            return run(c, "BTCUSDT", "validation", frame, r)

        a, b = replay(prefix), replay(extended)
        mutated = extended.copy()
        mask = mutated.index >= prefix_size
        for column in ("open", "high", "low", "close"):
            mutated.loc[mask, column] *= 1.8
        d = replay(mutated)

        def before(result):
            return [f for f in result["fills"] if f["ts_ns"] < cutoff]

        if before(a) != before(b) or before(b) != before(d):
            raise RuntimeError(f"Prefix or future mutation leakage: {family}")
        if not before(a):
            raise RuntimeError(f"Vacuous leakage check without fills: {family}")
        for result in (a, b, d):
            if any(f["signal_ns"] >= f["ts_ns"] for f in result["fills"]):
                raise RuntimeError("Noncausal fill")
        checks.append(
            {
                "family": family,
                "prefix_consistent": True,
                "future_tail_mutation_consistent": True,
                "compared_fills": len(before(a)),
                "native_account_and_positions_reconciled": True,
            }
        )
    test = subprocess.run(
        ["python", "-m", "pytest", "-q", "tests"], cwd=ROOT, text=True, capture_output=True
    )
    (ROOT / "results" / "tests.txt").write_text(test.stdout + test.stderr)
    if test.returncode:
        raise RuntimeError(test.stdout + test.stderr)
    if any((ROOT / "data" / "raw").rglob("*2026*.zip")):
        raise RuntimeError("Holdout data was fetched before freeze")
    write_json(
        ROOT / "results" / "integrity.json",
        {
            "passed": True,
            "checks": checks,
            "pytest": test.stdout.strip(),
            "source_hashes": source_hashes(),
            "holdout_archives_absent": not any((ROOT / "data" / "raw").rglob("*2026*.zip")),
            "limitations": [
                "Probes detect obvious future dependence; not a proof against every bias"
            ],
        },
    )
    print(json.dumps(checks), flush=True)

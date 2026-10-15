# Reproduce the frozen evidence

Use the exact upstream git revision and dependency locks in results/freeze.json,
results/runtime_provenance.json and upstream_locks/. Build the unchanged NautilusTrader
v2 package in the repository's python/.venv. The supplied experiment used the nextest
(unoptimized) build profile, high precision, and Python 3.13. Activate that environment
and run commands from this evaluation directory.

The code/results bundle and the public-data bundle preserve their paths relative to
this directory. Extract both here. Original result files, source signatures and the
single-use holdout marker are evidence: keep them intact.

```bash
python verify_artifacts.py
python replay_frozen.py --family trend_breakout --scenario base
# Optional full reproduction of all four frozen strategies and cost scenarios:
python replay_frozen.py
```

Replay writes only under work/replay, compares native trade counts and monetary totals
with the published holdout, and never ranks or replaces a strategy. It consumes an
already-opened historical sample; it is not a new independent OOS experiment. Do not
remove the one-use marker to claim another fresh holdout.

The artifact verifier also compares the loaded native extension with the original
binary checksum. That check requires the original runtime/path. For a separately
compiled platform, use the pinned revision/locks and the numerical replay comparison;
a different compiled binary cannot have the original binary checksum.

For reproducing the entire selection computation, use the source and preholdout raw
records in a separate copy, retaining the original frozen evidence. The README stage
commands describe a clean run. An exact rerun of already known historical data verifies
reproduction rather than providing another unseen sample.

Raw execution records retain the full source signatures observed when they ran. The
multi-period summary correction changed metrics, reporting and selection code, not
config.json or native execution/data code. Resume validates the execution-critical
sources explicitly. The freeze seals current corrected code and every original record;
no native record has been retagged to conceal its original signature.

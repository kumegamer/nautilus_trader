# NautilusTrader-only edge discovery

Self-contained local research under `evaluation/edge_discovery_v1`, on branch
`evaluation/edge-discovery-v1`. No EdgeLab dependency, Nautilus core edits, live clients,
private API credentials, or live trading configuration.

Read `PROTOCOL.md` and `config.json` before running. All dates are UTC. Full requested
metrics and family classifications are in `REPORT.md`, `results/metrics.csv`, and
`results/final.json` after execution. A family may correctly receive NO_EDGE.

## Environment

Use the repository's uv project at `python/.venv`, never a root virtualenv. This checkout
uses NautilusTrader v2.0.0rc7 (PyO3 v2 API); v1 wheels are not API-compatible. Build the
unchanged checkout using `CONTRIBUTING.md` and the locked `python/uv.lock`/`Cargo.lock`.
The run records the exact git base, Python, Nautilus, pandas and numpy versions in
`results/freeze.json`; `runtime-requirements.txt` records installed package pins.

In the supplied managed environment, first run:

```bash
source /workspace/toolchains/activate-nautilus.sh
cd /workspace/nautilus_trader/evaluation/edge_discovery_v1
```

For another machine, activate its existing `python/.venv` and enter this directory.
Public download requires HTTPS access to `data.binance.vision`; the execution stages
are offline once downloads are complete.

## Stages

```bash
python -m edge_discovery.workflow download
python -m pytest -q tests
python -m edge_discovery.workflow preholdout
python -m edge_discovery.workflow integrity
python -m edge_discovery.workflow freeze
python -m edge_discovery.workflow holdout
python -m edge_discovery.workflow report
```

`preholdout` resumes raw executions only when the configuration and execution/data source
hashes match. Each raw run retains its original full source signature. Reporting/metric
corrections recompute summaries and selection from those unchanged native records; they do
not relabel the original execution signature. Execution/data/config changes require reruns.
The final freeze hashes every current source, all raw evidence, and the rebuilt decisions. `freeze` requires passing integrity
checks and writes the immutable decision/evidence hashes. `holdout` verifies them,
creates an exclusive one-use marker *before any download*, downloads only January–June
2026 archives, and evaluates all four frozen representatives under all four cost
scenarios. A second invocation fails. A crash after opening leaves the marker and must
be investigated; deleting it does not create a fresh independent holdout. Fresh-machine
reproduction can replay the published frozen decisions in a separate artifact copy,
but cannot constitute another new OOS experiment.

## Artifacts

- `data/*manifest.json`: original URLs, sizes, publisher and local SHA256 hashes.
- `data/raw/`: retained original ZIPs and publisher checksum sidecars (gitignored).
- `data/audits/`: completeness, timestamp and funding valuation proxy counts.
- `results/runs/`: gzip JSON with every fill, trade, daily equity, native account
  reconciliation, and source signature.
- `results/grid_summary.json`: all 32 candidates across preholdout periods.
- `results/selection.json`: research/validation/WF choices, neighbor performance,
  stress runs, promotion gates, and rejection reasons.
- `results/freeze.json`: decisions, exact runtime/base revision and evidence hashes.
- `results/holdout_opened.json`: one-time opening timestamp and freeze checksum.
- `results/final.json`, `metrics.csv`, `artifact_checksums.json`: final evidence.
- `results/integrity.json`, `tests.txt`: causal prefix/mutation checks and tests.

No strategy is chosen by the holdout; reporting preserves family order and frozen
representatives. These historical classifications are not forward-validated profits.

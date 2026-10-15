# Nautilus Adaptive Trading System v1

Historical research only. Real-money execution is not implemented or enabled.
All adaptive modules live here; NautilusTrader core is unchanged. Prior research is read-only
at evaluation/edge-discovery-v1, commit 3c669f91dd195266107a2f5b77c5c991565840a8.
Development baseline: de794053685c3a3b7ae74eb995e2b31215786b25.
Persistence branch: evaluation/adaptive-trading-v1. Code, reports, tests, logs and result
metadata are versioned on this isolated branch. See PERSISTENCE.md for storage and verification.

Read REPORT.md for the conclusion and PROTOCOL.md for the predefined experiment.
Exact profile library, results, costs and all attempted hypotheses are under results/.

## Reproduce

Use the repository's uv-managed environment at python/.venv. See the baseline's
CONTRIBUTING.md and docs/developer_guide/environment_setup.md to build its Rust extension.
Do not silently replace that extension with a different Nautilus release.
The exact package and extension hashes are in results/environment.json; upstream locks are copied
under upstream_locks/. runtime-requirements.txt pins the research Python dependencies.

From the repository root:

```bash
export PYTHONPATH=evaluation/adaptive_trading_v1
python/.venv/bin/python -m adaptive.workflow verify
python/.venv/bin/python -m adaptive.reproduce replay --profile TB48_SHORT --period validation
python/.venv/bin/python -m adaptive.reproduce replay --profile ADAPTIVE --period holdout
```

Raw market archives and their downloaded sidecars are excluded from Git. The committed manifests
contain every exact URL and publisher SHA256. On a fresh clone, restore them before full verification
or replay (read-only public network):

```bash
python/.venv/bin/python -m adaptive.reproduce restore
python/.venv/bin/python -m adaptive.workflow verify
```

A complete fresh experiment in a separate output copy runs these stages in order:

```bash
python/.venv/bin/python -m adaptive.workflow download
python/.venv/bin/python -m adaptive.workflow preholdout
python/.venv/bin/python -m adaptive.workflow tests
python/.venv/bin/python -m adaptive.workflow freeze
python/.venv/bin/python -m adaptive.workflow holdout
python/.venv/bin/python -m adaptive.reproduce provenance
python/.venv/bin/python -m adaptive.workflow report
python/.venv/bin/python evaluation/adaptive_trading_v1/render_audited_report.py
python/.venv/bin/python -m adaptive.workflow verify
```

A reproduction does not make an already observed holdout pristine again. Never tune parameters
against July–September 2026 after opening it. Use a new untouched future period for v2.
Cached existing runs are resumed, not recomputed; to replay a specific frozen result use replay.
For a new experiment, choose a separate directory with no results or raw holdout files.
Independent cost scenarios may run as separate processes, each preserving period order.

## Audit artifacts

- results/final.json: classification, failed gates, static comparison and v2 recommendation.
- results/details.json and metrics.csv: all four systems, all periods, three cost scenarios.
- results/all_static_results.json: all 14 attempted profiles, including unsuccessful experiments.
- results/trades.csv: native fill-derived trade ledger, PnL, costs, signed funding, MAE/MFE in USDT.
- results/events/: complete decisions, switches, degradation, research, state transitions in JSONL/CSV.
- results/runs/: per-run native fills, trade/position accounting reconciliation and controller state.
- results/preholdout_evidence.json: timestamped profile gates, purged internal splits, neighbors and bands.
- results/freeze.json: exact source/threshold/static selection and preholdout evidence hashes.
- results/holdout_opened.json: opening timestamp bound to the freeze hash.
- data/*manifest.json, publisher CHECKSUM sidecars and data/audits/: data provenance and integrity.
- results/artifact_checksums.json: every source/report/evidence artifact except raw publisher archives,
  whose hashes are recorded separately in the manifests and verified too.
- results/development_superseded/: retained pre-freeze development outputs, excluded from conclusions.
- results/tests.txt/json, lint.txt and replay_checks.txt: validation evidence.

## Safety and limits

The research agent interface returns declared proposals only. An offline rule-based implementation
ships with v1; there is no external model connection. A future model implements ResearchAgent.propose
and receives structured diagnostics; trusted research code, not model output, supplies promotion
metrics. Profiles are frozen dataclasses. Live eligibility transitions are rejected. Material failures
quarantine and disable profiles, requiring a new passed validation cycle. The process is not a security
sandbox against arbitrary malicious Python code.

Only a finite predeclared hypothesis budget is evaluated. The adaptive system can abstain throughout
history if no candidate passes. That is safe behavior, not positive economic evidence. Historical
shadow eligibility is not forward paper-trading validation. Scheduled period flattening, OHLCV execution
proxies, heuristic regime confidence and the three-symbol universe limit inference.

## Reporting correction

The frozen report module omits symbol metadata on reference trades. The audited reporting
adapter above supplies the immutable parent run metadata before grouping, checks that all
symbol subtotals sum to each system total, and explicitly counts successful promotions.
It also corrects generic descriptive NO_TRADE defaults to zero expected frequency and zero R.
Original generated reports are retained; no experimental source or economic result changes.
See results/reporting_corrections.json. Re-render through the audited adapter after workflow report.

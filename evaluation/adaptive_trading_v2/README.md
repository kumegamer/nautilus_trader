# Nautilus Adaptive Trading System v2

New research experiment on branch `evaluation/adaptive-trading-v2`, based directly
on develop `de794053685c3a3b7ae74eb995e2b31215786b25`.
Read REPORT.md for the results and five requested conclusions. ARCHITECTURE.md
maps V1 failures to the implementation; PROTOCOL.md and GATES.md are predeclared.

All historical data through September 2026 are CONSUMED. Historical results are
RETROSPECTIVE_EVIDENCE. No reused historical holdout is called untouched, no
ROBUST_EDGE is declared, and no real-money execution or private API key exists.
The reference branches remain read-only, unmerged and unchanged.

## Contents

| Artifact | Purpose |
|---|---|
| REPORT.md | Full results, qualifications and final conclusions |
| DELIVERABLES.md | Complete request-to-artifact coverage and unresolved limitations |
| PROTOCOL.md / GATES.md / config.json | Hashed hypotheses, regimes, exits, gates and rolling chronology |
| ARCHITECTURE.md | Module diagram, V1 lessons, engineering corrections and limitations |
| results/predeclaration.json | Specification hashes recorded before scoring |
| results/profiles.json | Six directional profiles, NO_TRADE and 12 non-promotable neighbors |
| results/eligibility.json / validation_gates.csv | Every chronological gate record, evidence window, stress, bootstrap and failure |
| results/static_selection.json | Comparator selected from 2024 information only |
| results/system_comparisons.* | Static/adaptive/cash/passive risk, exposure, capital, costs and activity |
| results/walk_forward_monthly.csv | 21 subsequent monthly folds under three costs |
| results/charts/ | Offline native equity/exposure and exit-policy comparisons |
| results/profile_results.csv | All central and neighbor primary-policy results |
| results/exit_policy_results.csv | Complete four-policy counterfactuals under all costs |
| results/post_exit_excursions.csv | Descriptive 4h/24h/96h marks after interrupted exits |
| results/per_symbol_results.csv / system_per_symbol.csv | Symbol-level central-profile and comparison-system metrics |
| results/long_short_regime_decomposition.csv | Realized side/regime/profile attribution |
| results/profile_switches.jsonl / profile_decisions.jsonl | Auditable eligible sets, reasons, confidence and state |
| results/regime_statistics.json / regime_switches.csv | Unique raw/stable regime histories and duration statistics |
| results/edge_decay.jsonl / research_triggers.jsonl | Rolling performance/execution state and proposal-only triggers |
| results/research_proposals.json | Inert structured example research proposals |
| results/trades.csv / runs/*.json.gz | Trade diagnostics and full native ledgers for every retained run |
| results/native_integrity.json / reference_audit.json | Independent native accounting/chronology and frozen-source checks |
| results/shadow_validation_prefix_audit.json / verification/ | Exact continuous historical-prefix equivalence and final check logs |
| data/historical_manifest.json | Exact publisher archive hashes, URLs and sizes for consumed data |
| data/feature_cache_manifest.json | Reproducible causal feature/bar/rate cache hashes |
| prospective_freeze.json | Frozen code, rules, initial eligibility and runtime binding |
| artifact_checksums.json | Complete saved-artifact SHA256 manifest, excluding raw/cache bytes |
| SHADOW.md / deployment/ | Public-data prospective runner and persistent scheduling templates |

Full native runs retain fill prices, reference prices, exact decimal costs, signal
and fill timestamps, position IDs, funding transfers, trade PnL, daily equity,
exposure, decisions and switches. Repeated scenarios are not independent samples.
The raw/cache directories are optional local materializations, bound by manifests.

## Environment and reproduction

Use the repository at the baseline commit above and its uv-managed `python/.venv`.
Do not create a root `.venv`. Follow the baseline environment setup guide; use
`make build` for an optimized native engine. Preserve `Cargo.lock`,
`rust-toolchain.toml` and `python/uv.lock`. `runtime_snapshot.json` records the
observed Python dependency versions and native binary checksum. No core changes
are needed. Runtime pins supplement, rather than replace, the repository locks.

From repository root, on a copy of the frozen bundle:

```bash
export PYTHONPATH=evaluation/adaptive_trading_v2
python/.venv/bin/python -m ats.freeze verify
python/.venv/bin/python -m ats.restore
python/.venv/bin/python -m ats.workflow prepare
python/.venv/bin/python -m ats.workflow static --workers 3
python/.venv/bin/python -m ats.workflow evidence
python/.venv/bin/python -c 'from ats.report import static_selection; print(static_selection()["profile"])'
python/.venv/bin/python -m ats.workflow adaptive --workers 3
python/.venv/bin/python -m ats.report
python/.venv/bin/python -m ats.charts
python/.venv/bin/python -m ats.audit
python/.venv/bin/pytest -q -c /dev/null evaluation/adaptive_trading_v2/tests
python/.venv/bin/ruff check evaluation/adaptive_trading_v2/ats evaluation/adaptive_trading_v2/tests
python/.venv/bin/ruff format --check evaluation/adaptive_trading_v2/ats evaluation/adaptive_trading_v2/tests
```

The first command verifies the distributed evidence before reproduction. Retained
matching runs are cached by source/input fingerprint. To force independent reruns,
move `results/runs/` aside in a separate reproduction copy; do not erase the frozen
delivered evidence. Financial/event comparisons are deterministic; execution logs
and wall-clock completion metadata need not be byte-identical. Test fixtures are
engineering evidence and are never counted as market performance.

The matrix is 36 treatments x 3 symbols x 3 costs = 324 native static runs,
plus adaptive/cash/passive x 3 symbols x 3 costs = 27 native comparison runs.
All candidate rules and numerical gates were declared before scoring. No monthly
account resets or post-result threshold search are permitted.

## Read-only reference verification

Reference snapshots can be restored without checking out or merging their branches:

```bash
mkdir -p work/references
git archive 8acc5c4c3138b8057dc1da9f853b9a3a4bb9c4e9 evaluation/adaptive_trading_v1 | tar -x -C work/references
git archive 3c669f91dd195266107a2f5b77c5c991565840a8 evaluation/edge_discovery_v1 | tar -x -C work/references
python/.venv/bin/python work/references/evaluation/adaptive_trading_v1/autopsy/verify.py
python/.venv/bin/python -c 'from ats.audit import reference_audit; print(reference_audit())'
```

The extraction is scratch evidence only; no V1 path is added to the V2 branch.
No reference result, report, config, checksum or strategy is rewritten.

## Prospective operation

See SHADOW.md. The first forward collection starts a distinct, immutable observation
journal after checksum verification. Historical warmup is not forward performance.
The minute collector and monthly frozen-profile evaluator run separately. Proposals
remain inert; new gate evidence for unchanged profiles is available only on actual
completion. Changes to frozen rules require a new version and forward period.
This bundle does not deploy a server or claim prospective profitability.

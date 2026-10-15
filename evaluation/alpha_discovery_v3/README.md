# Nautilus Alpha Discovery v3

Standalone library discovery on `evaluation/alpha-discovery-v3`, based directly on
`develop` at de794053685c3a3b7ae74eb995e2b31215786b25. No reference branch merged.
Read REPORT.md for the outcome; profile_library.json contains only validated
historical profiles. All history through September 2026 was already consumed.

This bundle cannot enable live trading. It imports only Nautilus backtest APIs,
uses public archive GETs, and has no credential or live order configuration.

## Reproduce

Use the baseline repository and its uv-managed `python/.venv` (not a root venv).
The baseline runtime is already built in this workspace. Runtime versions and
baseline commit are in results/runtime_snapshot.json; repository locks remain
unchanged. Source reuse and changes are documented in PROVENANCE.md.

From repository root, in a separate reproduction copy of this bundle:

```bash
export PYTHONPATH=evaluation/alpha_discovery_v3
python/.venv/bin/python evaluation/alpha_discovery_v3/reporting/verify_delivery.py
python/.venv/bin/python -m alpha.restore
python/.venv/bin/python -m alpha.workflow prepare
python/.venv/bin/pytest -q -c /dev/null evaluation/alpha_discovery_v3/tests
python/.venv/bin/ruff check evaluation/alpha_discovery_v3/alpha evaluation/alpha_discovery_v3/tests
python/.venv/bin/ruff format --check evaluation/alpha_discovery_v3/alpha evaluation/alpha_discovery_v3/tests
python/.venv/bin/python -c 'from alpha.audit import causal_history_audit; print(causal_history_audit())'
python/.venv/bin/python -m alpha.workflow freeze
python/.venv/bin/python -m alpha.workflow run --workers 3
python/.venv/bin/python -m alpha.workflow report
python/.venv/bin/python evaluation/alpha_discovery_v3/reporting/diagnostics.py
python/.venv/bin/python evaluation/alpha_discovery_v3/reporting/charts.py
python/.venv/bin/python evaluation/alpha_discovery_v3/reporting/delivery_audit.py
python/.venv/bin/python evaluation/alpha_discovery_v3/reporting/verify_delivery.py --freeze-confirmation
python/.venv/bin/python -c 'from alpha.report import checksum_artifacts; checksum_artifacts()'
python/.venv/bin/python -m alpha.workflow verify
python/.venv/bin/python evaluation/alpha_discovery_v3/reporting/verify_delivery.py
```

Verify the distributed artifact checksums before reproducing. `prepare` deterministically
rebuilds data/features and past-only models. Fresh runtime timestamps may differ;
financial paths are deterministic. Retained matching runs are cached by source and
input fingerprint. To execute them independently, move results/runs aside in the
reproduction copy, preserving the delivered evidence. Never rewrite the frozen
reference branches or this delivered freeze to hide a failed experiment.

The 315 raw archives are restorable from data/historical_manifest.json against
both frozen V2 and publisher SHA256s. Raw/cache materializations are ignored by
git and excluded from the portable deliverable; their manifests are included.
No missing bar is forward-filled. Complete-grid/OHLC/funding audits are in data/audits.

## Artifacts

- PROTOCOL.md, GATES.md, FEATURES.md: finite plan, exact gates and causal dictionary.
- AUTOPSY.md, PROVENANCE.md: read-only reference findings and execution reuse.
- results/predeclaration.json: source/config/profile freeze before candidate scoring.
- results/experiments.json: every attempted path, costs, metrics and rejection reason.
- results/profile_evidence.json: exact profile classifications, gates and bootstrap.
- results/profile_results.csv: OOS mechanics, costs, risk and activity; development metrics are in experiments.json.
- results/per_symbol_results.csv and long_short_regime_results.csv: decompositions.
- results/walk_forward_quarterly.csv and monthly_contributions.csv: chronological paths.
- results/monthly_eligibility.json: matured past-only pseudo-live admission records.
- results/ml_training.json and ml_vs_rules.csv: past-only fits and baseline comparison.
- results/research_loop.json: diagnoses, fixed followups and inert next-version proposals.
- results/trades_base.csv and runs/*.json.gz: native trades, fills, funding, equity and exact financials.
- results/causality_audit.json, native_integrity.json, final_verification.json: integrity.
- prospective_freeze.json, profile_library.json: immutable future-shadow handoff.
- REPORT.md, DELIVERABLES.md: results and scope coverage.

The study is persisted on `evaluation/alpha-discovery-v3` with explicit user
authorization. Raw archives and caches remain excluded from Git; reproducible
code, manifests, logs, results and frozen evidence are retained. No PR is opened.

The supplementary delivery verifier binds the tested native binary and dependencies,
SHADOW.md, and the original prospective bundle in prospective_confirmation_freeze.json.
Runtime drift fails closed before reproduction. Reporting diagnostics in reporting/
have no strategy-generation, gate-changing or activation authority.

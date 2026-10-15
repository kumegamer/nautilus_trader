# Adaptive Trading v1 failure autopsy

Read `conclusions.md` for the twelve requested answers and `REPORT.md` for all
14 profile dossiers, exact gate thresholds, observations, chronological metrics,
cost results, concentrations, and the detached completed sealed evaluation.

This analysis reads existing result artifacts from commit
`8219e2f8747d77ece56398f8f150bd475dbe8b0a`. It does not invoke NautilusTrader,
download data, optimize parameters, create strategies, edit thresholds, or alter
original evidence. Only this directory is written. No new holdout run is performed.

From the repository root, using the existing project environment:

```bash
python/.venv/bin/python evaluation/adaptive_trading_v1/autopsy/analyze.py
python/.venv/bin/python evaluation/adaptive_trading_v1/autopsy/verify.py
python/.venv/bin/ruff check evaluation/adaptive_trading_v1/autopsy/
python/.venv/bin/ruff format --check evaluation/adaptive_trading_v1/autopsy/
```

The eight independent artifact-reconciliation checks verify the original 685-file
artifact manifest and all 686 tracked input files, all 168 gate decisions against
frozen evidence, native metric reconciliation, decomposition/accounting identities,
missing experiment coverage, actual regime counts, the NEAR_MISS-only diagnostic,
buy-and-hold economics/exposure, and the new autopsy manifest.

Machine-readable tables:

- `gate_decisions.csv`: exact frozen PASS/FAIL and descriptive status for 168 gates.
- `profile_period_metrics.csv`: outer native and internal realized-attribution metrics.
- `profile_groups.csv`: purged-gate side, symbol and regime decompositions.
- `cost_results.csv`: existing 1x/1.5x/2x experiments; absent tests remain absent.
- `month_contributions.csv`: monthly contribution attribution.
- `sealed_completed_evaluation_only.csv`: already-produced final aggregates only.
- `near_miss_eligibility.csv`: all 14 final-freeze and 378 preholdout request records.
- `actual_regime_transitions.csv`: actual changes on one adaptive market path.
- `exit_regime_coincidence.csv`: descriptive coincidence, not an exit counterfactual.
- `neighbor_timing_overlap.csv`: saved central/neighbor trade-timing comparisons.
- `risk_adjusted_comparison.csv`: frozen adaptive/static/reference metrics by period.

The original promotion gates contain no NEAR_MISS state. The audit annotation
means a failed PF gate with `1 < PF < 1.05`; it was established using preholdout
results before the user's clarification. Accepting only this annotation never
waives any true FAIL and admits no profile. Strictly accepting only NEAR_MISS
states recorded in the original experiment also admits no profile, because there
were none. Neither interpretation changes subsequent performance.

`input_checksums.json` binds original inputs. `autopsy_checksums.json` binds this
directory's source and generated artifacts, excluding itself and Python caches.
`audit_integrity.json` records the unchanged input commit and zero new runs/edits.
The original classification remains `ADAPTIVE_NO_EDGE`. No v2 design is proposed.

# Delivery coverage

The final classification is recorded in REPORT.md and results/conclusions.json.
All work is confined to Alpha Discovery v3; reference commits and core are unchanged.

| Requirement | Reviewable implementation / evidence |
|---|---|
| Prior failures and economic hypotheses | AUTOPSY.md; PROTOCOL.md; alpha/profiles.py |
| Finite AI scientist loop, no promotion authority | alpha/research.py; results/research_loop.json; per-run research_observation |
| Structurally different families and separate sides | Twelve economic profiles across six families; raw and logistic controls |
| Causal 5m/15m/1h/4h and intermarket features | FEATURES.md; alpha/features.py; results/causality_audit.json |
| Taker imbalance and public funding | data.py; public publisher manifests; feature_domain_audit.json; native funding ledgers |
| Separate entry and exit research | alpha/strategy.py; four full MHT exit interventions in profile_results.csv |
| Simple ML versus rules | alpha/ml.py; ml_training.json; ml_vs_rules.csv; no random shuffle |
| Chronological development, validation and pseudo-live | experiments.json development/OOS; walk_forward_quarterly.csv; monthly_eligibility.json |
| Deterministic native execution and realistic costs | alpha/native.py; three independently rerun cost scenarios; exact decimal financials |
| Sample, symbol/side/regime decomposition | profile_evidence.json; per_symbol_results.csv; long_short_regime_results.csv |
| Stability, concentration, resampling and turnover | profile_evidence.json; profile_results.csv; monthly_contributions.csv; neighbor_path_changes.csv; primary_daily_correlations.csv |
| All attempted paths and failures | experiments.json; 396 retained native matrix runs; research_loop.json |
| Machine-readable validated library | profile_library.json; empty means no validated profile, never forced success |
| Prospective evidence boundary | SHADOW.md; prospective_freeze.json; forward performance NOT_STARTED |
| Frozen references preserved | reference_audit.json; reference_final_audit.json; V2 prospective SHA256 verification |
| Reproducibility and validation | README.md; runtime_snapshot.json; data/cache manifests; tests.txt; artifact_checksums.json; final_verification.json |

The matrix contains 396 market-path executions; fixture, prefix-audit and duplicate
performance-probe executions are engineering checks, not additional alpha hypotheses
or independent performance observations. No strategy parameters or gates changed
after scoring began. No production credentials, real-money orders, controller
activation, persistent server deployment, merges or PR interactions. Persistence
on `evaluation/alpha-discovery-v3` is explicitly authorized by the user.

Historical validation cannot establish future edge or real depth/latency/capacity.
The future adaptive-controller experiment remains separate. An empty initial library
permits only observation of future data. Broader survivor-bias assessment and actual
forward confirmation remain unproven.

RESEARCH_INTERPRETATION.md provides profile-specific failure diagnoses and inert next
experiments. CONFIGURATION_NOTES.md identifies unused compatibility metadata. The
supplementary runtime verifier and prospective_confirmation_freeze.json bind the
actual native binary, dependencies, forward protocol and enriched experiment registry.

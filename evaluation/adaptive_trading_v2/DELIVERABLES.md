# V2 delivery coverage

This is an implementation and retrospective experiment, with negative admission
results. Delivering the controller does not establish its economic usefulness.

| Requested deliverable | Saved evidence / implementation | Result or limit |
|---|---|---|
| Architecture and V1 lessons | ARCHITECTURE.md | V1 references and Nautilus core unchanged |
| Predefined hypotheses | PROTOCOL.md; results/predeclaration.json | Hashed before scoring; consumed history only |
| Regime definitions | PROTOCOL.md; ats/regime.py | Causal confidence, persistence, hysteresis, dwell and history |
| Regime transition statistics | results/regime_statistics.json; regime_switches.csv | Unique market paths; short duration is not verified error |
| Compact strategy library | results/profiles.json; ats/profiles.py | Six directional central profiles, 12 distinct neighbors, cash |
| Entry versus exit experiment | results/exit_policy_results.csv; post_exit_excursions.csv | Four predeclared policies; alternative-policy promotion remains unvalidated |
| Validation-gate rationale | GATES.md; results/validation_gates.csv | No post-result waiver; skew-aware concentration diagnostics |
| Chronological walk-forward | results/eligibility.json; walk_forward_monthly.csv | Prior 365 days, seven-day embargo, boundary purging |
| Adaptive controller results | results/system_comparisons.*; ats/controller.py | Zero admissions and zero adaptive trades; economic exercise failed |
| Exposure and risk normalization | results/system_comparisons.*; profile_results.csv | Capital, volatility, drawdown, exposure, turnover and risk ratios |
| Cost stress | results/profile_results.csv; exit_policy_results.csv; system_comparisons.* | Base, 1.5x and 2x fees/slippage; signed observed funding |
| Per-symbol results | results/per_symbol_results.csv; system_per_symbol.csv | BTCUSDT, ETHUSDT and SOLUSDT |
| Long/short decomposition | results/long_short_regime_decomposition.csv | Independent profile directions and entry regimes |
| Profile switches and decisions | results/profile_switches.jsonl; profile_decisions.jsonl | Switch file is correctly empty; decisions explain NO_TRADE |
| Regime-switch logs | results/regime_switches.csv; *_regime_transitions.json | Raw and stable histories retained |
| Edge-decay monitoring | results/edge_decay.jsonl; research_triggers.jsonl | Multiple time, count, regime, risk and execution inputs |
| AI proposal-only interface | ats/research.py; results/research_proposals.json | Inert proposals; mandatory pipeline and new-version freeze |
| Prospective shadow runner | ats/shadow.py; shadow_validation.py; SHADOW.md; deployment/ | Public GET only, journal, hypothetical orders/fills and deterministic replay |
| Prospective protocol and freeze | SHADOW.md; prospective_freeze.json | No eligible initial profile; no forward performance observed |
| Reproducibility checksums | artifact_checksums.json; data/*manifest.json; runtime_snapshot.json | Exact input/source/artifact provenance; raw data restorable |
| Full report | REPORT.md; results/conclusions.json | V2_RETROSPECTIVE_NO_EDGE; five requested conclusions |

The public Binance smoke test is blocked by HTTP 451 in this environment. Native
fixture replay and a real consumed-history path-prefix audit pass; neither is
prospective market performance. No persistent server was deployed, no production
keys were read, and no real orders were sent. Active-profile shadow deployment
is not justified by the frozen evidence. Observation-only collection can support
future engineering and sample accumulation without changing admission rules.

Final verification logs are retained in results/verification/. The delivery audit
checks all comparison monthly PnL sums, required artifacts, admission claims and
native run count. The prospective and artifact manifests are verified after freeze.
The local branch is uncommitted and unpushed, consistent with repository policy.

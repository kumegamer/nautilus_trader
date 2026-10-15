# V2 validation gates fixed before scoring

These rules apply to central profiles under the primary ENTRY_ONLY policy.
Every monthly evaluation uses strictly matured, purged prior evidence. Missing
cost, neighborhood or sample evidence fails closed. No result-dependent waiver.

| Gate | Fixed rule | V1 rationale/change |
|---|---|---|
| Integrity | Causal features; every signal before fill; native financial reconciliation | Retained |
| Sample | >=60 trades in trailing 365-day window after purging | Retained; no arbitrary reduction to force activity |
| Economics | Net >0 and PF >=1.05 | Retained |
| Chronology | >=2 of 3 chronological thirds positive; final third positive | Replace nested tiny four-way partitions with explicit rolling temporal replication |
| Cost | Positive net under both 1.5x and 2x execution costs on independently rerun paths | Retained and expanded to every candidate/neighbor |
| Risk | Maximum marked daily drawdown <=15% | Retained; no unordered closed-trade drawdown |
| Transfer | >=2 positive symbols, each >=10 trades | Retained; no symbol parameter specialization |
| Stability | >=1 of 2 one-coordinate neighbors positive on same matured window | Retained; neighbors are distinct and direction-matched, no self-neighbor |
| Resampling | >=80% positive total PnL under 1,000 circular 7-day calendar-block resamples | New; descriptive dependence-aware stability, not an independent p-value |
| Concentration | Top 1 <=25% positive trade profits; largest positive month <=60% of positive month profits; largest positive symbol <=75% of positive symbol profits | Replace mandatory profitable deletion of top ten; preserve meaningful tail/transfer scrutiny |
| Direction/regime | Validate only predeclared side and compatible entry regimes; report all cells and counts | Replace requirement that unrelated directions/regimes must all profit; no post-hoc selection |

Top 1/5/10 shares, net after removal, largest month/symbol, win/loss quantiles,
skew and block-resampling interval are all reported. Top-five/top-ten deletion
is diagnostic only: deleting a trend strategy's intended right tail changes its
economic mechanism and is not a general statistical robustness criterion.
The new concentration gate still rejects a single dominant trade or narrow
month/symbol dependence. Subdivided cells do not become independent validations.

Shadow eligibility means permission to collect simulated forward observations,
never real-money activation. Research path is RESEARCH -> BACKTEST -> WALK_FORWARD
-> COST_STRESS -> STABILITY -> SHADOW_ELIGIBLE. The AI interface writes proposals
only. An untrusted proposal cannot set any gate, edit the frozen bundle, or modify
runtime parameters. Runtime eligibility comes only from the frozen evaluator.

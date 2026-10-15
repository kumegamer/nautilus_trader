# Failure diagnosis and answers to the twelve questions

**Primary diagnosis: STRATEGY_LIBRARY_WEAK (the implemented, regime-gated library) and ADAPTIVE_CONTROLLER_UNDEREXERCISED.** Additional supported causes: COST_MODEL_DOMINANT, INSUFFICIENT_SAMPLE, SYMBOL_DEPENDENCE and OTHER (incomplete experiment coverage and validation/reporting design limitations). No v2 strategy, parameter change, or proposal is made.

All selection conclusions below use developmental evidence ending before July 2026. Existing sealed results are referenced only for the requested final comparison and buy/hold explanation. This retrospective autopsy cannot turn reused developmental periods into independent evidence.

## 1. Which profiles came closest?

At the final freeze TB48_SHORT failed four of twelve gates, followed by VB48_WINDOW with five (including missing cost evidence). No profile was one gate short at that final snapshot. TB48_SHORT had 149 gate trades, +468.70 net, PF 1.375 and positive 2x net +247.34. Its failures were concentration, regime consistency, internal WF, and internal historical OOS. It was not close in the sense of passing after a single waiver.

At actual historical requests, TB48 and TB48_FUNDING reached eleven of twelve passed gates on 19 February 2026; only concentration failed. This is one timestamp, two profiles, repeated across three symbol controllers using the same pooled evidence, not six independent experiments. All three symbols saw RANGE_LOW_VOL at that timestamp, so passing would not itself mean an immediate entry. Closest-by-count is not a new strategy selection criterion.

| Profile | N gate | Net gate | Failures | Sample | Val | WF | Int.OOS | 2x | Nbr | Sym | DD | Conc | PF | Reg | Side |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| TB48_SHORT | 149 | 468.70 | 4 | PASS | PASS | FAIL | FAIL | PASS | PASS | PASS | PASS | FAIL | PASS | FAIL | PASS |
| VB48_WINDOW | 126 | 306.40 | 5 | PASS | FAIL | FAIL | PASS | FAIL | PASS | PASS | PASS | FAIL | PASS | FAIL | PASS |
| TB48 | 279 | 366.90 | 7 | PASS | PASS | FAIL | FAIL | FAIL | PASS | FAIL | PASS | FAIL | PASS | FAIL | FAIL |
| TB48_FUNDING | 279 | 366.90 | 7 | PASS | PASS | FAIL | FAIL | FAIL | PASS | FAIL | PASS | FAIL | PASS | FAIL | FAIL |
| TB48_STOP | 278 | 262.91 | 7 | PASS | PASS | FAIL | FAIL | FAIL | PASS | FAIL | PASS | FAIL | PASS | FAIL | FAIL |
| TB48_WINDOW | 276 | 377.05 | 7 | PASS | PASS | FAIL | FAIL | FAIL | PASS | FAIL | PASS | FAIL | PASS | FAIL | FAIL |
| VB48 | 169 | 90.81 | 7 | PASS | FAIL | FAIL | PASS | FAIL | PASS | PASS | PASS | FAIL | NEAR_MISS | FAIL | FAIL |
| VB48_STOP | 164 | 47.18 | 7 | PASS | FAIL | FAIL | PASS | FAIL | PASS | PASS | PASS | FAIL | NEAR_MISS | FAIL | FAIL |
| MR48_STOP | 733 | -2,581.71 | 10 | PASS | FAIL | FAIL | FAIL | FAIL | FAIL | FAIL | PASS | FAIL | FAIL | FAIL | FAIL |
| MR48_WINDOW | 592 | -2,171.41 | 10 | PASS | FAIL | FAIL | FAIL | FAIL | FAIL | FAIL | PASS | FAIL | FAIL | FAIL | FAIL |
| MR48 | 738 | -3,750.52 | 11 | PASS | FAIL | FAIL | FAIL | FAIL | FAIL | FAIL | FAIL | FAIL | FAIL | FAIL | FAIL |
| TP24 | 13 | -11.19 | 11 | FAIL | FAIL | FAIL | FAIL | FAIL | FAIL | FAIL | PASS | FAIL | FAIL | FAIL | FAIL |
| TP24_STOP | 13 | -8.68 | 11 | FAIL | FAIL | FAIL | FAIL | FAIL | FAIL | FAIL | PASS | FAIL | FAIL | FAIL | FAIL |
| TP24_WINDOW | 14 | -21.77 | 11 | FAIL | FAIL | FAIL | FAIL | FAIL | FAIL | FAIL | PASS | FAIL | FAIL | FAIL | FAIL |

## 2. Which gates killed the most?

| Original gate | Failures /14 |
| --- | --- |
| concentration | 14 |
| regimes | 14 |
| walk_forward | 14 |
| cost_stress | 13 |
| sides | 12 |
| sealed_oos | 11 |
| symbols | 10 |
| validation_positive | 9 |
| profit_factor | 8 |
| neighbors | 6 |
| sample | 3 |
| drawdown | 1 |

Cost stress: eight NOT TESTED + five measured failures + one pass, not thirteen observed stress losses. All 14 failed at least one internal WF subfold; this is distinct from the outer WF table. Only seven profiles were submitted by the offline reference research agent. The other seven existed as researched diagnostics but never traversed CANDIDATE in the real adaptive log.

## 3. Gates too strict, or weak strategies?

Both aspects matter, but arbitrary relaxation does not explain away the failure. The top-10-removal requirement is demanding for positively skewed trend strategies; removing every large winner can reject a legitimate fat-tail payoff. Requiring every declared compatible regime and allowed direction to show positive net is also stringent on subdivided samples. Conversely, an untested cost scenario is missing evidence, not excessive numerical strictness, and positive net +0.36 USDT on a qualifying symbol can pass the symbol gate without convincing economic significance.

At the freeze, removing concentration alone still leaves all 14 rejected. Even the best fully tested profile has negative internal WF2 and internal OOS. Mean-reversion losses are broad and persistent; pullback is drastically undersampled; breakout positives depend on time/symbol/side/regime. These are substantive weaknesses, not simply a 1.05 PF floor. VB48 (PF 1.04448) and VB48_STOP (1.02751) are descriptive PF-buffer near misses, but fail many other gates.

Gate counts are correlated and not independent statistical tests. The sample and top-10 gates duplicate failure mechanically for the pullbacks. The protocol text is looser than implementation about symbol coverage: code requires two qualifying positive symbols with >=10 trades, not all three. The configured 0.6 positive-WF fraction is not consulted by Registry/EvidenceProvider: promotion explicitly requires BOTH internal folds positive. With only two folds, >=0.6 would also require both.

## 4. What actually caused concentration failures?

Only 5 profiles fail the top-10 share cap: ['TB48_SHORT', 'TP24', 'TP24_STOP', 'TP24_WINDOW', 'VB48_WINDOW']. All 14 fail net-after-removing-top10 >0. Therefore “14 concentration failures” is not evidence that all 14 had profits dominated by outliers.

| Profile | Winners | Top10 % positive profits | Net ex-top10 | Best month / net | Net ex-month | Best symbol / net | Net ex-symbol |
| --- | --- | --- | --- | --- | --- | --- | --- |
| MR48 | 370 | 8.37 | -4,519.98 | 2026-06 / 259.15 | -4,009.67 | SOLUSDT / -756.88 | -2,993.64 |
| MR48_STOP | 397 | 8.01 | -3,196.85 | 2026-06 / 193.67 | -2,775.38 | SOLUSDT / -530.17 | -2,051.54 |
| MR48_WINDOW | 296 | 9.51 | -2,931.60 | 2025-03 / 122.51 | -2,293.92 | SOLUSDT / -472.79 | -1,698.62 |
| TB48 | 85 | 41.43 | -835.82 | 2025-04 / 393.60 | -26.70 | ETHUSDT / 664.36 | -297.46 |
| TB48_FUNDING | 85 | 41.43 | -835.82 | 2025-04 / 393.60 | -26.70 | ETHUSDT / 664.36 | -297.46 |
| TB48_SHORT | 52 | 60.80 | -577.12 | 2025-04 / 329.33 | 139.37 | ETHUSDT / 251.97 | 216.73 |
| TB48_STOP | 85 | 41.80 | -699.27 | 2025-04 / 311.49 | -48.59 | ETHUSDT / 486.32 | -223.41 |
| TB48_WINDOW | 84 | 41.45 | -825.67 | 2025-04 / 393.60 | -16.55 | ETHUSDT / 669.83 | -292.78 |
| TP24 | 6 | 100.00 | -50.96 | 2026-02 / 16.85 | -28.04 | ETHUSDT / 10.22 | -21.40 |
| TP24_STOP | 6 | 100.00 | -40.62 | 2026-02 / 13.51 | -22.19 | ETHUSDT / 8.18 | -16.87 |
| TP24_WINDOW | 6 | 100.00 | -58.60 | 2026-02 / 16.85 | -38.62 | BTCUSDT / -0.43 | -21.34 |
| VB48 | 64 | 49.33 | -960.96 | 2026-01 / 308.82 | -218.02 | ETHUSDT / 328.61 | -237.80 |
| VB48_STOP | 65 | 46.22 | -767.26 | 2026-01 / 271.48 | -224.30 | ETHUSDT / 174.99 | -127.82 |
| VB48_WINDOW | 51 | 58.98 | -732.10 | 2026-01 / 353.94 | -47.55 | ETHUSDT / 278.02 | 28.37 |

TB48_SHORT: 52 winners; the top 10 produce 60.80% of positive profits, leaving -577.12 net without them. All three symbols remain individually positive, and removing the best symbol still leaves +216.73. Removing April 2025 still leaves +139.37. Thus handful-of-winners and regime dependence are stronger explanations than sole-month or sole-symbol domination.

Both-direction breakout: ETH is the only positive symbol in the actual gate universe; removing it makes aggregate net negative. Removing April 2025 also makes net negative. The top-10 share ratio itself passes (~41–42%), but removing those profits makes net negative. Volatility breakout: ETH and January 2026 dominate offsets against losing symbols/folds. MR has broadly negative economics rather than concentrated alpha. TP has six winners, making a <=50% top-ten share mathematically impossible.

Best-month and best-symbol ratios in JSON use sums of POSITIVE monthly/symbol net contributions. Ratios to a tiny or negative total net are unstable and not used as admission rules. “Best” for all-negative symbols means least bad, not a positive contributor.

## 5. Why were walk-forward results unstable?

| Family/profile | Preholdout interpretation |
| --- | --- |
| MR48 / STOP / WINDOW | Large samples; negative expectancy on every outer validation/WF period and every symbol. Top-10 share only ~8–10%; the concentration flag mostly restates losses. Costs dominate or overwhelm small/negative gross edge. |
| TP24 / STOP / WINDOW | Only 15,15,16 total preholdout trades; 13,13,14 gate trades; six winners each. Statistical and conditional samples are inadequate. Top-10 share 100% is mechanically unavoidable. |
| TB48 / STOP / WINDOW / FUNDING | Positive purged gate net, but both-direction profit relies on ETH, April 2025 and shorts. High-volatility trends lose. Widening stops mostly changes size; most exits coincide with regime incompatibility. Funding filter makes no difference in gate OOS or later outer periods, though it does affect research 2024. |
| TB48_SHORT | Strongest fully cost-tested diagnostic candidate: all three symbols positive, 2x gate net +247.34, PF 1.375. But internal WF2 -64.08, internal OOS -15.11, high-vol trends -107.23, and top-10 share 60.80%, with net excluding top10 -577.12. Not merely a missing test or one overstrict gate. |
| VB48 / STOP / WINDOW | Gains during volatility expansion, losses during high-volatility trends. ETH and January 2026 drive aggregate positives; performance reverses across folds. Base 1.5x/2x costs turn net negative; neighbor stress tests absent. |

| Profile | Exit / incompatible-regime coincidence | Fraction % | Median holding h |
| --- | --- | --- | --- |
| MR48 | 41/1244 | 3.30 | 3.00 |
| MR48_STOP | 41/1234 | 3.32 | 3.50 |
| MR48_WINDOW | 29/1010 | 2.87 | 3.25 |
| TB48 | 429/462 | 92.86 | 4.00 |
| TB48_FUNDING | 421/452 | 93.14 | 4.00 |
| TB48_SHORT | 213/219 | 97.26 | 4.00 |
| TB48_STOP | 442/461 | 95.88 | 4.00 |
| TB48_WINDOW | 426/459 | 92.81 | 4.00 |
| TP24 | 14/15 | 93.33 | 1.00 |
| TP24_STOP | 14/15 | 93.33 | 1.00 |
| TP24_WINDOW | 15/16 | 93.75 | 1.00 |
| VB48 | 123/284 | 43.31 | 3.25 |
| VB48_STOP | 147/274 | 53.65 | 4.50 |
| VB48_WINDOW | 90/219 | 41.10 | 3.25 |

The code mandates an exit when the current regime leaves the profile compatibility set, even in the “static” runs. Around 93–97% of trend-breakout exits coincide with such transitions, with median holding time four hours despite hourly signals over 48/60-hour channels. This makes the regime/exit interaction a major mechanism to investigate in the diagnosis. Coincidence does not prove it was the sole exit condition or prove that suppressing these exits would improve results. An unfiltered controlled comparison is absent and no new one was run.

Breakout neighbors show similar later-period timing and losses: no general evidence of a sharp isolated profitable parameter peak. The funding filter does not change the purged gate trades. Volatility-breakout window changes affect trade timing, January contribution and fold signs, so parameter sensitivity is localized there. MR remains bad across its neighborhood. TP is too sparse for stability inference. Exact entry/exit/side overlap is recorded in neighbor_timing_overlap.csv; this excludes quantity so sizing effects remain visible separately.

## 6. Any positive expectancy in particular regimes?

| Profile | Regime | N | Net | E/trade | PF | Outer train / val / WF1 / WF2 nets |
| --- | --- | --- | --- | --- | --- | --- |
| TB48 | TREND_LOW_VOL | 183 | 413.26 | 2.258 | 1.265 | -204.84 / 537.79 / -7.20 / -113.52 |
| TB48_FUNDING | TREND_LOW_VOL | 183 | 413.26 | 2.258 | 1.265 | -101.19 / 537.79 / -7.20 / -113.52 |
| TB48_SHORT | TREND_LOW_VOL | 86 | 575.93 | 6.697 | 2.024 | 77.65 / 535.42 / -8.84 / 53.16 |
| TB48_STOP | TREND_LOW_VOL | 183 | 306.96 | 1.677 | 1.243 | -193.33 / 435.36 / -26.68 / -98.76 |
| TB48_WINDOW | TREND_LOW_VOL | 180 | 423.41 | 2.352 | 1.274 | -204.84 / 537.79 / -7.20 / -103.38 |
| VB48 | VOLATILITY_EXPANSION | 65 | 526.25 | 8.096 | 2.031 | 96.07 / 172.40 / 72.15 / 182.55 |
| VB48_STOP | VOLATILITY_EXPANSION | 64 | 411.78 | 6.434 | 1.916 | 134.17 / 115.38 / 36.33 / 175.98 |
| VB48_WINDOW | VOLATILITY_EXPANSION | 50 | 375.49 | 7.510 | 1.905 | 24.64 / 150.71 / -34.69 / 201.39 |

Yes. In particular VB48 volatility expansion has 65 purged gate trades, +526.25 net, +8.10/trade and PF 2.032; its outer expansion slice is positive in research, validation and both outer WF periods (+96.07/+172.40/+72.15/+182.55), although the latter first WF slice has just 10 trades. TREND_HIGH_VOL loses -435.44. TB48_SHORT low-volatility trends have 86 trades, +575.93 net and PF 2.024; high-volatility trends lose -107.23. These are descriptive preholdout subgroups, not newly validated strategies, and no sealed subgroup is used to choose a filter.

## 7. Could NO_TRADE / regime filtering plausibly help without hindsight?

The patterns are compatible with that possibility, but this experiment does not establish the counterfactual. Every active v1 profile ALREADY had regime entry filters and forced exits. Rejecting the known losing high-volatility trend slices after seeing them would be hindsight selection. A causal timestamp on a regime label does not make a subsequently chosen mapping independent of outcomes. Dropping saved losing trades is not a re-backtest: it changes open-position occupancy, later entries, costs and risk.

The most defensible statements are that existing compatibility mappings mix profitable and losing states, and that abstention avoided losses for failed profiles. Neither proves positive expectancy from a new filter. No new mapping or strategy is proposed here.

## 8. Was the controller meaningfully exercised?

No, for the central performance-adaptation objective. Actual trades: 0; actual switches: 0; successful VALIDATED/SHADOW admissions: zero. All 4,107 base-cost degradation evaluations were INSUFFICIENT_DATA. Features, regimes, eligibility checks, research throttling and abstention were exercised; performance-driven sizing, switching, side shutdown and recovery were not exercised on real historical positions. Their unit fixtures do not substitute for an economically exercised adaptive path.

## 9. How many regime transitions?

4,186 actual changes across BTC/ETH/SOL over 2024–September 2026: 3,886 before July and 300 in the completed holdout. The 4,189 rows additionally contain three UNKNOWN→UNKNOWN initializations. Repeating three cost scenarios produces 12,558 changes, not independent observations. The old 131,648 count includes static/reference run repetitions and must not be reported as distinct adaptive market transitions.

## 10. How many switches if gates were relaxed one level?

The user's clarified rule is applied exactly: accept PASS or existing diagnostic NEAR_MISS; any true FAIL blocks promotion. The original frozen promotion code has only binary gates and no NEAR_MISS state. The autopsy's descriptive PF-margin annotation (1 < PF < 1.05) was established from preholdout evidence before this clarification; it is not a frozen production acceptance rule. If 'pre-existing' means only states stored in the original frozen experiment, there are no such NEAR_MISS states and the outcome is also zero.

Result: ZERO newly eligible profiles at the final freeze or at recorded preholdout research requests; ZERO additional hypothetical switches; ZERO incremental subsequent PnL. Subsequent performance is unchanged, neither improved nor worsened. 392 final/historical evidence records were checked without using holdout performance. No arbitrary FAIL gate is waived and no switch counterfactual or new strategy run is needed.

The final-freeze annotations are exactly VB48 profit_factor: 1.044481 versus >=1.05, and VB48_STOP profit_factor: 1.027511 versus >=1.05. Each still has six other true FAIL gates. None of the 378 assessed preholdout research-request records has a PF-margin NEAR_MISS. Historical requests are listed in near_miss_eligibility.csv with every remaining FAIL. TB48/TB48_FUNDING's historical concentration FAIL remains a blocking FAIL, not a near miss. Original classification, promotion history and thresholds are unchanged.

## 11. Risk-adjusted adaptive versus static best

| Period | System | N | Net | Return % | Sharpe | Sortino | DD % | Ann.vol % |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| research | adaptive | 0 | 0.00 | 0.00 | N/A | N/A | 0.00 | 0.00 |
| research | static_best | 67 | 254.01 | 0.85 | 1.073 | 2.266 | 0.45 | 0.79 |
| research | buy_hold | 3 | 17,134.37 | 57.11 | 1.048 | 1.601 | 36.39 | 60.11 |
| research | no_trade | 0 | 0.00 | 0.00 | N/A | N/A | 0.00 | 0.00 |
| validation | adaptive | 0 | 0.00 | 0.00 | N/A | N/A | 0.00 | 0.00 |
| validation | static_best | 52 | 538.24 | 1.79 | 2.515 | 9.740 | 0.26 | 1.43 |
| validation | buy_hold | 3 | -3,085.20 | -10.28 | -0.077 | -0.112 | 44.26 | 59.05 |
| validation | no_trade | 0 | 0.00 | 0.00 | N/A | N/A | 0.00 | 0.00 |
| wf1 | adaptive | 0 | 0.00 | 0.00 | N/A | N/A | 0.00 | 0.00 |
| wf1 | static_best | 47 | -54.42 | -0.18 | -0.346 | -0.685 | 0.64 | 1.03 |
| wf1 | buy_hold | 3 | -2,328.89 | -7.76 | -0.022 | -0.031 | 38.30 | 54.51 |
| wf1 | no_trade | 0 | 0.00 | 0.00 | N/A | N/A | 0.00 | 0.00 |
| wf2 | adaptive | 0 | 0.00 | 0.00 | N/A | N/A | 0.00 | 0.00 |
| wf2 | static_best | 53 | -11.31 | -0.04 | -0.031 | -0.048 | 1.07 | 1.88 |
| wf2 | buy_hold | 3 | -10,917.92 | -36.39 | -1.553 | -2.060 | 44.91 | 50.48 |
| wf2 | no_trade | 0 | 0.00 | 0.00 | N/A | N/A | 0.00 | 0.00 |
| holdout | adaptive | 0 | 0.00 | 0.00 | N/A | N/A | 0.00 | 0.00 |
| holdout | static_best | 6 | -63.69 | -0.21 | -4.057 | -4.036 | 0.21 | 0.21 |
| holdout | buy_hold | 3 | 15,155.29 | 50.52 | 3.930 | 8.594 | 6.84 | 43.71 |
| holdout | no_trade | 0 | 0.00 | 0.00 | N/A | N/A | 0.00 | 0.00 |

The static comparator was frozen as TB48_SHORT using developmental validation+outer WF Sharpe. On completed holdout: net -63.69, Sharpe -4.057, Sortino -4.036, max DD 0.2123%, annualized daily volatility ~0.2078%, six trades. Adaptive: zero net, zero volatility/drawdown, and UNDEFINED Sharpe/Sortino (0/0), not Sharpe zero and not a statistically superior Sharpe. It avoided a loss by holding cash but did not demonstrate improved trading efficiency. Six static holdout trades also make annualized ratios fragile.

On preholdout pooled research+validation+WF data TB48_SHORT has Sharpe 0.784, Sortino 1.490, max DD 1.044% and 219 trades; the adaptive system still has no performance sample. This pooled figure includes research and is not independent OOS. Static validation Sharpe 2.515 falls to -0.346 and -0.031 across the two outer WF periods.

## 12. Why buy-and-hold made +15,155.29 USDT

| Symbol | Sleeve capital | Quantity | Entry fill | Exit fill | Entry notional | Gross | Fees | Slip | Funding | Net |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| BTCUSDT | 10000 | 0.153 | 58624.0 | 83576.7 | 8,969.47 | 3,819.95 | 10.88 | 2.19 | -176.74 | 3,630.14 |
| ETHUSDT | 10000 | 5.719 | 1573.63 | 2687.81 | 8,999.59 | 6,374.45 | 12.19 | 2.46 | -155.29 | 6,204.52 |
| SOLUSDT | 10000 | 122.1 | 73.708 | 118.148 | 8,999.75 | 5,428.57 | 11.71 | 2.44 | -93.78 | 5,320.63 |

Total initial capital 30,000 USDT: three independent 10,000 sleeves. Each takes a long linear USD-M perpetual position capped at 90% of sleeve capital, with lot rounding; total entry notional 26,968.80877 USDT (~89.896% of capital). Venue default leverage is 1; there is no leverage multiplier above one. Entry is 1 July 2026 00:15 UTC and exit 30 September 2026 23:45 UTC (both plus the declared 1ms quote offset), for 99.977% of the test duration. Fixed quantities are held without rebalancing or the active strategies' stop logic.

The BuyHold helper uses a synthetic sizing distance close×0.0025/0.9 to generate roughly 90% notional through the common sizing function. It does NOT enforce that distance as a protective stop; its overridden on_bar only maintains the long reference until the scheduled final quote. Thus this is not a 0.25%-risk stopped trade.

Exact identity: 15622.97159 gross − 34.77675003 fees − 7.08907 slippage + (-425.81528190) funding = 15155.29048807 net, or +50.5176% of initial 30,000. The profit comes from the saved entry-to-exit BTC, ETH and SOL price increases, not from adaptation. Completed holdout Sharpe 3.930, Sortino 8.594, max DD 6.836% and annualized volatility ~43.71% describe a much larger directional exposure.

Same initial capital and execution-cost venue make it a useful opportunity benchmark, but it is NOT economically apples-to-apples on risk. Active strategies budget <=25 USDT initial stop risk per entry (0.25% of each sleeve), spend much of the period flat, and may be short. On the SAME completed holdout, TB48_SHORT has 0.6039% position time across sleeves and approximately 0.1361% duration-weighted entry-notional exposure to initial portfolio capital. Buy/hold has 99.9774% position time and 89.8757% entry-notional exposure. The notional statistic is an entry-price proxy, not a full marked leverage series. No volatility-matched or beta-matched reference was supplied, and no new one is manufactured.

## Final failure classification

| Class | Diagnosis |
| --- | --- |
| STRATEGY_LIBRARY_WEAK | PRIMARY: as implemented with existing regime gating/forced exits, no profile demonstrates stable qualifying economics. Not a proof that the abstract strategy families can never work. |
| ADAPTIVE_CONTROLLER_UNDEREXERCISED | PRIMARY: no validated profiles, no trades, no switches, and no actual performance-decay feedback. |
| COST_MODEL_DOMINANT | SUPPORTED, especially MR and marginal both-side TB/VB. MR48_WINDOW gross +303.90 becomes net -2,171.41 after costs; MR48 already loses before costs. TB48_SHORT retains +247.34 at 2x, so costs are not a universal explanation. |
| INSUFFICIENT_SAMPLE | SUPPORTED for TP and small time/regime cells; not a blanket excuse for >700-trade losing MR samples. |
| SYMBOL_DEPENDENCE | SUPPORTED for both-direction TB and VB; short-only TB is positive on all three symbols and is less exposed to this failure. |
| REGIME_MODEL_WEAK | QUALIFIED: strong diagnostic evidence against the chosen compatibility/forced-exit overlay. Classifier quality or benefit from different thresholds cannot be identified without an absent controlled comparison. |
| VALIDATION_GATES_TOO_STRICT | QUALIFIED: tail-removal and every-cell positivity are conservative, but a one-gate waiver at the freeze admits nobody and missing stress tests are a coverage failure, not a threshold problem. |
| PARAMETER_INSTABILITY | LOCALIZED: VB window/stop timing and signs vary. TB neighbors are broadly similar; MR is consistently bad; TP cannot support a stability claim. |
| OTHER | Incomplete stress/holdout coverage; only seven agent-proposed candidates; central-family neighbor tests can include self and mismatched directions/filter permissions; nonchronological closed-trade DD; reused developmental history; uncalibrated confidence; no unfiltered or matched-risk control. |

The original ADAPTIVE_NO_EDGE conclusion stands. The diagnosis does not justify calling the flat system a profitable adaptive edge, does not prove all rejection counts represent independent failures, and does not support promoting a profile by quietly loosening one rule. No v2 design or optimization is proposed.

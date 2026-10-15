# Nautilus Alpha Discovery v3

**ALPHA_DISCOVERY_WEAK**. This is standalone alpha-library research, not Adaptive Trading v3.
Validated profiles: none. Research candidates: none.
Weak signals: ['MHT_LONG', 'BQ_LONG', 'CROSS_LONG', 'ML_LONG', 'ML_SHORT']. No real-money trading or credentials are enabled.

All historical results use CONSUMED data and are RETROSPECTIVE_EVIDENCE. Quarterly
OOS means chronological separation within reused history, not untouched evidence.
No prospective performance has been observed. Frozen references were neither
modified nor merged; V2 exact commit is 57703f7b5f77fed476adef323dc23e43f5a753b0.

## 1. Hypothesis families and rationale

Six economic families, separate sides: multi-horizon trend/resumption; breakout
quality with taker flow/volume; cross-asset BTC-conditioned ETH/SOL strength;
funding crowding/unwind; compression/expansion versus high-volatility downside
persistence; liquidity-shock range reversal. Two raw breakout controls and two
small chronological logistic filters compare complexity to simpler rules.
AUTOPSY.md documents prior failures and pre-result plausibility ranking.
FEATURES.md documents each formula, lookback, availability and rationale.

## 2. Experiment budget and research loop

16 central treatments (12 economic, two raw controls, two ML controls), 24
one-threshold stability paths and four exit interventions: **44 paths, 396
native runs** across three symbols and three costs. Repeated paths and cost runs
are not independent market samples. No additional search or result-dependent
parameter revisions. results/experiments.json records every hypothesis, parameters,
entry/exit/risk/cost rules, dates, results and rejection reason. The assistant's
hypotheses are inert; deterministic gates alone classify. results/research_loop.json
retains diagnoses and next-version proposals after the finite budget is exhausted.

## 3. Rejected hypotheses and gates

Controls, neighbors and exit interventions are deliberately non-promotable. ML
must beat its own side's raw control; no ML neighborhood search was budgeted, so
its stability gate remains unsatisfied even if gross ranking improves.

| profile | failed_gates |
|---|---|
| MHT_LONG | economics, cost, stability, resampling, multiple_testing, concentration, symbol_transfer |
| MHT_SHORT | economics, sample, chronology, cost, stability, resampling, multiple_testing, concentration, symbol_transfer |
| BQ_LONG | chronology, resampling, multiple_testing |
| BQ_SHORT | economics, chronology, cost, stability, resampling, multiple_testing, concentration, symbol_transfer |
| CROSS_LONG | economics, chronology, cost, resampling, multiple_testing, symbol_transfer |
| CROSS_SHORT | economics, chronology, cost, stability, resampling, multiple_testing, concentration, symbol_transfer |
| FUND_LONG | economics, chronology, cost, stability, resampling, multiple_testing, concentration, symbol_transfer |
| FUND_SHORT | economics, sample, chronology, cost, stability, resampling, multiple_testing, concentration, symbol_transfer |
| VOL_LONG | economics, chronology, cost, stability, resampling, multiple_testing, concentration, symbol_transfer |
| VOL_SHORT | economics, sample, chronology, cost, stability, resampling, multiple_testing, concentration, symbol_transfer |
| RANGE_LONG | economics, chronology, cost, stability, resampling, multiple_testing, concentration, symbol_transfer |
| RANGE_SHORT | economics, chronology, cost, stability, resampling, multiple_testing, concentration, symbol_transfer |
| ML_LONG | sample, stability, resampling, multiple_testing, concentration, symbol_transfer |
| ML_SHORT | chronology, stability, resampling, multiple_testing |

## 4–5. Strongest candidates and profile metrics

Highest marked retrospective PnL profiles: ML_SHORT, BQ_LONG, CROSS_LONG. This ranking is
post-result description; it does not override the classifications below.
Net is marked equity change in USDT, trade_net is fully contained/purged trade
attribution. PF/expectancy/R use those purged closed trades. Sharpe uses daily
marked returns, zero risk-free rate, 365-day scaling. DD is a fraction.

| profile | status | trades | net | trade_net | PF | Sharpe | DD | expectancy_R |
|---|---|---|---|---|---|---|---|---|
| MHT_LONG | WEAK_SIGNAL | 138 | 42.4910 | 42.4910 | 1.0404 | 0.1124 | 0.0094 | 0.0102 |
| MHT_SHORT | REJECTED | 88 | -299.3001 | -299.3001 | 0.5681 | -1.2403 | 0.0136 | -0.1760 |
| BQ_LONG | WEAK_SIGNAL | 464 | 954.6796 | 954.6796 | 1.2217 | 0.5098 | 0.0350 | 0.0582 |
| BQ_SHORT | REJECTED | 438 | -262.2453 | -262.2453 | 0.9349 | -0.2819 | 0.0266 | -0.0584 |
| CROSS_LONG | WEAK_SIGNAL | 328 | 265.1910 | 265.1910 | 1.0955 | 0.2740 | 0.0163 | 0.0035 |
| CROSS_SHORT | REJECTED | 314 | -32.4532 | -32.4532 | 0.9870 | -0.0413 | 0.0244 | -0.0419 |
| FUND_LONG | REJECTED | 244 | -977.8797 | -977.8797 | 0.5464 | -2.3121 | 0.0330 | -0.1997 |
| FUND_SHORT | REJECTED | 0 | 0.0000 | 0.0000 | undefined | undefined | 0.0000 | undefined |
| VOL_LONG | REJECTED | 262 | -514.4804 | -514.4804 | 0.8621 | -0.4962 | 0.0313 | -0.0937 |
| VOL_SHORT | REJECTED | 13 | -27.6790 | -27.6790 | 0.5268 | -0.7458 | 0.0011 | -0.2013 |
| RANGE_LONG | REJECTED | 642 | -1,268.0920 | -1,268.0920 | 0.7442 | -1.6610 | 0.0453 | -0.0871 |
| RANGE_SHORT | REJECTED | 397 | -1,150.7504 | -1,150.7504 | 0.6113 | -2.3330 | 0.0412 | -0.1082 |
| ML_LONG | WEAK_SIGNAL | 36 | 231.6271 | 231.6271 | 1.7689 | 0.4715 | 0.0063 | 0.2298 |
| ML_SHORT | WEAK_SIGNAL | 196 | 1,033.5756 | 1,033.5756 | 1.4420 | 0.9271 | 0.0174 | 0.2395 |

## 6. Per-symbol results

Independent 10,000USDT symbol sleeves, summed to 30,000USDT per path. Ineligible
BTC cross-asset sleeves remain cash and never supply transfer evidence.

| profile | symbol | trades | net | PF |
|---|---|---|---|---|
| MHT_LONG | BTCUSDT | 50 | -12.8242 | 0.9732 |
| MHT_LONG | ETHUSDT | 47 | 61.0178 | 1.2061 |
| MHT_LONG | SOLUSDT | 41 | -5.7026 | 0.9793 |
| MHT_SHORT | BTCUSDT | 28 | -96.1083 | 0.6116 |
| MHT_SHORT | ETHUSDT | 29 | -127.5432 | 0.4151 |
| MHT_SHORT | SOLUSDT | 31 | -75.6485 | 0.6674 |
| BQ_LONG | BTCUSDT | 157 | 126.4635 | 1.0708 |
| BQ_LONG | ETHUSDT | 139 | 665.0249 | 1.5977 |
| BQ_LONG | SOLUSDT | 168 | 163.1912 | 1.1160 |
| BQ_SHORT | BTCUSDT | 142 | -335.9766 | 0.7892 |
| BQ_SHORT | ETHUSDT | 141 | 238.5098 | 1.1995 |
| BQ_SHORT | SOLUSDT | 155 | -164.7785 | 0.8668 |
| CROSS_LONG | BTCUSDT | 0 | 0.0000 | undefined |
| CROSS_LONG | ETHUSDT | 153 | 231.9532 | 1.1660 |
| CROSS_LONG | SOLUSDT | 175 | 33.2377 | 1.0241 |
| CROSS_SHORT | BTCUSDT | 0 | 0.0000 | undefined |
| CROSS_SHORT | ETHUSDT | 145 | -112.6966 | 0.9054 |
| CROSS_SHORT | SOLUSDT | 169 | 80.2434 | 1.0616 |
| FUND_LONG | BTCUSDT | 7 | -80.5649 | 0.1407 |
| FUND_LONG | ETHUSDT | 29 | -128.9391 | 0.4937 |
| FUND_LONG | SOLUSDT | 208 | -768.3757 | 0.5749 |
| FUND_SHORT | BTCUSDT | 0 | 0.0000 | undefined |
| FUND_SHORT | ETHUSDT | 0 | 0.0000 | undefined |
| FUND_SHORT | SOLUSDT | 0 | 0.0000 | undefined |
| VOL_LONG | BTCUSDT | 96 | -84.7873 | 0.9403 |
| VOL_LONG | ETHUSDT | 97 | -103.9796 | 0.9251 |
| VOL_LONG | SOLUSDT | 69 | -325.7134 | 0.6468 |
| VOL_SHORT | BTCUSDT | 5 | -27.9315 | 0.1150 |
| VOL_SHORT | ETHUSDT | 6 | 1.3311 | 1.0583 |
| VOL_SHORT | SOLUSDT | 2 | -1.0786 | 0.7363 |
| RANGE_LONG | BTCUSDT | 218 | -479.7358 | 0.7636 |
| RANGE_LONG | ETHUSDT | 212 | -320.8810 | 0.7887 |
| RANGE_LONG | SOLUSDT | 212 | -467.4753 | 0.6682 |
| RANGE_SHORT | BTCUSDT | 129 | -567.7810 | 0.4922 |
| RANGE_SHORT | ETHUSDT | 138 | -271.5763 | 0.7264 |
| RANGE_SHORT | SOLUSDT | 130 | -311.3931 | 0.6336 |
| ML_LONG | BTCUSDT | 14 | 55.0136 | 1.3694 |
| ML_LONG | ETHUSDT | 10 | 231.3703 | 4.3743 |
| ML_LONG | SOLUSDT | 12 | -54.7568 | 0.3464 |
| ML_SHORT | BTCUSDT | 71 | 163.0515 | 1.1707 |
| ML_SHORT | ETHUSDT | 74 | 356.1065 | 1.3915 |
| ML_SHORT | SOLUSDT | 51 | 514.4176 | 2.0855 |

## 7. Long/short decomposition

Sides are separately specified and tested; gains on one side never validate the
other. Summing different research strategies is not a funded portfolio backtest.

| profile | side | trades | net |
|---|---|---|---|
| MHT_LONG | 1 | 138 | 42.4910 |
| BQ_LONG | 1 | 464 | 954.6796 |
| CROSS_LONG | 1 | 328 | 265.1910 |
| FUND_LONG | 1 | 244 | -977.8797 |
| VOL_LONG | 1 | 262 | -514.4804 |
| RANGE_LONG | 1 | 642 | -1,268.0920 |
| MHT_SHORT | -1 | 88 | -299.3001 |
| BQ_SHORT | -1 | 438 | -262.2453 |
| CROSS_SHORT | -1 | 314 | -32.4532 |
| FUND_SHORT | -1 | 0 | 0.0000 |
| VOL_SHORT | -1 | 13 | -27.6790 |
| RANGE_SHORT | -1 | 397 | -1,150.7504 |

## 8. Entry-regime decomposition

Causal regime labels are descriptive, not future classification targets or a
universal-profitability requirement. Complete profile/side/regime cells, counts,
net and PF are in results/long_short_regime_results.csv. Each group uses purged
realized outcomes and does not acquire an invented marked Sharpe.

| profile | side | regime | trades | net_pnl | profit_factor |
|---|---|---|---|---|---|
| BQ_LONG | 1 | COMPRESSION_LOW_VOL | 8 | -129.7912 | 0.0000 |
| BQ_LONG | 1 | RANGE_HIGH_VOL | 98 | 78.7980 | 1.1128 |
| BQ_LONG | 1 | RANGE_LOW_VOL | 337 | 1,080.5686 | 1.3255 |
| BQ_LONG | 1 | TREND_HIGH_VOL | 7 | -41.2528 | 0.2413 |
| BQ_LONG | 1 | TREND_LOW_VOL | 14 | -33.6430 | 0.6732 |
| CROSS_LONG | 1 | COMPRESSION_LOW_VOL | 38 | 58.0824 | 1.1429 |
| CROSS_LONG | 1 | RANGE_HIGH_VOL | 70 | -93.7192 | 0.7466 |
| CROSS_LONG | 1 | RANGE_LOW_VOL | 189 | 339.4758 | 1.1838 |
| CROSS_LONG | 1 | STRESS_HIGH_VOL | 17 | 0.1280 | 1.0019 |
| CROSS_LONG | 1 | TREND_HIGH_VOL | 5 | -34.9678 | 0.0000 |
| CROSS_LONG | 1 | TREND_LOW_VOL | 9 | -3.8084 | 0.9276 |
| ML_SHORT | -1 | COMPRESSION_LOW_VOL | 56 | 411.9657 | 1.4133 |
| ML_SHORT | -1 | RANGE_HIGH_VOL | 34 | 239.5893 | 3.2082 |
| ML_SHORT | -1 | RANGE_LOW_VOL | 99 | 347.1915 | 1.2950 |
| ML_SHORT | -1 | TREND_HIGH_VOL | 3 | -3.6928 | 0.7596 |
| ML_SHORT | -1 | TREND_LOW_VOL | 4 | 38.5220 | 1.9437 |

## 9. Walk-forward and pseudo-live simulation

2024 development; fixed-profile continuous accounts; seven subsequent quarters.
No parameter re-selection at quarter boundaries. ML alone retrains quarterly on
expanding prior labels with a 24-hour embargo. Every monthly eligibility decision
uses only its preceding matured 365 days, ending seven days earlier. The initial
window has six pre-simulation days with no executions; coverage is not fabricated.
Monthly records retain exact decision and evidence timestamps and all gate failures.
This evaluates profile eligibility, not adaptive controller returns or switches.
11 eligible profile-month decisions of 264.

| profile | 2025Q1 | 2025Q2 | 2025Q3 | 2025Q4 | 2026Q1 | 2026Q2 | 2026Q3 |
|---|---|---|---|---|---|---|---|
| MHT_LONG | 6.3665 | 39.0014 | 116.7567 | 80.5358 | 6.0579 | -221.9255 | 15.6981 |
| MHT_SHORT | 38.5985 | -0.1158 | -139.5705 | -34.6354 | -60.5244 | -46.0869 | -56.9656 |
| BQ_LONG | -270.1245 | 154.8050 | -54.4906 | -236.4508 | -162.3350 | -208.6643 | 1,731.9398 |
| BQ_SHORT | 375.0196 | -142.9197 | -295.9749 | 15.5107 | 304.6812 | -164.2722 | -354.2898 |
| CROSS_LONG | -128.3547 | -12.4414 | 186.3439 | -81.6225 | -7.0038 | -241.0886 | 549.3580 |
| CROSS_SHORT | 471.5797 | 26.4268 | -85.6033 | -281.4361 | 554.5009 | -418.9134 | -299.0079 |
| FUND_LONG | -94.6979 | -7.2328 | -59.8553 | -44.2866 | -418.2255 | -244.1824 | -109.3991 |
| FUND_SHORT | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| VOL_LONG | 243.8814 | -288.7536 | 160.5952 | -164.9401 | 353.2816 | -585.4755 | -233.0693 |
| VOL_SHORT | -10.6840 | 13.9876 | 0.0000 | -21.2525 | -9.7302 | 0.0000 | 0.0000 |
| RANGE_LONG | -189.8617 | -150.2632 | -303.1162 | -136.2222 | -299.7660 | -89.8951 | -98.9676 |
| RANGE_SHORT | -45.2810 | -267.4255 | -175.6209 | -189.4785 | -108.7679 | -263.2997 | -100.8769 |
| ML_LONG | 4.7131 | 5.4806 | 32.1209 | -105.1890 | -15.1783 | -38.4777 | 348.1576 |
| ML_SHORT | 301.7591 | 183.1976 | 162.2832 | -286.9193 | 1,077.1596 | -209.9051 | -193.9994 |

Quarterly marked PnL sums to full OOS marked PnL. Boundary positions remain in
marked outcomes; quarterly purged trade totals need not sum to full-period trade
net. Every month, including inactive months, is in monthly_contributions.csv.

## 10. Realistic costs and turnover

5bp taker plus 1bp adverse slippage/fill, outward tick rounding, quantity floor,
observed signed funding. Stress independently reexecutes changed prices/fees and
therefore can change sizing, occupancy and stop paths. Signed funding is not
multiplied. No maker fill claim. Exact decimal native fees, fills, funding and
accounts reconcile. period_turnover, fees, slippage, funding, exposure and time in
market are in profile_results.csv. Costs are stylized, not observed depth/spread.

| profile | base | cost1.5x | cost2x |
|---|---|---|---|
| MHT_LONG | 42.4910 | -90.6220 | -223.7996 |
| MHT_SHORT | -299.3001 | -374.4445 | -449.3608 |
| BQ_LONG | 954.6796 | 541.0589 | 153.6928 |
| BQ_SHORT | -262.2453 | -609.2056 | -947.1505 |
| CROSS_LONG | 265.1910 | 51.5192 | -163.9387 |
| CROSS_SHORT | -32.4532 | -223.6807 | -414.0634 |
| FUND_LONG | -977.8797 | -1,133.9795 | -1,329.2650 |
| FUND_SHORT | 0.0000 | 0.0000 | 0.0000 |
| VOL_LONG | -514.4804 | -1,021.7453 | -1,483.7997 |
| VOL_SHORT | -27.6790 | -30.6611 | -33.6491 |
| RANGE_LONG | -1,268.0920 | -1,990.0919 | -2,711.5660 |
| RANGE_SHORT | -1,150.7504 | -1,637.3264 | -2,112.3703 |
| ML_LONG | 231.6271 | 210.0943 | 188.5256 |
| ML_SHORT | 1,033.5756 | 811.8112 | 591.7644 |

## 11. Parameter-neighborhood stability and exits

Two one-coordinate +/-20% perturbations of the economic threshold, not an expanded
EMA/ATR/Donchian grid; neighbors cannot replace central profiles.

| profile | low_net | central_net | high_net | pass |
|---|---|---|---|---|
| MHT_LONG | -81.7376 | 42.4910 | -248.0697 | False |
| MHT_SHORT | -452.9698 | -299.3001 | -196.0621 | False |
| BQ_LONG | 980.0476 | 954.6796 | 983.7108 | True |
| BQ_SHORT | -268.2532 | -262.2453 | -219.3177 | False |
| CROSS_LONG | 405.2434 | 265.1910 | 405.0085 | True |
| CROSS_SHORT | 36.8994 | -32.4532 | 270.9816 | False |
| FUND_LONG | -1,446.7017 | -977.8797 | -738.9439 | False |
| FUND_SHORT | 24.1005 | 0.0000 | 0.0000 | False |
| VOL_LONG | -2.7863 | -514.4804 | -967.4554 | False |
| VOL_SHORT | -46.7283 | -27.6790 | -58.3148 | False |
| RANGE_LONG | -2,033.9245 | -1,268.0920 | -948.2257 | False |
| RANGE_SHORT | -1,826.9889 | -1,150.7504 | -972.3024 | False |
| ML_LONG | undefined | 231.6271 | undefined | False |
| ML_SHORT | undefined | 1,033.5756 | undefined | False |

Entry and exit are independent. Predeclared MHT structure and contraction exits
are fully reexecuted, never manufactured by deleting interrupted trades. Baseline
uses trailing risk stop plus time stop; funding uses fixed time plus risk stop;
range uses equilibrium/time plus risk stop. Entry-regime incompatibility alone
never forces an exit. All interventions and costs remain in profile_results.csv.

## 12. Concentration, sample and resampling

Top shares use positive closed-trade PnL; month share uses positive marked monthly
contributions; symbol share uses positive marked symbol contributions. Top-five/
ten deletion is diagnostic. Synchronized seven-day calendar blocks preserve
cross-asset co-movement and short-range dependence. 4,000 resamples are stability
diagnostics. Centered block-null p values face Bonferroni .05/16; they cannot undo
prior consumption, survivor bias, unknown market selection or longer dependence.

| profile | top1_share | top5_share | top10_share | ex_top1 | month_share | symbol_share | bootstrap_positive | centered_p |
|---|---|---|---|---|---|---|---|---|
| MHT_LONG | 0.0801 | 0.2916 | 0.4683 | -45.0545 | 0.1733 | 1.0000 | 0.5765 | 0.4396 |
| MHT_SHORT | 0.2052 | 0.5918 | 0.7570 | -380.0991 | 0.4917 | undefined | 0.0440 | 0.9608 |
| BQ_LONG | 0.1055 | 0.2936 | 0.4161 | 399.7902 | 0.4951 | 0.6966 | 0.7340 | 0.2354 |
| BQ_SHORT | 0.0504 | 0.1688 | 0.2862 | -452.1059 | 0.3977 | 1.0000 | 0.3560 | 0.6291 |
| CROSS_LONG | 0.0822 | 0.2993 | 0.4372 | 14.9997 | 0.4716 | 0.8747 | 0.6135 | 0.3339 |
| CROSS_SHORT | 0.0674 | 0.2399 | 0.3958 | -198.3425 | 0.3631 | 1.0000 | 0.4763 | 0.5129 |
| FUND_LONG | 0.1115 | 0.2386 | 0.3424 | -1,109.2649 | 0.4820 | undefined | 0.0018 | 0.9968 |
| FUND_SHORT | undefined | undefined | undefined | 0.0000 | undefined | undefined | 0.0000 | 1.0000 |
| VOL_LONG | 0.0794 | 0.2683 | 0.4293 | -769.8261 | 0.2051 | undefined | 0.2652 | 0.7646 |
| VOL_SHORT | 0.7489 | 1.0000 | 1.0000 | -50.7601 | 0.7893 | 1.0000 | 0.1180 | 0.8715 |
| RANGE_LONG | 0.0175 | 0.0659 | 0.1105 | -1,332.7006 | 0.3634 | undefined | 0.0107 | 0.9830 |
| RANGE_SHORT | 0.0212 | 0.0944 | 0.1662 | -1,189.1258 | 0.4704 | undefined | 0.0003 | 0.9985 |
| ML_LONG | 0.4695 | 0.8715 | 0.9652 | -18.5641 | 0.8783 | 0.8079 | 0.6432 | 0.2544 |
| ML_SHORT | 0.0684 | 0.2533 | 0.4239 | 802.8868 | 0.3588 | 0.4977 | 0.8510 | 0.1490 |

## 13. ML versus non-ML

Ten documented features, separate logistic directions, fixed L2 and threshold,
training-only standardization, no random shuffle, hourly sampled 4h labels.
All training cutoffs, latest label endpoints, sample counts and coefficients are
in ml_training.json. Models without enough past observations abstain.

| direction | rule_net | ml_net | delta | rule_sharpe | ml_sharpe | improvement_gate | classification |
|---|---|---|---|---|---|---|---|
| LONG | -152.4885 | 231.6271 | 384.1156 | -0.0400 | 0.4715 | True | WEAK_SIGNAL |
| SHORT | 437.4257 | 1,033.5756 | 596.1499 | 0.2450 | 0.9271 | True | WEAK_SIGNAL |

## 14. Failure modes and limits

Multiple testing and all prior historical consumption limit inference. Universe
contains three surviving liquid coins. Funding uses historical settlement marks;
fixed filters lack historical snapshots. OHLC-based synthetic quotes cannot
validate spread, queue, latency, capacity or impact. Close-observed stops can gap;
no intrabar protection is claimed. Daily DD can miss intraday troughs. A 0.25%
initial stop budget is not a guaranteed realized loss cap. Low activity reduces
confidence. Positive slices, changing exits and specialization discovered after
results cannot be promoted. No future observations or test fixtures count as
market success. ML labels use simplified cost proxy; actual execution controls
all economic conclusions. Statistical classification remains consumed-history
research evidence, not a forecast or a guarantee.

## 15. Final machine-readable profile library

profile_library.json contains **0 validated profile(s)** and complete
required definitions, risk rules, metrics, cost tolerance and known failure cells.
Empty is intentional when no profile passes. Research candidates and weak signals
remain in profile_evidence.json; they are not silently inserted into the library.
NO_TRADE is a defensive policy with zero exposure, not an alpha discovery.

## 16. Handoff to Adaptive Trading

Pass only validated frozen definitions plus their timestamped evidence and known
eligibility conditions; initial set: empty. Do not activate an
adaptive controller or infer diversification from strategy names. A validated
library requires two materially different families with abs daily-PnL correlation
below .80. Pair checks: not applicable.

## 17. What remains unproven

Future profitability, prospective replication, real executable capacity, broader
symbol robustness and adaptive allocation benefit. SHADOW.md reserves observations
after the new prospective freeze; it does not relabel historical replay as forward.
No collector/server is deployed, and no real-money execution is enabled.

## Reproducibility

README.md gives restore, freeze, execution, report and verify commands. Source,
feature inputs, publisher archives, runtime, native ledgers, checksums and the
prospective bundle are preserved. Frozen references unchanged. Integrity:
396 native runs reconciled; historical-prefix causality passed.

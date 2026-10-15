# NautilusTrader-only edge discovery v1

Historical research only. All executions, commissions, funding transfers, and accounts use NautilusTrader. No live trading is configured. No NautilusTrader core files were changed.

32 declared candidates across BTCUSDT, ETHUSDT, SOLUSDT. Research: 2022–2023; validation: 2024; two sequential six-month folds in 2025; sealed final: January–June 2026.

Selection frozen at 2026-10-15T11:23:21.593193+00:00. Holdout opened only after the freeze. The holdout never chooses or replaces candidates.

| Family | Classification | Preholdout eligible | Holdout net USDT | Holdout return | Trades |
|---|---|---|---:|---:|---:|
| mean_reversion | NO_EDGE | False | -290.37 | -0.97% | 300 |
| trend_breakout | WEAK_EDGE | False | 181.77 | 0.61% | 231 |
| trend_pullback | NO_EDGE | False | -529.34 | -1.76% | 230 |
| volatility_breakout | NO_EDGE | False | -1,220.78 | -4.07% | 573 |

Each family uses three 10,000 USDT symbol sleeves (30,000 USDT aggregate). Sleeves are evaluated independently with fixed initial-capital sizing. Fees are assumed VIP0 taker 5 bps/fill; base adverse slippage is 1 bp/fill with outward tick rounding. Slippage and fees are deducted separately; funding is signed income or expense.

## mean_reversion

Classification: **NO_EDGE**. Frozen representative: `mean_reversion_minutes15_lookback48_band_k2.5`.

| Metric | Holdout base |
|---|---:|
| total_trades | 300 |
| long_trades | 142 |
| short_trades | 158 |
| gross_pnl | 1,049.8760 |
| fees | 1,112.3004 |
| funding | 0.0879 |
| slippage_impact | 228.0364 |
| net_pnl | -290.3729 |
| return | -0.0097 |
| profit_factor | 0.9381 |
| sharpe | -0.5506 |
| sortino | -0.7584 |
| maximum_drawdown | 0.0359 |
| calmar | -0.5409 |
| win_rate | 0.5667 |
| average_win | 25.8661 |
| average_loss | -36.0585 |
| expectancy_per_trade | -0.9679 |
| exposure | 0.0937 |
| turnover | 74.1534 |

Chronological choices and true sequential OOS:

| Evaluation | Selected using | Candidate | Net USDT | Trades | Sharpe |
|---|---|---|---:|---:|---:|
| validation | research | mean_reversion_minutes15_lookback48_band_k2.5 | -2,365.11 | 647 | -2.3663 |
| wf1 | research, validation | mean_reversion_minutes15_lookback48_band_k2.5 | -1,376.91 | 300 | -3.2060 |
| wf2 | research, validation, wf1 | mean_reversion_minutes15_lookback48_band_k2.5 | -1,663.78 | 308 | -3.1832 |

Adaptive validation+WF net: -5,405.79 USDT. Final representative's retrospective validation+WF net: -5,405.79 USDT. The latter is selection-contaminated and is not an independent OOS claim.

Profitable parameter neighbors: 0%. Failed preholdout gates: both_sides_positive, both_walkforward_folds_positive, cost_stress, fixed_representative_positive, month_concentration, parameter_neighborhood, profit_factor, symbol_transfer, trade_concentration, validation_positive.

| Cost scenario | Adaptive preholdout OOS net | Frozen holdout net |
|---|---:|---:|
| base: 5bp fee + 1bp slippage | -5,405.79 | -290.37 |
| slip2 | -6,055.47 | -411.12 |
| slip3 | -6,850.42 | -670.41 |
| cost2x | -9,924.01 | -1,527.42 |

| Holdout breakdown | Trades | Net USDT | PF |
|---|---:|---:|---:|
| BTCUSDT | 99 | -88.63 | 0.9446 |
| ETHUSDT | 107 | -211.90 | 0.8748 |
| SOLUSDT | 94 | 10.15 | 1.0073 |
| long | 142 | -17.07 | 0.9924 |
| short | 158 | -273.31 | 0.8886 |
| range | 300 | -290.37 | 0.9381 |
| transition | 0 | 0.00 | undefined |
| trend | 0 | 0.00 | undefined |

Holdout net excluding best trade: -408.31; excluding best realized-exit month: -726.31. Best trade share of positive trade profits: 0.0268; best month share of positive monthly profits: 0.9444.

## trend_breakout

Classification: **WEAK_EDGE**. Frozen representative: `trend_breakout_minutes60_lookback48_stop_atr2.0`.

| Metric | Holdout base |
|---|---:|
| total_trades | 231 |
| long_trades | 109 |
| short_trades | 122 |
| gross_pnl | 654.2355 |
| fees | 372.4761 |
| funding | -23.6274 |
| slippage_impact | 76.3611 |
| net_pnl | 181.7708 |
| return | 0.0061 |
| profit_factor | 1.0526 |
| sharpe | 0.2752 |
| sortino | 0.4694 |
| maximum_drawdown | 0.0461 |
| calmar | 0.2660 |
| win_rate | 0.3896 |
| average_win | 40.4265 |
| average_loss | -24.5150 |
| expectancy_per_trade | 0.7869 |
| exposure | 0.4062 |
| turnover | 24.8317 |

Chronological choices and true sequential OOS:

| Evaluation | Selected using | Candidate | Net USDT | Trades | Sharpe |
|---|---|---|---:|---:|---:|
| validation | research | trend_breakout_minutes60_lookback48_stop_atr2.0 | 1,003.68 | 483 | 0.7884 |
| wf1 | research, validation | trend_breakout_minutes60_lookback48_stop_atr2.0 | 321.19 | 258 | 0.4559 |
| wf2 | research, validation, wf1 | trend_breakout_minutes60_lookback48_stop_atr2.0 | 167.01 | 245 | 0.2743 |

Adaptive validation+WF net: 1,491.88 USDT. Final representative's retrospective validation+WF net: 1,491.88 USDT. The latter is selection-contaminated and is not an independent OOS claim.

Profitable parameter neighbors: 100%. Failed preholdout gates: cost_stress.

| Cost scenario | Adaptive preholdout OOS net | Frozen holdout net |
|---|---:|---:|
| base: 5bp fee + 1bp slippage | 1,491.88 | 181.77 |
| slip2 | 1,162.81 | 121.17 |
| slip3 | 936.09 | 48.99 |
| cost2x | -260.09 | -251.30 |

| Holdout breakdown | Trades | Net USDT | PF |
|---|---:|---:|---:|
| BTCUSDT | 81 | 163.71 | 1.1436 |
| ETHUSDT | 72 | 20.56 | 1.0172 |
| SOLUSDT | 78 | -2.51 | 0.9978 |
| long | 109 | -619.92 | 0.6625 |
| short | 122 | 801.70 | 1.4950 |
| range | 131 | 637.03 | 1.3538 |
| transition | 86 | -361.05 | 0.7339 |
| trend | 14 | -94.21 | 0.6853 |

Holdout net excluding best trade: -109.22; excluding best realized-exit month: -278.20. Best trade share of positive trade profits: 0.0800; best month share of positive monthly profits: 0.3342.

## trend_pullback

Classification: **NO_EDGE**. Frozen representative: `trend_pullback_minutes60_lookback24_pullback_atr1.0`.

| Metric | Holdout base |
|---|---:|
| total_trades | 230 |
| long_trades | 99 |
| short_trades | 131 |
| gross_pnl | -175.2633 |
| fees | 296.2205 |
| funding | 2.9420 |
| slippage_impact | 60.7988 |
| net_pnl | -529.3406 |
| return | -0.0176 |
| profit_factor | 0.6819 |
| sharpe | -2.5345 |
| sortino | -2.9364 |
| maximum_drawdown | 0.0264 |
| calmar | -1.3371 |
| win_rate | 0.4913 |
| average_win | 10.0436 |
| average_loss | -14.2245 |
| expectancy_per_trade | -2.3015 |
| exposure | 0.1422 |
| turnover | 19.7480 |

Chronological choices and true sequential OOS:

| Evaluation | Selected using | Candidate | Net USDT | Trades | Sharpe |
|---|---|---|---:|---:|---:|
| validation | research | trend_pullback_minutes60_lookback24_pullback_atr1.0 | -677.36 | 497 | -1.5344 |
| wf1 | research, validation | trend_pullback_minutes60_lookback24_pullback_atr1.0 | -190.06 | 270 | -0.8287 |
| wf2 | research, validation, wf1 | trend_pullback_minutes60_lookback24_pullback_atr1.0 | -737.71 | 282 | -2.5783 |

Adaptive validation+WF net: -1,605.13 USDT. Final representative's retrospective validation+WF net: -1,605.13 USDT. The latter is selection-contaminated and is not an independent OOS claim.

Profitable parameter neighbors: 0%. Failed preholdout gates: both_sides_positive, both_walkforward_folds_positive, cost_stress, fixed_representative_positive, month_concentration, parameter_neighborhood, profit_factor, symbol_transfer, trade_concentration, validation_positive.

| Cost scenario | Adaptive preholdout OOS net | Frozen holdout net |
|---|---:|---:|
| base: 5bp fee + 1bp slippage | -1,605.13 | -529.34 |
| slip2 | -1,867.85 | -591.26 |
| slip3 | -2,131.22 | -650.48 |
| cost2x | -3,120.24 | -887.46 |

| Holdout breakdown | Trades | Net USDT | PF |
|---|---:|---:|---:|
| BTCUSDT | 78 | -212.65 | 0.6249 |
| ETHUSDT | 79 | -179.16 | 0.7017 |
| SOLUSDT | 73 | -137.53 | 0.7231 |
| long | 99 | -372.62 | 0.5615 |
| short | 131 | -156.72 | 0.8076 |
| range | 204 | -440.53 | 0.7005 |
| transition | 25 | -70.63 | 0.5965 |
| trend | 1 | -18.19 | 0.0000 |

Holdout net excluding best trade: -561.32; excluding best realized-exit month: -582.07. Best trade share of positive trade profits: 0.0282; best month share of positive monthly profits: 1.0000.

## volatility_breakout

Classification: **NO_EDGE**. Frozen representative: `volatility_breakout_minutes15_lookback48_compression0.8`.

| Metric | Holdout base |
|---|---:|
| total_trades | 573 |
| long_trades | 274 |
| short_trades | 299 |
| gross_pnl | 910.4785 |
| fees | 1,758.7185 |
| funding | -12.3284 |
| slippage_impact | 360.2166 |
| net_pnl | -1,220.7850 |
| return | -0.0407 |
| profit_factor | 0.8707 |
| sharpe | -1.1242 |
| sortino | -1.8765 |
| maximum_drawdown | 0.0782 |
| calmar | -1.0272 |
| win_rate | 0.3194 |
| average_win | 44.9232 |
| average_loss | -24.2096 |
| expectancy_per_trade | -2.1305 |
| exposure | 0.3015 |
| turnover | 117.2479 |

Chronological choices and true sequential OOS:

| Evaluation | Selected using | Candidate | Net USDT | Trades | Sharpe |
|---|---|---|---:|---:|---:|
| validation | research | volatility_breakout_minutes15_lookback48_compression0.8 | -3,583.50 | 1219 | -1.9292 |
| wf1 | research, validation | volatility_breakout_minutes15_lookback48_compression0.8 | -996.22 | 627 | -0.7866 |
| wf2 | research, validation, wf1 | volatility_breakout_minutes15_lookback48_compression0.8 | -2,955.92 | 613 | -3.7353 |

Adaptive validation+WF net: -7,535.64 USDT. Final representative's retrospective validation+WF net: -7,535.64 USDT. The latter is selection-contaminated and is not an independent OOS claim.

Profitable parameter neighbors: 0%. Failed preholdout gates: both_sides_positive, both_walkforward_folds_positive, cost_stress, drawdown, fixed_representative_positive, month_concentration, parameter_neighborhood, profit_factor, symbol_transfer, trade_concentration, validation_positive.

| Cost scenario | Adaptive preholdout OOS net | Frozen holdout net |
|---|---:|---:|
| base: 5bp fee + 1bp slippage | -7,535.64 | -1,220.78 |
| slip2 | -8,813.00 | -1,528.04 |
| slip3 | -10,295.10 | -1,916.59 |
| cost2x | -14,943.11 | -3,286.75 |

| Holdout breakdown | Trades | Net USDT | PF |
|---|---:|---:|---:|
| BTCUSDT | 207 | -171.73 | 0.9519 |
| ETHUSDT | 173 | -427.22 | 0.8458 |
| SOLUSDT | 193 | -621.83 | 0.7997 |
| long | 274 | -2,129.38 | 0.5516 |
| short | 299 | 908.60 | 1.1936 |
| range | 450 | -1,069.05 | 0.8575 |
| transition | 115 | 74.33 | 1.0433 |
| trend | 8 | -226.07 | 0.0000 |

Holdout net excluding best trade: -1,464.68; excluding best realized-exit month: -1,864.37. Best trade share of positive trade profits: 0.0297; best month share of positive monthly profits: 0.6504.

## Integrity and limits

Native closed-position and account reconciliations passed for every saved run. Funding boundary trade-open proxies: 30 across unique symbol-period datasets. All requested 5m grids were checked for missing/duplicate timestamps and OHLC validity; coarser bars are causal UTC-aligned aggregates.

Prefix replay and mutated future tails leave earlier fills unchanged. Integrity details and test output are in results/integrity.json and results/tests.txt. Every run retains fill reference prices, signal/fill timestamps, native fees, funding, trades, and daily equity.

The universe is fixed to three surviving liquid assets; broader market survival bias is not measured. Constant conservative instrument filters lack historical snapshots. Bar-derived executable quotes do not observe actual spread, queue, latency, or depth; stops are close-based and can gap. Funding mark proxies introduce valuation uncertainty. Consequently the strongest classification is unavailable in this experiment. Multi-period returns and risk statistics chain-link normalized period equity; USDT PnL remains the nominal sum of independent period PnLs. No p-value or significance claim is made after the 32-candidate search. Historical evidence does not establish future profitability.

Undefined statistics (for example PF without losses) are null in JSON/CSV and shown as undefined here. Drawdown is daily marked equity; exposure is invested symbol-time; turnover counts both entry and exit notional. Monthly attribution uses realized exit month and is distinct from daily marked-equity returns.

## Reproduction

See README.md for commands, runtime lock, and single-use holdout controls. Raw Binance archives are retained locally under data/raw and identified by publisher SHA256 in the two data manifests. Source/config, preholdout evidence, and decisions are hashed into results/freeze.json before holdout data access.

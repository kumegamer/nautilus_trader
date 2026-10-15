# Nautilus Adaptive Trading System v1

**Classification: ADAPTIVE_NO_EDGE.** Historical simulation only; real-money execution disabled.

Frozen static comparator: `TB48_SHORT`. Sealed holdout: July–September 2026. Adaptive net 0.00 USDT versus static -63.69 USDT. No demonstrated adaptive edge. Avoiding losses through abstention is not evidence of a profitable adaptive edge.

## 1. Architecture

Public Binance archives -> native events + causal feature engine -> regime engine -> finite-profile controller -> Nautilus Strategy/order/fills/portfolio. Closed native positions -> performance/drift -> proposal-only research agent -> timestamp-filtered historical research -> explicit promotion registry -> SHADOW. No live adapter is instantiated.

## 2. Feature definitions

Log-return 48-bar realized volatility; 14-bar true-range ATR and ATR/close; 24-bar momentum; EMA200 slope over six bars normalized by ATR; distance/ATR trend strength; 48-bar price efficiency; logarithmic choppiness; 48-bar channel breakout and one-bar failed breakout frequency over 96 bars; volatility/240-bar historical median; volume/96-bar median and 6/24 mean acceleration; 96-bar lag-one return correlation; absolute return/quote-volume liquidity proxy. Cross-symbol 96-bar return correlations and current return dispersion. Funding and first difference joined at actual publication time. Basis and observed spread unavailable. All four timeframes use closed bars. See adaptive/features.py and causal tests.

## 3. Regime definitions

UNKNOWN until features ready. Stress: volatility ratio >3, or absolute 15m 24-bar momentum >8% and volatility ratio >1.5. Expansion >1.8; compression <0.6. Otherwise trend requires 48-hour efficiency >0.3 and absolute hourly normalized slope >0.02; remaining observations are range. High volatility above 1.2. Confidence is a bounded distance-from-rule score, not a calibrated probability. Start, duration and complete transition logs are persisted.

## 4. Profile definitions

Four central economically motivated families, two neighbors each, short-only and funding-filter breakout hypotheses, and NO_TRADE. Exact parameters, regimes, permissions, sizing, provisional expected ranges and stop definitions: results/profiles.json. Expectations are hypotheses, not guaranteed historical bands; promotion evidence supplies estimated R confidence bands. All 14 attempts remain in all_static_results.json. Historical expected R bands and validation status are attached to each profile; they never mutate runtime parameters. Current profile definitions differ from the prior unfiltered WEAK_EDGE, so its results are not carried over.

## 5. Adaptation policy

Only point-in-time SHADOW-eligible profiles; fixed family/id preference avoids chasing recent winners. Regime hysteresis, 24h dwell and 12 switches/30-day ceiling. Safety exits bypass dwell. Discrete risk 0/0.5/1; side and symbol disablement. Exposure exits on risk reduction; parameters never mutate. State persists across chronological periods; accounts are flattened and reinitialized to 10,000 USDT per sleeve at scheduled boundaries, with nominal PnL carried in portfolio reports. This scheduled-reset simulation is a limitation versus uninterrupted deployment.

## 6. Degradation triggers

Daily time, 50 additional trades, significant regime transitions, marked/realized drawdown >8%, eight consecutive losses, >=20-trade negative expectancy/PF signals, >=50-trade corroborated failure, execution-cost deterioration, and two-sided historical confidence-band comparison. Sparse samples are INSUFFICIENT_DATA. All six performance states are explicit. PnL alone never authorizes promotion.

## 7. Research and promotion

RESEARCH -> CANDIDATE -> VALIDATED -> SHADOW; failed gates -> REJECTED. SHADOW -> CANARY_ELIGIBLE requires additional forward shadow observations; LIVE_ELIGIBLE transitions are forbidden. The offline rule agent proposes and ranks only declared experiments. At every request a seven-day embargo and strict entry/exit purge restrict evidence to the past. Chronological 40/20/10/10/20 research/validation/WF/WF/internal-OOS partitions are diagnostics using known developmental data. The new sealed period is separate and never supplied to the research provider. Limited candidate re-evaluation is implemented; open-ended AI code generation is outside v1.

## 8. Test periods

- research: [2024-01-01, 2025-01-01) UTC
- validation: [2025-01-01, 2025-07-01) UTC
- wf1: [2025-07-01, 2026-01-01) UTC
- wf2: [2026-01-01, 2026-07-01) UTC
- holdout: [2026-07-01, 2026-10-01) UTC

Every date through June 2026 was previously observed. Only July–September 2026 is new sealed evidence. Exact freeze/open timestamps and hashes are in results/freeze.json and holdout_opened.json.

## 9. Assumptions

5bp taker and 1bp adverse slippage per fill at base, both stressed 1.5x/2x with outward tick rounding. Signed actual funding is not artificially multiplied. Historical tick/lot schedules are approximated by declared fixed instrument specs. No historical order book: volume participation is a proxy, not partial-fill evidence. Stop exits wait for a close then next open; intrabar stop protection is not claimed. MAE/MFE use observed bar high/low after entry. Perpetual buy/hold is 90% notional long with funding, not a matched-volatility allocation. Three-symbol survivorship/universe choice is explicit. Sharpe/Sortino use daily returns, zero risk-free rate, 365-day scaling; short samples are noisy.

## 10–11. Static and adaptive results

| System | Period | Costs | Trades | Net USDT | Sharpe | Max DD |
|---|---|---|---:|---:|---:|---:|
| static_best | holdout | base | 6 | -63.69 | -4.06 | 0.21% |
| static_best | holdout | cost1.5x | 6 | -72.57 | -4.20 | 0.24% |
| static_best | holdout | cost2x | 6 | -81.46 | -4.30 | 0.27% |
| adaptive | holdout | base | 0 | 0.00 | undefined | 0.00% |
| adaptive | holdout | cost1.5x | 0 | 0.00 | undefined | 0.00% |
| adaptive | holdout | cost2x | 0 | 0.00 | undefined | 0.00% |
| buy_hold | holdout | base | 3 | 15,155.29 | 3.93 | 6.84% |
| buy_hold | holdout | cost1.5x | 3 | 15,128.90 | 3.93 | 6.83% |
| buy_hold | holdout | cost2x | 3 | 15,108.12 | 3.92 | 6.84% |
| no_trade | holdout | base | 0 | 0.00 | undefined | 0.00% |
| no_trade | holdout | cost1.5x | 0 | 0.00 | undefined | 0.00% |
| no_trade | holdout | cost2x | 0 | 0.00 | undefined | 0.00% |

Developmental chronological results:

| System | Period | Costs | Trades | Net USDT | Sharpe | Max DD |
|---|---|---|---:|---:|---:|---:|
| static_best | research | base | 67 | 254.01 | 1.07 | 0.45% |
| static_best | validation | base | 52 | 538.24 | 2.52 | 0.26% |
| static_best | wf1 | base | 47 | -54.42 | -0.35 | 0.64% |
| static_best | wf2 | base | 53 | -11.31 | -0.03 | 1.07% |
| adaptive | research | base | 0 | 0.00 | undefined | 0.00% |
| adaptive | validation | base | 0 | 0.00 | undefined | 0.00% |
| adaptive | wf1 | base | 0 | 0.00 | undefined | 0.00% |
| adaptive | wf2 | base | 0 | 0.00 | undefined | 0.00% |
| buy_hold | research | base | 3 | 17,134.37 | 1.05 | 36.39% |
| buy_hold | validation | base | 3 | -3,085.20 | -0.08 | 44.26% |
| buy_hold | wf1 | base | 3 | -2,328.89 | -0.02 | 38.30% |
| buy_hold | wf2 | base | 3 | -10,917.92 | -1.55 | 44.91% |
| no_trade | research | base | 0 | 0.00 | undefined | 0.00% |
| no_trade | validation | base | 0 | 0.00 | undefined | 0.00% |
| no_trade | wf1 | base | 0 | 0.00 | undefined | 0.00% |
| no_trade | wf2 | base | 0 | 0.00 | undefined | 0.00% |

## 12–14. Symbol, regime and long/short decomposition

All systems/costs/periods: results/details.json, with strategy/profile/symbol/regime/side and rolling 30/90/365-day breakdowns. Trade-level ledger: results/trades.csv. Group Sharpe is daily realized attribution; system Sharpe is marked equity. No-trade group metrics remain undefined where there are no observations.

Sealed base-cost results by symbol:

| System | Group | Trades | Net USDT | PF |
|---|---|---:|---:|---:|
| static_best | BTCUSDT | 2 | -18.07 | 0.00 |
| static_best | ETHUSDT | 1 | -37.04 | 0.00 |
| static_best | SOLUSDT | 3 | -8.58 | 0.00 |
| adaptive | BTCUSDT | 0 | 0.00 | undefined |
| adaptive | ETHUSDT | 0 | 0.00 | undefined |
| adaptive | SOLUSDT | 0 | 0.00 | undefined |
| buy_hold | BTCUSDT | 1 | 3,630.14 | undefined |
| buy_hold | ETHUSDT | 1 | 6,204.52 | undefined |
| buy_hold | SOLUSDT | 1 | 5,320.63 | undefined |
| no_trade | BTCUSDT | 0 | 0.00 | undefined |
| no_trade | ETHUSDT | 0 | 0.00 | undefined |
| no_trade | SOLUSDT | 0 | 0.00 | undefined |

Sealed base-cost results by regime:

| System | Group | Trades | Net USDT | PF |
|---|---|---:|---:|---:|
| static_best | TREND_LOW_VOL | 6 | -63.69 | 0.00 |
| buy_hold | REFERENCE | 3 | 15,155.29 | undefined |

Sealed base-cost results by side:

| System | Group | Trades | Net USDT | PF |
|---|---|---:|---:|---:|
| static_best | 1 | 0 | 0.00 | undefined |
| static_best | -1 | 6 | -63.69 | 0.00 |
| adaptive | 1 | 0 | 0.00 | undefined |
| adaptive | -1 | 0 | 0.00 | undefined |
| buy_hold | 1 | 3 | 15,155.29 | undefined |
| buy_hold | -1 | 0 | 0.00 | undefined |
| no_trade | 1 | 0 | 0.00 | undefined |
| no_trade | -1 | 0 | 0.00 | undefined |

## 15. Fees, slippage and funding

| System | Costs | Gross | Fees | Slippage | Signed funding | Net |
|---|---|---:|---:|---:|---:|---:|
| static_best | base | -45.46 | 14.86 | 3.12 | -0.25 | -63.69 |
| static_best | cost1.5x | -45.46 | 22.28 | 4.58 | -0.25 | -72.57 |
| static_best | cost2x | -45.46 | 29.71 | 6.04 | -0.25 | -81.46 |
| adaptive | base | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| adaptive | cost1.5x | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| adaptive | cost2x | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| buy_hold | base | 15,622.97 | 34.78 | 7.09 | -425.82 | 15,155.29 |
| buy_hold | cost1.5x | 15,617.41 | 52.15 | 10.65 | -425.71 | 15,128.90 |
| buy_hold | cost2x | 15,617.41 | 69.53 | 14.05 | -425.71 | 15,108.12 |
| no_trade | base | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| no_trade | cost1.5x | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| no_trade | cost2x | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |

## 16–17. Walk-forward and sealed holdout

See the period tables and exact results/details.json. All walk-forward profile eligibility uses only prior closed outcomes, never full-period scores. Sealed static results never enter adaptive decisions. A flat adaptive result demonstrates abstention, not improved Sharpe. Positive static PnL does not imply promotion eligibility.

## 18–21. Switch, degradation, research and promotion history

- decisions: 12,321 logged events across costs and symbols
- switches: 0 logged events across costs and symbols
- degradation: 12,321 logged events across costs and symbols
- research: 2,142 logged events across costs and symbols
- promotions: 3,906 logged events across costs and symbols
- regime_transitions: 131,648 logged events across costs and symbols

Complete JSONL and CSV in results/events/. Switch rows include timestamp, old/new profile, regime/confidence, performance state, reason and structured evidence. JSONL retains every decision payload; CSV includes the full JSON too. No switches is a reported outcome, not an omitted log. Historical promotion is SHADOW simulation eligibility only. Superseded pre-freeze runs lacking state continuation remain under results/development_superseded, excluded from all conclusions.

## 22. Failure modes and validation limits

Most frequent final gate failure: **concentration**. Failure counts: `{"concentration": 14, "cost_stress": 13, "drawdown": 1, "neighbors": 6, "profit_factor": 8, "regimes": 14, "sample": 3, "sealed_oos": 11, "sides": 12, "symbols": 10, "validation_positive": 9, "walk_forward": 14}`.

Handwritten regimes can fragment samples and create excessive eligibility churn. OHLCV cannot validate microstructure execution, latency or market impact. Confidence is heuristic. Known historical partitions and multiple candidate tests limit inference even with purging. Boundary flattening, fixed capital risk and reused warmup are not uninterrupted real operation. Withheld opportunities under NO_TRADE do not prove a profitable selection policy. AI process boundaries are a software capability convention, not a sandbox against malicious Python code. Forward shadow, calibrated uncertainty, stronger market-mechanism hypotheses and a new untouched OOS are required before advancement toward trading.

## Reproducibility

Exact source/evidence freeze, publisher SHA256s, normalized data audits, artifact checksums, runtime provenance and native reconciliation differences are persisted. Run `python -m adaptive.workflow verify` using the pinned environment; reproduction instructions are in README.md. No prior branch files or develop history were modified.

Tests: results/tests.txt. Current classification: **ADAPTIVE_NO_EDGE**. Strongest failure mode: **concentration**. Nautilus is worth advancing as the deterministic engine; trading-edge promotion to v2 needs new validated economics, not a more aggressive optimizer.

## Reporting audit correction

Reference trade grouping inherits symbol/profile/strategy from each immutable run. The original generated tables are retained in results/reporting_superseded. Every per-symbol count and PnL sum is independently checked against system totals. NO_TRADE expected frequency and R band are zero by construction; generic frozen descriptive defaults never affected its zero-exposure logic. Promotion state events comprise {'CANDIDATE': 1323, 'REJECTED': 1323, 'RESEARCH': 1260}; successful SHADOW promotions: 0. No experimental source, strategy parameters, fills, performance or decision logs changed. Exact correction scope is in results/reporting_corrections.json.

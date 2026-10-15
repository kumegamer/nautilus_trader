# Adaptive Trading System v1 protocol

Historical/shadow simulation only; no live client, key, venue connection or deployment.
NautilusTrader is the sole event/order/fill/funding/position/accounting engine.
Adaptive control is separate under adaptive/. No core source modifications.

## Chronology and prior evidence

Prior branch evaluation/edge-discovery-v1 at 3c669f91dd195266107a2f5b77c5c991565840a8 is read-only.
Its 2022–June 2026 results are known prior research, including the former holdout.
2024 is current research, January–June 2025 validation, July–December 2025 WF1,
January–June 2026 WF2. These reused periods are developmental evidence, not new sealed OOS.
July–September 2026 is the new sealed holdout. Source, thresholds, static choice,
preholdout results and profile evidence must be frozen before downloading it.
No policy or candidate tuning after its opening. Any correction affecting results invalidates
its pristine status and must be disclosed; a fresh future holdout is then required.

## Causality and fills

5m public Binance USD-M OHLCV is aggregated only into complete 15m, 1h and 4h bars.
Feature availability is bar close (end minus 1ms). Backward as-of joins use this availability,
not the open timestamp. Funding features use the publisher's original reporting timestamp.
Realized funding accounting uses its settlement-hour boundary and contemporaneous mark open;
trade open is an explicitly counted fallback. Basis and true spread are absent, never fabricated.
OHLCV liquidity proxy is absolute log return / quote turnover; it is not observed spread/depth.
Cross-symbol statistics use only simultaneously closed returns, never forward fills from the future.

Signals at 15m/1h closes execute on the next 15m opening quote, 1ms after open.
Hourly profiles generate signals only at a completed hourly close. Native bar fills disabled.
Stops are close-observed, next-open exits, not guaranteed intrabar protective orders.
Each profile has 96 signal bars maximum duration. Full exits occur before profile replacement;
no same-quote reversal. No partial-fill or latency claims from OHLCV.
Base: 5bp taker fee and >=1bp adverse slippage/fill with outward tick rounding.
1.5x and 2x multiply both. Signed realized funding stays observed, not multiplied as a fee.
Initial capital: independent 10,000 USDT symbol sleeves; fixed initial risk 0.25%/trade;
90% notional ceiling; 0.1% previous closed 15m volume cap; minimum notional 100 USDT.
Controller, monitor, regime, eligibility and research cooldown state carry across all consecutive
periods, including the new holdout; scheduled boundary flattening does not reset adaptation.
Feature windows are rebuilt from a declared 30-day warmup; the long 4h trend may remain UNKNOWN
for the first four days. No state is rewound through that warmup on resume.
Research boundaries flatten at final available next-open quote (last bar opening), charging costs.
The last unexecutable signal is discarded. This boundary convention applies to all systems.

## Candidate budget

Four families: 1h breakout48/2ATR, 1h pullback24/2.5ATR, 15m reversion48/2.5sigma,
15m compression breakout48/2.5ATR. Two neighbors per family (25% wider stop, 25% longer window).
Two targeted hypotheses: breakout short only and funding-sensitive breakout.
Total 14 active profiles plus NO_TRADE. No continuous optimizer or unbounded grid.
Each fixed profile enforces its declared compatible regime entry/exit filter. Static means
fixed family/parameters and full risk, with no performance adaptation.
Static diagnostics test all profiles; only four central profiles and two targeted hypotheses
receive full cost stress. Neighbors without cost evidence cannot be promoted.
Static best is selected solely on preholdout aggregate daily Sharpe (net PnL/id tie break).
Static choice remains a research comparator even if it fails promotion gates.

## Research and promotion

The offline structured agent proposes declared hypotheses only. It has no activation interface.
A real model can implement the ResearchAgent protocol but cannot edit profiles or Registry evidence.
Research events are throttled to once every 30 elapsed days per symbol; every rejected attempt logs.
The experiment is a bounded re-evaluation of the 14 predeclared profiles, not novel code generation.
At any event timestamp the evidence provider filters completed historical trades strictly earlier
than a seven-day embargo. Split the eligible elapsed history into chronological 40% research,
20% validation, 20% walk-forward (two equal subfolds), 20% internal sealed OOS. Purge trades
crossing split boundaries. Internal historical splits are reused developmental diagnostics,
not a substitute for the new sealed July–September OOS.
Promotion needs >=60 trades across non-research splits, >=10 per symbol, positive validation,
both walk-forward folds positive, positive internal OOS, positive 2x cost net, >=50% positive
neighbor profiles, >=2 positive symbols, drawdown <=15%, top-10 winners <=50% positive profits,
and positive net excluding top 10. It additionally requires PF >=1.05,
>=10 profitable observations in every declared compatible regime and permitted direction.
Drawdown uses both closed trades and known marked daily equity. Missing evidence fails closed.
All evidence includes its end time; availability starts strictly after SHADOW transition.
State sequence RESEARCH -> CANDIDATE -> VALIDATED -> SHADOW. Rejections stay explicit.
CANARY_ELIGIBLE additionally requires >=30 days/30 trades positive shadow economics and 2x stress.
LIVE_ELIGIBLE exists as a vocabulary state but every transition into it is prohibited.
The current historical run cannot certify forward shadow performance.

## Adaptation and decay

Compatible, historically validated profiles only. Fixed family/id preference, never recent PnL rank.
NO_TRADE whenever no eligible profile, unknown/stress regime or material failure.
Regime confidence >=0.55 and >=4 closed 15m bars before entry; >=24h between non-safety switches;
max 12 switches per rolling 30 days. Safety exits always allowed and count toward the budget.
Risk choices 0, 0.5, 1 times the validated 0.25% budget. No new parameter set enters runtime.
Restore full risk only after >=60 own-profile trades, positive >=0.1R expectancy and normal state.
Disable a side for 30 days after >=30 observations and net below -100 USDT; no symmetric inference.

Evaluate daily, after 50 additional closed trades, regime transition, drawdown, abnormal loss sequence,
expectancy/PF decay, execution cost changes, or historical confidence-band breach.
At least 20 trades before statistical decay; >=50 for combined PF/expectancy failure.
Risk reductions and side disablement also exit existing exposure at the next executable open.
Material failure disables the symbol for at least 30 days as well as the offending profile.
The registry moves the failed profile to DISABLED and quarantines it for 30 days;
a new passed research/promotion cycle is required before it can become eligible again.
Eight consecutive losses initiate investigation; not proof of failure by themselves.
Execution costs above 15bp turnover after >=10 trades isolate execution deterioration.
Realized expectancy +1.96SE below validation lower confidence band flags possible failure.
Multi-signal classifications: NORMAL_VARIANCE, EDGE_DEGRADING, REGIME_MISMATCH,
EXECUTION_DEGRADATION, POSSIBLE_EDGE_FAILURE, INSUFFICIENT_DATA.

## Success and reporting

No-trade is zero net with undefined Sharpe/PF. Buy/hold is an unlevered perpetual long reference
through Nautilus (fees, slippage, funding); it is not risk-equivalent to the active risk budget.
Report static/adaptive/reference/no-trade at all costs and all periods, symbol, regime, side,
monthly contributions, top-10 concentration, drawdowns and daily Sharpe/Sortino, MAE/MFE,
turnover, switches, research and promotion outcomes. Filtered group Sharpe is attributed daily
realized PnL and explicitly differs from marked sleeve Sharpe.
Classification ADAPTIVE_NO_EDGE if no positive sealed adaptive economics or no validated profile.
WEAK requires positive sealed economics but fails robust gates. EDGE_CANDIDATE requires
positive sealed net, >=60 sealed trades, positive majority (>50%) WF folds, <=15% drawdown,
positive 1.5x cost, parameter/symbol/regime support and risk-adjusted static improvement.
ROBUST additionally requires positive 2x costs, >=100 sealed trades, >=60% WF positive,
positive net excluding top 10 and <=50% top-10 profit share, >=2 profitable symbols,
both directions supported (or explicitly validated side restriction), all active regimes supported,
and independent forward shadow evidence. Historical v1 cannot attain ROBUST without that evidence.
Negative and failed experiments remain in artifacts. No profitability promise.

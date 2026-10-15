# NautilusTrader edge discovery v1

This local research experiment uses NautilusTrader's BacktestEngine, Strategy callbacks,
market orders, MakerTakerFeeModel, native funding settlement, and accounts. No EdgeLab,
core modifications, live clients, API keys, or live order routes are used.

## Declaration before data ingestion

The adjacent config declares 32 candidates: four parameter settings at each of two
predeclared timeframes per family. All symbols share each candidate's parameters.
No symbol-specific search, additional signals, or discretionary retries after looking
at results are permitted. Engineering corrections require rerunning affected preholdout
results and are logged. A correction after opening the holdout invalidates that holdout.

All periods are UTC, start-inclusive and end-exclusive. Research is 2022–2023,
validation is 2024, walk-forward folds are January–June and July–December 2025,
and final holdout is January–June 2026. Each run starts flat with 30 days of preceding
indicator-only warmup and 10,000 USDT per symbol. No positions cross boundaries.
The last available bar open is a scheduled liquidation; its close cannot trigger entries.
The final holdout data cannot be downloaded or loaded before the freeze file exists.

## Signals

Indicators update only from completed bars in Nautilus Strategy.on_bar. Breakout levels
exclude the decision bar. ATR(14), EMA(200), EMA(lookback), and Bollinger(lookback)
are Nautilus indicators. A causal 48-bar efficiency ratio (absolute net movement /
sum absolute close changes) classifies trend >=0.35, range <=0.20, transition otherwise.
Regimes and entry side are frozen on entry, without future labels.

- Trend breakout: close exceeds prior N-bar high/low, 2 or 3 ATR close-based trailing
  stop, exit on opposite half-N channel. Appropriate to 15m/1h.
- Trend pullback: close and EMA(N) agree with EMA(200) trend; price pulls 0.5 or
  1 ATR beyond EMA(N) while staying on trend side of EMA(200). Exit at EMA(N),
  trend failure, or 2.5 ATR close-based stop. Appropriate to 15m/1h.
- Mean reversion: close outside 2 or 2.5 standard-deviation bands; efficiency <=0.20
  and price within 3 ATR of EMA(200). Exit at band center, efficiency >0.35,
  or 2 ATR close-based stop. Appropriate to 5m/15m.
- Volatility breakout: prior bar's Bollinger width <=0.6 or 0.8 times trailing
  96-bar mean width; current width expands and close clears prior N-bar channel.
  Compression arms a 6-bar breakout window. Exit on opposite half-N channel
  or 2.5 ATR close-based trailing stop. Appropriate to 5m/15m.

All families have a fixed maximum 96-bar holding time and at most one position per
symbol. No immediate reversal, pyramiding, or intrabar stop assumptions. The native hedging OMS
assigns a distinct position ID to each round trip; the strategy permits only one active
position and never opens simultaneous opposing positions. ATR stops
are evaluated on completed closes and execute at the next open; gaps can exceed risk.

## Deterministic execution and funding

A completed bar arrives at its Binance close timestamp. A synthetic executable quote
at the following actual bar open +1 ms supplies bid/ask = open minus/plus adverse
slippage, rounded outward to venue ticks. Strategy.on_quote submits pending market
orders through Nautilus. Bar execution and trade execution are disabled: OHLC highs/lows
cannot fill orders. These quotes are an execution model derived from bars, not historical
order-book observations. Slippage includes an assumed spread/impact allowance and is
not a reconstruction of actual liquidity. Quotes have bounded depth; position notional
is <=0.9x capital and order size <=0.1% of prior completed bar base volume.

Sizing risks a fixed 0.25% of initial capital at the initial ATR distance, rounded down
to size step. Capital does not compound in sizing; all equity and returns include costs.
VIP0 USD-M assumed taker fee is 5 bps each side, without discounts. Slippage scenarios
are 1, 2, and 3 bps per fill; cost2x doubles taker fees and base slippage. Funding is
not doubled because it is a signed transfer rather than execution cost.

Download Binance Vision monthly USD-M klines, markPriceKlines, and fundingRate archives,
verify the publisher SHA256 sidecars, and retain raw archives plus local checksums.
Missing monthly kline timestamps are repaired only from checksum-verified public daily
archives; no interpolation or synthetic prices are allowed.
Funding archive calc_time has reporting jitter: normalize to the preceding minute only
when jitter is <60 seconds, retain original timestamp, and settle the historical rate
at its intended boundary. Rates never enter a signal. The mark bar OPEN at the exact
boundary is supplied as a native MarkPriceUpdate, then native FundingRateUpdate settles
before +1 ms quotes. No mark HIGH/LOW/CLOSE is used in settlement. If an archive lacks the exact funding-boundary
mark bar, use the contemporaneous trade-bar OPEN as an explicitly counted proxy; this
limits funding valuation accuracy and precludes the strongest classification.

Binance exchangeInfo can be region-restricted. Declared conservative fixed tick/lot
specifications and a 100 USDT minimum notional are used; these are not claimed to be
point-in-time filter snapshots. This limitation precludes ROBUST_EDGE_CANDIDATE until
historical filter evidence is supplied. No liquidation modeling is needed at <=0.9x
notional, but this remains an unlevered bar-resolution execution experiment.

## Selection and final one-time opening

Research ranks candidates by equal-weight daily portfolio Sharpe (tie: net PnL then ID).
The research winner in each family is tested on 2024 validation. WF1 selects using
research+validation; WF2 selects using research+validation+WF1. Each fold evaluates its
chosen candidate only in the subsequent unseen fold. All grid runs are persisted to
measure neighborhoods; unseen-fold candidate results never enter that fold's choice.

After WF2, one final representative per family is selected using all preholdout data
by the same fixed rank. Preholdout promotion requires validation and adaptive WF net
profit, >=60 OOS trades, >=10 trades for each symbol, >=2 profitable symbols, both
WF folds profitable, PF>=1.05, drawdown<=20%, positive at 3bp and doubled execution
cost, and at least half of same-timeframe one-coordinate parameter neighbors profitable
on validation+WF. Concentration gates require profit excluding the best trade and best
month to remain positive, best trade <=25% of positive-trade profits and best month
<=50% of positive-month profits. Long/short results are separately reported; both must
be positive for promotion. This intentionally demanding rule may select no eligible edges.

The freeze records all four representatives including failed controls, eligibility,
source/config/data/result hashes, and adaptive WF decisions. Only then can the final
holdout be opened once. All four frozen representatives run every cost scenario on the
holdout; no replacements, parameter changes, or rankings are allowed afterward.

NO_EDGE means final net<=0, nonpositive preholdout OOS, or failed integrity. WEAK_EDGE
means positive preholdout OOS and final net but insufficient robustness/sample evidence.
EDGE_CANDIDATE requires every preholdout gate, >=30 final trades, positive final net,
PF>=1.05, and positive final 3bp and doubled-cost outcomes. ROBUST_EDGE_CANDIDATE also
requires final >=60 trades, every symbol and side profitable, all concentration gates,
and verified historical instrument specifications. These are historical research labels,
not proof of future profit or forward validation. Failed integrity is labeled NO_EDGE
with an explicit invalid flag; it cannot establish absence of a real economic edge.

## Accounting and evidence

Gross PnL uses unshifted open references for the actual filled quantity. Slippage impact
is the signed difference between references and native fills including outward tick
rounding. Net = gross - slippage - native fees + native funding. Reconcile every run to
the native account and closed positions. Daily equity is marked to completed bar CLOSE,
with realized fees/funding and unrealized PnL, including a starting equity observation.
Sharpe/Sortino annualize daily returns with sqrt(365), no risk-free rate; Calmar uses
CAGR/drawdown. Undefined metrics are JSON null, never infinite. Portfolio metrics use
three equally funded sleeves. Capital resets only at declared period boundaries; research
is one continuous 2022–2023 run. Multi-period Sharpe, Sortino, drawdown and returns chain-link
the normalized equity of the independent period runs, avoiding artificial wealth below zero
from repeated capital resets. Net PnL remains the nominal sum of native period PnLs; a
multi-period compounded return is therefore distinct from nominal PnL / initial capital. Exposure is time invested / total symbol-time; turnover
is two-sided filled notional / initial capital. Trade PF, expectancy, win/loss are net
of fees, slippage, and funding. Trade/month exclusions and side/regime tables accompany
all representative runs. Multiple testing count is 32 candidates, reported without
claiming statistical significance. Prefix replay and future-tail mutation checks probe
obvious leakage; they do not certify the absence of every possible bias.

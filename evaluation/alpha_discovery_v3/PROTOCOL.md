# Alpha Discovery v3 protocol

This is alpha-library research, not Adaptive Trading v3. All history through
2026-09-30 is CONSUMED. Chronological validation and pseudo-live results are
RETROSPECTIVE_EVIDENCE. Future prospective shadow is reserved for confirmation.
No private endpoints, credentials, live orders, core modifications or reference merges.

## Finite research budget and sequence

Phase 0: read edge v1, adaptive v1 and adaptive v2 at the commits in config.json.
Phase 1: freeze 12 directional hypotheses across six mechanisms, two raw breakout
controls and two logistic breakout filters (16 primary treatments). Phase 2:
execute exactly two non-promotable threshold neighbors for each of the 12 economic
hypotheses (24 paths). Phase 3: four predeclared exit interventions on multi-horizon
trend (two directions x structure/invalidation or volatility contraction exits).
44 paths x 3 symbols x 3 costs = 396 native runs maximum. BTC cross-asset paths
are deliberate zero-trade controls. No result-dependent parameter, symbol, side,
exit or gate changes. Failures may generate inert next-version proposals only.
Engineering corrections must be documented and invalidate affected cached runs.

## Chronology

40-day warmup; continuous independent accounts 2024-01-01 to 2026-10-01 UTC.
Development: 2024. Rolling validation / walk-forward: seven fixed quarters from
2025-Q1 through 2026-Q3. Each monthly pseudo-live decision uses a trailing 365-day
window ending seven days before the decision; only fully contained trades count.
Profiles stay fixed. Rolling admission is evidence about past-only eligibility;
it does not pretend an adaptive controller has been exercised. No resets at monthly
or quarterly boundaries. Marked interval PnL retains boundary positions; purged
trade diagnostics are explicitly different from marked returns.

Logistic models fit expanding prior data quarterly, 24-hour embargo, labels use
16 subsequent 15m closes, sampled hourly to reduce overlap. Fit standardization
on training only; L2=1, 200 deterministic gradient steps, probability threshold .55.
Separate side-specific models. Labels measure signed 4h log return minus 12bp;
actual next-open fills and full costs decide economics, never label accuracy.
Compare each model to the same raw breakout control. No tuning or random shuffle.

## Mechanics

All signals use completed 5m/15m/1h/4h information; higher frames use backward joins
on availability timestamps. Signal end minus 1ms, execution next 15m open plus 1ms.
The position uses at most 0.25% of its 10,000USDT sleeve as initial stop risk,
0.9x notional and 0.1% of previous completed 15m volume. Risk is reduced by
min(1, trailing annual-volatility target .40 / estimated annual volatility).
No leverage increase. Conservative minimum 100USDT; outward tick rounding and
quantity floor; fixed instrument filters are not historical snapshots.
5bp taker and 1bp adverse slippage on every fill; 1.5x/2x multiply both.
Observed signed funding at each settlement, unscaled. Historical mark-open proxies
are disclosed. No maker queue fill assumptions. Stops observe completed closes
and can gap. Exit eligibility is independent of entry regime compatibility.

## Families and asymmetry

MHT: 4h and 1h trend agreement, 15m retracement/resumption, 5m directional entry.
BQ: prior 24h breakout plus participation, signed taker flow, range expansion,
volatility percentile and low recent failed-breakout frequency. Raw controls omit
quality filters. CROSS: altcoin relative strength against BTC, leader regime,
correlation and local confirmation; BTC deliberately ineligible. FUND: separate
negative-funding long squeeze and expensive-positive-funding short unwind, using
only last published settlement, with trend/price confirmation. VOL: prior
compression followed by range expansion long; high-volatility persistent downtrend
short. RANGE: liquidity shock reversal long / exhaustion short in inefficient
range, without trading every band touch. Exact formulas in alpha/profiles.py.
All threshold neighbors perturb one named economic threshold +/-20%, never replace
central profiles. Long and short logic may differ. Specialized symbol universes
and eligible regimes are declared before scoring; no hindsight specialization.

## AI research scientist boundary

The assistant diagnoses mechanisms, ranks plausibility, predeclares falsifiable
experiments, analyzes failures and emits inert proposals. The finite workflow
records experiment -> result -> diagnosis -> next-version hypothesis. Deterministic
gates alone classify profiles. No AI output activates or promotes a strategy.

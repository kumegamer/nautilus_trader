# Adaptive Trading v2 predeclared experiment

All history through 2026-09-30 is CONSUMED. Every historical result is
RETROSPECTIVE_EVIDENCE, including rolling simulations. No historical final holdout
exists in this experiment. Only events acquired after the prospective freeze and
forward start can be PROSPECTIVE_EVIDENCE. No ROBUST_EDGE classification is possible.

Read-only sources: adaptive v1 at 8acc5c4c3138b8057dc1da9f853b9a3a4bb9c4e9
and edge discovery v1 at 3c669f91dd195266107a2f5b77c5c991565840a8.
V2 branches from develop de794053685c3a3b7ae74eb995e2b31215786b25;
neither reference branch is merged. Source reused from these experiments is copied
into V2 with provenance, leaving the original objects and paths unchanged.

## Hypotheses and trial budget

A: short hourly 48-bar breakouts in low-volatility trends may transfer better than
their symmetric counterparts. B: 15-minute compression breakouts may work primarily
in expansion. C: regime entry eligibility and position invalidation should differ;
immediate regime exits may interrupt favorable right-tail outcomes. D: a slower
96-hour trend channel with 3ATR sizing and volatility scaling may offer an alternative.
E: a controller using prior validation and decay information may improve daily
Sharpe and return/drawdown versus fixed profiles. All are hypotheses, not edges.

Six active directional profiles + NO_TRADE. No symbol-specific parameters or
eligibility search. Each profile is run under four exits (24 treatments), each at
base/1.5x/2x execution costs. Two one-coordinate neighbors per profile (12) test
stability only under the primary ENTRY_ONLY policy, also at all three costs.
No neighbor may replace a central profile. No threshold search or post-result tuning.
VST sizes at min(1, 1/volatility_ratio) times the common risk budget; all profiles
risk at most 0.25% initial sleeve capital, with 0.9x notional cap, no leverage uplift.

## Entry versus exit policies

ENTRY_ONLY (primary): stable compatible regime controls entry; stops, opposite
half-channel and maximum age control exits. A controller change waits until flat.
PERSIST_4: same entry; exit after four consecutive completed hourly incompatible
stable observations. CONFIDENT_80: same entry; force exit when stable incompatibility
has confidence >=0.80 and raw candidate persistence >=2 completed hours.
V1_IMMEDIATE: raw v1 regime compatibility controls entry and immediate close-based
forced exit, without V2 smoothing, as an overlay control. It uses the new directional
profiles and therefore is not claimed to reproduce the complete V1 experiment.
Hard risk/execution safety exits can override every policy. No same-quote reversal.

## Regime rules

Features retain the causal v1 closed-bar calculations (5m -> 15m/1h/4h,
backward joins). Raw v1 labels remain available for the control.
V2 evaluates transitions on completed hours: minimum two matching candidate
observations and four-hour stable dwell, except immediate MARKET_STRESS.
Expansion enters at vol ratio >1.8 and remains until <1.6; compression enters
below 0.6 and remains until >0.7. Trend enters at efficiency >0.32 and absolute
slope >0.02; persists above 0.24 and 0.015. High vol enters above 1.25 and
remains above 1.10. Stress uses v1 >3 vol or >8% six-hour move with vol >1.5.
Confidence is an uncalibrated rule-distance score, never a probability. Pending
incompatible raw labels lower entry confidence; one noisy label cannot force a
V2 transition. Log raw candidates, confidence, persistence, dwell, transitions.
False/short-lived means stable duration <8 hours (descriptive, not a known truth).

## Walk-forward selection

Continuous simulation 2024-01-01 through 2026-10-01 UTC, 40-day indicator warmup.
Training: first calendar year. Evaluations start 2025-01-01, then monthly through
2026-09. At each boundary, use preceding 365 days ending seven days before the
boundary. Purge trades whose entry or exit crosses the window or chronological
third boundaries. Gate specification is frozen in GATES.md before any scoring.
Record exact window, evidence end, failed gates and all eligible profiles.
Profiles are evaluated on their own fully reexecuted paths, not by deleting trades
from v1. Only central ENTRY_ONLY profiles can enter the adaptive controller.
Training evidence and cost/stability simulations are timestamp-filtered to the past.
Historical feature precomputation must be prefix-invariant; no future labels or ranks.

Controller: fixed priority declared in config, compatible eligible profiles only,
entry confidence >=0.55; 24h switch spacing; maximum 12 changes per rolling 30 days.
Keep current profile while a position exists except a hard safety exit. New entries
are blocked immediately when eligibility expires. Daily/transition/trade events
evaluate rolling 90-day outcomes. >=20 trades AND >=30 elapsed days plus negative
expectancy/PF<1 reduce risk to half. >=4% marked drawdown also reduces risk;
>=8% drawdown or >=15bp execution cost per turnover after >=10 trades quarantines
for 30 days, exits at next executable open and triggers research. Recovery needs
a fresh monthly validation and normal rolling economics. Sparse samples never imply
positive evidence; elapsed time alone can trigger investigation but not promotion.

## Execution and comparisons

NautilusTrader is the only order/fill/position/account/funding execution engine.
No core changes, live execution clients, trading keys or exchange order calls.
Signals use completed closes (end minus 1ms), execute at next 15m open +1ms
with adverse synthetic bid/ask, outward tick rounding, 5bp taker fees per fill and
1bp base slippage. Stress multiplies fees and slippage 1.5x/2x, signed observed
funding remains unscaled. Native positions and final accounts must reconcile.
Bar fills disabled. Close-observed stops can gap; no intrabar protection claim.
No account resets at monthly boundaries. Only final retrospective liquidation.

Three independent 10,000USDT sleeves. 100USDT minimum and 0.1% previous completed
15m base-volume cap; fixed conservative symbol filters are not historical snapshots.
Best static is selected on 2024 only, frozen for 2025-Sep2026, even if ineligible;
also report best full-period static as a hindsight diagnostic explicitly.
NO_TRADE has zero returns and undefined risk ratios. Passive benchmark: long
perpetual, monthly rebalanced at min(25%, 10% annual volatility / trailing 30-day
annualized daily volatility), using only past closes, fees/slippage/funding included.
This shares risk restraint but is not an exact exposure/beta match. Report average
marked and entry-notional exposure, time in market, turnover, return/exposure,
allocated capital return, daily volatility, marked maximum DD, Sharpe, Sortino,
return/DD and CAGR/DD (Calmar). Never scale leverage upward to match PnL.

Exit diagnostics: interrupted trades and signed mark-to-market after forced exits
at 4h/24h/96h; these are descriptive excursions, not executable policy profit.
The full independent policy simulations provide the actual PnL counterfactual,
including occupancy changes, sizing and costs.

## Claims and freeze

NO_EDGE if no eligible profile, nonpositive adaptive PnL or integrity failure.
WEAK_EDGE if positive retrospective profile/controller economics but candidate
criteria fail. EDGE_CANDIDATE requires >=60 adaptive evaluation trades, positive
base/1.5x/2x net, Sharpe above the 2024-selected static, >half positive monthly
folds, DD <=15%, two positive symbols and at least one eligible profile.
Prefix causality and accounting checks must pass. These are descriptive labels
after multiple trials on consumed history, not statistical proof.

After development freeze executable source, profiles, regime, gates, policy,
initial eligibility and dependency versions with SHA256. Prospective shadow uses
exact frozen logic; proposals cannot activate changes. Any change after seeing
prospective performance requires a new version and fresh forward evidence.

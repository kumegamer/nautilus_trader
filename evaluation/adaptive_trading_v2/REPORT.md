# Nautilus Adaptive Trading System v2

Classification: **V2_RETROSPECTIVE_NO_EDGE**. All historical results below are
**RETROSPECTIVE_EVIDENCE** on consumed data. No new untouched historical holdout
exists, no ROBUST_EDGE is claimed, and real-money trading is disabled.

The fixed comparator selected from 2024 information is `TB_SHORT`.
The supplementary comparator selected from all 24 predeclared treatments using
2024 only is `TB_SHORT` with
`CONFIDENT_80`. The primary selection
remains unchanged.

Adaptive historical execution exercised: **False**.
Adaptive beats that comparator on both Sharpe and return/drawdown:
**False**.
Final prospective-shadow-eligible profiles: **none**.

## Evidence boundaries and experiment design

Read-only reference commits: adaptive v1 `8acc5c4c3138b8057dc1da9f853b9a3a4bb9c4e9`
and edge discovery v1 `3c669f91dd195266107a2f5b77c5c991565840a8`. The original V1
autopsy's eight artifact reconciliation tests pass unchanged. V2 branches from
develop `de794053685c3a3b7ae74eb995e2b31215786b25`; neither reference is merged.
All strategy, gate, data and report changes are confined to the new V2 directory.

`PROTOCOL.md`, `GATES.md` and `config.json` were hashed before candidate scoring.
The hypotheses are short breakout specialization in low-volatility trends,
volatility breakout specialization in expansion, entry-only regime gating versus
forced exits, slower volatility-scaled trends, and prior-information adaptive
selection. Prior TB48_SHORT/VB48 descriptive slices were hypothesis inputs only.
No V1 profile admission or profit observation is treated as independent validation.

There are six central directional profiles, four exit policies (24 treatments),
12 distinct one-coordinate stability neighbors, and three execution-cost scenarios.
No symbol-specific parameters, threshold search, neighbor replacement or gate waiver.
Engineering corrections and superseded runs are described in ARCHITECTURE.md.

## Architecture and regime definitions

See ARCHITECTURE.md for the component diagram and V1 lesson mapping. Public market
events feed causal completed-bar features, raw/stable regimes, immutable profiles,
the past-only evaluator, finite controller and native Nautilus order execution.
Native closed positions, fees, funding and final accounts reconcile in each run.

V2 retains raw v1 labels for control. Stable transitions use two completed hourly
candidate observations, four-hour dwell and immediate stress override. Expansion
1.8/1.6 and compression 0.6/0.7 have distinct entry/exit thresholds. Trend efficiency
0.32/0.24 and slope 0.02/0.015 similarly differ; high-volatility entry/exit is
1.25/1.10. Confidence is an uncalibrated rule-distance score. Entry compatibility
and position invalidation are separate decisions. Complete definitions are frozen
in PROTOCOL.md; confidence is never interpreted as a probability.

Unique market-path statistics, excluding warmup and repeated cost/strategy runs:

| symbol | raw changes | stable changes | short stable <8h | mean stable h |
|---|---|---|---|---|
| BTCUSDT | 1466 | 676 | 124 | 35.5923 |
| ETHUSDT | 1360 | 644 | 116 | 37.3581 |
| SOLUSDT | 1459 | 618 | 138 | 38.9273 |

Short-lived transitions are descriptive episodes shorter than eight hours, not
verified classification errors. Duration statistics include observed censored edge
episodes; short-lived counts exclude the initial and final censored episodes. The complete raw
and stable switch history is in results/regime_switches.csv.

## Strategy profiles and risk normalization

TB_SHORT/TB_LONG: separate 48-hour channel breakouts, 2ATR stop, low-volatility trend.
VB_SHORT/VB_LONG: separate 48x15m compression breakouts, 2.5ATR stop, expansion only.
VST_SHORT/VST_LONG: separate 96-hour channel/EMA200 trend confirmation, 3ATR stop,
both trend volatility states, risk reduced by min(1,1/volatility ratio). All positions
use a half-channel exit, trailing close-observed stop and 96 signal-bar maximum age.
NO_TRADE carries cash. Definitions and non-promotable neighbors: results/profiles.json.

Each symbol has 10,000USDT allocated capital, 0.25% maximum initial stop budget,
0.9x notional ceiling, 100USDT minimum and 0.1% prior completed 15m-volume cap.
No leverage was increased to make raw PnL comparable. The passive comparator is
an unlevered long perpetual allocation sized monthly from trailing 30 daily returns
to min(25% notional,10% annual-volatility target / estimated volatility). It pays
the same native costs and observed funding. It is a restrained opportunity
benchmark, not an exact exposure, beta or realized-volatility match.

## Retrospective pseudo-live comparison

Continuous accounts and positions run from January 2024 through September 2026.
2024 is the initial training year; evaluation below is January 2025–September 2026.
The adaptive controller starts flat, admits only prior validated profiles and
never resets at monthly boundaries. Static selection uses 2024 information only. The additional best-static hindsight
row ranks the same six fixed profiles using evaluation outcomes and is solely
a diagnostic upper comparator, never a controller or classification input.

| system | trades | net_pnl | return_on_allocated_capital | sharpe | sortino | maximum_drawdown | calmar |
|---|---|---|---|---|---|---|---|
| static_2024_selected | 45 | 187.6089 | 0.0063 | 0.4478 | 0.7456 | 0.0068 | 0.5172 |
| static_best_hindsight_diagnostic | 56 | 464.9103 | 0.0155 | 0.9004 | 2.1903 | 0.0069 | 1.2754 |
| adaptive | 0 | 0.0000 | 0.0000 | undefined | undefined | 0.0000 | undefined |
| no_trade | 0 | 0.0000 | 0.0000 | undefined | undefined | 0.0000 | undefined |
| risk_normalized_passive | 66 | -44.2520 | -0.0015 | 0.0357 | 0.0515 | 0.1505 | -0.0049 |
| static_full_grid_2024_selected | 45 | 136.0714 | 0.0045 | 0.3278 | 0.5490 | 0.0090 | 0.2837 |
| static_full_grid_best_hindsight_diagnostic | 45 | 564.7358 | 0.0188 | 1.3161 | 3.5970 | 0.0030 | 3.4886 |

| system | annual_volatility | average_exposure | time_in_market | turnover | return_per_unit_exposure | return_drawdown | time_no_trade |
|---|---|---|---|---|---|---|---|
| static_2024_selected | 0.0080 | 0.0026 | 0.0214 | 3.9328 | 2.3971 | 0.9052 | 0.0000 |
| static_best_hindsight_diagnostic | 0.0097 | 0.0021 | 0.0105 | 8.1120 | 7.4831 | 2.2366 | 0.0000 |
| adaptive | 0.0000 | 0.0000 | 0.0000 | 0.0000 | undefined | undefined | 1.0000 |
| no_trade | 0.0000 | 0.0000 | 0.0000 | 0.0000 | undefined | undefined | 1.0000 |
| risk_normalized_passive | 0.0882 | 0.1761 | 0.9996 | 7.4240 | -0.0084 | -0.0085 | 0.0000 |
| static_full_grid_2024_selected | 0.0079 | 0.0024 | 0.0197 | 3.9346 | 1.9097 | 0.4964 | 0.0000 |
| static_full_grid_best_hindsight_diagnostic | 0.0081 | 0.0009 | 0.0055 | 5.4216 | 19.9900 | 6.1221 | 0.0000 |

Returns, exposure and drawdown are decimal fractions. Net PnL is marked-equity
change over the comparison interval; allocated-capital return divides it by 30,000.
Daily Sharpe/Sortino use actual sleeve equity, zero risk-free rate and 365-day
scaling. Calmar is CAGR/marked drawdown. Average exposure is mean marked notional /
initial capital, not leverage rescaling. Return per exposure is descriptive and
does not imply that sparse capacity can be scaled safely. Undefined ratios remain
null; cash does not acquire a zero Sharpe or a superior trading Sharpe.

Trade counts, PF and concentration use realized exit-period attribution, including
full trades crossing the initial evaluation boundary. `closed_trade_attribution_net`
therefore differs from marked PnL when a position crosses a boundary. Period fees,
slippage, funding and turnover are timestamp-attributed native events. Monthly
marked PnL adds exactly to the full evaluation PnL. No cross-boundary position is
silently removed to manufacture a cleaner return.

## Central profile evaluation and side separation

| profile | side | trades | net_pnl | profit_factor | sharpe | maximum_drawdown | average_exposure |
|---|---|---|---|---|---|---|---|
| TB_SHORT | -1 | 45 | 187.6089 | 1.3116 | 0.4478 | 0.0068 | 0.0026 |
| TB_LONG | 1 | 58 | -239.0285 | 0.7438 | -0.5076 | 0.0176 | 0.0046 |
| VB_SHORT | -1 | 54 | 38.9221 | 1.0538 | 0.1026 | 0.0086 | 0.0014 |
| VB_LONG | 1 | 56 | 464.9103 | 1.8285 | 0.9004 | 0.0069 | 0.0021 |
| VST_SHORT | -1 | 62 | 156.9412 | 1.2617 | 0.3722 | 0.0068 | 0.0034 |
| VST_LONG | 1 | 73 | 63.0949 | 1.0693 | 0.1388 | 0.0126 | 0.0060 |

All profiles, neighbors, time windows and costs remain in results/profile_results.csv.
Per-symbol metrics are in per_symbol_results.csv; long/short, entry regime and
actual adaptive profile decomposition is in long_short_regime_decomposition.csv.
Regime/side attribution is realized-trade economics, not marked portfolio Sharpe.
The ex-post best evaluation static is `VB_LONG`;
it is the best primary ENTRY_ONLY diagnostic and never a controller input.
Across all 24 treatments, the best hindsight static is
`VB_LONG` with
`V1_IMMEDIATE`. Its full
metrics are also reported as a separate hindsight diagnostic. All hindsight
choices are explicitly selection-contaminated.

## Entry regime versus exit regime experiment

ENTRY_ONLY is primary and is never replaced after scoring. PERSIST_4 waits for
four incompatible completed hourly observations. CONFIDENT_80 requires >=0.80
confidence and two-hour candidate persistence. V1_IMMEDIATE uses the raw label to
block entries and force next-open exits. It is an overlay control on V2 profiles,
not a claimed reproduction of the entire frozen V1 system.

| profile | policy | trades | net | delta vs ENTRY_ONLY | interrupted | Sharpe |
|---|---|---|---|---|---|---|
| TB_SHORT | ENTRY_ONLY | 45 | 187.6089 | 0.0000 | 0 | 0.4478 |
| TB_SHORT | PERSIST_4 | 45 | 275.3277 | 87.7188 | 17 | 0.6826 |
| TB_SHORT | CONFIDENT_80 | 45 | 136.0714 | -51.5376 | 4 | 0.3278 |
| TB_SHORT | V1_IMMEDIATE | 95 | 457.3886 | 269.7797 | 93 | 1.0720 |
| TB_LONG | ENTRY_ONLY | 58 | -239.0285 | 0.0000 | 0 | -0.5076 |
| TB_LONG | PERSIST_4 | 58 | -186.9196 | 52.1089 | 22 | -0.4511 |
| TB_LONG | CONFIDENT_80 | 58 | -248.4739 | -9.4454 | 3 | -0.5303 |
| TB_LONG | V1_IMMEDIATE | 128 | -398.2757 | -159.2472 | 117 | -1.0147 |
| VB_SHORT | ENTRY_ONLY | 54 | 38.9221 | 0.0000 | 0 | 0.1026 |
| VB_SHORT | PERSIST_4 | 54 | -96.9589 | -135.8810 | 6 | -0.2941 |
| VB_SHORT | CONFIDENT_80 | 54 | -41.0220 | -79.9442 | 3 | -0.1037 |
| VB_SHORT | V1_IMMEDIATE | 37 | -116.7714 | -155.6935 | 10 | -0.4930 |
| VB_LONG | ENTRY_ONLY | 56 | 464.9103 | 0.0000 | 0 | 0.9004 |
| VB_LONG | PERSIST_4 | 56 | 368.4755 | -96.4348 | 15 | 0.8732 |
| VB_LONG | CONFIDENT_80 | 56 | 386.3837 | -78.5266 | 11 | 0.9021 |
| VB_LONG | V1_IMMEDIATE | 45 | 564.7358 | 99.8255 | 20 | 1.3161 |
| VST_SHORT | ENTRY_ONLY | 62 | 156.9412 | 0.0000 | 0 | 0.3722 |
| VST_SHORT | PERSIST_4 | 65 | 333.2126 | 176.2714 | 48 | 0.9294 |
| VST_SHORT | CONFIDENT_80 | 62 | 269.0984 | 112.1572 | 21 | 0.6614 |
| VST_SHORT | V1_IMMEDIATE | 144 | 366.7654 | 209.8242 | 144 | 0.8888 |
| VST_LONG | ENTRY_ONLY | 73 | 63.0949 | 0.0000 | 0 | 0.1388 |
| VST_LONG | PERSIST_4 | 73 | 13.5594 | -49.5355 | 46 | 0.0428 |
| VST_LONG | CONFIDENT_80 | 73 | 55.5687 | -7.5263 | 27 | 0.1355 |
| VST_LONG | V1_IMMEDIATE | 152 | -60.7596 | -123.8545 | 147 | -0.1587 |

These are independent complete Nautilus simulations, including changed position
occupancy, later entries, size, fees and funding. `post_exit_excursions.csv` also
reports signed 4h/24h/96h price excursions following interrupted exits. Favorable
excursions are premature-looking diagnostics, not realized alternative PnL, and
do not include a newly invented holding policy or future-information entry rule.

## Frozen gates and rolling eligibility

At each monthly boundary, train on the preceding 365 days ending seven days
earlier. Trades crossing window boundaries or chronological thirds are purged.
All data are prior to each decision. The first rolling window includes six
pre-simulation days without trades because execution starts January 2024; subsequent
windows have full execution-history coverage. Sample >=60, PF>=1.05, positive net, two of
three positive chronological thirds with the last positive, 1.5x/2x cost survival,
<=15% marked drawdown, two positive symbols with >=10 trades each, a distinct
positive neighbor, and >=80% positive circular seven-day block resamples remain
mandatory. Top-one/month/symbol concentration is bounded at 25%/60%/75% of positive
contributions. See GATES.md for the pre-result rationale for every V1 gate change.
Top-five and top-ten shares/deletions remain reported diagnostics; deleting a trend
strategy's entire intended right tail is not a mandatory profitability veto.

Final matured evaluation, decision timestamp 2026-10-01 UTC:

| profile | trades | net | PF | eligible | failures |
|---|---|---|---|---|---|
| TB_SHORT | 22 | -4.0703 | 0.9886 | False | chronology, concentration, cost, economics, resampling, sample, stability, transfer |
| TB_LONG | 30 | -302.4559 | 0.3531 | False | chronology, concentration, cost, economics, resampling, sample, stability, transfer |
| VB_SHORT | 28 | 45.1219 | 1.1195 | False | chronology, concentration, cost, resampling, sample, transfer |
| VB_LONG | 25 | 558.7306 | 4.0642 | False | sample, transfer |
| VST_SHORT | 33 | 53.7900 | 1.1499 | False | chronology, concentration, resampling, sample, transfer |
| VST_LONG | 38 | -306.6420 | 0.4091 | False | chronology, concentration, cost, economics, resampling, sample, stability, transfer |

All monthly gate failures: `{'concentration': 103, 'sample': 132, 'transfer': 99, 'chronology': 75, 'cost': 66, 'economics': 55, 'resampling': 99, 'stability': 47}`. Historical admissions by profile:
`{}`. Gate counts are correlated diagnostics, not independent tests.
Primary-profile maximum matured rolling trade counts are:
`{'TB_SHORT': 30, 'TB_LONG': 43, 'VB_SHORT': 34, 'VB_LONG': 46, 'VST_SHORT': 41, 'VST_LONG': 49}`.
All primary profiles blocked by sample requirements in every window:
**True**. The primary admission
library is ENTRY_ONLY; alternative exit treatments are predeclared diagnostic
controls and do not acquire eligibility from an ex-post ranking. Their separate
policy-specific promotion/stability pipeline is not established by this experiment.
When no profiles qualify, the performance-adaptation objective remains
underexercised and adaptive trading benefit remains unproven. Mechanical fixture
trades do not change that conclusion. The gates remain unchanged.

Every record retains its availability, expiry, training window, costs, neighbors,
resampling distribution and gate failures in results/eligibility.json.

## Adaptive decisions and edge decay

Fixed priority among compatible eligible profiles avoids hindsight return ranking.
Entry confidence >=0.55, 24h switch spacing and 12 switches per 30 days limit churn.
Existing positions retain their strategy management until flat, except a hard
risk/execution safety exit. Expired eligibility blocks entries without automatically
invalidating a position. Full switch records contain timestamp, symbol, old/new
profile, regime, confidence, performance state, reason and available eligible set.

Daily time, new trades and regime changes trigger monitoring. Rolling 90-day
expectancy, PF, daily Sharpe, MAE/MFE, drawdown, costs, slippage and side/regime
decomposition are retained. Negative expectancy and PF<1 require >=20 observations
and >=30 elapsed days before performance risk reduction; drawdown or execution
degradation can act separately. The controller uses no fixed 50-trade activation
rule. Zero/half/full risk choices and 30-day quarantine never mutate parameters.
Mechanical fixture switching is explicitly separate from actual historical exercise.

## Cost stress and monthly walk-forward outcomes

Base costs: 5bp taker fee plus 1bp adverse slippage per fill with outward tick
rounding. Both are multiplied 1.5x/2x. Signed observed funding is not multiplied.

| system | scenario | net_pnl | fees | funding | slippage | sharpe | maximum_drawdown | profile_switches |
|---|---|---|---|---|---|---|---|---|
| static_2024_selected | base | 187.6089 | 58.9926 | -0.6445 | 12.0766 | 0.4478 | 0.0068 | 0 |
| static_2024_selected | cost1.5x | 152.2648 | 88.4889 | -0.6445 | 17.9244 | 0.3629 | 0.0075 | 0 |
| static_2024_selected | cost2x | 116.7845 | 117.9852 | -0.6445 | 23.9084 | 0.2782 | 0.0081 | 0 |
| static_best_hindsight_diagnostic | base | 464.9103 | 121.6798 | 0.3044 | 24.7812 | 0.9004 | 0.0069 | 0 |
| static_best_hindsight_diagnostic | cost1.5x | 391.8492 | 182.5197 | 0.3044 | 37.0024 | 0.7600 | 0.0074 | 0 |
| static_best_hindsight_diagnostic | cost2x | 279.7248 | 251.8459 | 0.2527 | 50.7578 | 0.5372 | 0.0092 | 0 |
| adaptive | base | 0.0000 | 0.0000 | 0.0000 | 0.0000 | undefined | 0.0000 | 0 |
| adaptive | cost1.5x | 0.0000 | 0.0000 | 0.0000 | 0.0000 | undefined | 0.0000 | 0 |
| adaptive | cost2x | 0.0000 | 0.0000 | 0.0000 | 0.0000 | undefined | 0.0000 | 0 |
| no_trade | base | 0.0000 | 0.0000 | 0.0000 | 0.0000 | undefined | 0.0000 | 0 |
| no_trade | cost1.5x | 0.0000 | 0.0000 | 0.0000 | 0.0000 | undefined | 0.0000 | 0 |
| no_trade | cost2x | 0.0000 | 0.0000 | 0.0000 | 0.0000 | undefined | 0.0000 | 0 |
| risk_normalized_passive | base | -44.2520 | 111.3599 | -296.6355 | 22.7543 | 0.0357 | 0.1505 | 0 |
| risk_normalized_passive | cost1.5x | -111.0027 | 167.0397 | -296.6355 | 33.8252 | 0.0232 | 0.1515 | 0 |
| risk_normalized_passive | cost2x | -177.8189 | 222.7194 | -296.6355 | 44.9617 | 0.0107 | 0.1524 | 0 |
| static_full_grid_2024_selected | base | 136.0714 | 59.0184 | -0.5352 | 12.0811 | 0.3278 | 0.0090 | 0 |
| static_full_grid_2024_selected | cost1.5x | 100.7121 | 88.5277 | -0.5352 | 17.9312 | 0.2430 | 0.0096 | 0 |
| static_full_grid_2024_selected | cost2x | 65.2142 | 118.0369 | -0.5352 | 23.9199 | 0.1582 | 0.0102 | 0 |
| static_full_grid_best_hindsight_diagnostic | base | 564.7358 | 81.3234 | 0.8079 | 16.5564 | 1.3161 | 0.0030 | 0 |
| static_full_grid_best_hindsight_diagnostic | cost1.5x | 515.9116 | 121.9852 | 0.8079 | 24.7190 | 1.2085 | 0.0032 | 0 |
| static_full_grid_best_hindsight_diagnostic | cost2x | 427.9312 | 171.1332 | 0.7562 | 34.5086 | 0.9896 | 0.0044 | 0 |

Monthly marked PnL (USDT), with decisions based on preceding information only:

| month | static_2024_selected | adaptive | no_trade | risk_normalized_passive |
|---|---|---|---|---|
| 2025-01 | 3.1571 | 0.0000 | 0.0000 | 444.8443 |
| 2025-02 | 209.7039 | 0.0000 | 0.0000 | -1,247.1274 |
| 2025-03 | -58.6213 | 0.0000 | 0.0000 | -487.3852 |
| 2025-04 | 21.4017 | 0.0000 | 0.0000 | 293.7374 |
| 2025-05 | -21.9528 | 0.0000 | 0.0000 | 676.9539 |
| 2025-06 | -26.4363 | 0.0000 | 0.0000 | 15.1295 |
| 2025-07 | -16.6966 | 0.0000 | 0.0000 | 1,106.4502 |
| 2025-08 | -14.8752 | 0.0000 | 0.0000 | 374.8744 |
| 2025-09 | 95.9986 | 0.0000 | 0.0000 | 100.6979 |
| 2025-10 | -46.4630 | 0.0000 | 0.0000 | -383.9280 |
| 2025-11 | 0.0000 | 0.0000 | 0.0000 | -1,035.7348 |
| 2025-12 | -42.6158 | 0.0000 | 0.0000 | -123.2089 |
| 2026-01 | 10.3146 | 0.0000 | 0.0000 | -867.6387 |
| 2026-02 | 34.5398 | 0.0000 | 0.0000 | -904.7484 |
| 2026-03 | -50.5301 | 0.0000 | 0.0000 | 89.4358 |
| 2026-04 | 0.0000 | 0.0000 | 0.0000 | 352.7653 |
| 2026-05 | -8.9623 | 0.0000 | 0.0000 | -329.7185 |
| 2026-06 | 165.1482 | 0.0000 | 0.0000 | -1,327.1456 |
| 2026-07 | 0.0000 | 0.0000 | 0.0000 | 428.9625 |
| 2026-08 | -65.5016 | 0.0000 | 0.0000 | 2,302.6651 |
| 2026-09 | 0.0000 | 0.0000 | 0.0000 | 475.8674 |

Positive adaptive monthly folds and stressed outcomes affect the predeclared
classification. All 21 monthly folds/costs and risk/exposure metrics are retained.
Consumed-history causal decisions establish mechanical prior-information use;
the V1-informed design remains selection-contaminated. They cannot demonstrate
an independent economic improvement or rule out research hindsight.

## AI research and prospective shadow

The proposal-only `ResearchAgent` interface receives a structured copy of evidence
and writes hypotheses, modifications and experiment explanations as inert data.
It has no registry activation or executable parameter interface. Proposals require
RESEARCH -> BACKTEST -> WALK_FORWARD -> COST_STRESS -> STABILITY -> SHADOW_ELIGIBLE
and a new frozen version before activation. Sample proposal and diagnostic triggers
are saved; no language-model credentials or calls are needed by the controller.

SHADOW.md documents the public GET-only collector, immutable checksummed SQLite
journal, actual receipt timestamps, hypothetical native execution, deterministic
restart replay, monthly frozen-rule revalidation and VPS/desktop deployment templates.
The freeze binds profiles, regime, gates, controller, initial eligibility, source
and runtime provenance. Future evidence is stored separately; future observations
never silently rewrite the retrospective report. No persistent deployment was made. Public Binance futures time and book-ticker
endpoints returned HTTP 451 from this execution environment; a forward public-data
smoke test could not complete here. Native shadow replay/restart tests use
explicit engineering fixtures and are not prospective economic evidence.

## Reproducibility and limitations

Reproduction commands and exact checksums are in README.md and the artifact/freeze
manifests. All retained runs share the final execution fingerprint and native
account reconciliation. Prefix mutation, eligibility timing, entry/exit separation,
controller exercise, public-endpoint restrictions, journal restart and revision
checks are included. The original V1 inputs and results remain byte-for-byte intact.
DELIVERABLES.md maps every requested output to its saved artifact and limitation.
Final verification logs, complete matrix coverage and monthly marked-PnL
reconciliation are retained. Monthly shadow revalidation also matches an actual
continuous historical native-path prefix exactly for closed trades, fills and
funding, without a flat-window reset or cutoff liquidation. These remain
engineering checks rather than prospective economic evidence.

Only three surviving symbols are tested; historical filters are approximated.
Historical quotes are bar-derived adverse fills without observed queue/depth.
Stops are close-based and can gap. Forward polling has latency; shadow funding
at receipt can differ from exact boundary-holder settlement. Daily ratios on
sparse samples are noisy. Block resampling reuses known outcomes; 36 treatments
and V1-informed hypotheses introduce multiple-testing and selection uncertainty.
No future profitability, independent edge or real-money readiness is established.

## Required final conclusions

1. Stronger retrospective evidence under frozen gates:
   **False**. This is a descriptive V2
   comparison, not independent confirmation of the V1-derived hypotheses.
2. Adaptive beats the 2024-selected static on Sharpe and return/drawdown:
   **False**.
   Historical controller execution exercised: **False**.
3. Eligible for prospective shadow at the freeze:
   **none**.
4. Unproven: independent forward edge, future profitability, broader symbol
   transfer, realistic queue/impact and exact forward funding settlement.
5. Persistent active-profile shadow deployment justified by the frozen evidence:
   **False**. Observation-only collection
   remains useful engineering; it must not be presented as validated trading edge.

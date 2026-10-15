# Strict failure autopsy — Adaptive Trading v1

Read-only audit of commit 8219e2f8747d77ece56398f8f150bd475dbe8b0a. No optimization, strategy creation, threshold edits, trading simulation, market-data downloads, or new sealed strategy tests. The frozen evidence and source remain unchanged.

## Evidence boundaries and metric definitions

The 14-profile selection diagnosis uses preholdout evidence exclusively. The already-completed July–September 2026 final evaluation is a detached reporting appendix. Eight neighbor profiles have no sealed or cost-stress runs: N/A means NOT TESTED, not zero return or measured failure.

Outer periods: research 2024; validation Jan–Jun 2025; WF1 Jul–Dec 2025; WF2 Jan–Jun 2026. Native marked daily equity supplies their Sharpe, Sortino and drawdown. Internal promotion gates use a different 40/20/10/10/20 split with a seven-day embargo and entry/exit purge. Internal Sharpe/Sortino below are supplementary daily realized attribution, not original gate statistics or native marked subgroup equity.

Actual frozen promotion intervals: ["2024-01-01T00:00:00+00:00", "2024-12-28T00:00:00+00:00", "2025-06-27T00:00:00+00:00", "2025-09-25T12:00:00+00:00", "2025-12-25T00:00:00+00:00", "2026-06-24T00:00:00+00:00"]

The concentration gate uses the ten largest POSITIVE net trades / sum of all positive net trade profits and separately requires positive net after removing those winners. Month/symbol concentrations are descriptive; they were not additional promotion gates. Sharpe/Sortino/expectancy/win rate have no standalone admission threshold. PF has an explicit 1.05 floor.

NEAR_MISS is an annotation only for a failed PF margin with PF > 1 and < 1.05; the original frozen decision is still FAIL. There is no invented economic tolerance around negative PnL, no missing test treated as near success, and no live threshold is changed.

## Gate failure census

| Gate | Failed /14 |
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

Cost failures split into eight absent stress experiments and five measured nonpositive 2x outcomes; only TB48_SHORT passed the frozen stress gate. Seven profiles were never proposed by the reference research agent, despite being scored in the final 14-profile diagnostic snapshot.

## Closest at the final preholdout freeze

| Profile | Failed gates | Gate N | Gate net | Gate PF | Measured 2x? |
| --- | --- | --- | --- | --- | --- |
| TB48_SHORT | 4 | 149 | 468.70 | 1.375 | True |
| VB48_WINDOW | 5 | 126 | 306.40 | 1.211 | False |
| TB48 | 7 | 279 | 366.90 | 1.145 | True |
| TB48_FUNDING | 7 | 279 | 366.90 | 1.145 | True |
| TB48_STOP | 7 | 278 | 262.91 | 1.129 | False |
| TB48_WINDOW | 7 | 276 | 377.05 | 1.149 | False |
| VB48 | 7 | 169 | 90.81 | 1.044 | True |
| VB48_STOP | 7 | 164 | 47.18 | 1.028 | False |
| MR48_STOP | 10 | 733 | -2,581.71 | 0.748 | False |
| MR48_WINDOW | 10 | 592 | -2,171.41 | 0.786 | False |
| MR48 | 11 | 738 | -3,750.52 | 0.710 | True |
| TP24 | 11 | 13 | -11.19 | 0.780 | True |
| TP24_STOP | 11 | 13 | -8.68 | 0.786 | False |
| TP24_WINDOW | 11 | 14 | -21.77 | 0.628 | False |

This is a descriptive count of original failures, not a new optimizer or economic ranking. At the freeze even the closest profile needed four joint failures resolved. Historically TB48 and TB48_FUNDING reached 11/12 passed gates at the same 19 February 2026 request; concentration alone failed then. Both were in incompatible RANGE_LOW_VOL at that moment. No promotion occurred.

## Controller exercise and transition count

{
  "actual_changes_one_market_path": 4186,
  "logged_records_one_cost": 4189,
  "actual_changes_all_three_cost_repetitions": 12558,
  "recorded_promotions": {
    "CANDIDATE": 441,
    "REJECTED": 441,
    "RESEARCH": 420
  },
  "degradation_states_base": {
    "INSUFFICIENT_DATA": 4107
  },
  "actual_profile_switches": 0,
  "actual_trades": 0,
  "research_records_base": 714,
  "assessed_research_records_base": 441,
  "gate_failure_count_distribution": {
    "5": 54,
    "11": 51,
    "10": 87,
    "9": 27,
    "3": 36,
    "4": 63,
    "2": 33,
    "6": 30,
    "7": 39,
    "1": 6,
    "8": 15
  },
  "proposed_profiles": [
    "MR48",
    "TB48",
    "TB48_FUNDING",
    "TB48_SHORT",
    "TB48_STOP",
    "TP24",
    "VB48"
  ],
  "near_miss_only_diagnostic": {
    "rule": "Accept PASS or pre-established autopsy PF-margin NEAR_MISS only; every true FAIL blocks",
    "annotation_provenance": "Original frozen promotion gates are binary. Autopsy NEAR_MISS means failed PF floor with 1 < PF < 1.05, established using preholdout data only before clarification.",
    "eligible_profiles_at_final_freeze": [],
    "eligible_profiles_at_recorded_preholdout_requests": [],
    "additional_hypothetical_switches": 0,
    "incremental_subsequent_net_pnl": 0,
    "performance_effect": "UNCHANGED: no newly eligible profiles, so no additional positions or switches",
    "final_freeze_near_misses": [
      {
        "profile": "VB48",
        "gates": [
          "profit_factor"
        ],
        "profit_factor": 1.0444813217561744
      },
      {
        "profile": "VB48_STOP",
        "gates": [
          "profit_factor"
        ],
        "profit_factor": 1.0275114141374169
      }
    ],
    "records_checked": 392,
    "holdout_used_for_eligibility": false,
    "thresholds_changed": false,
    "arbitrary_fail_waivers": 0
  }
}

| Period | Symbol | Recorded | Actual changes |
| --- | --- | --- | --- |
| research | BTCUSDT | 542 | 541 |
| research | ETHUSDT | 504 | 503 |
| research | SOLUSDT | 535 | 534 |
| validation | BTCUSDT | 242 | 242 |
| validation | ETHUSDT | 238 | 238 |
| validation | SOLUSDT | 293 | 293 |
| wf1 | BTCUSDT | 259 | 259 |
| wf1 | ETHUSDT | 259 | 259 |
| wf1 | SOLUSDT | 247 | 247 |
| wf2 | BTCUSDT | 282 | 282 |
| wf2 | ETHUSDT | 241 | 241 |
| wf2 | SOLUSDT | 247 | 247 |
| holdout | BTCUSDT | 106 | 106 |
| holdout | ETHUSDT | 84 | 84 |
| holdout | SOLUSDT | 110 | 110 |

The 131,648 figure in the original report summed regime logs from static/reference/adaptive runs and cost repetitions. The independent adaptive market path contains 4,186 changes across three symbols, including 300 in the completed holdout. 4,189 recorded rows include three UNKNOWN→UNKNOWN initialization records. Three cost repetitions are not three independent market histories.

## Hypothetical relaxation: bounded interpretation only

{
  "rule": "Accept PASS or pre-established autopsy PF-margin NEAR_MISS only; every true FAIL blocks",
  "annotation_provenance": "Original frozen promotion gates are binary. Autopsy NEAR_MISS means failed PF floor with 1 < PF < 1.05, established using preholdout data only before clarification.",
  "eligible_profiles_at_final_freeze": [],
  "eligible_profiles_at_recorded_preholdout_requests": [],
  "additional_hypothetical_switches": 0,
  "incremental_subsequent_net_pnl": 0,
  "performance_effect": "UNCHANGED: no newly eligible profiles, so no additional positions or switches",
  "final_freeze_near_misses": [
    {
      "profile": "VB48",
      "gates": [
        "profit_factor"
      ],
      "profit_factor": 1.0444813217561744
    },
    {
      "profile": "VB48_STOP",
      "gates": [
        "profit_factor"
      ],
      "profit_factor": 1.0275114141374169
    }
  ],
  "records_checked": 392,
  "holdout_used_for_eligibility": false,
  "thresholds_changed": false,
  "arbitrary_fail_waivers": 0
}

Only existing PF-buffer NEAR_MISS annotations may be accepted. Every true FAIL blocks eligibility. The original frozen gates are binary and contain no NEAR_MISS state; the descriptive PF annotation was defined in this autopsy from preholdout evidence before the user clarification, not in the original trading protocol. No eligible profile means zero additional switches and zero incremental subsequent performance. No holdout performance is used for this decision.

## Per-profile dossiers

### TB48_SHORT

Family: trend_breakout. Symbols: BTCUSDT, ETHUSDT, SOLUSDT. Signal timeframe: 60m; execution grid: 15m; causal context: 5m/15m/1h/4h. Parameters: `{"allow_long": false, "allow_short": true, "band_k": 2.5, "compression": 0.8, "funding_filter": false, "lookback": 48, "minutes": 60, "pullback_atr": 1.0, "stop_atr": 2.0}`. Compatible regimes: ['TREND_LOW_VOL', 'TREND_HIGH_VOL'].

Total preholdout trades: 219; purged qualifying gate trades: 149. These are different universes; neither includes the July–September sealed evaluation.

Outer chronological metrics — native marked risk statistics:

| Scope | N | Net | PF | Sharpe | Sortino | E/trade | DD % | Win % | Fees | Slip | Funding | Long net | Short net |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| research | 67 | 254.01 | 1.607 | 1.073 | 2.266 | 3.791 | 0.45 | 44.78 | 73.58 | 14.97 | 4.68 | 0.00 | 254.01 |
| validation | 52 | 538.24 | 2.687 | 2.515 | 9.740 | 10.351 | 0.26 | 44.23 | 57.49 | 11.70 | 1.32 | 0.00 | 538.24 |
| wf1 | 47 | -54.42 | 0.852 | -0.346 | -0.685 | -1.158 | 0.64 | 21.28 | 56.22 | 11.38 | 0.95 | 0.00 | -54.42 |
| wf2 | 53 | -11.31 | 0.980 | -0.031 | -0.048 | -0.213 | 1.07 | 39.62 | 74.89 | 15.25 | -1.60 | 0.00 | -11.31 |

Actual internal promotion splits — realized daily attribution for Sharpe/Sortino/DD; exact original drawdown gate separately below:

| Scope | N | Net | PF | Sharpe | Sortino | E/trade | DD % | Win % | Fees | Slip | Funding | Long net | Short net |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| internal_train | 67 | 254.01 | 1.607 | 0.974 | 2.623 | 3.791 | 0.57 | 44.78 | 73.58 | 14.97 | 4.68 | 0.00 | 254.01 |
| internal_validation | 52 | 538.24 | 2.687 | 1.909 | 8.288 | 10.351 | 0.43 | 44.23 | 57.49 | 11.70 | 1.32 | 0.00 | 538.24 |
| internal_wf1 | 14 | 9.66 | 1.124 | 0.259 | 0.561 | 0.690 | 0.19 | 21.43 | 19.85 | 4.01 | 0.46 | 0.00 | 9.66 |
| internal_wf2 | 33 | -64.08 | 0.779 | -0.616 | -1.200 | -1.942 | 0.64 | 21.21 | 36.37 | 7.36 | 0.49 | 0.00 | -64.08 |
| internal_oos | 50 | -15.11 | 0.973 | -0.104 | -0.160 | -0.302 | 0.77 | 38.00 | 70.73 | 14.39 | -1.60 | 0.00 | -15.11 |

Exact frozen gates:

| Gate | Status (original) | Threshold | Observed | Comment |
| --- | --- | --- | --- | --- |
| sample | PASS (PASS) | {"number_of_trades": ">=60"} | 149 |  |
| validation_positive | PASS (PASS) | {"trades": ">=10", "net": ">0"} | {"trades": 52, "net": 538.2420604299999} |  |
| walk_forward | FAIL (FAIL) | {"each_of_two_folds": {"trades": ">=10", "net": ">0"}} | [{"trades": 14, "net": 9.658683589999999}, {"trades": 33, "net": -64.08227016999999}] |  |
| sealed_oos | FAIL (FAIL) | {"internal_developmental_OOS": {"trades": ">=10", "net": ">0"}} | {"trades": 50, "net": -15.11414407000004} | Internal historical partition only; NOT July–September 2026 |
| cost_stress | PASS (PASS) | {"observed_2x_trades": ">=10", "observed_2x_net": ">0"} | {"trades": 149, "net": 247.34464089999997, "tested": true} | Measured result |
| neighbors | PASS (PASS) | {"positive_fraction": ">=0.5", "positive_net": ">0"} | {"positive_fraction": 1.0, "neighbors": {"TB48_STOP": true, "TB48_WINDOW": true}} | Central-family neighbors shared across profiles; self-inclusion and unmatched side/filter caveats |
| symbols | PASS (PASS) | {"qualifying_symbols": ">=2", "per_qualifier": {"trades": ">=10", "net": ">0"}} | {"BTCUSDT": {"trades": 57, "net": 120.5765937}, "ETHUSDT": {"trades": 44, "net": 251.97302731}, "SOLUSDT": {"trades": 48, "net": 96.15470877000001}} |  |
| drawdown | PASS (PASS) | {"closed_trade_order_drawdown": "<=0.15", "full_history_marked_drawdown": "<=0.15"} | {"stored_closed_order": 0.006673932952268147, "marked": 0.010437778832458555} | Stored closed-trade order is not globally chronological; marked comparison is separate full-history check |
| concentration | FAIL (FAIL) | {"top10_positive_profit_share": "<=0.5", "net_excluding_top10": ">0"} | {"top10_positive_profit_share": 0.6080242477874084, "net_excluding_top10": -577.1181784500001} |  |
| profit_factor | PASS (PASS) | {"profit_factor": ">=1.05"} | {"value": 1.3745649618447835, "gap_to_threshold": 0.32456496184478345} | NEAR_MISS is descriptive only: PF>1 but below required 1.05 buffer; original gate remains FAIL |
| regimes | FAIL (FAIL) | {"every_declared_compatible_regime": {"trades": ">=10", "net": ">0"}} | {"TREND_HIGH_VOL": {"trades": 63, "net": -107.22621820000003}, "TREND_LOW_VOL": {"trades": 86, "net": 575.93054798}} |  |
| sides | PASS (PASS) | {"every_permitted_direction": {"trades": ">=10", "net": ">0"}} | {"-1": {"trades": 149, "net": 468.70432977999997}} |  |

Concentration and decomposition in the actual purged gate universe:

| Diagnostic | Observed |
| --- | --- |
| Winning trades | 52 |
| Top-10 positive net profits | 1,045.82 |
| Top-10 / all positive trade profits | 60.80% |
| Net excluding top 10 | -577.12 |
| Best realized-exit month | 2025-04: 329.33 |
| Best month / positive monthly net | 36.86% |
| Net excluding best month | 139.37 |
| Best symbol | ETHUSDT: 251.97 |
| Best symbol / positive symbol net | 53.76% |
| Net excluding best symbol | 216.73 |
| Long / short net | 0.00 / 468.70 |
| Original unsorted closed DD / chronological closed DD / full-history marked DD | 0.6674% / 0.8843% / 1.0438% |

Cost outcomes (N / net), without synthesizing absent stress tests:

| Cost | All preholdout | Actual purged gate universe |
| --- | --- | --- |
| base | 219 / 726.53 | 149 / 468.70 |
| cost1.5x | 219 / 569.19 | 149 / 358.03 |
| cost2x | 219 / 411.86 | 149 / 247.34 |

Neighbor gate evidence:

| Neighbor | Gate-interval net | Positive? | Self? | Same sides? | Same funding filter? |
| --- | --- | --- | --- | --- | --- |
| TB48_STOP | 262.91 | True | False | False | True |
| TB48_WINDOW | 377.05 | True | False | False | True |

Preholdout regime decomposition (realized attribution):

| Scope | N | Net | PF | Sharpe | Sortino | E/trade | DD % | Win % | Fees | Slip | Funding | Long net | Short net |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| TREND_LOW_VOL | 86 | 575.93 | 2.024 | 1.093 | 3.955 | 6.697 | 0.53 | 38.37 | 122.03 | 24.79 | 0.13 | 0.00 | 575.93 |
| TREND_HIGH_VOL | 63 | -107.23 | 0.844 | -0.330 | -0.580 | -1.702 | 0.70 | 30.16 | 62.41 | 12.68 | 0.53 | 0.00 | -107.23 |

### VB48_WINDOW

Family: volatility_breakout. Symbols: BTCUSDT, ETHUSDT, SOLUSDT. Signal timeframe: 15m; execution grid: 15m; causal context: 5m/15m/1h/4h. Parameters: `{"allow_long": true, "allow_short": true, "band_k": 2.5, "compression": 0.8, "funding_filter": false, "lookback": 60, "minutes": 15, "pullback_atr": 1.0, "stop_atr": 2.5}`. Compatible regimes: ['VOLATILITY_EXPANSION', 'TREND_HIGH_VOL'].

Total preholdout trades: 219; purged qualifying gate trades: 126. These are different universes; neither includes the July–September sealed evaluation.

Outer chronological metrics — native marked risk statistics:

| Scope | N | Net | PF | Sharpe | Sortino | E/trade | DD % | Win % | Fees | Slip | Funding | Long net | Short net |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| research | 88 | 178.09 | 1.183 | 0.486 | 1.117 | 2.024 | 0.96 | 40.91 | 142.61 | 28.99 | -4.78 | 152.16 | 25.93 |
| validation | 51 | -32.71 | 0.932 | -0.214 | -0.337 | -0.641 | 0.58 | 41.18 | 76.99 | 15.62 | -0.81 | -33.92 | 1.21 |
| wf1 | 37 | -199.86 | 0.593 | -1.642 | -2.009 | -5.402 | 1.02 | 35.14 | 79.43 | 16.05 | -2.65 | 73.28 | -273.14 |
| wf2 | 43 | 480.90 | 1.890 | 1.444 | 4.646 | 11.184 | 0.50 | 39.53 | 85.06 | 17.32 | 0.89 | 170.79 | 310.11 |

Actual internal promotion splits — realized daily attribution for Sharpe/Sortino/DD; exact original drawdown gate separately below:

| Scope | N | Net | PF | Sharpe | Sortino | E/trade | DD % | Win % | Fees | Slip | Funding | Long net | Short net |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| internal_train | 88 | 178.09 | 1.183 | 0.503 | 1.175 | 2.024 | 0.96 | 40.91 | 142.61 | 28.99 | -4.78 | 152.16 | 25.93 |
| internal_validation | 51 | -32.71 | 0.932 | -0.262 | -0.380 | -0.641 | 0.43 | 41.18 | 76.99 | 15.62 | -0.81 | -33.92 | 1.21 |
| internal_wf1 | 20 | -133.85 | 0.560 | -1.797 | -2.283 | -6.692 | 0.77 | 25.00 | 45.95 | 9.30 | -0.85 | -9.52 | -124.33 |
| internal_wf2 | 17 | -66.01 | 0.646 | -1.238 | -1.489 | -3.883 | 0.43 | 47.06 | 33.48 | 6.75 | -1.80 | 82.79 | -148.81 |
| internal_oos | 38 | 538.97 | 2.117 | 2.034 | 6.839 | 14.183 | 0.47 | 44.74 | 71.33 | 14.56 | 1.10 | 201.93 | 337.04 |

Exact frozen gates:

| Gate | Status (original) | Threshold | Observed | Comment |
| --- | --- | --- | --- | --- |
| sample | PASS (PASS) | {"number_of_trades": ">=60"} | 126 |  |
| validation_positive | FAIL (FAIL) | {"trades": ">=10", "net": ">0"} | {"trades": 51, "net": -32.71480102000003} |  |
| walk_forward | FAIL (FAIL) | {"each_of_two_folds": {"trades": ">=10", "net": ">0"}} | [{"trades": 20, "net": -133.84994987000002}, {"trades": 17, "net": -66.01025204}] |  |
| sealed_oos | PASS (PASS) | {"internal_developmental_OOS": {"trades": ">=10", "net": ">0"}} | {"trades": 38, "net": 538.9704404} | Internal historical partition only; NOT July–September 2026 |
| cost_stress | FAIL (FAIL) | {"observed_2x_trades": ">=10", "observed_2x_net": ">0"} | {"trades": 0, "net": 0.0, "tested": false} | NOT TESTED: absent cost evidence is an automatic failure, not an observed loss |
| neighbors | PASS (PASS) | {"positive_fraction": ">=0.5", "positive_net": ">0"} | {"positive_fraction": 1.0, "neighbors": {"VB48_STOP": true, "VB48_WINDOW": true}} | Central-family neighbors shared across profiles; self-inclusion and unmatched side/filter caveats |
| symbols | PASS (PASS) | {"qualifying_symbols": ">=2", "per_qualifier": {"trades": ">=10", "net": ">0"}} | {"BTCUSDT": {"trades": 45, "net": -62.26936790000001}, "ETHUSDT": {"trades": 42, "net": 278.02152376000004}, "SOLUSDT": {"trades": 39, "net": 90.64328161}} |  |
| drawdown | PASS (PASS) | {"closed_trade_order_drawdown": "<=0.15", "full_history_marked_drawdown": "<=0.15"} | {"stored_closed_order": 0.015756955274651596, "marked": 0.01826896676994294} | Stored closed-trade order is not globally chronological; marked comparison is separate full-history check |
| concentration | FAIL (FAIL) | {"top10_positive_profit_share": "<=0.5", "net_excluding_top10": ">0"} | {"top10_positive_profit_share": 0.5898477978901088, "net_excluding_top10": -732.1048408799999} |  |
| profit_factor | PASS (PASS) | {"profit_factor": ">=1.05"} | {"value": 1.2106927436034383, "gap_to_threshold": 0.16069274360343822} | NEAR_MISS is descriptive only: PF>1 but below required 1.05 buffer; original gate remains FAIL |
| regimes | FAIL (FAIL) | {"every_declared_compatible_regime": {"trades": ">=10", "net": ">0"}} | {"TREND_HIGH_VOL": {"trades": 76, "net": -69.09639809999992}, "VOLATILITY_EXPANSION": {"trades": 50, "net": 375.49183557000003}} |  |
| sides | PASS (PASS) | {"every_permitted_direction": {"trades": ">=10", "net": ">0"}} | {"-1": {"trades": 69, "net": 65.10740448000001}, "1": {"trades": 57, "net": 241.28803299}} |  |

Concentration and decomposition in the actual purged gate universe:

| Diagnostic | Observed |
| --- | --- |
| Winning trades | 51 |
| Top-10 positive net profits | 1,038.50 |
| Top-10 / all positive trade profits | 58.98% |
| Net excluding top 10 | -732.10 |
| Best realized-exit month | 2026-01: 353.94 |
| Best month / positive monthly net | 47.76% |
| Net excluding best month | -47.55 |
| Best symbol | ETHUSDT: 278.02 |
| Best symbol / positive symbol net | 75.41% |
| Net excluding best symbol | 28.37 |
| Long / short net | 241.29 / 65.11 |
| Original unsorted closed DD / chronological closed DD / full-history marked DD | 1.5757% / 1.1669% / 1.8269% |

Cost outcomes (N / net), without synthesizing absent stress tests:

| Cost | All preholdout | Actual purged gate universe |
| --- | --- | --- |
| base | 219 / 426.42 | 126 / 306.40 |
| cost1.5x | NOT TESTED | NOT TESTED |
| cost2x | NOT TESTED | NOT TESTED |

Neighbor gate evidence:

| Neighbor | Gate-interval net | Positive? | Self? | Same sides? | Same funding filter? |
| --- | --- | --- | --- | --- | --- |
| VB48_STOP | 47.18 | True | False | True | True |
| VB48_WINDOW | 306.40 | True | True | True | True |

Preholdout regime decomposition (realized attribution):

| Scope | N | Net | PF | Sharpe | Sortino | E/trade | DD % | Win % | Fees | Slip | Funding | Long net | Short net |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| VOLATILITY_EXPANSION | 50 | 375.49 | 1.905 | 1.406 | 3.405 | 7.510 | 0.31 | 58.00 | 76.70 | 15.61 | -0.49 | 365.34 | 10.15 |
| TREND_HIGH_VOL | 76 | -69.10 | 0.934 | -0.137 | -0.280 | -0.909 | 1.26 | 28.95 | 151.06 | 30.62 | -1.87 | -124.05 | 54.95 |

### TB48

Family: trend_breakout. Symbols: BTCUSDT, ETHUSDT, SOLUSDT. Signal timeframe: 60m; execution grid: 15m; causal context: 5m/15m/1h/4h. Parameters: `{"allow_long": true, "allow_short": true, "band_k": 2.5, "compression": 0.8, "funding_filter": false, "lookback": 48, "minutes": 60, "pullback_atr": 1.0, "stop_atr": 2.0}`. Compatible regimes: ['TREND_LOW_VOL', 'TREND_HIGH_VOL'].

Total preholdout trades: 462; purged qualifying gate trades: 279. These are different universes; neither includes the July–September sealed evaluation.

Outer chronological metrics — native marked risk statistics:

| Scope | N | Net | PF | Sharpe | Sortino | E/trade | DD % | Win % | Fees | Slip | Funding | Long net | Short net |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| research | 180 | -275.57 | 0.834 | -0.598 | -0.965 | -1.531 | 1.56 | 30.56 | 231.11 | 47.03 | -16.42 | -529.59 | 254.01 |
| validation | 96 | 567.89 | 1.755 | 1.931 | 5.539 | 5.916 | 0.61 | 35.42 | 119.60 | 24.30 | -1.64 | 29.65 | 538.24 |
| wf1 | 100 | 57.50 | 1.067 | 0.241 | 0.519 | 0.575 | 0.88 | 27.00 | 143.69 | 29.06 | -6.70 | 111.93 | -54.42 |
| wf2 | 86 | -254.69 | 0.728 | -0.854 | -1.263 | -2.961 | 1.93 | 30.23 | 126.34 | 25.81 | -2.87 | -243.38 | -11.31 |

Actual internal promotion splits — realized daily attribution for Sharpe/Sortino/DD; exact original drawdown gate separately below:

| Scope | N | Net | PF | Sharpe | Sortino | E/trade | DD % | Win % | Fees | Slip | Funding | Long net | Short net |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| internal_train | 180 | -275.57 | 0.834 | -0.681 | -1.107 | -1.531 | 1.61 | 30.56 | 231.11 | 47.03 | -16.42 | -529.59 | 254.01 |
| internal_validation | 94 | 594.35 | 1.819 | 1.795 | 5.977 | 6.323 | 0.67 | 36.17 | 117.04 | 23.76 | -1.54 | 56.11 | 538.24 |
| internal_wf1 | 51 | 153.72 | 1.337 | 1.011 | 2.896 | 3.014 | 0.67 | 23.53 | 75.19 | 15.23 | -4.04 | 144.06 | 9.66 |
| internal_wf2 | 51 | -122.67 | 0.712 | -1.121 | -2.030 | -2.405 | 0.75 | 29.41 | 71.05 | 14.36 | -2.77 | -58.59 | -64.08 |
| internal_oos | 83 | -258.49 | 0.722 | -1.603 | -2.231 | -3.114 | 1.63 | 28.92 | 122.17 | 24.95 | -2.87 | -243.38 | -15.11 |

Exact frozen gates:

| Gate | Status (original) | Threshold | Observed | Comment |
| --- | --- | --- | --- | --- |
| sample | PASS (PASS) | {"number_of_trades": ">=60"} | 279 |  |
| validation_positive | PASS (PASS) | {"trades": ">=10", "net": ">0"} | {"trades": 94, "net": 594.35327801} |  |
| walk_forward | FAIL (FAIL) | {"each_of_two_folds": {"trades": ">=10", "net": ">0"}} | [{"trades": 51, "net": 153.71967095999997}, {"trades": 51, "net": -122.67362355999998}] |  |
| sealed_oos | FAIL (FAIL) | {"internal_developmental_OOS": {"trades": ">=10", "net": ">0"}} | {"trades": 83, "net": -258.49452198} | Internal historical partition only; NOT July–September 2026 |
| cost_stress | FAIL (FAIL) | {"observed_2x_trades": ">=10", "observed_2x_net": ">0"} | {"trades": 279, "net": -95.69746117999966, "tested": true} | Measured result |
| neighbors | PASS (PASS) | {"positive_fraction": ">=0.5", "positive_net": ">0"} | {"positive_fraction": 1.0, "neighbors": {"TB48_STOP": true, "TB48_WINDOW": true}} | Central-family neighbors shared across profiles; self-inclusion and unmatched side/filter caveats |
| symbols | FAIL (FAIL) | {"qualifying_symbols": ">=2", "per_qualifier": {"trades": ">=10", "net": ">0"}} | {"BTCUSDT": {"trades": 105, "net": -24.54214335999997}, "ETHUSDT": {"trades": 77, "net": 664.3611792800002}, "SOLUSDT": {"trades": 97, "net": -272.91423248999996}} |  |
| drawdown | PASS (PASS) | {"closed_trade_order_drawdown": "<=0.15", "full_history_marked_drawdown": "<=0.15"} | {"stored_closed_order": 0.019810319538069554, "marked": 0.019531584634741583} | Stored closed-trade order is not globally chronological; marked comparison is separate full-history check |
| concentration | FAIL (FAIL) | {"top10_positive_profit_share": "<=0.5", "net_excluding_top10": ">0"} | {"top10_positive_profit_share": 0.41425993669271116, "net_excluding_top10": -835.8180557999999} |  |
| profit_factor | PASS (PASS) | {"profit_factor": ">=1.05"} | {"value": 1.1446557345527437, "gap_to_threshold": 0.09465573455274368} | NEAR_MISS is descriptive only: PF>1 but below required 1.05 buffer; original gate remains FAIL |
| regimes | FAIL (FAIL) | {"every_declared_compatible_regime": {"trades": ">=10", "net": ">0"}} | {"TREND_HIGH_VOL": {"trades": 96, "net": -46.35443083000004}, "TREND_LOW_VOL": {"trades": 183, "net": 413.25923426}} |  |
| sides | FAIL (FAIL) | {"every_permitted_direction": {"trades": ">=10", "net": ">0"}} | {"-1": {"trades": 149, "net": 468.70432977999997}, "1": {"trades": 130, "net": -101.79952634999995}} |  |

Concentration and decomposition in the actual purged gate universe:

| Diagnostic | Observed |
| --- | --- |
| Winning trades | 85 |
| Top-10 positive net profits | 1,202.72 |
| Top-10 / all positive trade profits | 41.43% |
| Net excluding top 10 | -835.82 |
| Best realized-exit month | 2025-04: 393.60 |
| Best month / positive monthly net | 32.26% |
| Net excluding best month | -26.70 |
| Best symbol | ETHUSDT: 664.36 |
| Best symbol / positive symbol net | 100.00% |
| Net excluding best symbol | -297.46 |
| Long / short net | -101.80 / 468.70 |
| Original unsorted closed DD / chronological closed DD / full-history marked DD | 1.9810% / 1.9696% / 1.9532% |

Cost outcomes (N / net), without synthesizing absent stress tests:

| Cost | All preholdout | Actual purged gate universe |
| --- | --- | --- |
| base | 462 / 95.14 | 279 / 366.90 |
| cost1.5x | 462 / -277.34 | 279 / 135.62 |
| cost2x | 462 / -649.79 | 279 / -95.70 |

Neighbor gate evidence:

| Neighbor | Gate-interval net | Positive? | Self? | Same sides? | Same funding filter? |
| --- | --- | --- | --- | --- | --- |
| TB48_STOP | 262.91 | True | False | True | True |
| TB48_WINDOW | 377.05 | True | False | True | True |

Preholdout regime decomposition (realized attribution):

| Scope | N | Net | PF | Sharpe | Sortino | E/trade | DD % | Win % | Fees | Slip | Funding | Long net | Short net |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| TREND_LOW_VOL | 183 | 413.26 | 1.265 | 0.640 | 1.719 | 2.258 | 1.41 | 31.15 | 279.32 | 56.78 | -9.88 | -162.67 | 575.93 |
| TREND_HIGH_VOL | 96 | -46.35 | 0.953 | -0.111 | -0.211 | -0.483 | 0.88 | 29.17 | 106.13 | 21.52 | -1.34 | 60.87 | -107.23 |

### TB48_FUNDING

Family: trend_breakout. Symbols: BTCUSDT, ETHUSDT, SOLUSDT. Signal timeframe: 60m; execution grid: 15m; causal context: 5m/15m/1h/4h. Parameters: `{"allow_long": true, "allow_short": true, "band_k": 2.5, "compression": 0.8, "funding_filter": true, "lookback": 48, "minutes": 60, "pullback_atr": 1.0, "stop_atr": 2.0}`. Compatible regimes: ['TREND_LOW_VOL', 'TREND_HIGH_VOL'].

Total preholdout trades: 452; purged qualifying gate trades: 279. These are different universes; neither includes the July–September sealed evaluation.

Outer chronological metrics — native marked risk statistics:

| Scope | N | Net | PF | Sharpe | Sortino | E/trade | DD % | Win % | Fees | Slip | Funding | Long net | Short net |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| research | 170 | -153.85 | 0.899 | -0.339 | -0.560 | -0.905 | 1.17 | 31.76 | 221.20 | 45.01 | -11.91 | -407.86 | 254.01 |
| validation | 96 | 567.89 | 1.755 | 1.931 | 5.539 | 5.916 | 0.61 | 35.42 | 119.60 | 24.30 | -1.64 | 29.65 | 538.24 |
| wf1 | 100 | 57.50 | 1.067 | 0.241 | 0.519 | 0.575 | 0.88 | 27.00 | 143.69 | 29.06 | -6.70 | 111.93 | -54.42 |
| wf2 | 86 | -254.69 | 0.728 | -0.854 | -1.263 | -2.961 | 1.93 | 30.23 | 126.34 | 25.81 | -2.87 | -243.38 | -11.31 |

Actual internal promotion splits — realized daily attribution for Sharpe/Sortino/DD; exact original drawdown gate separately below:

| Scope | N | Net | PF | Sharpe | Sortino | E/trade | DD % | Win % | Fees | Slip | Funding | Long net | Short net |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| internal_train | 170 | -153.85 | 0.899 | -0.384 | -0.642 | -0.905 | 1.22 | 31.76 | 221.20 | 45.01 | -11.91 | -407.86 | 254.01 |
| internal_validation | 94 | 594.35 | 1.819 | 1.795 | 5.977 | 6.323 | 0.67 | 36.17 | 117.04 | 23.76 | -1.54 | 56.11 | 538.24 |
| internal_wf1 | 51 | 153.72 | 1.337 | 1.011 | 2.896 | 3.014 | 0.67 | 23.53 | 75.19 | 15.23 | -4.04 | 144.06 | 9.66 |
| internal_wf2 | 51 | -122.67 | 0.712 | -1.121 | -2.030 | -2.405 | 0.75 | 29.41 | 71.05 | 14.36 | -2.77 | -58.59 | -64.08 |
| internal_oos | 83 | -258.49 | 0.722 | -1.603 | -2.231 | -3.114 | 1.63 | 28.92 | 122.17 | 24.95 | -2.87 | -243.38 | -15.11 |

Exact frozen gates:

| Gate | Status (original) | Threshold | Observed | Comment |
| --- | --- | --- | --- | --- |
| sample | PASS (PASS) | {"number_of_trades": ">=60"} | 279 |  |
| validation_positive | PASS (PASS) | {"trades": ">=10", "net": ">0"} | {"trades": 94, "net": 594.35327801} |  |
| walk_forward | FAIL (FAIL) | {"each_of_two_folds": {"trades": ">=10", "net": ">0"}} | [{"trades": 51, "net": 153.71967095999997}, {"trades": 51, "net": -122.67362355999998}] |  |
| sealed_oos | FAIL (FAIL) | {"internal_developmental_OOS": {"trades": ">=10", "net": ">0"}} | {"trades": 83, "net": -258.49452198} | Internal historical partition only; NOT July–September 2026 |
| cost_stress | FAIL (FAIL) | {"observed_2x_trades": ">=10", "observed_2x_net": ">0"} | {"trades": 279, "net": -95.69746117999966, "tested": true} | Measured result |
| neighbors | PASS (PASS) | {"positive_fraction": ">=0.5", "positive_net": ">0"} | {"positive_fraction": 1.0, "neighbors": {"TB48_STOP": true, "TB48_WINDOW": true}} | Central-family neighbors shared across profiles; self-inclusion and unmatched side/filter caveats |
| symbols | FAIL (FAIL) | {"qualifying_symbols": ">=2", "per_qualifier": {"trades": ">=10", "net": ">0"}} | {"BTCUSDT": {"trades": 105, "net": -24.54214335999997}, "ETHUSDT": {"trades": 77, "net": 664.3611792800002}, "SOLUSDT": {"trades": 97, "net": -272.91423248999996}} |  |
| drawdown | PASS (PASS) | {"closed_trade_order_drawdown": "<=0.15", "full_history_marked_drawdown": "<=0.15"} | {"stored_closed_order": 0.019810319538069554, "marked": 0.019454146745052525} | Stored closed-trade order is not globally chronological; marked comparison is separate full-history check |
| concentration | FAIL (FAIL) | {"top10_positive_profit_share": "<=0.5", "net_excluding_top10": ">0"} | {"top10_positive_profit_share": 0.41425993669271116, "net_excluding_top10": -835.8180557999999} |  |
| profit_factor | PASS (PASS) | {"profit_factor": ">=1.05"} | {"value": 1.1446557345527437, "gap_to_threshold": 0.09465573455274368} | NEAR_MISS is descriptive only: PF>1 but below required 1.05 buffer; original gate remains FAIL |
| regimes | FAIL (FAIL) | {"every_declared_compatible_regime": {"trades": ">=10", "net": ">0"}} | {"TREND_HIGH_VOL": {"trades": 96, "net": -46.35443083000004}, "TREND_LOW_VOL": {"trades": 183, "net": 413.25923426}} |  |
| sides | FAIL (FAIL) | {"every_permitted_direction": {"trades": ">=10", "net": ">0"}} | {"-1": {"trades": 149, "net": 468.70432977999997}, "1": {"trades": 130, "net": -101.79952634999995}} |  |

Concentration and decomposition in the actual purged gate universe:

| Diagnostic | Observed |
| --- | --- |
| Winning trades | 85 |
| Top-10 positive net profits | 1,202.72 |
| Top-10 / all positive trade profits | 41.43% |
| Net excluding top 10 | -835.82 |
| Best realized-exit month | 2025-04: 393.60 |
| Best month / positive monthly net | 32.26% |
| Net excluding best month | -26.70 |
| Best symbol | ETHUSDT: 664.36 |
| Best symbol / positive symbol net | 100.00% |
| Net excluding best symbol | -297.46 |
| Long / short net | -101.80 / 468.70 |
| Original unsorted closed DD / chronological closed DD / full-history marked DD | 1.9810% / 1.9696% / 1.9454% |

Cost outcomes (N / net), without synthesizing absent stress tests:

| Cost | All preholdout | Actual purged gate universe |
| --- | --- | --- |
| base | 452 / 216.86 | 279 / 366.90 |
| cost1.5x | 452 / -149.67 | 279 / 135.62 |
| cost2x | 452 / -516.18 | 279 / -95.70 |

Neighbor gate evidence:

| Neighbor | Gate-interval net | Positive? | Self? | Same sides? | Same funding filter? |
| --- | --- | --- | --- | --- | --- |
| TB48_STOP | 262.91 | True | False | True | False |
| TB48_WINDOW | 377.05 | True | False | True | False |

Preholdout regime decomposition (realized attribution):

| Scope | N | Net | PF | Sharpe | Sortino | E/trade | DD % | Win % | Fees | Slip | Funding | Long net | Short net |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| TREND_LOW_VOL | 183 | 413.26 | 1.265 | 0.640 | 1.719 | 2.258 | 1.41 | 31.15 | 279.32 | 56.78 | -9.88 | -162.67 | 575.93 |
| TREND_HIGH_VOL | 96 | -46.35 | 0.953 | -0.111 | -0.211 | -0.483 | 0.88 | 29.17 | 106.13 | 21.52 | -1.34 | 60.87 | -107.23 |

### TB48_STOP

Family: trend_breakout. Symbols: BTCUSDT, ETHUSDT, SOLUSDT. Signal timeframe: 60m; execution grid: 15m; causal context: 5m/15m/1h/4h. Parameters: `{"allow_long": true, "allow_short": true, "band_k": 2.5, "compression": 0.8, "funding_filter": false, "lookback": 48, "minutes": 60, "pullback_atr": 1.0, "stop_atr": 2.5}`. Compatible regimes: ['TREND_LOW_VOL', 'TREND_HIGH_VOL'].

Total preholdout trades: 461; purged qualifying gate trades: 278. These are different universes; neither includes the July–September sealed evaluation.

Outer chronological metrics — native marked risk statistics:

| Scope | N | Net | PF | Sharpe | Sortino | E/trade | DD % | Win % | Fees | Slip | Funding | Long net | Short net |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| research | 180 | -252.55 | 0.811 | -0.682 | -1.085 | -1.403 | 1.22 | 30.56 | 184.38 | 37.53 | -14.26 | -456.51 | 203.95 |
| validation | 95 | 479.15 | 1.826 | 2.060 | 6.040 | 5.044 | 0.46 | 35.79 | 94.88 | 19.27 | -1.32 | 27.32 | 451.84 |
| wf1 | 100 | 24.85 | 1.036 | 0.132 | 0.280 | 0.248 | 0.77 | 27.00 | 114.22 | 23.10 | -5.39 | 69.57 | -44.72 |
| wf2 | 86 | -238.13 | 0.689 | -0.983 | -1.423 | -2.769 | 1.65 | 30.23 | 100.75 | 20.59 | -2.24 | -219.72 | -18.41 |

Actual internal promotion splits — realized daily attribution for Sharpe/Sortino/DD; exact original drawdown gate separately below:

| Scope | N | Net | PF | Sharpe | Sortino | E/trade | DD % | Win % | Fees | Slip | Funding | Long net | Short net |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| internal_train | 180 | -252.55 | 0.811 | -0.784 | -1.245 | -1.403 | 1.26 | 30.56 | 184.38 | 37.53 | -14.26 | -456.51 | 203.95 |
| internal_validation | 93 | 500.36 | 1.895 | 1.906 | 6.378 | 5.380 | 0.51 | 36.56 | 92.83 | 18.85 | -1.24 | 48.52 | 451.84 |
| internal_wf1 | 51 | 112.90 | 1.310 | 0.931 | 2.659 | 2.214 | 0.53 | 23.53 | 59.86 | 12.13 | -3.21 | 105.73 | 7.17 |
| internal_wf2 | 51 | -109.26 | 0.693 | -1.246 | -2.211 | -2.142 | 0.61 | 29.41 | 56.41 | 11.40 | -2.26 | -57.37 | -51.89 |
| internal_oos | 83 | -241.10 | 0.682 | -1.900 | -2.546 | -2.905 | 1.37 | 28.92 | 97.43 | 19.90 | -2.24 | -219.72 | -21.37 |

Exact frozen gates:

| Gate | Status (original) | Threshold | Observed | Comment |
| --- | --- | --- | --- | --- |
| sample | PASS (PASS) | {"number_of_trades": ">=60"} | 278 |  |
| validation_positive | PASS (PASS) | {"trades": ">=10", "net": ">0"} | {"trades": 93, "net": 500.3601419299999} |  |
| walk_forward | FAIL (FAIL) | {"each_of_two_folds": {"trades": ">=10", "net": ">0"}} | [{"trades": 51, "net": 112.90428184000002}, {"trades": 51, "net": -109.26197719999998}] |  |
| sealed_oos | FAIL (FAIL) | {"internal_developmental_OOS": {"trades": ">=10", "net": ">0"}} | {"trades": 83, "net": -241.09679378999996} | Internal historical partition only; NOT July–September 2026 |
| cost_stress | FAIL (FAIL) | {"observed_2x_trades": ">=10", "observed_2x_net": ">0"} | {"trades": 0, "net": 0.0, "tested": false} | NOT TESTED: absent cost evidence is an automatic failure, not an observed loss |
| neighbors | PASS (PASS) | {"positive_fraction": ">=0.5", "positive_net": ">0"} | {"positive_fraction": 1.0, "neighbors": {"TB48_STOP": true, "TB48_WINDOW": true}} | Central-family neighbors shared across profiles; self-inclusion and unmatched side/filter caveats |
| symbols | FAIL (FAIL) | {"qualifying_symbols": ">=2", "per_qualifier": {"trades": ">=10", "net": ">0"}} | {"BTCUSDT": {"trades": 105, "net": -31.465421280000008}, "ETHUSDT": {"trades": 77, "net": 486.31776031}, "SOLUSDT": {"trades": 96, "net": -191.94668624999997}} |  |
| drawdown | PASS (PASS) | {"closed_trade_order_drawdown": "<=0.15", "full_history_marked_drawdown": "<=0.15"} | {"stored_closed_order": 0.017106103781944215, "marked": 0.017260478436370352} | Stored closed-trade order is not globally chronological; marked comparison is separate full-history check |
| concentration | FAIL (FAIL) | {"top10_positive_profit_share": "<=0.5", "net_excluding_top10": ">0"} | {"top10_positive_profit_share": 0.41804772651741295, "net_excluding_top10": -699.27183347} |  |
| profit_factor | PASS (PASS) | {"profit_factor": ">=1.05"} | {"value": 1.1289580320422723, "gap_to_threshold": 0.07895803204227225} | NEAR_MISS is descriptive only: PF>1 but below required 1.05 buffer; original gate remains FAIL |
| regimes | FAIL (FAIL) | {"every_declared_compatible_regime": {"trades": ">=10", "net": ">0"}} | {"TREND_HIGH_VOL": {"trades": 95, "net": -44.051781150000004}, "TREND_LOW_VOL": {"trades": 183, "net": 306.95743393}} |  |
| sides | FAIL (FAIL) | {"every_permitted_direction": {"trades": ">=10", "net": ">0"}} | {"-1": {"trades": 148, "net": 385.74621797000003}, "1": {"trades": 130, "net": -122.84056518999995}} |  |

Concentration and decomposition in the actual purged gate universe:

| Diagnostic | Observed |
| --- | --- |
| Winning trades | 85 |
| Top-10 positive net profits | 962.18 |
| Top-10 / all positive trade profits | 41.80% |
| Net excluding top 10 | -699.27 |
| Best realized-exit month | 2025-04: 311.49 |
| Best month / positive monthly net | 31.76% |
| Net excluding best month | -48.59 |
| Best symbol | ETHUSDT: 486.32 |
| Best symbol / positive symbol net | 100.00% |
| Net excluding best symbol | -223.41 |
| Long / short net | -122.84 / 385.75 |
| Original unsorted closed DD / chronological closed DD / full-history marked DD | 1.7106% / 1.7393% / 1.7260% |

Cost outcomes (N / net), without synthesizing absent stress tests:

| Cost | All preholdout | Actual purged gate universe |
| --- | --- | --- |
| base | 461 / 13.32 | 278 / 262.91 |
| cost1.5x | NOT TESTED | NOT TESTED |
| cost2x | NOT TESTED | NOT TESTED |

Neighbor gate evidence:

| Neighbor | Gate-interval net | Positive? | Self? | Same sides? | Same funding filter? |
| --- | --- | --- | --- | --- | --- |
| TB48_STOP | 262.91 | True | True | True | True |
| TB48_WINDOW | 377.05 | True | False | True | True |

Preholdout regime decomposition (realized attribution):

| Scope | N | Net | PF | Sharpe | Sortino | E/trade | DD % | Win % | Fees | Slip | Funding | Long net | Short net |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| TREND_LOW_VOL | 183 | 306.96 | 1.243 | 0.598 | 1.581 | 1.677 | 1.19 | 31.15 | 222.26 | 45.19 | -7.85 | -164.76 | 471.71 |
| TREND_HIGH_VOL | 95 | -44.05 | 0.943 | -0.134 | -0.252 | -0.464 | 0.79 | 29.47 | 84.26 | 17.09 | -1.11 | 41.91 | -85.97 |

### TB48_WINDOW

Family: trend_breakout. Symbols: BTCUSDT, ETHUSDT, SOLUSDT. Signal timeframe: 60m; execution grid: 15m; causal context: 5m/15m/1h/4h. Parameters: `{"allow_long": true, "allow_short": true, "band_k": 2.5, "compression": 0.8, "funding_filter": false, "lookback": 60, "minutes": 60, "pullback_atr": 1.0, "stop_atr": 2.0}`. Compatible regimes: ['TREND_LOW_VOL', 'TREND_HIGH_VOL'].

Total preholdout trades: 459; purged qualifying gate trades: 276. These are different universes; neither includes the July–September sealed evaluation.

Outer chronological metrics — native marked risk statistics:

| Scope | N | Net | PF | Sharpe | Sortino | E/trade | DD % | Win % | Fees | Slip | Funding | Long net | Short net |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| research | 180 | -275.57 | 0.834 | -0.598 | -0.965 | -1.531 | 1.56 | 30.56 | 231.11 | 47.03 | -16.42 | -529.59 | 254.01 |
| validation | 96 | 567.89 | 1.755 | 1.931 | 5.539 | 5.916 | 0.61 | 35.42 | 119.60 | 24.30 | -1.64 | 29.65 | 538.24 |
| wf1 | 100 | 57.50 | 1.067 | 0.241 | 0.519 | 0.575 | 0.88 | 27.00 | 143.69 | 29.06 | -6.70 | 111.93 | -54.42 |
| wf2 | 83 | -244.54 | 0.736 | -0.819 | -1.213 | -2.946 | 1.90 | 30.12 | 121.70 | 24.86 | -2.65 | -231.59 | -12.95 |

Actual internal promotion splits — realized daily attribution for Sharpe/Sortino/DD; exact original drawdown gate separately below:

| Scope | N | Net | PF | Sharpe | Sortino | E/trade | DD % | Win % | Fees | Slip | Funding | Long net | Short net |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| internal_train | 180 | -275.57 | 0.834 | -0.681 | -1.107 | -1.531 | 1.61 | 30.56 | 231.11 | 47.03 | -16.42 | -529.59 | 254.01 |
| internal_validation | 94 | 594.35 | 1.819 | 1.795 | 5.977 | 6.323 | 0.67 | 36.17 | 117.04 | 23.76 | -1.54 | 56.11 | 538.24 |
| internal_wf1 | 51 | 153.72 | 1.337 | 1.011 | 2.896 | 3.014 | 0.67 | 23.53 | 75.19 | 15.23 | -4.04 | 144.06 | 9.66 |
| internal_wf2 | 51 | -122.67 | 0.712 | -1.121 | -2.030 | -2.405 | 0.75 | 29.41 | 71.05 | 14.36 | -2.77 | -58.59 | -64.08 |
| internal_oos | 80 | -248.35 | 0.729 | -1.545 | -2.158 | -3.104 | 1.60 | 28.75 | 117.53 | 24.00 | -2.65 | -231.59 | -16.76 |

Exact frozen gates:

| Gate | Status (original) | Threshold | Observed | Comment |
| --- | --- | --- | --- | --- |
| sample | PASS (PASS) | {"number_of_trades": ">=60"} | 276 |  |
| validation_positive | PASS (PASS) | {"trades": ">=10", "net": ">0"} | {"trades": 94, "net": 594.35327801} |  |
| walk_forward | FAIL (FAIL) | {"each_of_two_folds": {"trades": ">=10", "net": ">0"}} | [{"trades": 51, "net": 153.71967095999997}, {"trades": 51, "net": -122.67362355999998}] |  |
| sealed_oos | FAIL (FAIL) | {"internal_developmental_OOS": {"trades": ">=10", "net": ">0"}} | {"trades": 80, "net": -248.3485713} | Internal historical partition only; NOT July–September 2026 |
| cost_stress | FAIL (FAIL) | {"observed_2x_trades": ">=10", "observed_2x_net": ">0"} | {"trades": 0, "net": 0.0, "tested": false} | NOT TESTED: absent cost evidence is an automatic failure, not an observed loss |
| neighbors | PASS (PASS) | {"positive_fraction": ">=0.5", "positive_net": ">0"} | {"positive_fraction": 1.0, "neighbors": {"TB48_STOP": true, "TB48_WINDOW": true}} | Central-family neighbors shared across profiles; self-inclusion and unmatched side/filter caveats |
| symbols | FAIL (FAIL) | {"qualifying_symbols": ">=2", "per_qualifier": {"trades": ">=10", "net": ">0"}} | {"BTCUSDT": {"trades": 104, "net": -26.187334359999966}, "ETHUSDT": {"trades": 76, "net": 669.8325911000003}, "SOLUSDT": {"trades": 96, "net": -266.59450262999997}} |  |
| drawdown | PASS (PASS) | {"closed_trade_order_drawdown": "<=0.15", "full_history_marked_drawdown": "<=0.15"} | {"stored_closed_order": 0.019482532152395038, "marked": 0.01919979690107898} | Stored closed-trade order is not globally chronological; marked comparison is separate full-history check |
| concentration | FAIL (FAIL) | {"top10_positive_profit_share": "<=0.5", "net_excluding_top10": ">0"} | {"top10_positive_profit_share": 0.41449481493939844, "net_excluding_top10": -825.67210512} |  |
| profit_factor | PASS (PASS) | {"profit_factor": ">=1.05"} | {"value": 1.1493501674969637, "gap_to_threshold": 0.09935016749696368} | NEAR_MISS is descriptive only: PF>1 but below required 1.05 buffer; original gate remains FAIL |
| regimes | FAIL (FAIL) | {"every_declared_compatible_regime": {"trades": ">=10", "net": ">0"}} | {"TREND_HIGH_VOL": {"trades": 96, "net": -46.35443083000004}, "TREND_LOW_VOL": {"trades": 180, "net": 423.40518494}} |  |
| sides | FAIL (FAIL) | {"every_permitted_direction": {"trades": ">=10", "net": ">0"}} | {"-1": {"trades": 148, "net": 467.0591387799999}, "1": {"trades": 128, "net": -90.00838466999997}} |  |

Concentration and decomposition in the actual purged gate universe:

| Diagnostic | Observed |
| --- | --- |
| Winning trades | 84 |
| Top-10 positive net profits | 1,202.72 |
| Top-10 / all positive trade profits | 41.45% |
| Net excluding top 10 | -825.67 |
| Best realized-exit month | 2025-04: 393.60 |
| Best month / positive monthly net | 32.26% |
| Net excluding best month | -16.55 |
| Best symbol | ETHUSDT: 669.83 |
| Best symbol / positive symbol net | 100.00% |
| Net excluding best symbol | -292.78 |
| Long / short net | -90.01 / 467.06 |
| Original unsorted closed DD / chronological closed DD / full-history marked DD | 1.9483% / 1.9367% / 1.9200% |

Cost outcomes (N / net), without synthesizing absent stress tests:

| Cost | All preholdout | Actual purged gate universe |
| --- | --- | --- |
| base | 459 / 105.29 | 276 / 377.05 |
| cost1.5x | NOT TESTED | NOT TESTED |
| cost2x | NOT TESTED | NOT TESTED |

Neighbor gate evidence:

| Neighbor | Gate-interval net | Positive? | Self? | Same sides? | Same funding filter? |
| --- | --- | --- | --- | --- | --- |
| TB48_STOP | 262.91 | True | False | True | True |
| TB48_WINDOW | 377.05 | True | True | True | True |

Preholdout regime decomposition (realized attribution):

| Scope | N | Net | PF | Sharpe | Sortino | E/trade | DD % | Win % | Fees | Slip | Funding | Long net | Short net |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| TREND_LOW_VOL | 180 | 423.41 | 1.274 | 0.655 | 1.768 | 2.352 | 1.38 | 31.11 | 274.68 | 55.83 | -9.66 | -150.88 | 574.29 |
| TREND_HIGH_VOL | 96 | -46.35 | 0.953 | -0.111 | -0.211 | -0.483 | 0.88 | 29.17 | 106.13 | 21.52 | -1.34 | 60.87 | -107.23 |

### VB48

Family: volatility_breakout. Symbols: BTCUSDT, ETHUSDT, SOLUSDT. Signal timeframe: 15m; execution grid: 15m; causal context: 5m/15m/1h/4h. Parameters: `{"allow_long": true, "allow_short": true, "band_k": 2.5, "compression": 0.8, "funding_filter": false, "lookback": 48, "minutes": 15, "pullback_atr": 1.0, "stop_atr": 2.5}`. Compatible regimes: ['VOLATILITY_EXPANSION', 'TREND_HIGH_VOL'].

Total preholdout trades: 284; purged qualifying gate trades: 169. These are different universes; neither includes the July–September sealed evaluation.

Outer chronological metrics — native marked risk statistics:

| Scope | N | Net | PF | Sharpe | Sortino | E/trade | DD % | Win % | Fees | Slip | Funding | Long net | Short net |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| research | 109 | 130.63 | 1.113 | 0.360 | 0.765 | 1.198 | 0.84 | 38.53 | 191.90 | 39.00 | -4.87 | 176.63 | -46.00 |
| validation | 69 | -141.05 | 0.814 | -0.698 | -0.924 | -2.044 | 0.89 | 39.13 | 107.12 | 21.76 | -0.51 | -24.35 | -116.71 |
| wf1 | 51 | -188.60 | 0.708 | -1.490 | -1.823 | -3.698 | 1.01 | 33.33 | 117.32 | 23.68 | -1.02 | 129.27 | -317.87 |
| wf2 | 55 | 321.30 | 1.436 | 0.946 | 2.512 | 5.842 | 0.63 | 36.36 | 110.09 | 22.43 | 0.85 | 25.29 | 296.01 |

Actual internal promotion splits — realized daily attribution for Sharpe/Sortino/DD; exact original drawdown gate separately below:

| Scope | N | Net | PF | Sharpe | Sortino | E/trade | DD % | Win % | Fees | Slip | Funding | Long net | Short net |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| internal_train | 109 | 130.63 | 1.113 | 0.378 | 0.842 | 1.198 | 0.84 | 38.53 | 191.90 | 39.00 | -4.87 | 176.63 | -46.00 |
| internal_validation | 69 | -141.05 | 0.814 | -0.964 | -1.216 | -2.044 | 0.82 | 39.13 | 107.12 | 21.76 | -0.51 | -24.35 | -116.71 |
| internal_wf1 | 25 | -225.19 | 0.442 | -2.768 | -3.320 | -9.007 | 0.92 | 20.00 | 62.36 | 12.60 | -0.62 | -32.79 | -192.40 |
| internal_wf2 | 26 | 36.59 | 1.151 | 0.696 | 1.119 | 1.407 | 0.24 | 46.15 | 54.96 | 11.08 | -0.40 | 162.06 | -125.47 |
| internal_oos | 49 | 420.46 | 1.659 | 1.519 | 4.102 | 8.581 | 0.58 | 40.82 | 94.68 | 19.31 | 1.07 | 56.44 | 364.02 |

Exact frozen gates:

| Gate | Status (original) | Threshold | Observed | Comment |
| --- | --- | --- | --- | --- |
| sample | PASS (PASS) | {"number_of_trades": ">=60"} | 169 |  |
| validation_positive | FAIL (FAIL) | {"trades": ">=10", "net": ">0"} | {"trades": 69, "net": -141.05063038} |  |
| walk_forward | FAIL (FAIL) | {"each_of_two_folds": {"trades": ">=10", "net": ">0"}} | [{"trades": 25, "net": -225.18511364}, {"trades": 26, "net": 36.58855215000002}] |  |
| sealed_oos | PASS (PASS) | {"internal_developmental_OOS": {"trades": ">=10", "net": ">0"}} | {"trades": 49, "net": 420.45524720000003} | Internal historical partition only; NOT July–September 2026 |
| cost_stress | FAIL (FAIL) | {"observed_2x_trades": ">=10", "observed_2x_net": ">0"} | {"trades": 170, "net": -331.38401114, "tested": true} | Measured result |
| neighbors | PASS (PASS) | {"positive_fraction": ">=0.5", "positive_net": ">0"} | {"positive_fraction": 1.0, "neighbors": {"VB48_STOP": true, "VB48_WINDOW": true}} | Central-family neighbors shared across profiles; self-inclusion and unmatched side/filter caveats |
| symbols | PASS (PASS) | {"qualifying_symbols": ">=2", "per_qualifier": {"trades": ">=10", "net": ">0"}} | {"BTCUSDT": {"trades": 62, "net": -238.15879649000007}, "ETHUSDT": {"trades": 60, "net": 328.60508132}, "SOLUSDT": {"trades": 47, "net": 0.3617705000000129}} |  |
| drawdown | PASS (PASS) | {"closed_trade_order_drawdown": "<=0.15", "full_history_marked_drawdown": "<=0.15"} | {"stored_closed_order": 0.022861541109161387, "marked": 0.021517696072369086} | Stored closed-trade order is not globally chronological; marked comparison is separate full-history check |
| concentration | FAIL (FAIL) | {"top10_positive_profit_share": "<=0.5", "net_excluding_top10": ">0"} | {"top10_positive_profit_share": 0.4932581850448184, "net_excluding_top10": -960.9641024399998} |  |
| profit_factor | NEAR_MISS (FAIL) | {"profit_factor": ">=1.05"} | {"value": 1.0444813217561744, "gap_to_threshold": -0.005518678243825681} | NEAR_MISS is descriptive only: PF>1 but below required 1.05 buffer; original gate remains FAIL |
| regimes | FAIL (FAIL) | {"every_declared_compatible_regime": {"trades": ">=10", "net": ">0"}} | {"TREND_HIGH_VOL": {"trades": 104, "net": -435.44029503}, "VOLATILITY_EXPANSION": {"trades": 65, "net": 526.24835036}} |  |
| sides | FAIL (FAIL) | {"every_permitted_direction": {"trades": ">=10", "net": ">0"}} | {"-1": {"trades": 93, "net": -70.55520934999997}, "1": {"trades": 76, "net": 161.36326468}} |  |

Concentration and decomposition in the actual purged gate universe:

| Diagnostic | Observed |
| --- | --- |
| Winning trades | 64 |
| Top-10 positive net profits | 1,051.77 |
| Top-10 / all positive trade profits | 49.33% |
| Net excluding top 10 | -960.96 |
| Best realized-exit month | 2026-01: 308.82 |
| Best month / positive monthly net | 40.04% |
| Net excluding best month | -218.02 |
| Best symbol | ETHUSDT: 328.61 |
| Best symbol / positive symbol net | 99.89% |
| Net excluding best symbol | -237.80 |
| Long / short net | 161.36 / -70.56 |
| Original unsorted closed DD / chronological closed DD / full-history marked DD | 2.2862% / 1.5995% / 2.1518% |

Cost outcomes (N / net), without synthesizing absent stress tests:

| Cost | All preholdout | Actual purged gate universe |
| --- | --- | --- |
| base | 284 / 122.28 | 169 / 90.81 |
| cost1.5x | 284 / -192.50 | 169 / -100.66 |
| cost2x | 285 / -547.63 | 170 / -331.38 |

Neighbor gate evidence:

| Neighbor | Gate-interval net | Positive? | Self? | Same sides? | Same funding filter? |
| --- | --- | --- | --- | --- | --- |
| VB48_STOP | 47.18 | True | False | True | True |
| VB48_WINDOW | 306.40 | True | False | True | True |

Preholdout regime decomposition (realized attribution):

| Scope | N | Net | PF | Sharpe | Sortino | E/trade | DD % | Win % | Fees | Slip | Funding | Long net | Short net |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| VOLATILITY_EXPANSION | 65 | 526.25 | 2.031 | 1.698 | 3.696 | 8.096 | 0.50 | 56.92 | 97.54 | 19.85 | 0.36 | 435.64 | 90.61 |
| TREND_HIGH_VOL | 104 | -435.44 | 0.716 | -0.840 | -1.473 | -4.187 | 2.02 | 25.96 | 221.57 | 44.90 | -0.83 | -274.28 | -161.16 |

### VB48_STOP

Family: volatility_breakout. Symbols: BTCUSDT, ETHUSDT, SOLUSDT. Signal timeframe: 15m; execution grid: 15m; causal context: 5m/15m/1h/4h. Parameters: `{"allow_long": true, "allow_short": true, "band_k": 2.5, "compression": 0.8, "funding_filter": false, "lookback": 48, "minutes": 15, "pullback_atr": 1.0, "stop_atr": 3.125}`. Compatible regimes: ['VOLATILITY_EXPANSION', 'TREND_HIGH_VOL'].

Total preholdout trades: 274; purged qualifying gate trades: 164. These are different universes; neither includes the July–September sealed evaluation.

Outer chronological metrics — native marked risk statistics:

| Scope | N | Net | PF | Sharpe | Sortino | E/trade | DD % | Win % | Fees | Slip | Funding | Long net | Short net |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| research | 104 | 351.59 | 1.415 | 1.065 | 2.438 | 3.381 | 0.50 | 46.15 | 146.66 | 29.78 | -5.11 | 188.59 | 163.01 |
| validation | 67 | -112.35 | 0.823 | -0.617 | -0.828 | -1.677 | 0.76 | 40.30 | 84.51 | 17.17 | -0.60 | 53.51 | -165.85 |
| wf1 | 51 | -287.16 | 0.531 | -2.702 | -2.993 | -5.631 | 1.12 | 31.37 | 93.41 | 18.86 | -1.21 | 30.95 | -318.11 |
| wf2 | 52 | 362.59 | 1.659 | 1.271 | 3.176 | 6.973 | 0.58 | 42.31 | 84.94 | 17.32 | 0.07 | 41.33 | 321.26 |

Actual internal promotion splits — realized daily attribution for Sharpe/Sortino/DD; exact original drawdown gate separately below:

| Scope | N | Net | PF | Sharpe | Sortino | E/trade | DD % | Win % | Fees | Slip | Funding | Long net | Short net |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| internal_train | 104 | 351.59 | 1.415 | 1.071 | 2.467 | 3.381 | 0.50 | 46.15 | 146.66 | 29.78 | -5.11 | 188.59 | 163.01 |
| internal_validation | 67 | -112.35 | 0.823 | -0.874 | -1.089 | -1.677 | 0.71 | 40.30 | 84.51 | 17.17 | -0.60 | 53.51 | -165.85 |
| internal_wf1 | 25 | -267.81 | 0.296 | -4.157 | -4.335 | -10.712 | 0.94 | 20.00 | 49.76 | 10.06 | -0.89 | -90.75 | -177.06 |
| internal_wf2 | 26 | -19.35 | 0.917 | -0.485 | -0.642 | -0.744 | 0.22 | 42.31 | 43.65 | 8.80 | -0.31 | 121.70 | -141.05 |
| internal_oos | 46 | 446.68 | 1.959 | 1.899 | 4.993 | 9.710 | 0.57 | 47.83 | 72.59 | 14.83 | 0.23 | 66.25 | 380.43 |

Exact frozen gates:

| Gate | Status (original) | Threshold | Observed | Comment |
| --- | --- | --- | --- | --- |
| sample | PASS (PASS) | {"number_of_trades": ">=60"} | 164 |  |
| validation_positive | FAIL (FAIL) | {"trades": ">=10", "net": ">0"} | {"trades": 67, "net": -112.34690770999995} |  |
| walk_forward | FAIL (FAIL) | {"each_of_two_folds": {"trades": ">=10", "net": ">0"}} | [{"trades": 25, "net": -267.81008069}, {"trades": 26, "net": -19.346247579999993}] |  |
| sealed_oos | PASS (PASS) | {"internal_developmental_OOS": {"trades": ">=10", "net": ">0"}} | {"trades": 46, "net": 446.67870113000004} | Internal historical partition only; NOT July–September 2026 |
| cost_stress | FAIL (FAIL) | {"observed_2x_trades": ">=10", "observed_2x_net": ">0"} | {"trades": 0, "net": 0.0, "tested": false} | NOT TESTED: absent cost evidence is an automatic failure, not an observed loss |
| neighbors | PASS (PASS) | {"positive_fraction": ">=0.5", "positive_net": ">0"} | {"positive_fraction": 1.0, "neighbors": {"VB48_STOP": true, "VB48_WINDOW": true}} | Central-family neighbors shared across profiles; self-inclusion and unmatched side/filter caveats |
| symbols | PASS (PASS) | {"qualifying_symbols": ">=2", "per_qualifier": {"trades": ">=10", "net": ">0"}} | {"BTCUSDT": {"trades": 60, "net": -159.71090045}, "ETHUSDT": {"trades": 60, "net": 174.99484635000002}, "SOLUSDT": {"trades": 44, "net": 31.891519249999998}} |  |
| drawdown | PASS (PASS) | {"closed_trade_order_drawdown": "<=0.15", "full_history_marked_drawdown": "<=0.15"} | {"stored_closed_order": 0.02015439585972567, "marked": 0.018644349598405108} | Stored closed-trade order is not globally chronological; marked comparison is separate full-history check |
| concentration | FAIL (FAIL) | {"top10_positive_profit_share": "<=0.5", "net_excluding_top10": ">0"} | {"top10_positive_profit_share": 0.4622364201903734, "net_excluding_top10": -767.2551532699999} |  |
| profit_factor | NEAR_MISS (FAIL) | {"profit_factor": ">=1.05"} | {"value": 1.0275114141374169, "gap_to_threshold": -0.022488585862583177} | NEAR_MISS is descriptive only: PF>1 but below required 1.05 buffer; original gate remains FAIL |
| regimes | FAIL (FAIL) | {"every_declared_compatible_regime": {"trades": ">=10", "net": ">0"}} | {"TREND_HIGH_VOL": {"trades": 100, "net": -364.6020185400001}, "VOLATILITY_EXPANSION": {"trades": 64, "net": 411.77748369000005}} |  |
| sides | FAIL (FAIL) | {"every_permitted_direction": {"trades": ">=10", "net": ">0"}} | {"-1": {"trades": 91, "net": -103.52933060999997}, "1": {"trades": 73, "net": 150.70479576000002}} |  |

Concentration and decomposition in the actual purged gate universe:

| Diagnostic | Observed |
| --- | --- |
| Winning trades | 65 |
| Top-10 positive net profits | 814.43 |
| Top-10 / all positive trade profits | 46.22% |
| Net excluding top 10 | -767.26 |
| Best realized-exit month | 2026-01: 271.48 |
| Best month / positive monthly net | 39.07% |
| Net excluding best month | -224.30 |
| Best symbol | ETHUSDT: 174.99 |
| Best symbol / positive symbol net | 84.59% |
| Net excluding best symbol | -127.82 |
| Long / short net | 150.70 / -103.53 |
| Original unsorted closed DD / chronological closed DD / full-history marked DD | 2.0154% / 1.6623% / 1.8644% |

Cost outcomes (N / net), without synthesizing absent stress tests:

| Cost | All preholdout | Actual purged gate universe |
| --- | --- | --- |
| base | 274 / 314.68 | 164 / 47.18 |
| cost1.5x | NOT TESTED | NOT TESTED |
| cost2x | NOT TESTED | NOT TESTED |

Neighbor gate evidence:

| Neighbor | Gate-interval net | Positive? | Self? | Same sides? | Same funding filter? |
| --- | --- | --- | --- | --- | --- |
| VB48_STOP | 47.18 | True | True | True | True |
| VB48_WINDOW | 306.40 | True | False | True | True |

Preholdout regime decomposition (realized attribution):

| Scope | N | Net | PF | Sharpe | Sortino | E/trade | DD % | Win % | Fees | Slip | Funding | Long net | Short net |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| VOLATILITY_EXPANSION | 64 | 411.78 | 1.916 | 1.522 | 3.113 | 6.434 | 0.40 | 56.25 | 77.17 | 15.70 | 0.42 | 345.04 | 66.73 |
| TREND_HIGH_VOL | 100 | -364.60 | 0.712 | -0.839 | -1.376 | -3.646 | 1.94 | 29.00 | 173.34 | 35.15 | -2.00 | -194.34 | -170.26 |

### MR48_STOP

Family: mean_reversion. Symbols: BTCUSDT, ETHUSDT, SOLUSDT. Signal timeframe: 15m; execution grid: 15m; causal context: 5m/15m/1h/4h. Parameters: `{"allow_long": true, "allow_short": true, "band_k": 2.5, "compression": 0.8, "funding_filter": false, "lookback": 48, "minutes": 15, "pullback_atr": 1.0, "stop_atr": 2.5}`. Compatible regimes: ['RANGE_LOW_VOL', 'VOLATILITY_COMPRESSION'].

Total preholdout trades: 1234; purged qualifying gate trades: 733. These are different universes; neither includes the July–September sealed evaluation.

Outer chronological metrics — native marked risk statistics:

| Scope | N | Net | PF | Sharpe | Sortino | E/trade | DD % | Win % | Fees | Slip | Funding | Long net | Short net |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| research | 504 | -1,555.82 | 0.776 | -2.257 | -2.736 | -3.087 | 5.92 | 56.75 | 1,346.53 | 273.80 | -17.31 | -907.97 | -647.85 |
| validation | 225 | -824.84 | 0.742 | -2.739 | -3.304 | -3.666 | 3.02 | 50.67 | 596.31 | 121.23 | 3.19 | -547.76 | -277.08 |
| wf1 | 266 | -1,187.36 | 0.693 | -2.923 | -3.312 | -4.464 | 4.01 | 54.51 | 764.62 | 154.94 | 3.94 | -271.23 | -916.13 |
| wf2 | 239 | -155.56 | 0.947 | -0.410 | -0.563 | -0.651 | 2.37 | 60.25 | 734.38 | 150.78 | 1.56 | 8.24 | -163.80 |

Actual internal promotion splits — realized daily attribution for Sharpe/Sortino/DD; exact original drawdown gate separately below:

| Scope | N | Net | PF | Sharpe | Sortino | E/trade | DD % | Win % | Fees | Slip | Funding | Long net | Short net |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| internal_train | 491 | -1,343.25 | 0.799 | -2.061 | -2.538 | -2.736 | 5.45 | 57.43 | 1,304.71 | 265.36 | -16.78 | -802.12 | -541.13 |
| internal_validation | 234 | -1,052.11 | 0.695 | -3.276 | -3.871 | -4.496 | 3.73 | 49.15 | 623.08 | 126.57 | 2.76 | -624.79 | -427.32 |
| internal_wf1 | 113 | -346.51 | 0.770 | -2.166 | -2.667 | -3.066 | 1.41 | 57.52 | 363.56 | 73.60 | 2.41 | 63.43 | -409.94 |
| internal_wf2 | 134 | -620.09 | 0.691 | -2.864 | -3.232 | -4.628 | 2.60 | 52.24 | 312.63 | 63.40 | 0.31 | -397.91 | -222.18 |
| internal_oos | 252 | -563.01 | 0.830 | -1.439 | -1.815 | -2.234 | 3.14 | 58.33 | 818.66 | 167.91 | 2.60 | -7.96 | -555.05 |

Exact frozen gates:

| Gate | Status (original) | Threshold | Observed | Comment |
| --- | --- | --- | --- | --- |
| sample | PASS (PASS) | {"number_of_trades": ">=60"} | 733 |  |
| validation_positive | FAIL (FAIL) | {"trades": ">=10", "net": ">0"} | {"trades": 234, "net": -1052.10634626} |  |
| walk_forward | FAIL (FAIL) | {"each_of_two_folds": {"trades": ">=10", "net": ">0"}} | [{"trades": 113, "net": -346.51121614999994}, {"trades": 134, "net": -620.09009526}] |  |
| sealed_oos | FAIL (FAIL) | {"internal_developmental_OOS": {"trades": ">=10", "net": ">0"}} | {"trades": 252, "net": -563.0063897000001} | Internal historical partition only; NOT July–September 2026 |
| cost_stress | FAIL (FAIL) | {"observed_2x_trades": ">=10", "observed_2x_net": ">0"} | {"trades": 0, "net": 0.0, "tested": false} | NOT TESTED: absent cost evidence is an automatic failure, not an observed loss |
| neighbors | FAIL (FAIL) | {"positive_fraction": ">=0.5", "positive_net": ">0"} | {"positive_fraction": 0.0, "neighbors": {"MR48_STOP": false, "MR48_WINDOW": false}} | Central-family neighbors shared across profiles; self-inclusion and unmatched side/filter caveats |
| symbols | FAIL (FAIL) | {"qualifying_symbols": ">=2", "per_qualifier": {"trades": ">=10", "net": ">0"}} | {"BTCUSDT": {"trades": 238, "net": -1287.13832378}, "ETHUSDT": {"trades": 250, "net": -764.40387672}, "SOLUSDT": {"trades": 245, "net": -530.1718468700001}} |  |
| drawdown | PASS (PASS) | {"closed_trade_order_drawdown": "<=0.15", "full_history_marked_drawdown": "<=0.15"} | {"stored_closed_order": 0.0973395240803574, "marked": 0.14788056653794546} | Stored closed-trade order is not globally chronological; marked comparison is separate full-history check |
| concentration | FAIL (FAIL) | {"top10_positive_profit_share": "<=0.5", "net_excluding_top10": ">0"} | {"top10_positive_profit_share": 0.08008716203331552, "net_excluding_top10": -3196.85290229} |  |
| profit_factor | FAIL (FAIL) | {"profit_factor": ">=1.05"} | {"value": 0.7484342400277916, "gap_to_threshold": -0.30156575997220847} | NEAR_MISS is descriptive only: PF>1 but below required 1.05 buffer; original gate remains FAIL |
| regimes | FAIL (FAIL) | {"every_declared_compatible_regime": {"trades": ">=10", "net": ">0"}} | {"RANGE_LOW_VOL": {"trades": 638, "net": -1941.00187971}, "VOLATILITY_COMPRESSION": {"trades": 95, "net": -640.7121676600001}} |  |
| sides | FAIL (FAIL) | {"every_permitted_direction": {"trades": ">=10", "net": ">0"}} | {"-1": {"trades": 351, "net": -1614.485566}, "1": {"trades": 382, "net": -967.22848137}} |  |

Concentration and decomposition in the actual purged gate universe:

| Diagnostic | Observed |
| --- | --- |
| Winning trades | 397 |
| Top-10 positive net profits | 615.14 |
| Top-10 / all positive trade profits | 8.01% |
| Net excluding top 10 | -3,196.85 |
| Best realized-exit month | 2026-06: 193.67 |
| Best month / positive monthly net | 95.02% |
| Net excluding best month | -2,775.38 |
| Best symbol | SOLUSDT: -530.17 |
| Best symbol / positive symbol net | N/A% |
| Net excluding best symbol | -2,051.54 |
| Long / short net | -967.23 / -1,614.49 |
| Original unsorted closed DD / chronological closed DD / full-history marked DD | 9.7340% / 9.7043% / 14.7881% |

Cost outcomes (N / net), without synthesizing absent stress tests:

| Cost | All preholdout | Actual purged gate universe |
| --- | --- | --- |
| base | 1234 / -3,723.59 | 733 / -2,581.71 |
| cost1.5x | NOT TESTED | NOT TESTED |
| cost2x | NOT TESTED | NOT TESTED |

Neighbor gate evidence:

| Neighbor | Gate-interval net | Positive? | Self? | Same sides? | Same funding filter? |
| --- | --- | --- | --- | --- | --- |
| MR48_STOP | -2,574.17 | False | True | True | True |
| MR48_WINDOW | -2,171.41 | False | False | True | True |

Preholdout regime decomposition (realized attribution):

| Scope | N | Net | PF | Sharpe | Sortino | E/trade | DD % | Win % | Fees | Slip | Funding | Long net | Short net |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| RANGE_LOW_VOL | 638 | -1,941.00 | 0.775 | -1.961 | -2.393 | -3.042 | 7.25 | 54.39 | 1,753.99 | 357.61 | 6.34 | -394.51 | -1,546.49 |
| VOLATILITY_COMPRESSION | 95 | -640.71 | 0.611 | -1.323 | -1.491 | -6.744 | 2.46 | 52.63 | 363.93 | 73.86 | 1.73 | -572.72 | -67.99 |

### MR48_WINDOW

Family: mean_reversion. Symbols: BTCUSDT, ETHUSDT, SOLUSDT. Signal timeframe: 15m; execution grid: 15m; causal context: 5m/15m/1h/4h. Parameters: `{"allow_long": true, "allow_short": true, "band_k": 2.5, "compression": 0.8, "funding_filter": false, "lookback": 60, "minutes": 15, "pullback_atr": 1.0, "stop_atr": 2.0}`. Compatible regimes: ['RANGE_LOW_VOL', 'VOLATILITY_COMPRESSION'].

Total preholdout trades: 1010; purged qualifying gate trades: 592. These are different universes; neither includes the July–September sealed evaluation.

Outer chronological metrics — native marked risk statistics:

| Scope | N | Net | PF | Sharpe | Sortino | E/trade | DD % | Win % | Fees | Slip | Funding | Long net | Short net |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| research | 417 | -1,247.21 | 0.819 | -1.736 | -2.178 | -2.991 | 5.14 | 52.76 | 1,335.39 | 271.70 | -18.91 | -798.42 | -448.79 |
| validation | 182 | -235.23 | 0.917 | -0.750 | -1.077 | -1.292 | 1.90 | 51.10 | 558.82 | 113.52 | 3.21 | -124.24 | -110.99 |
| wf1 | 219 | -1,136.44 | 0.712 | -2.619 | -3.210 | -5.189 | 3.88 | 49.77 | 755.79 | 153.14 | 2.68 | -404.44 | -731.99 |
| wf2 | 192 | -498.50 | 0.846 | -1.279 | -1.706 | -2.596 | 2.85 | 51.04 | 741.80 | 152.30 | 1.42 | -125.09 | -373.41 |

Actual internal promotion splits — realized daily attribution for Sharpe/Sortino/DD; exact original drawdown gate separately below:

| Scope | N | Net | PF | Sharpe | Sortino | E/trade | DD % | Win % | Fees | Slip | Funding | Long net | Short net |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| internal_train | 410 | -1,131.51 | 0.832 | -1.603 | -2.032 | -2.760 | 4.85 | 52.93 | 1,305.71 | 265.71 | -18.98 | -717.55 | -413.96 |
| internal_validation | 186 | -401.42 | 0.866 | -1.262 | -1.787 | -2.158 | 1.93 | 50.00 | 576.55 | 117.03 | 3.08 | -220.36 | -181.06 |
| internal_wf1 | 85 | -393.24 | 0.714 | -2.393 | -2.915 | -4.626 | 1.98 | 50.59 | 330.21 | 66.81 | 1.76 | -60.01 | -333.23 |
| internal_wf2 | 118 | -479.97 | 0.777 | -2.154 | -2.759 | -4.068 | 2.03 | 50.00 | 336.07 | 68.17 | -0.10 | -355.93 | -124.04 |
| internal_oos | 203 | -896.79 | 0.754 | -2.071 | -2.577 | -4.418 | 3.81 | 49.75 | 819.68 | 168.07 | 2.54 | -118.65 | -778.14 |

Exact frozen gates:

| Gate | Status (original) | Threshold | Observed | Comment |
| --- | --- | --- | --- | --- |
| sample | PASS (PASS) | {"number_of_trades": ">=60"} | 592 |  |
| validation_positive | FAIL (FAIL) | {"trades": ">=10", "net": ">0"} | {"trades": 186, "net": -401.4174313099999} |  |
| walk_forward | FAIL (FAIL) | {"each_of_two_folds": {"trades": ">=10", "net": ">0"}} | [{"trades": 85, "net": -393.23747893999996}, {"trades": 118, "net": -479.97025761}] |  |
| sealed_oos | FAIL (FAIL) | {"internal_developmental_OOS": {"trades": ">=10", "net": ">0"}} | {"trades": 203, "net": -896.78922671} | Internal historical partition only; NOT July–September 2026 |
| cost_stress | FAIL (FAIL) | {"observed_2x_trades": ">=10", "observed_2x_net": ">0"} | {"trades": 0, "net": 0.0, "tested": false} | NOT TESTED: absent cost evidence is an automatic failure, not an observed loss |
| neighbors | FAIL (FAIL) | {"positive_fraction": ">=0.5", "positive_net": ">0"} | {"positive_fraction": 0.0, "neighbors": {"MR48_STOP": false, "MR48_WINDOW": false}} | Central-family neighbors shared across profiles; self-inclusion and unmatched side/filter caveats |
| symbols | FAIL (FAIL) | {"qualifying_symbols": ">=2", "per_qualifier": {"trades": ">=10", "net": ">0"}} | {"BTCUSDT": {"trades": 199, "net": -1046.65506685}, "ETHUSDT": {"trades": 211, "net": -651.9644203699999}, "SOLUSDT": {"trades": 182, "net": -472.79490734999996}} |  |
| drawdown | PASS (PASS) | {"closed_trade_order_drawdown": "<=0.15", "full_history_marked_drawdown": "<=0.15"} | {"stored_closed_order": 0.07967116446511391, "marked": 0.12273829962232952} | Stored closed-trade order is not globally chronological; marked comparison is separate full-history check |
| concentration | FAIL (FAIL) | {"top10_positive_profit_share": "<=0.5", "net_excluding_top10": ">0"} | {"top10_positive_profit_share": 0.09512235443567137, "net_excluding_top10": -2931.59927393} |  |
| profit_factor | FAIL (FAIL) | {"profit_factor": ">=1.05"} | {"value": 0.7863426225067781, "gap_to_threshold": -0.26365737749322193} | NEAR_MISS is descriptive only: PF>1 but below required 1.05 buffer; original gate remains FAIL |
| regimes | FAIL (FAIL) | {"every_declared_compatible_regime": {"trades": ">=10", "net": ">0"}} | {"RANGE_LOW_VOL": {"trades": 509, "net": -2145.1521930000004}, "VOLATILITY_COMPRESSION": {"trades": 83, "net": -26.262201570000006}} |  |
| sides | FAIL (FAIL) | {"every_permitted_direction": {"trades": ">=10", "net": ">0"}} | {"-1": {"trades": 279, "net": -1416.46282599}, "1": {"trades": 313, "net": -754.95156858}} |  |

Concentration and decomposition in the actual purged gate universe:

| Diagnostic | Observed |
| --- | --- |
| Winning trades | 296 |
| Top-10 positive net profits | 760.18 |
| Top-10 / all positive trade profits | 9.51% |
| Net excluding top 10 | -2,931.60 |
| Best realized-exit month | 2025-03: 122.51 |
| Best month / positive monthly net | 48.13% |
| Net excluding best month | -2,293.92 |
| Best symbol | SOLUSDT: -472.79 |
| Best symbol / positive symbol net | N/A% |
| Net excluding best symbol | -1,698.62 |
| Long / short net | -754.95 / -1,416.46 |
| Original unsorted closed DD / chronological closed DD / full-history marked DD | 7.9671% / 8.1924% / 12.2738% |

Cost outcomes (N / net), without synthesizing absent stress tests:

| Cost | All preholdout | Actual purged gate universe |
| --- | --- | --- |
| base | 1010 / -3,117.38 | 592 / -2,171.41 |
| cost1.5x | NOT TESTED | NOT TESTED |
| cost2x | NOT TESTED | NOT TESTED |

Neighbor gate evidence:

| Neighbor | Gate-interval net | Positive? | Self? | Same sides? | Same funding filter? |
| --- | --- | --- | --- | --- | --- |
| MR48_STOP | -2,574.17 | False | False | True | True |
| MR48_WINDOW | -2,171.41 | False | True | True | True |

Preholdout regime decomposition (realized attribution):

| Scope | N | Net | PF | Sharpe | Sortino | E/trade | DD % | Win % | Fees | Slip | Funding | Long net | Short net |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| RANGE_LOW_VOL | 509 | -2,145.15 | 0.753 | -2.031 | -2.579 | -4.214 | 7.73 | 48.72 | 1,688.51 | 344.15 | 4.80 | -865.89 | -1,279.26 |
| VOLATILITY_COMPRESSION | 83 | -26.26 | 0.982 | -0.054 | -0.068 | -0.316 | 1.03 | 57.83 | 374.00 | 75.93 | 2.47 | 110.94 | -137.20 |

### MR48

Family: mean_reversion. Symbols: BTCUSDT, ETHUSDT, SOLUSDT. Signal timeframe: 15m; execution grid: 15m; causal context: 5m/15m/1h/4h. Parameters: `{"allow_long": true, "allow_short": true, "band_k": 2.5, "compression": 0.8, "funding_filter": false, "lookback": 48, "minutes": 15, "pullback_atr": 1.0, "stop_atr": 2.0}`. Compatible regimes: ['RANGE_LOW_VOL', 'VOLATILITY_COMPRESSION'].

Total preholdout trades: 1244; purged qualifying gate trades: 738. These are different universes; neither includes the July–September sealed evaluation.

Outer chronological metrics — native marked risk statistics:

| Scope | N | Net | PF | Sharpe | Sortino | E/trade | DD % | Win % | Fees | Slip | Funding | Long net | Short net |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| research | 508 | -1,694.92 | 0.794 | -2.131 | -2.651 | -3.336 | 6.32 | 53.35 | 1,668.05 | 339.30 | -17.23 | -1,000.25 | -694.67 |
| validation | 228 | -1,429.44 | 0.663 | -3.838 | -4.422 | -6.269 | 5.16 | 46.05 | 747.40 | 151.92 | 3.15 | -989.12 | -440.32 |
| wf1 | 267 | -1,635.25 | 0.657 | -3.414 | -3.846 | -6.125 | 5.45 | 49.81 | 920.04 | 186.51 | 4.20 | -580.44 | -1,054.80 |
| wf2 | 241 | -182.97 | 0.950 | -0.390 | -0.547 | -0.759 | 2.96 | 57.68 | 907.24 | 186.30 | 1.35 | -43.31 | -139.66 |

Actual internal promotion splits — realized daily attribution for Sharpe/Sortino/DD; exact original drawdown gate separately below:

| Scope | N | Net | PF | Sharpe | Sortino | E/trade | DD % | Win % | Fees | Slip | Funding | Long net | Short net |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| internal_train | 496 | -1,444.93 | 0.818 | -1.846 | -2.337 | -2.913 | 5.74 | 54.03 | 1,625.06 | 330.61 | -16.82 | -879.74 | -565.19 |
| internal_validation | 236 | -1,703.79 | 0.623 | -4.525 | -5.118 | -7.219 | 5.95 | 44.49 | 771.58 | 156.73 | 2.86 | -1,079.67 | -624.12 |
| internal_wf1 | 114 | -504.19 | 0.728 | -2.661 | -3.327 | -4.423 | 1.96 | 51.75 | 450.46 | 91.19 | 2.01 | 60.01 | -564.20 |
| internal_wf2 | 136 | -831.68 | 0.667 | -3.246 | -3.641 | -6.115 | 3.34 | 48.53 | 388.61 | 78.83 | 1.06 | -658.08 | -173.61 |
| internal_oos | 252 | -710.86 | 0.825 | -1.500 | -1.903 | -2.821 | 4.08 | 55.56 | 982.94 | 201.75 | 2.24 | -119.14 | -591.72 |

Exact frozen gates:

| Gate | Status (original) | Threshold | Observed | Comment |
| --- | --- | --- | --- | --- |
| sample | PASS (PASS) | {"number_of_trades": ">=60"} | 738 |  |
| validation_positive | FAIL (FAIL) | {"trades": ">=10", "net": ">0"} | {"trades": 236, "net": -1703.78839294} |  |
| walk_forward | FAIL (FAIL) | {"each_of_two_folds": {"trades": ">=10", "net": ">0"}} | [{"trades": 114, "net": -504.1916079699999}, {"trades": 136, "net": -831.6836878700001}] |  |
| sealed_oos | FAIL (FAIL) | {"internal_developmental_OOS": {"trades": ">=10", "net": ">0"}} | {"trades": 252, "net": -710.8599902600001} | Internal historical partition only; NOT July–September 2026 |
| cost_stress | FAIL (FAIL) | {"observed_2x_trades": ">=10", "observed_2x_net": ">0"} | {"trades": 735, "net": -6723.659536550001, "tested": true} | Measured result |
| neighbors | FAIL (FAIL) | {"positive_fraction": ">=0.5", "positive_net": ">0"} | {"positive_fraction": 0.0, "neighbors": {"MR48_STOP": false, "MR48_WINDOW": false}} | Central-family neighbors shared across profiles; self-inclusion and unmatched side/filter caveats |
| symbols | FAIL (FAIL) | {"qualifying_symbols": ">=2", "per_qualifier": {"trades": ">=10", "net": ">0"}} | {"BTCUSDT": {"trades": 239, "net": -2000.44702724}, "ETHUSDT": {"trades": 253, "net": -993.1973329099999}, "SOLUSDT": {"trades": 246, "net": -756.8793188899999}} |  |
| drawdown | FAIL (FAIL) | {"closed_trade_order_drawdown": "<=0.15", "full_history_marked_drawdown": "<=0.15"} | {"stored_closed_order": 0.14155659102264284, "marked": 0.1934478753690443} | Stored closed-trade order is not globally chronological; marked comparison is separate full-history check |
| concentration | FAIL (FAIL) | {"top10_positive_profit_share": "<=0.5", "net_excluding_top10": ">0"} | {"top10_positive_profit_share": 0.08367097202582813, "net_excluding_top10": -4519.98251747} |  |
| profit_factor | FAIL (FAIL) | {"profit_factor": ">=1.05"} | {"value": 0.710312009581088, "gap_to_threshold": -0.33968799041891207} | NEAR_MISS is descriptive only: PF>1 but below required 1.05 buffer; original gate remains FAIL |
| regimes | FAIL (FAIL) | {"every_declared_compatible_regime": {"trades": ">=10", "net": ">0"}} | {"RANGE_LOW_VOL": {"trades": 643, "net": -2879.08679123}, "VOLATILITY_COMPRESSION": {"trades": 95, "net": -871.4368878099999}} |  |
| sides | FAIL (FAIL) | {"every_permitted_direction": {"trades": ">=10", "net": ">0"}} | {"-1": {"trades": 356, "net": -1953.64789591}, "1": {"trades": 382, "net": -1796.87578313}} |  |

Concentration and decomposition in the actual purged gate universe:

| Diagnostic | Observed |
| --- | --- |
| Winning trades | 370 |
| Top-10 positive net profits | 769.46 |
| Top-10 / all positive trade profits | 8.37% |
| Net excluding top 10 | -4,519.98 |
| Best realized-exit month | 2026-06: 259.15 |
| Best month / positive monthly net | 94.92% |
| Net excluding best month | -4,009.67 |
| Best symbol | SOLUSDT: -756.88 |
| Best symbol / positive symbol net | N/A% |
| Net excluding best symbol | -2,993.64 |
| Long / short net | -1,796.88 / -1,953.65 |
| Original unsorted closed DD / chronological closed DD / full-history marked DD | 14.1557% / 14.0207% / 19.3448% |

Cost outcomes (N / net), without synthesizing absent stress tests:

| Cost | All preholdout | Actual purged gate universe |
| --- | --- | --- |
| base | 1244 / -4,942.58 | 738 / -3,750.52 |
| cost1.5x | 1240 / -7,292.06 | 737 / -5,283.55 |
| cost2x | 1236 / -9,669.14 | 735 / -6,723.66 |

Neighbor gate evidence:

| Neighbor | Gate-interval net | Positive? | Self? | Same sides? | Same funding filter? |
| --- | --- | --- | --- | --- | --- |
| MR48_STOP | -2,574.17 | False | False | True | True |
| MR48_WINDOW | -2,171.41 | False | False | True | True |

Preholdout regime decomposition (realized attribution):

| Scope | N | Net | PF | Sharpe | Sortino | E/trade | DD % | Win % | Fees | Slip | Funding | Long net | Short net |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| RANGE_LOW_VOL | 643 | -2,879.09 | 0.735 | -2.411 | -2.939 | -4.478 | 10.72 | 50.23 | 2,168.20 | 442.09 | 6.18 | -1,143.56 | -1,735.52 |
| VOLATILITY_COMPRESSION | 95 | -871.44 | 0.580 | -1.486 | -1.651 | -9.173 | 3.30 | 49.47 | 425.39 | 86.41 | 2.00 | -653.31 | -218.12 |

### TP24

Family: trend_pullback. Symbols: BTCUSDT, ETHUSDT, SOLUSDT. Signal timeframe: 60m; execution grid: 15m; causal context: 5m/15m/1h/4h. Parameters: `{"allow_long": true, "allow_short": true, "band_k": 2.5, "compression": 0.8, "funding_filter": false, "lookback": 24, "minutes": 60, "pullback_atr": 1.0, "stop_atr": 2.5}`. Compatible regimes: ['TREND_LOW_VOL'].

Total preholdout trades: 15; purged qualifying gate trades: 13. These are different universes; neither includes the July–September sealed evaluation.

Outer chronological metrics — native marked risk statistics:

| Scope | N | Net | PF | Sharpe | Sortino | E/trade | DD % | Win % | Fees | Slip | Funding | Long net | Short net |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| research | 2 | -5.00 | 0.417 | -0.570 | -0.625 | -2.498 | 0.03 | 50.00 | 3.30 | 0.68 | 0.12 | 3.58 | -8.57 |
| validation | 1 | -2.86 | 0.000 | -1.420 | -1.420 | -2.861 | 0.01 | 0.00 | 2.01 | 0.42 | 0.00 | 0.00 | -2.86 |
| wf1 | 4 | 0.38 | 1.023 | 0.034 | 0.051 | 0.094 | 0.03 | 50.00 | 6.38 | 1.29 | 0.00 | 11.96 | -11.58 |
| wf2 | 8 | -8.70 | 0.726 | -0.465 | -0.637 | -1.088 | 0.06 | 50.00 | 9.26 | 1.91 | -0.07 | -5.29 | -3.42 |

Actual internal promotion splits — realized daily attribution for Sharpe/Sortino/DD; exact original drawdown gate separately below:

| Scope | N | Net | PF | Sharpe | Sortino | E/trade | DD % | Win % | Fees | Slip | Funding | Long net | Short net |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| internal_train | 2 | -5.00 | 0.417 | -0.539 | -0.585 | -2.498 | 0.03 | 50.00 | 3.30 | 0.68 | 0.12 | 3.58 | -8.57 |
| internal_validation | 1 | -2.86 | 0.000 | -1.420 | -1.420 | -2.861 | 0.01 | 0.00 | 2.01 | 0.42 | 0.00 | 0.00 | -2.86 |
| internal_wf1 | 2 | -1.26 | 0.792 | -2.003 | -2.003 | -0.629 | 0.00 | 50.00 | 1.89 | 0.38 | 0.00 | 0.00 | -1.26 |
| internal_wf2 | 2 | 1.63 | 1.158 | 0.206 | 0.318 | 0.817 | 0.03 | 50.00 | 4.49 | 0.90 | 0.00 | 11.96 | -10.32 |
| internal_oos | 8 | -8.70 | 0.726 | -0.466 | -0.637 | -1.088 | 0.06 | 50.00 | 9.26 | 1.91 | -0.07 | -5.29 | -3.42 |

Exact frozen gates:

| Gate | Status (original) | Threshold | Observed | Comment |
| --- | --- | --- | --- | --- |
| sample | FAIL (FAIL) | {"number_of_trades": ">=60"} | 13 |  |
| validation_positive | FAIL (FAIL) | {"trades": ">=10", "net": ">0"} | {"trades": 1, "net": -2.86123498} |  |
| walk_forward | FAIL (FAIL) | {"each_of_two_folds": {"trades": ">=10", "net": ">0"}} | [{"trades": 2, "net": -1.2578360000000002}, {"trades": 2, "net": 1.6331375999999995}] |  |
| sealed_oos | FAIL (FAIL) | {"internal_developmental_OOS": {"trades": ">=10", "net": ">0"}} | {"trades": 8, "net": -8.70096361} | Internal historical partition only; NOT July–September 2026 |
| cost_stress | FAIL (FAIL) | {"observed_2x_trades": ">=10", "observed_2x_net": ">0"} | {"trades": 13, "net": -32.36580055, "tested": true} | Measured result |
| neighbors | FAIL (FAIL) | {"positive_fraction": ">=0.5", "positive_net": ">0"} | {"positive_fraction": 0.0, "neighbors": {"TP24_STOP": false, "TP24_WINDOW": false}} | Central-family neighbors shared across profiles; self-inclusion and unmatched side/filter caveats |
| symbols | FAIL (FAIL) | {"qualifying_symbols": ">=2", "per_qualifier": {"trades": ">=10", "net": ">0"}} | {"BTCUSDT": {"trades": 3, "net": -3.6527364}, "ETHUSDT": {"trades": 5, "net": 10.215813409999999}, "SOLUSDT": {"trades": 5, "net": -17.749974}} |  |
| drawdown | PASS (PASS) | {"closed_trade_order_drawdown": "<=0.15", "full_history_marked_drawdown": "<=0.15"} | {"stored_closed_order": 0.0006339731764332113, "marked": 0.0008311771780503685} | Stored closed-trade order is not globally chronological; marked comparison is separate full-history check |
| concentration | FAIL (FAIL) | {"top10_positive_profit_share": "<=0.5", "net_excluding_top10": ">0"} | {"top10_positive_profit_share": 1.0, "net_excluding_top10": -50.96277844} |  |
| profit_factor | FAIL (FAIL) | {"profit_factor": ">=1.05"} | {"value": 0.7804888718308272, "gap_to_threshold": -0.2695111281691729} | NEAR_MISS is descriptive only: PF>1 but below required 1.05 buffer; original gate remains FAIL |
| regimes | FAIL (FAIL) | {"every_declared_compatible_regime": {"trades": ">=10", "net": ">0"}} | {"TREND_LOW_VOL": {"trades": 13, "net": -11.186896990000001}} |  |
| sides | FAIL (FAIL) | {"every_permitted_direction": {"trades": ">=10", "net": ">0"}} | {"-1": {"trades": 11, "net": -17.857360890000002}, "1": {"trades": 2, "net": 6.6704639}} |  |

Concentration and decomposition in the actual purged gate universe:

| Diagnostic | Observed |
| --- | --- |
| Winning trades | 6 |
| Top-10 positive net profits | 39.78 |
| Top-10 / all positive trade profits | 100.00% |
| Net excluding top 10 | -50.96 |
| Best realized-exit month | 2026-02: 16.85 |
| Best month / positive monthly net | 48.53% |
| Net excluding best month | -28.04 |
| Best symbol | ETHUSDT: 10.22 |
| Best symbol / positive symbol net | 100.00% |
| Net excluding best symbol | -21.40 |
| Long / short net | 6.67 / -17.86 |
| Original unsorted closed DD / chronological closed DD / full-history marked DD | 0.0634% / 0.0840% / 0.0831% |

Cost outcomes (N / net), without synthesizing absent stress tests:

| Cost | All preholdout | Actual purged gate universe |
| --- | --- | --- |
| base | 15 / -16.18 | 13 / -11.19 |
| cost1.5x | 15 / -28.75 | 13 / -21.78 |
| cost2x | 15 / -41.32 | 13 / -32.37 |

Neighbor gate evidence:

| Neighbor | Gate-interval net | Positive? | Self? | Same sides? | Same funding filter? |
| --- | --- | --- | --- | --- | --- |
| TP24_STOP | -8.68 | False | False | True | True |
| TP24_WINDOW | -21.77 | False | False | True | True |

Preholdout regime decomposition (realized attribution):

| Scope | N | Net | PF | Sharpe | Sortino | E/trade | DD % | Win % | Fees | Slip | Funding | Long net | Short net |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| TREND_LOW_VOL | 13 | -11.19 | 0.780 | -0.296 | -0.413 | -0.861 | 0.08 | 46.15 | 17.66 | 3.61 | -0.07 | 6.67 | -17.86 |

### TP24_STOP

Family: trend_pullback. Symbols: BTCUSDT, ETHUSDT, SOLUSDT. Signal timeframe: 60m; execution grid: 15m; causal context: 5m/15m/1h/4h. Parameters: `{"allow_long": true, "allow_short": true, "band_k": 2.5, "compression": 0.8, "funding_filter": false, "lookback": 24, "minutes": 60, "pullback_atr": 1.0, "stop_atr": 3.125}`. Compatible regimes: ['TREND_LOW_VOL'].

Total preholdout trades: 15; purged qualifying gate trades: 13. These are different universes; neither includes the July–September sealed evaluation.

Outer chronological metrics — native marked risk statistics:

| Scope | N | Net | PF | Sharpe | Sortino | E/trade | DD % | Win % | Fees | Slip | Funding | Long net | Short net |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| research | 2 | -4.11 | 0.405 | -0.585 | -0.638 | -2.053 | 0.02 | 50.00 | 2.61 | 0.54 | 0.10 | 2.80 | -6.90 |
| validation | 1 | -2.29 | 0.000 | -1.420 | -1.420 | -2.288 | 0.01 | 0.00 | 1.61 | 0.33 | 0.00 | 0.00 | -2.29 |
| wf1 | 4 | 0.47 | 1.036 | 0.053 | 0.082 | 0.118 | 0.03 | 50.00 | 5.11 | 1.03 | 0.00 | 9.66 | -9.19 |
| wf2 | 8 | -6.87 | 0.729 | -0.458 | -0.628 | -0.858 | 0.04 | 50.00 | 7.37 | 1.52 | -0.06 | -4.08 | -2.78 |

Actual internal promotion splits — realized daily attribution for Sharpe/Sortino/DD; exact original drawdown gate separately below:

| Scope | N | Net | PF | Sharpe | Sortino | E/trade | DD % | Win % | Fees | Slip | Funding | Long net | Short net |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| internal_train | 2 | -4.11 | 0.405 | -0.553 | -0.597 | -2.053 | 0.02 | 50.00 | 2.61 | 0.54 | 0.10 | 2.80 | -6.90 |
| internal_validation | 1 | -2.29 | 0.000 | -1.420 | -1.420 | -2.288 | 0.01 | 0.00 | 1.61 | 0.33 | 0.00 | 0.00 | -2.29 |
| internal_wf1 | 2 | -1.07 | 0.781 | -2.003 | -2.003 | -0.537 | 0.00 | 50.00 | 1.52 | 0.31 | 0.00 | 0.00 | -1.07 |
| internal_wf2 | 2 | 1.55 | 1.191 | 0.245 | 0.382 | 0.773 | 0.03 | 50.00 | 3.59 | 0.72 | 0.00 | 9.66 | -8.11 |
| internal_oos | 8 | -6.87 | 0.729 | -0.459 | -0.628 | -0.858 | 0.05 | 50.00 | 7.37 | 1.52 | -0.06 | -4.08 | -2.78 |

Exact frozen gates:

| Gate | Status (original) | Threshold | Observed | Comment |
| --- | --- | --- | --- | --- |
| sample | FAIL (FAIL) | {"number_of_trades": ">=60"} | 13 |  |
| validation_positive | FAIL (FAIL) | {"trades": ">=10", "net": ">0"} | {"trades": 1, "net": -2.28827178} |  |
| walk_forward | FAIL (FAIL) | {"each_of_two_folds": {"trades": ">=10", "net": ">0"}} | [{"trades": 2, "net": -1.0748440000000001}, {"trades": 2, "net": 1.545956200000001}] |  |
| sealed_oos | FAIL (FAIL) | {"internal_developmental_OOS": {"trades": ">=10", "net": ">0"}} | {"trades": 8, "net": -6.867497459999999} | Internal historical partition only; NOT July–September 2026 |
| cost_stress | FAIL (FAIL) | {"observed_2x_trades": ">=10", "observed_2x_net": ">0"} | {"trades": 0, "net": 0.0, "tested": false} | NOT TESTED: absent cost evidence is an automatic failure, not an observed loss |
| neighbors | FAIL (FAIL) | {"positive_fraction": ">=0.5", "positive_net": ">0"} | {"positive_fraction": 0.0, "neighbors": {"TP24_STOP": false, "TP24_WINDOW": false}} | Central-family neighbors shared across profiles; self-inclusion and unmatched side/filter caveats |
| symbols | FAIL (FAIL) | {"qualifying_symbols": ">=2", "per_qualifier": {"trades": ">=10", "net": ">0"}} | {"BTCUSDT": {"trades": 3, "net": -2.5385827999999995}, "ETHUSDT": {"trades": 5, "net": 8.18055726}, "SOLUSDT": {"trades": 5, "net": -14.326631500000001}} |  |
| drawdown | PASS (PASS) | {"closed_trade_order_drawdown": "<=0.15", "full_history_marked_drawdown": "<=0.15"} | {"stored_closed_order": 0.0004991813866369599, "marked": 0.0006605830020989245} | Stored closed-trade order is not globally chronological; marked comparison is separate full-history check |
| concentration | FAIL (FAIL) | {"top10_positive_profit_share": "<=0.5", "net_excluding_top10": ">0"} | {"top10_positive_profit_share": 0.9999999999999999, "net_excluding_top10": -40.622676059999996} |  |
| profit_factor | FAIL (FAIL) | {"profit_factor": ">=1.05"} | {"value": 0.7862115970111696, "gap_to_threshold": -0.26378840298883044} | NEAR_MISS is descriptive only: PF>1 but below required 1.05 buffer; original gate remains FAIL |
| regimes | FAIL (FAIL) | {"every_declared_compatible_regime": {"trades": ">=10", "net": ">0"}} | {"TREND_LOW_VOL": {"trades": 13, "net": -8.684657039999998}} |  |
| sides | FAIL (FAIL) | {"every_permitted_direction": {"trades": ">=10", "net": ">0"}} | {"-1": {"trades": 11, "net": -14.25716019}, "1": {"trades": 2, "net": 5.57250315}} |  |

Concentration and decomposition in the actual purged gate universe:

| Diagnostic | Observed |
| --- | --- |
| Winning trades | 6 |
| Top-10 positive net profits | 31.94 |
| Top-10 / all positive trade profits | 100.00% |
| Net excluding top 10 | -40.62 |
| Best realized-exit month | 2026-02: 13.51 |
| Best month / positive monthly net | 48.42% |
| Net excluding best month | -22.19 |
| Best symbol | ETHUSDT: 8.18 |
| Best symbol / positive symbol net | 100.00% |
| Net excluding best symbol | -16.87 |
| Long / short net | 5.57 / -14.26 |
| Original unsorted closed DD / chronological closed DD / full-history marked DD | 0.0499% / 0.0664% / 0.0661% |

Cost outcomes (N / net), without synthesizing absent stress tests:

| Cost | All preholdout | Actual purged gate universe |
| --- | --- | --- |
| base | 15 / -12.79 | 13 / -8.68 |
| cost1.5x | NOT TESTED | NOT TESTED |
| cost2x | NOT TESTED | NOT TESTED |

Neighbor gate evidence:

| Neighbor | Gate-interval net | Positive? | Self? | Same sides? | Same funding filter? |
| --- | --- | --- | --- | --- | --- |
| TP24_STOP | -8.68 | False | True | True | True |
| TP24_WINDOW | -21.77 | False | False | True | True |

Preholdout regime decomposition (realized attribution):

| Scope | N | Net | PF | Sharpe | Sortino | E/trade | DD % | Win % | Fees | Slip | Funding | Long net | Short net |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| TREND_LOW_VOL | 13 | -8.68 | 0.786 | -0.287 | -0.402 | -0.668 | 0.07 | 46.15 | 14.10 | 2.88 | -0.06 | 5.57 | -14.26 |

### TP24_WINDOW

Family: trend_pullback. Symbols: BTCUSDT, ETHUSDT, SOLUSDT. Signal timeframe: 60m; execution grid: 15m; causal context: 5m/15m/1h/4h. Parameters: `{"allow_long": true, "allow_short": true, "band_k": 2.5, "compression": 0.8, "funding_filter": false, "lookback": 30, "minutes": 60, "pullback_atr": 1.0, "stop_atr": 2.5}`. Compatible regimes: ['TREND_LOW_VOL'].

Total preholdout trades: 16; purged qualifying gate trades: 14. These are different universes; neither includes the July–September sealed evaluation.

Outer chronological metrics — native marked risk statistics:

| Scope | N | Net | PF | Sharpe | Sortino | E/trade | DD % | Win % | Fees | Slip | Funding | Long net | Short net |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| research | 2 | -5.00 | 0.417 | -0.570 | -0.625 | -2.498 | 0.03 | 50.00 | 3.30 | 0.68 | 0.12 | 3.58 | -8.57 |
| validation | 2 | 0.36 | 1.125 | 0.118 | 0.178 | 0.180 | 0.01 | 50.00 | 3.64 | 0.74 | 0.00 | 0.00 | 0.36 |
| wf1 | 4 | 0.38 | 1.023 | 0.034 | 0.051 | 0.094 | 0.03 | 50.00 | 6.38 | 1.29 | 0.00 | 11.96 | -11.58 |
| wf2 | 8 | -22.51 | 0.428 | -1.195 | -1.543 | -2.813 | 0.08 | 37.50 | 9.24 | 1.90 | -0.07 | -5.29 | -17.22 |

Actual internal promotion splits — realized daily attribution for Sharpe/Sortino/DD; exact original drawdown gate separately below:

| Scope | N | Net | PF | Sharpe | Sortino | E/trade | DD % | Win % | Fees | Slip | Funding | Long net | Short net |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| internal_train | 2 | -5.00 | 0.417 | -0.539 | -0.585 | -2.498 | 0.03 | 50.00 | 3.30 | 0.68 | 0.12 | 3.58 | -8.57 |
| internal_validation | 2 | 0.36 | 1.125 | 0.118 | 0.178 | 0.180 | 0.01 | 50.00 | 3.64 | 0.74 | 0.00 | 0.00 | 0.36 |
| internal_wf1 | 2 | -1.26 | 0.792 | -2.003 | -2.003 | -0.629 | 0.00 | 50.00 | 1.89 | 0.38 | 0.00 | 0.00 | -1.26 |
| internal_wf2 | 2 | 1.63 | 1.158 | 0.206 | 0.318 | 0.817 | 0.03 | 50.00 | 4.49 | 0.90 | 0.00 | 11.96 | -10.32 |
| internal_oos | 8 | -22.51 | 0.428 | -1.213 | -1.581 | -2.813 | 0.08 | 37.50 | 9.24 | 1.90 | -0.07 | -5.29 | -17.22 |

Exact frozen gates:

| Gate | Status (original) | Threshold | Observed | Comment |
| --- | --- | --- | --- | --- |
| sample | FAIL (FAIL) | {"number_of_trades": ">=60"} | 14 |  |
| validation_positive | FAIL (FAIL) | {"trades": ">=10", "net": ">0"} | {"trades": 2, "net": 0.35900567000000017} |  |
| walk_forward | FAIL (FAIL) | {"each_of_two_folds": {"trades": ">=10", "net": ">0"}} | [{"trades": 2, "net": -1.2578360000000002}, {"trades": 2, "net": 1.6331375999999995}] |  |
| sealed_oos | FAIL (FAIL) | {"internal_developmental_OOS": {"trades": ">=10", "net": ">0"}} | {"trades": 8, "net": -22.506278000000002} | Internal historical partition only; NOT July–September 2026 |
| cost_stress | FAIL (FAIL) | {"observed_2x_trades": ">=10", "observed_2x_net": ">0"} | {"trades": 0, "net": 0.0, "tested": false} | NOT TESTED: absent cost evidence is an automatic failure, not an observed loss |
| neighbors | FAIL (FAIL) | {"positive_fraction": ">=0.5", "positive_net": ">0"} | {"positive_fraction": 0.0, "neighbors": {"TP24_STOP": false, "TP24_WINDOW": false}} | Central-family neighbors shared across profiles; self-inclusion and unmatched side/filter caveats |
| symbols | FAIL (FAIL) | {"qualifying_symbols": ">=2", "per_qualifier": {"trades": ">=10", "net": ">0"}} | {"BTCUSDT": {"trades": 4, "net": -0.43249575000000107}, "ETHUSDT": {"trades": 5, "net": -3.589500980000001}, "SOLUSDT": {"trades": 5, "net": -17.749974}} |  |
| drawdown | PASS (PASS) | {"closed_trade_order_drawdown": "<=0.15", "full_history_marked_drawdown": "<=0.15"} | {"stored_closed_order": 0.0010939127450513286, "marked": 0.0010940948530110406} | Stored closed-trade order is not globally chronological; marked comparison is separate full-history check |
| concentration | FAIL (FAIL) | {"top10_positive_profit_share": "<=0.5", "net_excluding_top10": ">0"} | {"top10_positive_profit_share": 1.0, "net_excluding_top10": -58.599806} |  |
| profit_factor | FAIL (FAIL) | {"profit_factor": ">=1.05"} | {"value": 0.6284634333089771, "gap_to_threshold": -0.4215365666910229} | NEAR_MISS is descriptive only: PF>1 but below required 1.05 buffer; original gate remains FAIL |
| regimes | FAIL (FAIL) | {"every_declared_compatible_regime": {"trades": ">=10", "net": ">0"}} | {"TREND_LOW_VOL": {"trades": 14, "net": -21.77197073}} |  |
| sides | FAIL (FAIL) | {"every_permitted_direction": {"trades": ">=10", "net": ">0"}} | {"-1": {"trades": 12, "net": -28.44243463}, "1": {"trades": 2, "net": 6.6704639}} |  |

Concentration and decomposition in the actual purged gate universe:

| Diagnostic | Observed |
| --- | --- |
| Winning trades | 6 |
| Top-10 positive net profits | 36.83 |
| Top-10 / all positive trade profits | 100.00% |
| Net excluding top 10 | -58.60 |
| Best realized-exit month | 2026-02: 16.85 |
| Best month / positive monthly net | 52.61% |
| Net excluding best month | -38.62 |
| Best symbol | BTCUSDT: -0.43 |
| Best symbol / positive symbol net | N/A% |
| Net excluding best symbol | -21.34 |
| Long / short net | 6.67 / -28.44 |
| Original unsorted closed DD / chronological closed DD / full-history marked DD | 0.1094% / 0.1094% / 0.1094% |

Cost outcomes (N / net), without synthesizing absent stress tests:

| Cost | All preholdout | Actual purged gate universe |
| --- | --- | --- |
| base | 16 / -26.77 | 14 / -21.77 |
| cost1.5x | NOT TESTED | NOT TESTED |
| cost2x | NOT TESTED | NOT TESTED |

Neighbor gate evidence:

| Neighbor | Gate-interval net | Positive? | Self? | Same sides? | Same funding filter? |
| --- | --- | --- | --- | --- | --- |
| TP24_STOP | -8.68 | False | False | True | True |
| TP24_WINDOW | -21.77 | False | True | True | True |

Preholdout regime decomposition (realized attribution):

| Scope | N | Net | PF | Sharpe | Sortino | E/trade | DD % | Win % | Fees | Slip | Funding | Long net | Short net |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| TREND_LOW_VOL | 14 | -21.77 | 0.628 | -0.575 | -0.779 | -1.555 | 0.11 | 42.86 | 19.26 | 3.93 | -0.07 | 6.67 | -28.44 |

## Detached sealed evaluation — completed results only; no selection or diagnosis uses this section

| Profile | Cost | Coverage | N | Net | PF | Sharpe | Sortino | Expectancy | DD % | Win % | Fees | Slip | Funding |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| MR48 | base | COMPLETED_FINAL_EVALUATION | 139 | -741.24 | 0.673 | -3.438 | -4.023 | -5.333 | 2.55 | 51.08 | 616.66 | 126.35 | 4.60 |
| MR48 | cost1.5x | COMPLETED_FINAL_EVALUATION | 139 | -1,064.94 | 0.559 | -4.855 | -5.312 | -7.661 | 3.55 | 49.64 | 924.96 | 188.58 | 4.60 |
| MR48 | cost2x | COMPLETED_FINAL_EVALUATION | 139 | -1,426.93 | 0.452 | -6.308 | -6.505 | -10.266 | 4.76 | 47.48 | 1,233.57 | 250.04 | 4.87 |
| MR48_STOP | base | NOT_TESTED | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| MR48_STOP | cost1.5x | NOT_TESTED | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| MR48_STOP | cost2x | NOT_TESTED | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| MR48_WINDOW | base | NOT_TESTED | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| MR48_WINDOW | cost1.5x | NOT_TESTED | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| MR48_WINDOW | cost2x | NOT_TESTED | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| TB48 | base | COMPLETED_FINAL_EVALUATION | 22 | 92.97 | 1.424 | 0.754 | 2.398 | 4.226 | 0.56 | 36.36 | 47.90 | 9.90 | -5.32 |
| TB48 | cost1.5x | COMPLETED_FINAL_EVALUATION | 22 | 64.27 | 1.269 | 0.530 | 1.590 | 2.921 | 0.62 | 36.36 | 71.86 | 14.65 | -5.32 |
| TB48 | cost2x | COMPLETED_FINAL_EVALUATION | 22 | 35.50 | 1.137 | 0.299 | 0.849 | 1.613 | 0.67 | 36.36 | 95.81 | 19.48 | -5.32 |
| TB48_FUNDING | base | COMPLETED_FINAL_EVALUATION | 22 | 92.97 | 1.424 | 0.754 | 2.398 | 4.226 | 0.56 | 36.36 | 47.90 | 9.90 | -5.32 |
| TB48_FUNDING | cost1.5x | COMPLETED_FINAL_EVALUATION | 22 | 64.27 | 1.269 | 0.530 | 1.590 | 2.921 | 0.62 | 36.36 | 71.86 | 14.65 | -5.32 |
| TB48_FUNDING | cost2x | COMPLETED_FINAL_EVALUATION | 22 | 35.50 | 1.137 | 0.299 | 0.849 | 1.613 | 0.67 | 36.36 | 95.81 | 19.48 | -5.32 |
| TB48_SHORT | base | COMPLETED_FINAL_EVALUATION | 6 | -63.69 | 0.000 | -4.057 | -4.036 | -10.614 | 0.21 | 0.00 | 14.86 | 3.12 | -0.25 |
| TB48_SHORT | cost1.5x | COMPLETED_FINAL_EVALUATION | 6 | -72.57 | 0.000 | -4.200 | -4.155 | -12.095 | 0.24 | 0.00 | 22.28 | 4.58 | -0.25 |
| TB48_SHORT | cost2x | COMPLETED_FINAL_EVALUATION | 6 | -81.46 | 0.000 | -4.302 | -4.238 | -13.577 | 0.27 | 0.00 | 29.71 | 6.04 | -0.25 |
| TB48_STOP | base | NOT_TESTED | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| TB48_STOP | cost1.5x | NOT_TESTED | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| TB48_STOP | cost2x | NOT_TESTED | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| TB48_WINDOW | base | NOT_TESTED | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| TB48_WINDOW | cost1.5x | NOT_TESTED | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| TB48_WINDOW | cost2x | NOT_TESTED | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| TP24 | base | COMPLETED_FINAL_EVALUATION | 0 | 0.00 | N/A | N/A | N/A | N/A | 0.00 | N/A | 0.00 | 0.00 | 0.00 |
| TP24 | cost1.5x | COMPLETED_FINAL_EVALUATION | 0 | 0.00 | N/A | N/A | N/A | N/A | 0.00 | N/A | 0.00 | 0.00 | 0.00 |
| TP24 | cost2x | COMPLETED_FINAL_EVALUATION | 0 | 0.00 | N/A | N/A | N/A | N/A | 0.00 | N/A | 0.00 | 0.00 | 0.00 |
| TP24_STOP | base | NOT_TESTED | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| TP24_STOP | cost1.5x | NOT_TESTED | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| TP24_STOP | cost2x | NOT_TESTED | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| TP24_WINDOW | base | NOT_TESTED | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| TP24_WINDOW | cost1.5x | NOT_TESTED | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| TP24_WINDOW | cost2x | NOT_TESTED | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| VB48 | base | COMPLETED_FINAL_EVALUATION | 19 | 199.59 | 1.867 | 1.654 | 3.980 | 10.505 | 0.47 | 47.37 | 58.50 | 11.97 | -0.11 |
| VB48 | cost1.5x | COMPLETED_FINAL_EVALUATION | 19 | 164.51 | 1.660 | 1.358 | 3.006 | 8.659 | 0.53 | 47.37 | 87.74 | 17.80 | -0.11 |
| VB48 | cost2x | COMPLETED_FINAL_EVALUATION | 19 | 129.42 | 1.482 | 1.062 | 2.179 | 6.812 | 0.58 | 47.37 | 116.99 | 23.64 | -0.11 |
| VB48_STOP | base | NOT_TESTED | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| VB48_STOP | cost1.5x | NOT_TESTED | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| VB48_STOP | cost2x | NOT_TESTED | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| VB48_WINDOW | base | NOT_TESTED | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| VB48_WINDOW | cost1.5x | NOT_TESTED | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |
| VB48_WINDOW | cost2x | NOT_TESTED | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A | N/A |

No held-out profile or parameter is selected, replaced, ranked, or optimized. Neighbor holdouts are absent, not extrapolated from central profiles.

## Files and audit trail

preholdout_profiles.json contains full metrics, side/symbol/regime decompositions and concentration details for all 14 profiles. gate_decisions.csv preserves both display status and exact frozen status, thresholds and observations. profile_period_metrics.csv, profile_groups.csv, cost_results.csv and month_contributions.csv contain the complete tables. actual_regime_transitions.csv preserves counts; near_miss_eligibility.csv preserves the authorized diagnostic. See conclusions.md for the twelve questions and final failure classification. input_checksums.json binds original inputs; autopsy_checksums.json binds new outputs.

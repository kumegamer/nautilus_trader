"""Descriptive failure attribution and twelve-question answers from saved outputs."""

import csv
import gzip
import json
from decimal import Decimal

import numpy as np
import pandas as pd


def explain(
    base, out, profiles, ranking, failures, control, pre_runs, fmt, table, dump
):
    exit_rows = []
    overlap_rows = []
    for name, d in profiles.items():
        runs = [
            r for r in pre_runs if r["candidate"] == name and r["scenario"] == "base"
        ]
        coincident = 0
        durations = []
        for r in runs:
            changes = {e["timestamp"]: e["new"] for e in r["regime_transitions"]}
            exits = {e["position_id"]: e for e in r["fills"] if e["action"] == "exit"}
            for trade in r["trades"]:
                signal = exits[trade["position_id"]]["signal_ns"]
                state = changes.get(signal)
                coincident += int(
                    state is not None
                    and state not in d["definition"]["compatible_regimes"]
                )
                durations.append(trade["duration_ns"] / 3.6e12)
        total = sum(len(r["trades"]) for r in runs)
        exit_rows.append(
            {
                "profile": name,
                "trades": total,
                "exit_coincides_with_incompatible_regime": coincident,
                "fraction": coincident / total if total else None,
                "median_holding_hours": float(np.median(durations))
                if durations
                else None,
            }
        )
    for family, central in [
        ("trend_breakout", "TB48"),
        ("trend_pullback", "TP24"),
        ("mean_reversion", "MR48"),
        ("volatility_breakout", "VB48"),
    ]:
        for variant in (central + "_STOP", central + "_WINDOW"):
            for period in ("research", "validation", "wf1", "wf2"):

                def keys(p, period=period):
                    return {
                        (r["symbol"], t["entry_ns"], t["exit_ns"], t["side"])
                        for r in pre_runs
                        if r["candidate"] == p
                        and r["period"] == period
                        and r["scenario"] == "base"
                        for t in r["trades"]
                    }

                a, b = keys(central), keys(variant)
                overlap_rows.append(
                    {
                        "family": family,
                        "central": central,
                        "variant": variant,
                        "period": period,
                        "central_trades": len(a),
                        "variant_trades": len(b),
                        "matching_entry_exit_side": len(a & b),
                        "timing_jaccard": len(a & b) / len(a | b) if a | b else None,
                    }
                )
    with (out / "exit_regime_coincidence.csv").open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(exit_rows[0]))
        w.writeheader()
        w.writerows(exit_rows)
    with (out / "neighbor_timing_overlap.csv").open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(overlap_rows[0]))
        w.writeheader()
        w.writerows(overlap_rows)
    positive_regimes = []
    for p, d in profiles.items():
        for regime, m in d["groups"]["regime"].items():
            if m["net_pnl"] > 0:
                positive_regimes.append(
                    {
                        "profile": p,
                        "regime": regime,
                        "trades": m["number_of_trades"],
                        "net": m["net_pnl"],
                        "expectancy": m["expectancy"],
                        "pf": m["profit_factor"],
                        "outer_period_nets": {
                            period: v["net_pnl"]
                            for period, v in m["outer_periods"].items()
                        },
                    }
                )
    details = json.loads((base / "results/details.json").read_text())
    comparisons = []
    for period in ("research", "validation", "wf1", "wf2", "holdout"):
        for system in ("adaptive", "static_best", "buy_hold", "no_trade"):
            m = details[system][period]["base"]["metrics"]
            series = pd.Series(
                {int(t): float(e) for t, e in m["daily_equity"]}
            ).sort_index()
            returns = series.pct_change().dropna()
            comparisons.append(
                {
                    "period": period,
                    "system": system,
                    "net": m["net_pnl"],
                    "trades": m["number_of_trades"],
                    "return": m["return"],
                    "sharpe": m["sharpe"],
                    "sortino": m["sortino"],
                    "maximum_drawdown": m["maximum_drawdown"],
                    "annualized_volatility": float(returns.std(ddof=1) * np.sqrt(365)),
                }
            )
    with (out / "risk_adjusted_comparison.csv").open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(comparisons[0]))
        w.writeheader()
        w.writerows(comparisons)
    # Explicitly requested explanation of the already-produced final buy/hold reference
    buy = []
    for path in sorted((base / "results/runs/holdout/base").glob("BUY_HOLD__*.gz")):
        with gzip.open(path, "rt") as f:
            r = json.load(f)
        t = r["trades"][0]
        buy.append(
            {
                "symbol": r["symbol"],
                "capital": 10000,
                "quantity": t["quantity"],
                "entry_price": t["entry_price"],
                "exit_price": t["exit_price"],
                "entry_notional": float(
                    Decimal(str(t["quantity"])) * Decimal(str(t["entry_price"]))
                ),
                "gross": t["gross_pnl"],
                "fees": t["fees"],
                "slippage": t["slippage"],
                "funding": t["funding"],
                "net": t["net_pnl"],
                "entry_utc": pd.Timestamp(t["entry_ns"], tz="UTC").isoformat(),
                "exit_utc": pd.Timestamp(t["exit_ns"], tz="UTC").isoformat(),
                "fraction_of_period_holding": t["duration_ns"] / (92 * 86400 * 1e9),
            }
        )
    total = {
        k: sum(Decimal(str(t[k])) for t in buy)
        for k in ("gross", "fees", "slippage", "funding", "net")
    }
    assert (
        total["gross"] - total["fees"] - total["slippage"] + total["funding"]
        == total["net"]
    )
    assert total["net"] == Decimal("15155.29048807")
    # Descriptive exposure from the already-completed holdout ledger only.
    # Entry-price notional is a proxy, not a continuously marked leverage series.
    with (base / "results/trades.csv").open() as f:
        completed = [
            t
            for t in csv.DictReader(f)
            if t["period"] == "holdout" and t["scenario"] == "base"
        ]
    exposure = {}
    period_ns = 92 * 86400 * 10**9
    for profile in ("TB48_SHORT", "BUY_HOLD"):
        trades = [t for t in completed if t["profile"] == profile]
        exposure[profile] = {
            "trades": len(trades),
            "position_time_fraction_across_three_sleeves": sum(
                int(t["duration_ns"]) for t in trades
            )
            / (3 * period_ns),
            "duration_weighted_entry_notional_to_initial_capital": sum(
                int(t["duration_ns"]) * float(t["quantity"]) * float(t["entry_price"])
                for t in trades
            )
            / (30000 * period_ns),
            "scope": "COMPLETED_HOLDOUT_DESCRIPTIVE_ONLY",
        }
    stress_missing = [p for p, d in profiles.items() if not d["assessed_costs"]]
    ratio_fail = [
        p
        for p, d in profiles.items()
        if d["actual_gate"]["top10_positive_profit_share"] is None
        or d["actual_gate"]["top10_positive_profit_share"] > 0.5
    ]
    no_top_failure = [
        p for p, d in profiles.items() if d["actual_gate"]["net_excluding_top10"] <= 0
    ]
    dd_order_affected = [
        p
        for p, d in profiles.items()
        if abs(
            d["actual_gate"]["chronological_closed_drawdown"]
            - d["actual_frozen_gate_metrics"]["maximum_drawdown"]
        )
        > 1e-10
    ]
    summary = {
        "primary_failure_classes": [
            "STRATEGY_LIBRARY_WEAK",
            "ADAPTIVE_CONTROLLER_UNDEREXERCISED",
        ],
        "secondary_failure_classes": [
            "COST_MODEL_DOMINANT",
            "INSUFFICIENT_SAMPLE",
            "SYMBOL_DEPENDENCE",
            "OTHER",
        ],
        "qualified_concerns": {
            "REGIME_MODEL_WEAK": "Strong evidence of regime/exit interaction; classifier predictive weakness itself cannot be isolated without an unfiltered control",
            "VALIDATION_GATES_TOO_STRICT": "Concentration removal and all-regime/all-side requirements are conservative; not sufficient to explain multi-gate failures",
            "PARAMETER_INSTABILITY": "Localized volatility-breakout timing/sign sensitivity; not a universal cause",
        },
        "concentration_share_failures": ratio_fail,
        "net_after_top10_failures": no_top_failure,
        "unmeasured_cost_profiles": stress_missing,
        "marked_and_closed_DD_differ": dd_order_affected,
        "positive_developmental_regime_slices": positive_regimes,
        "exit_coincidence": exit_rows,
        "risk_adjusted_comparison": comparisons,
        "buy_hold": buy,
        "buy_hold_totals": {k: str(v) for k, v in total.items()},
        "completed_holdout_exposure": exposure,
        "sealed_used_to_select_profile_or_parameters": False,
        "v2_proposals": [],
    }
    dump("diagnosis_summary.json", summary)
    gate_matrix = table(
        [
            "Profile",
            "N gate",
            "Net gate",
            "Failures",
            "Sample",
            "Val",
            "WF",
            "Int.OOS",
            "2x",
            "Nbr",
            "Sym",
            "DD",
            "Conc",
            "PF",
            "Reg",
            "Side",
        ],
        [
            [
                p,
                d["actual_gate"]["number_of_trades"],
                fmt(d["actual_gate"]["net_pnl"]),
                d["failed_gate_count"],
                *[
                    next(r["status"] for r in d["gates"] if r["gate"] == g)
                    for g in (
                        "sample",
                        "validation_positive",
                        "walk_forward",
                        "sealed_oos",
                        "cost_stress",
                        "neighbors",
                        "symbols",
                        "drawdown",
                        "concentration",
                        "profit_factor",
                        "regimes",
                        "sides",
                    )
                ],
            ]
            for p, d in sorted(
                profiles.items(), key=lambda kv: (kv[1]["failed_gate_count"], kv[0])
            )
        ],
    )
    concentration_table = table(
        [
            "Profile",
            "Winners",
            "Top10 % positive profits",
            "Net ex-top10",
            "Best month / net",
            "Net ex-month",
            "Best symbol / net",
            "Net ex-symbol",
        ],
        [
            [
                p,
                m["winning_trades"],
                fmt(100 * m["top10_positive_profit_share"]),
                fmt(m["net_excluding_top10"]),
                f"{m['best_month']} / {fmt(m['best_month_net'])}",
                fmt(m["net_excluding_best_month"]),
                f"{m['best_symbol']} / {fmt(m['best_symbol_net'])}",
                fmt(m["net_excluding_best_symbol"]),
            ]
            for p, d in profiles.items()
            for m in (d["actual_gate"],)
        ],
    )
    subtype = table(
        ["Family/profile", "Preholdout interpretation"],
        [
            [
                "MR48 / STOP / WINDOW",
                "Large samples; negative expectancy on every outer validation/WF period and every symbol. Top-10 share only ~8–10%; the concentration flag mostly restates losses. Costs dominate or overwhelm small/negative gross edge.",
            ],
            [
                "TP24 / STOP / WINDOW",
                "Only 15,15,16 total preholdout trades; 13,13,14 gate trades; six winners each. Statistical and conditional samples are inadequate. Top-10 share 100% is mechanically unavoidable.",
            ],
            [
                "TB48 / STOP / WINDOW / FUNDING",
                "Positive purged gate net, but both-direction profit relies on ETH, April 2025 and shorts. High-volatility trends lose. Widening stops mostly changes size; most exits coincide with regime incompatibility. Funding filter makes no difference in gate OOS or later outer periods, though it does affect research 2024.",
            ],
            [
                "TB48_SHORT",
                "Strongest fully cost-tested diagnostic candidate: all three symbols positive, 2x gate net +247.34, PF 1.375. But internal WF2 -64.08, internal OOS -15.11, high-vol trends -107.23, and top-10 share 60.80%, with net excluding top10 -577.12. Not merely a missing test or one overstrict gate.",
            ],
            [
                "VB48 / STOP / WINDOW",
                "Gains during volatility expansion, losses during high-volatility trends. ETH and January 2026 drive aggregate positives; performance reverses across folds. Base 1.5x/2x costs turn net negative; neighbor stress tests absent.",
            ],
        ],
    )
    risk_table = table(
        [
            "Period",
            "System",
            "N",
            "Net",
            "Return %",
            "Sharpe",
            "Sortino",
            "DD %",
            "Ann.vol %",
        ],
        [
            [
                r["period"],
                r["system"],
                r["trades"],
                fmt(r["net"]),
                fmt(100 * r["return"]),
                fmt(r["sharpe"], 3),
                fmt(r["sortino"], 3),
                fmt(100 * r["maximum_drawdown"]),
                fmt(100 * r["annualized_volatility"]),
            ]
            for r in comparisons
        ],
    )
    lines = [
        "# Failure diagnosis and answers to the twelve questions",
        "**Primary diagnosis: STRATEGY_LIBRARY_WEAK (the implemented, regime-gated library) and ADAPTIVE_CONTROLLER_UNDEREXERCISED.** Additional supported causes: COST_MODEL_DOMINANT, INSUFFICIENT_SAMPLE, SYMBOL_DEPENDENCE and OTHER (incomplete experiment coverage and validation/reporting design limitations). No v2 strategy, parameter change, or proposal is made.",
        "All selection conclusions below use developmental evidence ending before July 2026. Existing sealed results are referenced only for the requested final comparison and buy/hold explanation. This retrospective autopsy cannot turn reused developmental periods into independent evidence.",
        "## 1. Which profiles came closest?",
        "At the final freeze TB48_SHORT failed four of twelve gates, followed by VB48_WINDOW with five (including missing cost evidence). No profile was one gate short at that final snapshot. TB48_SHORT had 149 gate trades, +468.70 net, PF 1.375 and positive 2x net +247.34. Its failures were concentration, regime consistency, internal WF, and internal historical OOS. It was not close in the sense of passing after a single waiver.",
        "At actual historical requests, TB48 and TB48_FUNDING reached eleven of twelve passed gates on 19 February 2026; only concentration failed. This is one timestamp, two profiles, repeated across three symbol controllers using the same pooled evidence, not six independent experiments. All three symbols saw RANGE_LOW_VOL at that timestamp, so passing would not itself mean an immediate entry. Closest-by-count is not a new strategy selection criterion.",
        gate_matrix,
        "## 2. Which gates killed the most?",
        table(
            ["Original gate", "Failures /14"],
            [
                [k, v]
                for k, v in sorted(failures.items(), key=lambda kv: (-kv[1], kv[0]))
            ],
        ),
        "Cost stress: eight NOT TESTED + five measured failures + one pass, not thirteen observed stress losses. All 14 failed at least one internal WF subfold; this is distinct from the outer WF table. Only seven profiles were submitted by the offline reference research agent. The other seven existed as researched diagnostics but never traversed CANDIDATE in the real adaptive log.",
        "## 3. Gates too strict, or weak strategies?",
        "Both aspects matter, but arbitrary relaxation does not explain away the failure. The top-10-removal requirement is demanding for positively skewed trend strategies; removing every large winner can reject a legitimate fat-tail payoff. Requiring every declared compatible regime and allowed direction to show positive net is also stringent on subdivided samples. Conversely, an untested cost scenario is missing evidence, not excessive numerical strictness, and positive net +0.36 USDT on a qualifying symbol can pass the symbol gate without convincing economic significance.",
        "At the freeze, removing concentration alone still leaves all 14 rejected. Even the best fully tested profile has negative internal WF2 and internal OOS. Mean-reversion losses are broad and persistent; pullback is drastically undersampled; breakout positives depend on time/symbol/side/regime. These are substantive weaknesses, not simply a 1.05 PF floor. VB48 (PF 1.04448) and VB48_STOP (1.02751) are descriptive PF-buffer near misses, but fail many other gates.",
        "Gate counts are correlated and not independent statistical tests. The sample and top-10 gates duplicate failure mechanically for the pullbacks. The protocol text is looser than implementation about symbol coverage: code requires two qualifying positive symbols with >=10 trades, not all three. The configured 0.6 positive-WF fraction is not consulted by Registry/EvidenceProvider: promotion explicitly requires BOTH internal folds positive. With only two folds, >=0.6 would also require both.",
        "## 4. What actually caused concentration failures?",
        f"Only {len(ratio_fail)} profiles fail the top-10 share cap: {ratio_fail}. All {len(no_top_failure)} fail net-after-removing-top10 >0. Therefore “14 concentration failures” is not evidence that all 14 had profits dominated by outliers.",
        concentration_table,
        "TB48_SHORT: 52 winners; the top 10 produce 60.80% of positive profits, leaving -577.12 net without them. All three symbols remain individually positive, and removing the best symbol still leaves +216.73. Removing April 2025 still leaves +139.37. Thus handful-of-winners and regime dependence are stronger explanations than sole-month or sole-symbol domination.",
        "Both-direction breakout: ETH is the only positive symbol in the actual gate universe; removing it makes aggregate net negative. Removing April 2025 also makes net negative. The top-10 share ratio itself passes (~41–42%), but removing those profits makes net negative. Volatility breakout: ETH and January 2026 dominate offsets against losing symbols/folds. MR has broadly negative economics rather than concentrated alpha. TP has six winners, making a <=50% top-ten share mathematically impossible.",
        "Best-month and best-symbol ratios in JSON use sums of POSITIVE monthly/symbol net contributions. Ratios to a tiny or negative total net are unstable and not used as admission rules. “Best” for all-negative symbols means least bad, not a positive contributor.",
        "## 5. Why were walk-forward results unstable?",
        subtype,
        table(
            [
                "Profile",
                "Exit / incompatible-regime coincidence",
                "Fraction %",
                "Median holding h",
            ],
            [
                [
                    r["profile"],
                    f"{r['exit_coincides_with_incompatible_regime']}/{r['trades']}",
                    fmt(100 * r["fraction"]),
                    fmt(r["median_holding_hours"]),
                ]
                for r in exit_rows
            ],
        ),
        "The code mandates an exit when the current regime leaves the profile compatibility set, even in the “static” runs. Around 93–97% of trend-breakout exits coincide with such transitions, with median holding time four hours despite hourly signals over 48/60-hour channels. This makes the regime/exit interaction a major mechanism to investigate in the diagnosis. Coincidence does not prove it was the sole exit condition or prove that suppressing these exits would improve results. An unfiltered controlled comparison is absent and no new one was run.",
        "Breakout neighbors show similar later-period timing and losses: no general evidence of a sharp isolated profitable parameter peak. The funding filter does not change the purged gate trades. Volatility-breakout window changes affect trade timing, January contribution and fold signs, so parameter sensitivity is localized there. MR remains bad across its neighborhood. TP is too sparse for stability inference. Exact entry/exit/side overlap is recorded in neighbor_timing_overlap.csv; this excludes quantity so sizing effects remain visible separately.",
        "## 6. Any positive expectancy in particular regimes?",
        table(
            [
                "Profile",
                "Regime",
                "N",
                "Net",
                "E/trade",
                "PF",
                "Outer train / val / WF1 / WF2 nets",
            ],
            [
                [
                    r["profile"],
                    r["regime"],
                    r["trades"],
                    fmt(r["net"]),
                    fmt(r["expectancy"], 3),
                    fmt(r["pf"], 3),
                    " / ".join(
                        fmt(r["outer_period_nets"][k])
                        for k in ("research", "validation", "wf1", "wf2")
                    ),
                ]
                for r in positive_regimes
            ],
        ),
        "Yes. In particular VB48 volatility expansion has 65 purged gate trades, +526.25 net, +8.10/trade and PF 2.032; its outer expansion slice is positive in research, validation and both outer WF periods (+96.07/+172.40/+72.15/+182.55), although the latter first WF slice has just 10 trades. TREND_HIGH_VOL loses -435.44. TB48_SHORT low-volatility trends have 86 trades, +575.93 net and PF 2.024; high-volatility trends lose -107.23. These are descriptive preholdout subgroups, not newly validated strategies, and no sealed subgroup is used to choose a filter.",
        "## 7. Could NO_TRADE / regime filtering plausibly help without hindsight?",
        "The patterns are compatible with that possibility, but this experiment does not establish the counterfactual. Every active v1 profile ALREADY had regime entry filters and forced exits. Rejecting the known losing high-volatility trend slices after seeing them would be hindsight selection. A causal timestamp on a regime label does not make a subsequently chosen mapping independent of outcomes. Dropping saved losing trades is not a re-backtest: it changes open-position occupancy, later entries, costs and risk.",
        "The most defensible statements are that existing compatibility mappings mix profitable and losing states, and that abstention avoided losses for failed profiles. Neither proves positive expectancy from a new filter. No new mapping or strategy is proposed here.",
        "## 8. Was the controller meaningfully exercised?",
        f"No, for the central performance-adaptation objective. Actual trades: {control['actual_trades']}; actual switches: {control['actual_profile_switches']}; successful VALIDATED/SHADOW admissions: zero. All {sum(control['degradation_states_base'].values()):,} base-cost degradation evaluations were INSUFFICIENT_DATA. Features, regimes, eligibility checks, research throttling and abstention were exercised; performance-driven sizing, switching, side shutdown and recovery were not exercised on real historical positions. Their unit fixtures do not substitute for an economically exercised adaptive path.",
        "## 9. How many regime transitions?",
        f"{control['actual_changes_one_market_path']:,} actual changes across BTC/ETH/SOL over 2024–September 2026: 3,886 before July and 300 in the completed holdout. The 4,189 rows additionally contain three UNKNOWN→UNKNOWN initializations. Repeating three cost scenarios produces 12,558 changes, not independent observations. The old 131,648 count includes static/reference run repetitions and must not be reported as distinct adaptive market transitions.",
        "## 10. How many switches if gates were relaxed one level?",
        "The user's clarified rule is applied exactly: accept PASS or existing diagnostic NEAR_MISS; any true FAIL blocks promotion. The original frozen promotion code has only binary gates and no NEAR_MISS state. The autopsy's descriptive PF-margin annotation (1 < PF < 1.05) was established from preholdout evidence before this clarification; it is not a frozen production acceptance rule. If 'pre-existing' means only states stored in the original frozen experiment, there are no such NEAR_MISS states and the outcome is also zero.",
        f"Result: ZERO newly eligible profiles at the final freeze or at recorded preholdout research requests; ZERO additional hypothetical switches; ZERO incremental subsequent PnL. Subsequent performance is unchanged, neither improved nor worsened. {control['near_miss_only_diagnostic']['records_checked']} final/historical evidence records were checked without using holdout performance. No arbitrary FAIL gate is waived and no switch counterfactual or new strategy run is needed.",
        "The final-freeze annotations are exactly VB48 profit_factor: 1.044481 versus >=1.05, and VB48_STOP profit_factor: 1.027511 versus >=1.05. Each still has six other true FAIL gates. None of the 378 assessed preholdout research-request records has a PF-margin NEAR_MISS. Historical requests are listed in near_miss_eligibility.csv with every remaining FAIL. TB48/TB48_FUNDING's historical concentration FAIL remains a blocking FAIL, not a near miss. Original classification, promotion history and thresholds are unchanged.",
        "## 11. Risk-adjusted adaptive versus static best",
        risk_table,
        "The static comparator was frozen as TB48_SHORT using developmental validation+outer WF Sharpe. On completed holdout: net -63.69, Sharpe -4.057, Sortino -4.036, max DD 0.2123%, annualized daily volatility ~0.2078%, six trades. Adaptive: zero net, zero volatility/drawdown, and UNDEFINED Sharpe/Sortino (0/0), not Sharpe zero and not a statistically superior Sharpe. It avoided a loss by holding cash but did not demonstrate improved trading efficiency. Six static holdout trades also make annualized ratios fragile.",
        "On preholdout pooled research+validation+WF data TB48_SHORT has Sharpe 0.784, Sortino 1.490, max DD 1.044% and 219 trades; the adaptive system still has no performance sample. This pooled figure includes research and is not independent OOS. Static validation Sharpe 2.515 falls to -0.346 and -0.031 across the two outer WF periods.",
        "## 12. Why buy-and-hold made +15,155.29 USDT",
        table(
            [
                "Symbol",
                "Sleeve capital",
                "Quantity",
                "Entry fill",
                "Exit fill",
                "Entry notional",
                "Gross",
                "Fees",
                "Slip",
                "Funding",
                "Net",
            ],
            [
                [
                    t["symbol"],
                    t["capital"],
                    t["quantity"],
                    t["entry_price"],
                    t["exit_price"],
                    fmt(t["entry_notional"]),
                    fmt(t["gross"]),
                    fmt(t["fees"]),
                    fmt(t["slippage"]),
                    fmt(t["funding"]),
                    fmt(t["net"]),
                ]
                for t in buy
            ],
        ),
        f"Total initial capital 30,000 USDT: three independent 10,000 sleeves. Each takes a long linear USD-M perpetual position capped at 90% of sleeve capital, with lot rounding; total entry notional {sum(t['entry_notional'] for t in buy):,.5f} USDT (~{100 * sum(t['entry_notional'] for t in buy) / 30000:.3f}% of capital). Venue default leverage is 1; there is no leverage multiplier above one. Entry is 1 July 2026 00:15 UTC and exit 30 September 2026 23:45 UTC (both plus the declared 1ms quote offset), for 99.977% of the test duration. Fixed quantities are held without rebalancing or the active strategies' stop logic.",
        "The BuyHold helper uses a synthetic sizing distance close×0.0025/0.9 to generate roughly 90% notional through the common sizing function. It does NOT enforce that distance as a protective stop; its overridden on_bar only maintains the long reference until the scheduled final quote. Thus this is not a 0.25%-risk stopped trade.",
        f"Exact identity: {total['gross']} gross − {total['fees']} fees − {total['slippage']} slippage + ({total['funding']}) funding = {total['net']} net, or +50.5176% of initial 30,000. The profit comes from the saved entry-to-exit BTC, ETH and SOL price increases, not from adaptation. Completed holdout Sharpe 3.930, Sortino 8.594, max DD 6.836% and annualized volatility ~43.71% describe a much larger directional exposure.",
        f"Same initial capital and execution-cost venue make it a useful opportunity benchmark, but it is NOT economically apples-to-apples on risk. Active strategies budget <=25 USDT initial stop risk per entry (0.25% of each sleeve), spend much of the period flat, and may be short. On the SAME completed holdout, TB48_SHORT has {100 * exposure['TB48_SHORT']['position_time_fraction_across_three_sleeves']:.4f}% position time across sleeves and approximately {100 * exposure['TB48_SHORT']['duration_weighted_entry_notional_to_initial_capital']:.4f}% duration-weighted entry-notional exposure to initial portfolio capital. Buy/hold has {100 * exposure['BUY_HOLD']['position_time_fraction_across_three_sleeves']:.4f}% position time and {100 * exposure['BUY_HOLD']['duration_weighted_entry_notional_to_initial_capital']:.4f}% entry-notional exposure. The notional statistic is an entry-price proxy, not a full marked leverage series. No volatility-matched or beta-matched reference was supplied, and no new one is manufactured.",
        "## Final failure classification",
        table(
            ["Class", "Diagnosis"],
            [
                [
                    "STRATEGY_LIBRARY_WEAK",
                    "PRIMARY: as implemented with existing regime gating/forced exits, no profile demonstrates stable qualifying economics. Not a proof that the abstract strategy families can never work.",
                ],
                [
                    "ADAPTIVE_CONTROLLER_UNDEREXERCISED",
                    "PRIMARY: no validated profiles, no trades, no switches, and no actual performance-decay feedback.",
                ],
                [
                    "COST_MODEL_DOMINANT",
                    "SUPPORTED, especially MR and marginal both-side TB/VB. MR48_WINDOW gross +303.90 becomes net -2,171.41 after costs; MR48 already loses before costs. TB48_SHORT retains +247.34 at 2x, so costs are not a universal explanation.",
                ],
                [
                    "INSUFFICIENT_SAMPLE",
                    "SUPPORTED for TP and small time/regime cells; not a blanket excuse for >700-trade losing MR samples.",
                ],
                [
                    "SYMBOL_DEPENDENCE",
                    "SUPPORTED for both-direction TB and VB; short-only TB is positive on all three symbols and is less exposed to this failure.",
                ],
                [
                    "REGIME_MODEL_WEAK",
                    "QUALIFIED: strong diagnostic evidence against the chosen compatibility/forced-exit overlay. Classifier quality or benefit from different thresholds cannot be identified without an absent controlled comparison.",
                ],
                [
                    "VALIDATION_GATES_TOO_STRICT",
                    "QUALIFIED: tail-removal and every-cell positivity are conservative, but a one-gate waiver at the freeze admits nobody and missing stress tests are a coverage failure, not a threshold problem.",
                ],
                [
                    "PARAMETER_INSTABILITY",
                    "LOCALIZED: VB window/stop timing and signs vary. TB neighbors are broadly similar; MR is consistently bad; TP cannot support a stability claim.",
                ],
                [
                    "OTHER",
                    "Incomplete stress/holdout coverage; only seven agent-proposed candidates; central-family neighbor tests can include self and mismatched directions/filter permissions; nonchronological closed-trade DD; reused developmental history; uncalibrated confidence; no unfiltered or matched-risk control.",
                ],
            ],
        ),
        "The original ADAPTIVE_NO_EDGE conclusion stands. The diagnosis does not justify calling the flat system a profitable adaptive edge, does not prove all rejection counts represent independent failures, and does not support promoting a profile by quietly loosening one rule. No v2 design or optimization is proposed.",
    ]
    (out / "conclusions.md").write_text("\n\n".join(lines) + "\n")

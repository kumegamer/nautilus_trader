"""Read-only failure autopsy of frozen Adaptive Trading v1 outputs.

No market downloads, backtests, optimization, strategy creation or threshold mutation.
Only saved preholdout trades inform diagnostics/ranking. Completed sealed aggregates are
rendered separately afterward. Hypothetical eligibility accepts only prior PF-margin annotations, never true FAILs.
"""

import csv
import gzip
import hashlib
import json
import subprocess
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
import pandas as pd

BASE = Path(__file__).resolve().parents[1]
OUT = Path(__file__).resolve().parent
PRE = ("research", "validation", "wf1", "wf2")
DAY = 86400 * 10**9
CFG = json.loads((BASE / "config.json").read_text())
PROFILES = {
    k: v
    for k, v in json.loads((BASE / "results/profiles.json").read_text()).items()
    if k != "NO_TRADE"
}
EVIDENCE = json.loads((BASE / "results/preholdout_evidence.json").read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def ns(value):
    return pd.Timestamp(value, tz="UTC").value


def iso(value):
    return pd.Timestamp(value, tz="UTC").isoformat()


def dump(name, value):
    (OUT / name).write_text(
        json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n"
    )


def csv_write(name, rows):
    fields = list(dict.fromkeys(k for r in rows for k in r))
    with (OUT / name).open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in rows:
            w.writerow(
                {
                    k: json.dumps(v, sort_keys=True)
                    if isinstance(v, (dict, list))
                    else v
                    for k, v in r.items()
                }
            )


def read_pre():
    runs = []
    for period in PRE:
        for p in sorted((BASE / "results/runs" / period).glob("*/*.json.gz")):
            with gzip.open(p, "rt") as f:
                r = json.load(f)
            runs.append(r)
    return runs


def trade_stats(trades):
    t = sorted(trades, key=lambda x: x["exit_ns"])
    values = np.array([x["net_pnl"] for x in t], dtype=float)
    wins = sorted(
        [x for x in t if x["net_pnl"] > 0], key=lambda x: x["net_pnl"], reverse=True
    )
    losses = [x["net_pnl"] for x in t if x["net_pnl"] < 0]
    win_sum = sum(x["net_pnl"] for x in wins)
    net = float(values.sum())
    top = sum(x["net_pnl"] for x in wins[:10])
    months = defaultdict(float)
    symbols = defaultdict(float)
    for x in t:
        months[pd.Timestamp(x["exit_ns"], tz="UTC").strftime("%Y-%m")] += x["net_pnl"]
        symbols[x["symbol"]] += x["net_pnl"]
    best_month = max(months, key=months.get) if months else None
    best_symbol = max(symbols, key=symbols.get) if symbols else None
    positive_months = sum(v for v in months.values() if v > 0)
    positive_symbols = sum(v for v in symbols.values() if v > 0)
    curve = np.r_[30000, 30000 + np.cumsum(values)]
    return {
        "number_of_trades": len(t),
        "gross_pnl": sum(x["gross_pnl"] for x in t),
        "net_pnl": net,
        "profit_factor": win_sum / -sum(losses) if losses else None,
        "expectancy": float(values.mean()) if len(t) else None,
        "expectancy_r": float(np.mean([x["net_pnl"] / x["initial_risk"] for x in t]))
        if t
        else None,
        "win_rate": len(wins) / len(t) if t else None,
        "fees": sum(x["fees"] for x in t),
        "slippage": sum(x["slippage"] for x in t),
        "funding": sum(x["funding"] for x in t),
        "winning_trades": len(wins),
        "positive_trade_profit": win_sum,
        "top10_profit": top,
        "top10_positive_profit_share": top / win_sum if win_sum else None,
        "net_excluding_top10": net - top,
        "best_month": best_month,
        "best_month_net": months.get(best_month),
        "best_month_positive_month_profit_share": months[best_month] / positive_months
        if best_month and positive_months
        else None,
        "net_excluding_best_month": net - months[best_month] if best_month else None,
        "best_symbol": best_symbol,
        "best_symbol_net": symbols.get(best_symbol),
        "best_symbol_positive_symbol_profit_share": symbols[best_symbol]
        / positive_symbols
        if best_symbol and positive_symbols
        else None,
        "net_excluding_best_symbol": net - symbols[best_symbol]
        if best_symbol
        else None,
        "long_net": sum(x["net_pnl"] for x in t if x["side"] == 1),
        "short_net": sum(x["net_pnl"] for x in t if x["side"] == -1),
        "long_trades": sum(x["side"] == 1 for x in t),
        "short_trades": sum(x["side"] == -1 for x in t),
        "chronological_closed_drawdown": float(
            np.max(1 - curve / np.maximum.accumulate(curve))
        ),
        "monthly_net_pnl": dict(sorted(months.items())),
        "symbol_net_pnl": dict(symbols),
    }


def daily_stats(points, capital=30000):
    s = pd.Series({int(t): float(e) for t, e in points}).sort_index()
    r = s.pct_change().dropna()
    sd = r.std(ddof=1)
    downside = (
        float(np.sqrt(np.mean(np.minimum(r.to_numpy(), 0) ** 2))) if len(r) else 0
    )
    return {
        "sharpe": float(r.mean() / sd * np.sqrt(365)) if sd > 0 else None,
        "sortino": float(r.mean() / downside * np.sqrt(365)) if downside > 0 else None,
        "maximum_drawdown": float((1 - s / s.cummax()).max()) if len(s) else None,
        "annualized_daily_volatility": float(sd * np.sqrt(365)) if len(r) > 1 else None,
        "return": float(s.iloc[-1] / capital - 1) if len(s) else None,
        "daily_observations": len(r),
    }


def marked_stats(runs):
    trades = [t for r in runs for t in r["trades"]]
    m = trade_stats(trades)
    points = []
    wealth = 30000.0
    for period in sorted(
        {r["period"] for r in runs}, key=lambda p: ns(CFG["periods"][p][0])
    ):
        changes = []
        for r in runs:
            if r["period"] == period:
                s = pd.Series({int(t): float(e) for t, e in r["daily"]}).sort_index()
                changes.append(s.diff().fillna(0))
        delta = pd.concat(changes).groupby(level=0).sum().sort_index()
        curve = wealth + delta.cumsum()
        points.extend((int(t), float(e)) for t, e in curve.items())
        wealth = float(curve.iloc[-1])
    m.update(daily_stats(points))
    start = min(ns(CFG["periods"][r["period"]][0]) for r in runs)
    end = max(ns(CFG["periods"][r["period"]][1]) for r in runs)
    duration = end - start
    m["position_time_fraction"] = sum(t["exit_ns"] - t["entry_ns"] for t in trades) / (
        3 * duration
    )
    m["entry_notional_time_weighted_capital_fraction_proxy"] = sum(
        t["quantity"] * t["entry_price"] * (t["exit_ns"] - t["entry_ns"])
        for t in trades
    ) / (30000 * duration)
    m["risk_statistic_basis"] = (
        "Native saved daily marked equity; fixed-risk nominal period PnL carried"
    )
    return m


def attributed_stats(trades, lo, hi):
    m = trade_stats(trades)
    days = pd.date_range(
        pd.Timestamp(lo, tz="UTC").normalize(),
        pd.Timestamp(hi, tz="UTC").ceil("D"),
        freq="D",
    )
    pnl = pd.Series(0.0, index=days)
    for t in trades:
        d = pd.Timestamp(t["exit_ns"], tz="UTC").ceil("D")
        pnl.loc[d] += t["net_pnl"]
    m.update(
        daily_stats([(int(t.value), 30000 + float(v)) for t, v in pnl.cumsum().items()])
    )
    m["risk_statistic_basis"] = (
        "Supplementary daily realized-PnL attribution; not native marked subgroup equity or an original gate metric"
    )
    return m


def gate_rows(profile, e):
    rows = []

    def add(gate, threshold, observed, reason="", near=False):
        passed = e["gates"][gate]
        rows.append(
            {
                "profile": profile,
                "gate": gate,
                "status": "PASS" if passed else "NEAR_MISS" if near else "FAIL",
                "frozen_result": "PASS" if passed else "FAIL",
                "threshold": threshold,
                "observed": observed,
                "reason": reason,
                "end_ns": e["end_ns"],
            }
        )

    m = e["metrics"]
    add("sample", {"number_of_trades": ">=60"}, m["number_of_trades"])

    def compound(m):
        return {"trades": m["number_of_trades"], "net": m["net_pnl"]}

    add(
        "validation_positive",
        {"trades": ">=10", "net": ">0"},
        compound(e["validation"]),
    )
    add(
        "walk_forward",
        {"each_of_two_folds": {"trades": ">=10", "net": ">0"}},
        [compound(x) for x in e["walk_forward"]],
    )
    add(
        "sealed_oos",
        {"internal_developmental_OOS": {"trades": ">=10", "net": ">0"}},
        compound(e["internal_sealed"]),
        "Internal historical partition only; NOT July–September 2026",
    )
    tested = profile in {"TB48", "TP24", "MR48", "VB48", "TB48_SHORT", "TB48_FUNDING"}
    add(
        "cost_stress",
        {"observed_2x_trades": ">=10", "observed_2x_net": ">0"},
        {**compound(e["cost2x"]), "tested": tested},
        "Measured result"
        if tested
        else "NOT TESTED: absent cost evidence is an automatic failure, not an observed loss",
    )
    add(
        "neighbors",
        {"positive_fraction": ">=0.5", "positive_net": ">0"},
        {
            "positive_fraction": sum(e["neighbors"].values()) / len(e["neighbors"]),
            "neighbors": e["neighbors"],
        },
        "Central-family neighbors shared across profiles; self-inclusion and unmatched side/filter caveats",
    )
    add(
        "symbols",
        {"qualifying_symbols": ">=2", "per_qualifier": {"trades": ">=10", "net": ">0"}},
        {s: compound(v) for s, v in e["by_symbol"].items()},
    )
    add(
        "drawdown",
        {
            "closed_trade_order_drawdown": "<=0.15",
            "full_history_marked_drawdown": "<=0.15",
        },
        {
            "stored_closed_order": m["maximum_drawdown"],
            "marked": m.get("marked_maximum_drawdown"),
        },
        "Stored closed-trade order is not globally chronological; marked comparison is separate full-history check",
    )
    add(
        "concentration",
        {"top10_positive_profit_share": "<=0.5", "net_excluding_top10": ">0"},
        {
            "top10_positive_profit_share": m["top10_positive_profit_share"],
            "net_excluding_top10": m["net_excluding_top10"],
        },
    )
    pf = m["profit_factor"]
    add(
        "profit_factor",
        {"profit_factor": ">=1.05"},
        {"value": pf, "gap_to_threshold": None if pf is None else pf - 1.05},
        "NEAR_MISS is descriptive only: PF>1 but below required 1.05 buffer; original gate remains FAIL",
        near=pf is not None and 1 < pf < 1.05,
    )
    add(
        "regimes",
        {"every_declared_compatible_regime": {"trades": ">=10", "net": ">0"}},
        {k: compound(v) for k, v in e["by_regime"].items()},
    )
    add(
        "sides",
        {"every_permitted_direction": {"trades": ">=10", "net": ">0"}},
        {k: compound(v) for k, v in e["by_side"].items()},
    )
    assert {r["gate"]: r["frozen_result"] == "PASS" for r in rows} == e["gates"]
    return rows


def select(trades, lo, hi):
    return [t for t in trades if lo <= t["entry_ns"] < t["exit_ns"] < hi]


def flatten(m):
    return {k: v for k, v in m.items() if not isinstance(v, dict)}


def analyze_pre(runs):
    profiles = {}
    period_rows, gates, groups, costs, months = [], [], [], [], []
    for p, definition in PROFILES.items():
        base = [r for r in runs if r["candidate"] == p and r["scenario"] == "base"]
        trades = [t for r in base for t in r["trades"]]
        e = EVIDENCE[p]
        bounds = e["bounds_ns"]
        segments = [
            (name, lo, hi)
            for name, lo, hi in zip(
                (
                    "internal_train",
                    "internal_validation",
                    "internal_wf1",
                    "internal_wf2",
                    "internal_oos",
                ),
                bounds[:-1],
                bounds[1:],
            )
        ]
        internal = {
            name: attributed_stats(select(trades, lo, hi), lo, hi)
            for name, lo, hi in segments
        }
        gate_trades = [t for _, lo, hi in segments[1:] for t in select(trades, lo, hi)]
        assert len(gate_trades) == e["metrics"]["number_of_trades"]
        assert (
            abs(sum(t["net_pnl"] for t in gate_trades) - e["metrics"]["net_pnl"])
            < 0.000001
        )
        pooled = marked_stats(base)
        gate_m = attributed_stats(gate_trades, bounds[1], bounds[-1])
        outer = {
            period: marked_stats([r for r in base if r["period"] == period])
            for period in PRE
        }
        rows = gate_rows(p, e)
        gates.extend(rows)
        for period, m in outer.items():
            period_rows.append(
                {
                    "profile": p,
                    "scope": "outer_native_marked",
                    "period": period,
                    **flatten(m),
                }
            )
        for period, m in internal.items():
            period_rows.append(
                {
                    "profile": p,
                    "scope": "internal_realized_attribution",
                    "period": period,
                    **flatten(m),
                }
            )
        period_rows.append(
            {
                "profile": p,
                "scope": "preholdout_pooled_native_marked",
                "period": "all_pre",
                **flatten(pooled),
            }
        )
        period_rows.append(
            {
                "profile": p,
                "scope": "actual_gate_eligible_trades",
                "period": "purged_internal_nontrain",
                **flatten(gate_m),
            }
        )
        grouped = {}
        for axis in ("symbol", "side", "regime"):
            values = (
                CFG["symbols"]
                if axis == "symbol"
                else [1, -1]
                if axis == "side"
                else definition["compatible_regimes"]
            )
            grouped[axis] = {}
            for value in values:
                chosen = [t for t in gate_trades if t[axis] == value]
                gm = attributed_stats(chosen, bounds[1], bounds[-1])
                gm["outer_periods"] = {
                    period: trade_stats(
                        [
                            t
                            for r in base
                            if r["period"] == period
                            for t in r["trades"]
                            if t[axis] == value
                        ]
                    )
                    for period in PRE
                }
                grouped[axis][str(value)] = gm
                groups.append(
                    {
                        "profile": p,
                        "scope": "actual_gate_eligible_trades",
                        "axis": axis,
                        "value": value,
                        **flatten(gm),
                    }
                )
        for scope, tr in (("actual_gate", gate_trades), ("all_pre", trades)):
            for month, net in trade_stats(tr)["monthly_net_pnl"].items():
                chosen = [
                    t
                    for t in tr
                    if pd.Timestamp(t["exit_ns"], tz="UTC").strftime("%Y-%m") == month
                ]
                months.append(
                    {
                        "profile": p,
                        "scope": scope,
                        "month": month,
                        "trades": len(chosen),
                        "net_pnl": net,
                    }
                )
        cost_metrics = {}
        for scenario in CFG["scenarios"]:
            chosen_runs = [
                r for r in runs if r["candidate"] == p and r["scenario"] == scenario
            ]
            if not chosen_runs:
                cost_metrics[scenario] = None
                for scope in ("all_pre", "actual_gate", *PRE):
                    costs.append(
                        {
                            "profile": p,
                            "scope": scope,
                            "scenario": scenario,
                            "coverage": "NOT_TESTED",
                        }
                    )
                continue
            sc_trades = [t for r in chosen_runs for t in r["trades"]]
            selected_gate = [
                t for _, lo, hi in segments[1:] for t in select(sc_trades, lo, hi)
            ]
            cm = {
                "all_pre": marked_stats(chosen_runs),
                "actual_gate": attributed_stats(selected_gate, bounds[1], bounds[-1]),
            }
            cm.update(
                {
                    period: marked_stats(
                        [r for r in chosen_runs if r["period"] == period]
                    )
                    for period in PRE
                }
            )
            cost_metrics[scenario] = cm
            for scope, m in cm.items():
                costs.append(
                    {
                        "profile": p,
                        "scope": scope,
                        "scenario": scenario,
                        "coverage": "TESTED",
                        **flatten(m),
                    }
                )
        neighbor_ids = list(e["neighbors"])
        neighbor_info = {}
        for neighbor in neighbor_ids:
            nruns = [
                r
                for r in runs
                if r["candidate"] == neighbor and r["scenario"] == "base"
            ]
            nt = [t for r in nruns for t in r["trades"]]
            # Exact gate neighbor interval is NOT purged across internal subfolds
            actual_neighbor = select(nt, bounds[1], bounds[-1])
            neighbor_info[neighbor] = {
                "gate_interval_net": sum(t["net_pnl"] for t in actual_neighbor),
                "positive": e["neighbors"][neighbor],
                "is_self": neighbor == p,
                "side_permissions_match": (
                    definition["allow_long"],
                    definition["allow_short"],
                )
                == (
                    PROFILES[neighbor]["allow_long"],
                    PROFILES[neighbor]["allow_short"],
                ),
                "funding_filter_matches": definition["funding_filter"]
                == PROFILES[neighbor]["funding_filter"],
                "outer_net": {
                    period: sum(
                        t["net_pnl"]
                        for r in nruns
                        if r["period"] == period
                        for t in r["trades"]
                    )
                    for period in PRE
                },
            }
            assert (neighbor_info[neighbor]["gate_interval_net"] > 0) == e["neighbors"][
                neighbor
            ]
        profiles[p] = {
            "definition": definition,
            "failed_gate_count": sum(not x for x in e["gates"].values()),
            "assessed_costs": cost_metrics["cost2x"] is not None,
            "gates": rows,
            "all_pre": pooled,
            "actual_gate": gate_m,
            "actual_frozen_gate_metrics": e["metrics"],
            "internal": internal,
            "outer": outer,
            "groups": grouped,
            "costs": cost_metrics,
            "neighbors": neighbor_info,
            "bounds_ns": bounds,
            "bounds_utc": [iso(t) for t in bounds],
        }
    ranking = sorted(profiles, key=lambda p: (profiles[p]["failed_gate_count"], p))
    failures = Counter(r["gate"] for r in gates if r["frozen_result"] == "FAIL")
    dump("preholdout_profiles.json", profiles)
    dump(
        "preholdout_diagnosis.json",
        {
            "ranking_by_original_failed_gate_count": ranking,
            "gate_failure_counts": dict(failures),
            "missing_stress_profiles": [
                p for p in profiles if not profiles[p]["assessed_costs"]
            ],
            "selection_scope": "Saved preholdout evidence only; no sealed observations used",
        },
    )
    csv_write("profile_period_metrics.csv", period_rows)
    csv_write("gate_decisions.csv", gates)
    csv_write("profile_groups.csv", groups)
    csv_write("cost_results.csv", costs)
    csv_write("month_contributions.csv", months)
    return profiles, ranking, failures


def analyze_control(pre_runs):
    # Completed saved adaptive logs only; no market bars or backtest engine is invoked
    adaptive = [r for r in pre_runs if r["candidate"] == "ADAPTIVE"]
    for p in sorted((BASE / "results/runs/holdout").glob("*/ADAPTIVE__*.json.gz")):
        with gzip.open(p, "rt") as f:
            adaptive.append(json.load(f))
    base = [r for r in adaptive if r["scenario"] == "base"]
    transitions = []
    counts = []
    for r in base:
        lo, hi = map(ns, CFG["periods"][r["period"]])
        actual = [
            e
            for e in r["regime_transitions"]
            if lo <= e["timestamp"] < hi and e["old"] != e["new"]
        ]
        transitions.extend(
            {"period": r["period"], "symbol": r["symbol"], **e} for e in actual
        )
        counts.append(
            {
                "period": r["period"],
                "symbol": r["symbol"],
                "logged_records": len(r["regime_transitions"]),
                "actual_changes": len(actual),
            }
        )
    researched = [e for r in base for e in r["research"]]
    assessed = [e for e in researched if e["evidence"]]
    near = []
    for r in base:
        if r["period"] not in PRE:
            continue
        for e in r["research"]:
            ev = e["evidence"]
            if ev and sum(not b for b in ev["gates"].values()) == 1:
                near.append(
                    {
                        "period": r["period"],
                        "symbol": r["symbol"],
                        "timestamp": e["timestamp"],
                        "profile": e["proposal"]["candidate"],
                        "failed_gate": [k for k, v in ev["gates"].items() if not v],
                        "regime": e["diagnostics"]["regime"]["regime"],
                        "metrics": ev["metrics"],
                    }
                )
    control = {
        "actual_changes_one_market_path": len(transitions),
        "logged_records_one_cost": sum(len(r["regime_transitions"]) for r in base),
        "actual_changes_all_three_cost_repetitions": 3 * len(transitions),
        "by_symbol_period": counts,
        "recorded_promotions": dict(
            Counter(e["new_state"] for r in base for e in r["promotions"])
        ),
        "degradation_states_base": dict(
            Counter(e["state"] for r in base for e in r["degradation"])
        ),
        "actual_profile_switches": sum(len(r["switches"]) for r in base),
        "actual_trades": sum(len(r["trades"]) for r in base),
        "research_records_base": len(researched),
        "assessed_research_records_base": len(assessed),
        "gate_failure_count_distribution": dict(
            Counter(
                sum(not b for b in e["evidence"]["gates"].values()) for e in assessed
            )
        ),
        "proposed_profiles": sorted({e["proposal"]["candidate"] for e in researched}),
        "one_failed_gate_records": near,
    }
    csv_write("actual_regime_transitions.csv", transitions)
    # User-authorized diagnostic: no arbitrary FAIL waiver. This annotation was
    # established from developmental PF margins before the clarification; original
    # promotion code has only booleans, and no threshold is changed here.
    eligibility = []

    def assess(scope, profile, ev, timestamp, symbol="ALL"):
        statuses = {
            k: "PASS"
            if passed
            else "NEAR_MISS"
            if k == "profit_factor"
            and ev["metrics"]["profit_factor"] is not None
            and 1 < ev["metrics"]["profit_factor"] < 1.05
            else "FAIL"
            for k, passed in ev["gates"].items()
        }
        eligibility.append(
            {
                "scope": scope,
                "profile": profile,
                "symbol": symbol,
                "timestamp": timestamp,
                "near_miss_gates": [k for k, v in statuses.items() if v == "NEAR_MISS"],
                "true_fail_gates": [k for k, v in statuses.items() if v == "FAIL"],
                "gate_statuses": statuses,
                "eligible": all(v != "FAIL" for v in statuses.values()),
                "profit_factor": ev["metrics"]["profit_factor"],
            }
        )

    for p, ev in EVIDENCE.items():
        assess("FINAL_PREHOLDOUT_FREEZE", p, ev, ev["end_ns"])
    for r in base:
        if r["period"] not in PRE:
            continue
        for e in r["research"]:
            if e["evidence"]:
                assess(
                    "RECORDED_PREHOLDOUT_REQUEST",
                    e["proposal"]["candidate"],
                    e["evidence"],
                    e["timestamp"],
                    r["symbol"],
                )
    qualified = [e for e in eligibility if e["eligible"]]
    assert not qualified, "Do not infer switch/performance effects without evidence"
    control["near_miss_only_diagnostic"] = {
        "rule": "Accept PASS or pre-established autopsy PF-margin NEAR_MISS only; every true FAIL blocks",
        "annotation_provenance": "Original frozen promotion gates are binary. Autopsy NEAR_MISS means failed PF floor with 1 < PF < 1.05, established using preholdout data only before clarification.",
        "eligible_profiles_at_final_freeze": [],
        "eligible_profiles_at_recorded_preholdout_requests": [],
        "additional_hypothetical_switches": 0,
        "incremental_subsequent_net_pnl": 0,
        "performance_effect": "UNCHANGED: no newly eligible profiles, so no additional positions or switches",
        "final_freeze_near_misses": [
            {
                "profile": e["profile"],
                "gates": e["near_miss_gates"],
                "profit_factor": e["profit_factor"],
            }
            for e in eligibility
            if e["scope"] == "FINAL_PREHOLDOUT_FREEZE" and e["near_miss_gates"]
        ],
        "records_checked": len(eligibility),
        "holdout_used_for_eligibility": False,
        "thresholds_changed": False,
        "arbitrary_fail_waivers": 0,
    }
    csv_write("near_miss_eligibility.csv", eligibility)
    return control


def sealed_render():
    # Firewall: called after preholdout diagnosis/ranking have already been written
    saved = json.loads((BASE / "results/all_static_results.json").read_text())
    rows = []
    for p in PROFILES:
        for scenario in CFG["scenarios"]:
            m = saved[p].get("holdout/" + scenario)
            rows.append(
                {
                    "profile": p,
                    "scenario": scenario,
                    "coverage": "COMPLETED_FINAL_EVALUATION"
                    if m is not None
                    else "NOT_TESTED",
                    **(
                        {
                            k: v
                            for k, v in m.items()
                            if k not in ("daily_equity", "monthly_net_pnl")
                        }
                        if m is not None
                        else {}
                    ),
                }
            )
    csv_write("sealed_completed_evaluation_only.csv", rows)
    return rows


def fmt(x, n=2):
    if x is None:
        return "N/A"
    if isinstance(x, str):
        return x
    return f"{x:,.{n}f}"


def table(headers, rows):
    return "\n".join(
        [
            "| " + " | ".join(headers) + " |",
            "| " + " | ".join("---" for _ in headers) + " |",
            *[
                "| " + " | ".join(str(v).replace("|", "/") for v in row) + " |"
                for row in rows
            ],
        ]
    )


def metric_table(items):
    return table(
        [
            "Scope",
            "N",
            "Net",
            "PF",
            "Sharpe",
            "Sortino",
            "E/trade",
            "DD %",
            "Win %",
            "Fees",
            "Slip",
            "Funding",
            "Long net",
            "Short net",
        ],
        [
            [
                name,
                m["number_of_trades"],
                fmt(m["net_pnl"]),
                fmt(m["profit_factor"], 3),
                fmt(m.get("sharpe"), 3),
                fmt(m.get("sortino"), 3),
                fmt(m["expectancy"], 3),
                fmt(100 * m["maximum_drawdown"]),
                fmt(None if m["win_rate"] is None else 100 * m["win_rate"]),
                fmt(m["fees"]),
                fmt(m["slippage"]),
                fmt(m["funding"]),
                fmt(m.get("long_net")),
                fmt(m.get("short_net")),
            ]
            for name, m in items
        ],
    )


def report(profiles, ranking, failures, control, sealed):
    lines = [
        "# Strict failure autopsy — Adaptive Trading v1",
        "Read-only audit of commit 8219e2f8747d77ece56398f8f150bd475dbe8b0a. No optimization, strategy creation, threshold edits, trading simulation, market-data downloads, or new sealed strategy tests. The frozen evidence and source remain unchanged.",
        "## Evidence boundaries and metric definitions",
        "The 14-profile selection diagnosis uses preholdout evidence exclusively. The already-completed July–September 2026 final evaluation is a detached reporting appendix. Eight neighbor profiles have no sealed or cost-stress runs: N/A means NOT TESTED, not zero return or measured failure.",
        "Outer periods: research 2024; validation Jan–Jun 2025; WF1 Jul–Dec 2025; WF2 Jan–Jun 2026. Native marked daily equity supplies their Sharpe, Sortino and drawdown. Internal promotion gates use a different 40/20/10/10/20 split with a seven-day embargo and entry/exit purge. Internal Sharpe/Sortino below are supplementary daily realized attribution, not original gate statistics or native marked subgroup equity.",
        "Actual frozen promotion intervals: "
        + json.dumps(next(iter(profiles.values()))["bounds_utc"]),
        "The concentration gate uses the ten largest POSITIVE net trades / sum of all positive net trade profits and separately requires positive net after removing those winners. Month/symbol concentrations are descriptive; they were not additional promotion gates. Sharpe/Sortino/expectancy/win rate have no standalone admission threshold. PF has an explicit 1.05 floor.",
        "NEAR_MISS is an annotation only for a failed PF margin with PF > 1 and < 1.05; the original frozen decision is still FAIL. There is no invented economic tolerance around negative PnL, no missing test treated as near success, and no live threshold is changed.",
        "## Gate failure census",
        table(
            ["Gate", "Failed /14"],
            [[k, v] for k, v in sorted(failures.items(), key=lambda x: (-x[1], x[0]))],
        ),
        "Cost failures split into eight absent stress experiments and five measured nonpositive 2x outcomes; only TB48_SHORT passed the frozen stress gate. Seven profiles were never proposed by the reference research agent, despite being scored in the final 14-profile diagnostic snapshot.",
        "## Closest at the final preholdout freeze",
        table(
            [
                "Profile",
                "Failed gates",
                "Gate N",
                "Gate net",
                "Gate PF",
                "Measured 2x?",
            ],
            [
                [
                    p,
                    profiles[p]["failed_gate_count"],
                    profiles[p]["actual_gate"]["number_of_trades"],
                    fmt(profiles[p]["actual_gate"]["net_pnl"]),
                    fmt(profiles[p]["actual_gate"]["profit_factor"], 3),
                    profiles[p]["assessed_costs"],
                ]
                for p in ranking
            ],
        ),
        "This is a descriptive count of original failures, not a new optimizer or economic ranking. At the freeze even the closest profile needed four joint failures resolved. Historically TB48 and TB48_FUNDING reached 11/12 passed gates at the same 19 February 2026 request; concentration alone failed then. Both were in incompatible RANGE_LOW_VOL at that moment. No promotion occurred.",
        "## Controller exercise and transition count",
        json.dumps(
            {
                k: v
                for k, v in control.items()
                if k not in ("one_failed_gate_records", "by_symbol_period")
            },
            indent=2,
        ),
        table(
            ["Period", "Symbol", "Recorded", "Actual changes"],
            [
                [r["period"], r["symbol"], r["logged_records"], r["actual_changes"]]
                for r in control["by_symbol_period"]
            ],
        ),
        "The 131,648 figure in the original report summed regime logs from static/reference/adaptive runs and cost repetitions. The independent adaptive market path contains 4,186 changes across three symbols, including 300 in the completed holdout. 4,189 recorded rows include three UNKNOWN→UNKNOWN initialization records. Three cost repetitions are not three independent market histories.",
        "## Hypothetical relaxation: bounded interpretation only",
        json.dumps(control["near_miss_only_diagnostic"], indent=2),
        "Only existing PF-buffer NEAR_MISS annotations may be accepted. Every true FAIL blocks eligibility. The original frozen gates are binary and contain no NEAR_MISS state; the descriptive PF annotation was defined in this autopsy from preholdout evidence before the user clarification, not in the original trading protocol. No eligible profile means zero additional switches and zero incremental subsequent performance. No holdout performance is used for this decision.",
        "## Per-profile dossiers",
    ]
    for p in ranking:
        d = profiles[p]
        definition = d["definition"]
        m = d["actual_gate"]
        active = {
            k: definition[k]
            for k in (
                "minutes",
                "lookback",
                "stop_atr",
                "band_k",
                "pullback_atr",
                "compression",
                "allow_long",
                "allow_short",
                "funding_filter",
            )
        }
        lines += [
            f"### {p}",
            f"Family: {definition['family']}. Symbols: BTCUSDT, ETHUSDT, SOLUSDT. Signal timeframe: {definition['minutes']}m; execution grid: 15m; causal context: 5m/15m/1h/4h. Parameters: `{json.dumps(active, sort_keys=True)}`. Compatible regimes: {definition['compatible_regimes']}.",
            f"Total preholdout trades: {d['all_pre']['number_of_trades']}; purged qualifying gate trades: {m['number_of_trades']}. These are different universes; neither includes the July–September sealed evaluation.",
            "Outer chronological metrics — native marked risk statistics:",
            metric_table(d["outer"].items()),
            "Actual internal promotion splits — realized daily attribution for Sharpe/Sortino/DD; exact original drawdown gate separately below:",
            metric_table(d["internal"].items()),
            "Exact frozen gates:",
            table(
                ["Gate", "Status (original)", "Threshold", "Observed", "Comment"],
                [
                    [
                        r["gate"],
                        r["status"] + " (" + r["frozen_result"] + ")",
                        json.dumps(r["threshold"]),
                        json.dumps(r["observed"]),
                        r["reason"],
                    ]
                    for r in d["gates"]
                ],
            ),
            "Concentration and decomposition in the actual purged gate universe:",
            table(
                ["Diagnostic", "Observed"],
                [
                    ["Winning trades", m["winning_trades"]],
                    ["Top-10 positive net profits", fmt(m["top10_profit"])],
                    [
                        "Top-10 / all positive trade profits",
                        fmt(
                            None
                            if m["top10_positive_profit_share"] is None
                            else 100 * m["top10_positive_profit_share"]
                        )
                        + "%",
                    ],
                    ["Net excluding top 10", fmt(m["net_excluding_top10"])],
                    [
                        "Best realized-exit month",
                        f"{m['best_month']}: {fmt(m['best_month_net'])}",
                    ],
                    [
                        "Best month / positive monthly net",
                        fmt(
                            None
                            if m["best_month_positive_month_profit_share"] is None
                            else 100 * m["best_month_positive_month_profit_share"]
                        )
                        + "%",
                    ],
                    ["Net excluding best month", fmt(m["net_excluding_best_month"])],
                    ["Best symbol", f"{m['best_symbol']}: {fmt(m['best_symbol_net'])}"],
                    [
                        "Best symbol / positive symbol net",
                        fmt(
                            None
                            if m["best_symbol_positive_symbol_profit_share"] is None
                            else 100 * m["best_symbol_positive_symbol_profit_share"]
                        )
                        + "%",
                    ],
                    ["Net excluding best symbol", fmt(m["net_excluding_best_symbol"])],
                    [
                        "Long / short net",
                        f"{fmt(m['long_net'])} / {fmt(m['short_net'])}",
                    ],
                    [
                        "Original unsorted closed DD / chronological closed DD / full-history marked DD",
                        f"{100 * d['actual_frozen_gate_metrics']['maximum_drawdown']:.4f}% / {100 * m['chronological_closed_drawdown']:.4f}% / {100 * d['actual_frozen_gate_metrics'].get('marked_maximum_drawdown', 0):.4f}%",
                    ],
                ],
            ),
            "Cost outcomes (N / net), without synthesizing absent stress tests:",
            table(
                ["Cost", "All preholdout", "Actual purged gate universe"],
                [
                    [
                        s,
                        f"{v['all_pre']['number_of_trades']} / {fmt(v['all_pre']['net_pnl'])}"
                        if v
                        else "NOT TESTED",
                        f"{v['actual_gate']['number_of_trades']} / {fmt(v['actual_gate']['net_pnl'])}"
                        if v
                        else "NOT TESTED",
                    ]
                    for s, v in d["costs"].items()
                ],
            ),
            "Neighbor gate evidence:",
            table(
                [
                    "Neighbor",
                    "Gate-interval net",
                    "Positive?",
                    "Self?",
                    "Same sides?",
                    "Same funding filter?",
                ],
                [
                    [
                        n,
                        fmt(v["gate_interval_net"]),
                        v["positive"],
                        v["is_self"],
                        v["side_permissions_match"],
                        v["funding_filter_matches"],
                    ]
                    for n, v in d["neighbors"].items()
                ],
            ),
            "Preholdout regime decomposition (realized attribution):",
            metric_table(d["groups"]["regime"].items()),
        ]
    lines += [
        "## Detached sealed evaluation — completed results only; no selection or diagnosis uses this section",
        table(
            [
                "Profile",
                "Cost",
                "Coverage",
                "N",
                "Net",
                "PF",
                "Sharpe",
                "Sortino",
                "Expectancy",
                "DD %",
                "Win %",
                "Fees",
                "Slip",
                "Funding",
            ],
            [
                [
                    r["profile"],
                    r["scenario"],
                    r["coverage"],
                    r.get("number_of_trades", "N/A"),
                    fmt(r.get("net_pnl")),
                    fmt(r.get("profit_factor"), 3),
                    fmt(r.get("sharpe"), 3),
                    fmt(r.get("sortino"), 3),
                    fmt(r.get("expectancy"), 3),
                    fmt(
                        None
                        if r.get("maximum_drawdown") is None
                        else 100 * r["maximum_drawdown"]
                    ),
                    fmt(None if r.get("win_rate") is None else 100 * r["win_rate"]),
                    fmt(r.get("fees")),
                    fmt(r.get("slippage")),
                    fmt(r.get("funding")),
                ]
                for r in sealed
            ],
        ),
        "No held-out profile or parameter is selected, replaced, ranked, or optimized. Neighbor holdouts are absent, not extrapolated from central profiles.",
        "## Files and audit trail",
        "preholdout_profiles.json contains full metrics, side/symbol/regime decompositions and concentration details for all 14 profiles. gate_decisions.csv preserves both display status and exact frozen status, thresholds and observations. profile_period_metrics.csv, profile_groups.csv, cost_results.csv and month_contributions.csv contain the complete tables. actual_regime_transitions.csv preserves counts; near_miss_eligibility.csv preserves the authorized diagnostic. See conclusions.md for the twelve questions and final failure classification. input_checksums.json binds original inputs; autopsy_checksums.json binds new outputs.",
    ]
    (OUT / "REPORT.md").write_text("\n\n".join(lines) + "\n")


def main():
    original = subprocess.check_output(
        ["git", "ls-files", "-z", "evaluation/adaptive_trading_v1"], cwd=BASE.parents[1]
    ).split(b"\0")
    inputs = {
        p.decode(): sha(BASE.parents[1] / p.decode())
        for p in original
        if p and "/autopsy/" not in p.decode()
    }
    pre = read_pre()
    profiles, ranking, failures = analyze_pre(pre)
    control = analyze_control(pre)
    dump("control_audit.json", control)
    sealed = sealed_render()
    report(profiles, ranking, failures, control, sealed)
    from explain import explain

    explain(BASE, OUT, profiles, ranking, failures, control, pre, fmt, table, dump)
    for p, expected in inputs.items():
        assert sha(BASE.parents[1] / p) == expected, p
    dump("input_checksums.json", inputs)
    dump(
        "audit_integrity.json",
        {
            "original_tracked_files_checked": len(inputs),
            "original_files_unchanged": True,
            "new_optimization_runs": 0,
            "new_backtests": 0,
            "strategy_or_threshold_changes": 0,
            "profile_count": len(profiles),
            "gate_rows": sum(len(d["gates"]) for d in profiles.values()),
            "sealed_use": "Already-produced final metric aggregates rendered separately, never supplied to preholdout ranking",
            "input_commit": subprocess.check_output(
                ["git", "rev-parse", "HEAD"], cwd=BASE.parents[1], text=True
            ).strip(),
        },
    )
    dump(
        "autopsy_checksums.json",
        {
            str(p.relative_to(OUT)): sha(p)
            for p in sorted(OUT.rglob("*"))
            if p.is_file()
            and p.name != "autopsy_checksums.json"
            and "__pycache__" not in p.parts
        },
    )
    print("AUTOPSY", len(profiles), "profiles", dict(failures))
    print(
        "CONTROL",
        control["actual_changes_one_market_path"],
        control["near_miss_only_diagnostic"],
    )


if __name__ == "__main__":
    main()

"""Generate all report tables from retained native runs; no strategy selection by future PnL."""

import csv
import gzip
import json
from collections import Counter
from decimal import Decimal
from itertools import pairwise

import numpy as np
import pandas as pd

from .common import HOUR, ROOT, config, ns, write_json
from .metrics import portfolio_daily, summarize, trade_metrics
from .profiles import BASE, POLICIES, library
from .research import DiagnosticAgent, save_proposals
from .workflow import execution_hash, read_run

START, EVALUATION, END = ns("2024-01-01"), ns("2025-01-01"), ns("2026-10-01")


def write_csv(name, rows):
    path = ROOT / "results" / name
    path.parent.mkdir(parents=True, exist_ok=True)
    columns = list(dict.fromkeys(k for row in rows for k in row))
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, columns)
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    k: json.dumps(v, sort_keys=True)
                    if isinstance(v, (dict, list, tuple))
                    else v
                    for k, v in row.items()
                }
            )


def write_jsonl(name, rows):
    (ROOT / "results" / name).write_text(
        "".join(json.dumps(r, sort_keys=True, allow_nan=False) + "\n" for r in rows)
    )


def bundle(profile, policy="ENTRY_ONLY", scenario="base"):
    return [read_run(profile, policy, scenario, s) for s in config()["symbols"]]


def period_metrics(runs, begin, end):
    m = summarize(runs, begin, end)
    daily = portfolio_daily(runs, begin, end)
    marked = daily[-1][1] - daily[0][1] if daily else 0
    trades = sorted(
        [t for r in runs for t in r["trades"] if begin <= t["exit_ns"] < end],
        key=lambda t: (t["exit_ns"], t["symbol"]),
    )
    attribution = trade_metrics(trades)
    m.update(
        {
            k: v
            for k, v in attribution.items()
            if k not in ("net_pnl", "fees", "funding", "slippage", "turnover_notional")
        }
    )
    m["closed_trade_attribution_net"] = attribution["net_pnl"]
    m["net_pnl"] = marked
    fills = [f for r in runs for f in r["fills"] if begin <= f["ts_ns"] < end]
    for key, fill_key in (("fees", "fee"), ("slippage", "slippage")):
        m[key] = float(sum((Decimal(f[fill_key]) for f in fills), Decimal(0)))
    m["funding"] = float(
        sum(
            (
                Decimal(e["amount"])
                for r in runs
                for e in r.get("funding_events", [])
                if begin <= e["timestamp"] < end
            ),
            Decimal(0),
        )
    )
    m["turnover_notional"] = float(
        sum((Decimal(f["quantity"]) * Decimal(f["price"]) for f in fills), Decimal(0))
    )
    capital = config()["capital_per_symbol"] * len(runs)
    m["turnover"] = m["turnover_notional"] / capital
    m["return_on_allocated_capital"] = marked / capital
    m["gross_pnl_including_mark_change"] = (
        marked + m["fees"] + m["slippage"] - m["funding"]
    )
    m["return_per_unit_exposure"] = (
        m["return_on_allocated_capital"] / m["average_exposure"]
        if m["average_exposure"]
        else None
    )
    m["regime_switches"] = None
    return m


def static_selection():
    scores = {p.id: period_metrics(bundle(p.id), START, EVALUATION) for p in BASE}
    winner = max(
        scores,
        key=lambda p: (
            scores[p]["sharpe"] if scores[p]["sharpe"] is not None else -1e30,
            scores[p]["net_pnl"],
            p,
        ),
    )
    value = {
        "profile": winner,
        "policy": "ENTRY_ONLY",
        "selection_window": [START, EVALUATION],
        "selection_information": "2024 data only; not a new independent validation",
        "scores": scores,
    }
    path = ROOT / "results/static_selection.json"
    if path.exists() and json.loads(path.read_text()) != value:
        raise RuntimeError("Frozen static comparator would change")
    write_json(path, value)
    return value


def static_selection_full_grid():
    scores = {
        f"{p.id}|{policy}": period_metrics(bundle(p.id, policy), START, EVALUATION)
        for p in BASE
        for policy in POLICIES
    }
    winner = max(
        scores,
        key=lambda key: (
            scores[key]["sharpe"] if scores[key]["sharpe"] is not None else -1e30,
            scores[key]["net_pnl"],
            key,
        ),
    )
    profile, policy = winner.split("|")
    value = {
        "profile": profile,
        "policy": policy,
        "selection_window": [START, EVALUATION],
        "selection_information": "2024 data only; all 24 predeclared profile/exit treatments; supplementary comparator",
        "scores": scores,
    }
    path = ROOT / "results/static_full_grid_selection.json"
    if path.exists() and json.loads(path.read_text()) != value:
        raise RuntimeError("Full-grid 2024-only comparator would change")
    write_json(path, value)
    return value


def regime_diagnostics():
    stats, logs = [], []
    for symbol in config()["symbols"]:
        frame = pd.read_parquet(ROOT / "data/cache" / f"{symbol}_features.parquet")
        frame = frame[(frame.available_ns >= START) & (frame.available_ns < END)]
        counts = {}
        for label, column, confidence in (
            ("stable", "regime", "transition_confidence"),
            ("raw_v1", "raw_regime", "raw_confidence"),
        ):
            changes = frame[column] != frame[column].shift()
            groups = changes.cumsum()
            durations = frame.groupby(groups).size().to_numpy() * 0.25
            counts[label] = {
                "transitions": int(changes.sum() - 1),
                "short_lived_under_8h": int((durations[1:-1] < 8).sum()),
                "average_duration_hours": float(durations.mean()),
                "median_duration_hours": float(np.median(durations)),
            }
            old = None
            previous_timestamp = int(frame.available_ns.iloc[0])
            for f in frame[changes].to_dict("records"):
                if old is not None:
                    logs.append(
                        {
                            "timestamp": int(f["available_ns"]),
                            "symbol": symbol,
                            "path": label,
                            "old_regime": old,
                            "new_regime": f[column],
                            "confidence": f[confidence],
                            "persistence_hours": f["persistence_hours"],
                            "dwell_ns": f["dwell_ns"],
                            "previous_observed_duration_ns": int(f["available_ns"])
                            - previous_timestamp,
                        }
                    )
                old = f[column]
                previous_timestamp = int(f["available_ns"])
        stats.append({"symbol": symbol, **counts})
    write_json(ROOT / "results/regime_statistics.json", stats)
    write_csv(
        "regime_switches.csv",
        sorted(logs, key=lambda r: (r["timestamp"], r["symbol"], r["path"])),
    )
    return stats


def exit_diagnostics():
    rows, excursions = [], []
    for p in BASE:
        entry = {
            scenario: period_metrics(bundle(p.id, scenario=scenario), EVALUATION, END)
            for scenario in config()["scenarios"]
        }
        for policy in POLICIES:
            for scenario in config()["scenarios"]:
                runs = bundle(p.id, policy, scenario)
                m = period_metrics(runs, EVALUATION, END)
                forced = [
                    t
                    for r in runs
                    for t in r["trades"]
                    if EVALUATION <= t["exit_ns"] < END
                    and "REGIME_INVALIDATED" in t["exit_reasons"]
                ]
                rows.append(
                    {
                        "profile": p.id,
                        "side": p.side,
                        "policy": policy,
                        "scenario": scenario,
                        **m,
                        "interrupted_trades": len(forced),
                        "regime_only_exits": sum(
                            t["exit_reasons"] == ["REGIME_INVALIDATED"] for t in forced
                        ),
                        "pnl_delta_vs_entry_only": m["net_pnl"]
                        - entry[scenario]["net_pnl"],
                    }
                )
                if scenario == "base":
                    for r in runs:
                        frame = pd.read_parquet(
                            ROOT / "data/cache" / f"{r['symbol']}_features.parquet"
                        )
                        times, closes = (
                            frame.available_ns.to_numpy(),
                            frame.close.to_numpy(),
                        )
                        for t in r["trades"]:
                            if "REGIME_INVALIDATED" not in t["exit_reasons"]:
                                continue
                            row = {
                                "profile": p.id,
                                "policy": policy,
                                "symbol": r["symbol"],
                                "exit_ns": t["exit_ns"],
                                "exit_reasons": t["exit_reasons"],
                                "scope": "DESCRIPTIVE_MARK_EXCURSION_NOT_EXECUTABLE_PNL",
                                "period": "training_2024"
                                if t["exit_ns"] < EVALUATION
                                else "evaluation_2025_to_2026_09",
                            }
                            for h in (4, 24, 96):
                                target = t["exit_ns"] + h * HOUR
                                index = np.searchsorted(times, target, side="right") - 1
                                row[f"signed_mark_pnl_after_{h}h"] = (
                                    t["side"]
                                    * t["quantity"]
                                    * (float(closes[index]) - float(t["exit_price"]))
                                    if target <= times[-1] and index >= 0
                                    else None
                                )
                            excursions.append(row)
    write_csv("exit_policy_results.csv", rows)
    write_csv("post_exit_excursions.csv", excursions)
    return rows, excursions


def generate():
    fingerprint = execution_hash()
    for path in (ROOT / "results/runs").glob("*.json.gz"):
        result = json.loads(gzip.decompress(path.read_bytes()))
        if result["execution_hash"] != fingerprint:
            raise RuntimeError(f"Stale native result: {path.name}")
    selection = static_selection()
    chosen = selection["profile"]
    full_selection = static_selection_full_grid()
    hindsight_scores = {
        p.id: period_metrics(bundle(p.id), EVALUATION, END) for p in BASE
    }
    hindsight_profile = max(
        hindsight_scores,
        key=lambda p: (
            hindsight_scores[p]["sharpe"]
            if hindsight_scores[p]["sharpe"] is not None
            else -1e30,
            hindsight_scores[p]["net_pnl"],
            p,
        ),
    )
    systems = {
        "static_2024_selected": chosen,
        "static_best_hindsight_diagnostic": hindsight_profile,
        "adaptive": "ADAPTIVE",
        "no_trade": "NO_TRADE",
        "risk_normalized_passive": "PASSIVE",
    }
    full_grid_scores = {
        f"{p.id}|{policy}": period_metrics(bundle(p.id, policy), EVALUATION, END)
        for p in BASE
        for policy in POLICIES
    }
    full_grid_best = max(
        full_grid_scores,
        key=lambda key: (
            full_grid_scores[key]["sharpe"]
            if full_grid_scores[key]["sharpe"] is not None
            else -1e30,
            full_grid_scores[key]["net_pnl"],
            key,
        ),
    )
    best_grid_profile, best_grid_policy = full_grid_best.split("|")
    systems["static_full_grid_2024_selected"] = full_selection["profile"]
    systems["static_full_grid_best_hindsight_diagnostic"] = best_grid_profile
    system_policies = {
        "static_full_grid_2024_selected": full_selection["policy"],
        "static_full_grid_best_hindsight_diagnostic": best_grid_policy,
    }
    stats = regime_diagnostics()
    regime_count = sum(s["stable"]["transitions"] for s in stats)
    rows = []
    for name, profile in systems.items():
        for scenario in config()["scenarios"]:
            for label, begin, end in (
                ("training_2024", START, EVALUATION),
                ("evaluation_2025_to_2026_09", EVALUATION, END),
                ("all_consumed_history", START, END),
            ):
                m = period_metrics(
                    bundle(profile, system_policies.get(name, "ENTRY_ONLY"), scenario),
                    begin,
                    end,
                )
                m["regime_switches"] = (
                    regime_count
                    if label == "all_consumed_history"
                    else sum(
                        begin <= r["timestamp"] < end
                        for r in read_regime_logs()
                        if r["path"] == "stable"
                    )
                )
                rows.append(
                    {
                        "system": name,
                        "profile": profile,
                        "exit_policy": system_policies.get(name, "ENTRY_ONLY"),
                        "scenario": scenario,
                        "period": label,
                        **m,
                    }
                )
    write_csv("system_comparisons.csv", rows)
    write_json(ROOT / "results/system_comparisons.json", rows)
    monthly = []
    boundaries = [
        ns(t) for t in pd.date_range("2025-01-01", "2026-10-01", freq="MS", tz="UTC")
    ]
    for name, profile in systems.items():
        for scenario in config()["scenarios"]:
            runs = bundle(profile, system_policies.get(name, "ENTRY_ONLY"), scenario)
            for a, b in pairwise(boundaries):
                monthly.append(
                    {
                        "system": name,
                        "scenario": scenario,
                        "month": pd.Timestamp(a, unit="ns", tz="UTC").strftime("%Y-%m"),
                        **period_metrics(runs, a, b),
                    }
                )
    write_csv("walk_forward_monthly.csv", monthly)
    profile_rows = []
    decomposition = []
    all_trades = []
    for p in library().values():
        if p.id == "NO_TRADE":
            continue
        for scenario in config()["scenarios"]:
            runs = bundle(p.id, scenario=scenario)
            for label, begin in (
                ("training_2024", START),
                ("evaluation_2025_to_2026_09", EVALUATION),
            ):
                end = EVALUATION if label == "training_2024" else END
                profile_rows.append(
                    {
                        "profile": p.id,
                        "family": p.family,
                        "side": p.side,
                        "scenario": scenario,
                        "period": label,
                        **period_metrics(runs, begin, end),
                    }
                )
            for r in runs:
                if scenario == "base" and p.id in {x.id for x in BASE}:
                    decomposition.append(
                        {
                            "profile": p.id,
                            "axis": "symbol",
                            "group": r["symbol"],
                            **period_metrics([r], EVALUATION, END),
                        }
                    )
                for trade in r["trades"]:
                    all_trades.append(
                        {
                            "candidate": p.id,
                            "policy": "ENTRY_ONLY",
                            "scenario": scenario,
                            **trade,
                        }
                    )
    write_csv("profile_results.csv", profile_rows)
    write_csv("per_symbol_results.csv", decomposition)
    directions = []
    for name, p in systems.items():
        trades = [
            t
            for r in bundle(p, system_policies.get(name, "ENTRY_ONLY"))
            for t in r["trades"]
            if EVALUATION <= t["exit_ns"] < END
        ]
        for axis in ("side", "regime", "profile"):
            for value in sorted({str(t[axis]) for t in trades}):
                directions.append(
                    {
                        "system": name,
                        "axis": axis,
                        "group": value,
                        "metric_scope": "REALIZED_CLOSED_TRADE_ATTRIBUTION",
                        **trade_metrics([t for t in trades if str(t[axis]) == value]),
                    }
                )
    write_csv("long_short_regime_decomposition.csv", directions)
    for profile in [p.id for p in BASE] + ["ADAPTIVE", "PASSIVE", "NO_TRADE"]:
        policies_for_ledger = (
            POLICIES[1:] if profile in {p.id for p in BASE} else ("ENTRY_ONLY",)
        )
        for policy in policies_for_ledger:
            for scenario in config()["scenarios"]:
                for run in bundle(profile, policy, scenario):
                    all_trades.extend(
                        {
                            "candidate": profile,
                            "policy": policy,
                            "scenario": scenario,
                            **t,
                        }
                        for t in run["trades"]
                    )
    write_csv("trades.csv", all_trades)
    system_symbols = [
        {
            "system": name,
            "symbol": run["symbol"],
            "scenario": scenario,
            **period_metrics([run], EVALUATION, END),
        }
        for name, profile in systems.items()
        for scenario in config()["scenarios"]
        for run in bundle(profile, system_policies.get(name, "ENTRY_ONLY"), scenario)
    ]
    write_csv("system_per_symbol.csv", system_symbols)
    policy_rows, _excursions = exit_diagnostics()
    evidence = json.loads((ROOT / "results/eligibility.json").read_text())
    write_csv(
        "validation_gates.csv",
        [
            {
                "profile": e["profile"],
                "timestamp": e["timestamp"],
                "begin_ns": e["begin_ns"],
                "end_ns": e["end_ns"],
                "eligible": e["eligible"],
                **e["gates"],
            }
            for e in evidence
        ],
    )
    write_json(
        ROOT / "results/profiles.json",
        {p: d.definition() for p, d in library().items()},
    )
    for key, output in (
        ("switches", "profile_switches.jsonl"),
        ("decisions", "profile_decisions.jsonl"),
        ("degradation", "edge_decay.jsonl"),
        ("research", "research_triggers.jsonl"),
    ):
        records = [
            {"scenario": s, **r}
            for s in config()["scenarios"]
            for run in bundle("ADAPTIVE", scenario=s)
            for r in run[key]
        ]
        write_jsonl(
            output,
            sorted(records, key=lambda r: (r["timestamp"], r["symbol"], r["scenario"])),
        )
    save_proposals(
        DiagnosticAgent(),
        {
            "references": [
                "results/exit_policy_results.csv",
                "results/validation_gates.csv",
            ],
            "scope": "RETROSPECTIVE_EVIDENCE_ONLY",
            "exit_policy_evidence": [
                {
                    k: r[k]
                    for k in (
                        "profile",
                        "policy",
                        "net_pnl",
                        "trades",
                        "sharpe",
                        "pnl_delta_vs_entry_only",
                    )
                }
                for r in policy_rows
                if r["scenario"] == "base"
            ],
            "gate_failures": dict(
                Counter(k for e in evidence for k, v in e["gates"].items() if not v)
            ),
        },
        ROOT / "results/research_proposals.json",
    )
    finals = [e for e in evidence if e["timestamp"] == END]
    sample_summary = {
        p.id: {
            "maximum_matured_window_trades": max(
                e["metrics"]["trades"] for e in evidence if e["profile"] == p.id
            ),
            "windows_passing_sample": sum(
                e["gates"]["sample"] for e in evidence if e["profile"] == p.id
            ),
            "minimum_required": config()["validation"]["minimum_trades"],
        }
        for p in BASE
    }
    write_json(ROOT / "results/sample_adequacy.json", sample_summary)
    eligible = [e["profile"] for e in finals if e["eligible"]]
    evaluation = {
        r["system"]: r
        for r in rows
        if r["scenario"] == "base" and r["period"] == "evaluation_2025_to_2026_09"
    }
    adaptive, static = evaluation["adaptive"], evaluation["static_2024_selected"]
    exercised = adaptive["trades"] > 0
    beats = (
        exercised
        and adaptive["sharpe"] is not None
        and static["sharpe"] is not None
        and adaptive["sharpe"] > static["sharpe"]
        and adaptive["return_drawdown"] is not None
        and static["return_drawdown"] is not None
        and adaptive["return_drawdown"] > static["return_drawdown"]
    )
    positive_months = sum(
        r["net_pnl"] > 0
        for r in monthly
        if r["system"] == "adaptive" and r["scenario"] == "base"
    )
    stressed_positive = all(
        r["net_pnl"] > 0
        for r in rows
        if r["system"] == "adaptive" and r["period"] == "evaluation_2025_to_2026_09"
    )
    classification = "V2_RETROSPECTIVE_NO_EDGE"
    if adaptive["net_pnl"] > 0 and any(e["eligible"] for e in evidence):
        classification = "V2_RETROSPECTIVE_WEAK_EDGE"
        if (
            adaptive["trades"] >= 60
            and beats
            and stressed_positive
            and positive_months > 10.5
            and adaptive["maximum_drawdown"] <= 0.15
            and sum(x > 0 for x in adaptive["symbols"].values()) >= 2
        ):
            classification = "V2_RETROSPECTIVE_EDGE_CANDIDATE"
    score = {p.id: period_metrics(bundle(p.id), EVALUATION, END) for p in BASE}
    hindsight = max(
        score,
        key=lambda p: (
            score[p]["sharpe"] if score[p]["sharpe"] is not None else -1e30,
            score[p]["net_pnl"],
            p,
        ),
    )
    conclusions = {
        "classification": classification,
        "evidence_class": "RETROSPECTIVE_EVIDENCE",
        "static_selected_from_2024": chosen,
        "static_full_grid_2024_choice": {
            "profile": full_selection["profile"],
            "policy": full_selection["policy"],
        },
        "best_static_all_exit_policies_hindsight": {
            "profile": best_grid_profile,
            "policy": best_grid_policy,
            "metrics": full_grid_scores[full_grid_best],
        },
        "best_evaluation_static_hindsight_only": hindsight,
        "hindsight_static_metrics": score[hindsight],
        "adaptive_exercised": exercised,
        "maximum_rolling_sample": sample_summary,
        "all_primary_profiles_sample_blocked": all(
            r["windows_passing_sample"] == 0 for r in sample_summary.values()
        ),
        "policy_admission_scope": "Central ENTRY_ONLY profiles only; three alternative exit policies are diagnostic controls",
        "adaptive_beats_static_on_sharpe_and_return_drawdown": beats,
        "prospective_shadow_eligible_profiles": eligible,
        "any_historical_admissions": any(e["eligible"] for e in evidence),
        "stronger_retrospective_evidence": bool(eligible)
        and any(score[p]["net_pnl"] > 0 for p in eligible),
        "prospective_performance_observed": False,
        "persistent_shadow_justified": bool(eligible),
        "unproven": [
            "future profitability",
            "independent prospective edge",
            "adaptive benefit beyond reused history",
            "broader symbol transfer",
            "real spread/queue/impact and exact funding timing",
        ],
    }
    write_json(ROOT / "results/conclusions.json", conclusions)
    render(rows, profile_rows, policy_rows, evidence, stats, monthly, conclusions)
    return conclusions


def read_regime_logs():
    with (ROOT / "results/regime_switches.csv").open() as f:
        return [{**r, "timestamp": int(r["timestamp"])} for r in csv.DictReader(f)]


def table(rows, columns):
    def cell(value):
        if value is None:
            return "undefined"
        if isinstance(value, float):
            return f"{value:,.4f}"
        return str(value)

    return (
        "| "
        + " | ".join(columns)
        + " |\n|"
        + "|".join("---" for _ in columns)
        + "|\n"
        + "\n".join(
            "| " + " | ".join(cell(r.get(c)) for c in columns) + " |" for r in rows
        )
    )


def render(rows, profiles, policies, evidence, regimes, monthly, conclusions):
    headline = [
        r
        for r in rows
        if r["scenario"] == "base" and r["period"] == "evaluation_2025_to_2026_09"
    ]
    central = [
        r
        for r in profiles
        if r["profile"] in {p.id for p in BASE}
        and r["scenario"] == "base"
        and r["period"] == "evaluation_2025_to_2026_09"
    ]
    final = [e for e in evidence if e["timestamp"] == END]
    gate_rows = [
        {
            "profile": e["profile"],
            "trades": e["metrics"]["trades"],
            "net": e["metrics"]["net_pnl"],
            "PF": e["metrics"]["profit_factor"],
            "eligible": e["eligible"],
            "failures": ", ".join(k for k, v in e["gates"].items() if not v),
        }
        for e in final
    ]
    failed = Counter(k for e in evidence for k, v in e["gates"].items() if not v)
    admitted = Counter(e["profile"] for e in evidence if e["eligible"])
    regime_rows = [
        {
            "symbol": r["symbol"],
            "raw changes": r["raw_v1"]["transitions"],
            "stable changes": r["stable"]["transitions"],
            "short stable <8h": r["stable"]["short_lived_under_8h"],
            "mean stable h": r["stable"]["average_duration_hours"],
        }
        for r in regimes
    ]
    exit_rows = [
        {
            "profile": r["profile"],
            "policy": r["policy"],
            "trades": r["trades"],
            "net": r["net_pnl"],
            "delta vs ENTRY_ONLY": r["pnl_delta_vs_entry_only"],
            "interrupted": r["interrupted_trades"],
            "Sharpe": r["sharpe"],
        }
        for r in policies
        if r["scenario"] == "base"
    ]
    stress = [r for r in rows if r["period"] == "evaluation_2025_to_2026_09"]
    monthly_rows = [
        {
            "month": month,
            **{
                r["system"]: r["net_pnl"]
                for r in monthly
                if r["month"] == month and r["scenario"] == "base"
            },
        }
        for month in sorted({r["month"] for r in monthly})
    ]
    body = f"""# Nautilus Adaptive Trading System v2

Classification: **{conclusions["classification"]}**. All historical results below are
**RETROSPECTIVE_EVIDENCE** on consumed data. No new untouched historical holdout
exists, no ROBUST_EDGE is claimed, and real-money trading is disabled.

The fixed comparator selected from 2024 information is `{conclusions["static_selected_from_2024"]}`.
The supplementary comparator selected from all 24 predeclared treatments using
2024 only is `{conclusions["static_full_grid_2024_choice"]["profile"]}` with
`{conclusions["static_full_grid_2024_choice"]["policy"]}`. The primary selection
remains unchanged.

Adaptive historical execution exercised: **{conclusions["adaptive_exercised"]}**.
Adaptive beats that comparator on both Sharpe and return/drawdown:
**{conclusions["adaptive_beats_static_on_sharpe_and_return_drawdown"]}**.
Final prospective-shadow-eligible profiles: **{", ".join(conclusions["prospective_shadow_eligible_profiles"]) or "none"}**.

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

{table(regime_rows, ["symbol", "raw changes", "stable changes", "short stable <8h", "mean stable h"])}

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

{table(headline, ["system", "trades", "net_pnl", "return_on_allocated_capital", "sharpe", "sortino", "maximum_drawdown", "calmar"])}

{table(headline, ["system", "annual_volatility", "average_exposure", "time_in_market", "turnover", "return_per_unit_exposure", "return_drawdown", "time_no_trade"])}

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

{table(central, ["profile", "side", "trades", "net_pnl", "profit_factor", "sharpe", "maximum_drawdown", "average_exposure"])}

All profiles, neighbors, time windows and costs remain in results/profile_results.csv.
Per-symbol metrics are in per_symbol_results.csv; long/short, entry regime and
actual adaptive profile decomposition is in long_short_regime_decomposition.csv.
Regime/side attribution is realized-trade economics, not marked portfolio Sharpe.
The ex-post best evaluation static is `{conclusions["best_evaluation_static_hindsight_only"]}`;
it is the best primary ENTRY_ONLY diagnostic and never a controller input.
Across all 24 treatments, the best hindsight static is
`{conclusions["best_static_all_exit_policies_hindsight"]["profile"]}` with
`{conclusions["best_static_all_exit_policies_hindsight"]["policy"]}`. Its full
metrics are also reported as a separate hindsight diagnostic. All hindsight
choices are explicitly selection-contaminated.

## Entry regime versus exit regime experiment

ENTRY_ONLY is primary and is never replaced after scoring. PERSIST_4 waits for
four incompatible completed hourly observations. CONFIDENT_80 requires >=0.80
confidence and two-hour candidate persistence. V1_IMMEDIATE uses the raw label to
block entries and force next-open exits. It is an overlay control on V2 profiles,
not a claimed reproduction of the entire frozen V1 system.

{table(exit_rows, ["profile", "policy", "trades", "net", "delta vs ENTRY_ONLY", "interrupted", "Sharpe"])}

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

{table(gate_rows, ["profile", "trades", "net", "PF", "eligible", "failures"])}

All monthly gate failures: `{dict(failed)}`. Historical admissions by profile:
`{dict(admitted)}`. Gate counts are correlated diagnostics, not independent tests.
Primary-profile maximum matured rolling trade counts are:
`{ {p: r["maximum_matured_window_trades"] for p, r in conclusions["maximum_rolling_sample"].items()} }`.
All primary profiles blocked by sample requirements in every window:
**{conclusions["all_primary_profiles_sample_blocked"]}**. The primary admission
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

{table(stress, ["system", "scenario", "net_pnl", "fees", "funding", "slippage", "sharpe", "maximum_drawdown", "profile_switches"])}

Monthly marked PnL (USDT), with decisions based on preceding information only:

{table(monthly_rows, ["month", "static_2024_selected", "adaptive", "no_trade", "risk_normalized_passive"])}

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
   **{conclusions["stronger_retrospective_evidence"]}**. This is a descriptive V2
   comparison, not independent confirmation of the V1-derived hypotheses.
2. Adaptive beats the 2024-selected static on Sharpe and return/drawdown:
   **{conclusions["adaptive_beats_static_on_sharpe_and_return_drawdown"]}**.
   Historical controller execution exercised: **{conclusions["adaptive_exercised"]}**.
3. Eligible for prospective shadow at the freeze:
   **{", ".join(conclusions["prospective_shadow_eligible_profiles"]) or "none"}**.
4. Unproven: independent forward edge, future profitability, broader symbol
   transfer, realistic queue/impact and exact forward funding settlement.
5. Persistent active-profile shadow deployment justified by the frozen evidence:
   **{conclusions["persistent_shadow_justified"]}**. Observation-only collection
   remains useful engineering; it must not be presented as validated trading edge.
"""
    (ROOT / "REPORT.md").write_text(body)


if __name__ == "__main__":
    print(json.dumps(generate(), indent=2))

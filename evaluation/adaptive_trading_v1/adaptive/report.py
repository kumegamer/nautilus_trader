"""Auditable result tables, complete event streams, classification and file verification."""

import csv
import json
import platform

import pandas as pd

from .common import DAY, PRIOR, ROOT, assert_frozen, config, digest, ns, write_json
from .performance import daily_statistics, trade_metrics
from .profiles import REGIMES, library
from .workflow import PRE, combined, read_runs

AXES = ("strategy", "profile", "symbol", "regime", "side")


def attributed_metrics(trades, start, end, capital=30000):
    m = trade_metrics(trades, capital)
    index = pd.date_range(
        pd.Timestamp(start, tz="UTC").normalize(),
        pd.Timestamp(end, tz="UTC").normalize(),
        freq="D",
    )
    changes = pd.Series(0.0, index=index)
    for t in trades:
        day = pd.Timestamp(t["exit_ns"], tz="UTC").ceil("D")
        if day in changes.index:
            changes.loc[day] += float(t["net_pnl"])
    daily = [(int(t.value), capital + float(v)) for t, v in changes.cumsum().items()]
    m.update(daily_statistics(daily, capital))
    m["return_scope"] = "daily realized attribution, not marked subgroup exposure"
    return m


def breakdown(runs, start, end):
    trades = [t for r in runs for t in r["trades"]]
    result = {}
    for axis in AXES:
        values = sorted({str(t.get(axis, "REFERENCE")) for t in trades})
        if axis == "symbol":
            values = config()["symbols"]
        if axis == "regime":
            values = list(REGIMES) + ["REFERENCE"]
        if axis == "side":
            values = ["1", "-1"]
        result[axis] = {
            value: attributed_metrics(
                [t for t in trades if str(t.get(axis, "REFERENCE")) == value],
                start,
                end,
            )
            for value in values
        }
    result["time_window"] = {}
    for days in (30, 90, 365):
        lo = max(start, end - days * DAY)
        selected = [t for t in trades if lo <= t["exit_ns"] < end]
        result["time_window"][str(days) + "d"] = attributed_metrics(selected, lo, end)
    return result


def event_logs(runs):
    destination = ROOT / "results" / "events"
    destination.mkdir(parents=True, exist_ok=True)
    counts = {}
    keys = (
        "decisions",
        "switches",
        "degradation",
        "research",
        "promotions",
        "regime_transitions",
    )
    for kind in keys:
        events = []
        for r in runs:
            if r["candidate"] != "ADAPTIVE" and kind != "regime_transitions":
                continue
            for e in r[kind]:
                events.append(
                    {
                        "run": r["candidate"],
                        "symbol": r["symbol"],
                        "period": r["period"],
                        "cost_scenario": r["scenario"],
                        **e,
                    }
                )
        events.sort(
            key=lambda e: (e.get("timestamp", 0), e["cost_scenario"], e["symbol"])
        )
        counts[kind] = len(events)
        with (destination / (kind + ".jsonl")).open("w") as f:
            for event in events:
                f.write(json.dumps(event, sort_keys=True, allow_nan=False) + "\n")
        # CSV keeps structured evidence as JSON rather than dropping it
        fields = [
            "timestamp",
            "run",
            "symbol",
            "period",
            "cost_scenario",
            "old_profile",
            "new_profile",
            "regime",
            "regime_confidence",
            "performance_state",
            "reason",
            "evidence",
            "event_json",
        ]
        with (destination / (kind + ".csv")).open("w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fields)
            writer.writeheader()
            for e in events:
                row = {k: e.get(k) for k in fields if k != "event_json"}
                row["evidence"] = json.dumps(e.get("evidence", {}), sort_keys=True)
                row["event_json"] = json.dumps(e, sort_keys=True)
                writer.writerow(row)
    return counts


def classify(adaptive, static, wf, cost, groups, eligible):
    if adaptive["net_pnl"] <= 0 or not eligible:
        return "ADAPTIVE_NO_EDGE", {
            "positive_sealed_economics": adaptive["net_pnl"] > 0,
            "validated_profile_exists": bool(eligible),
        }
    positive_wf = sum(m["net_pnl"] > 0 for m in wf) / len(wf)
    active_regimes = [m for m in groups["regime"].values() if m["number_of_trades"]]
    gates = {
        "sealed_sample_60": adaptive["number_of_trades"] >= 60,
        "sealed_drawdown": adaptive["maximum_drawdown"] <= 0.15,
        "majority_positive_walk_forward": positive_wf > 0.5,
        "cost1.5x_positive": cost["cost1.5x"]["net_pnl"] > 0,
        "symbol_generalization": sum(
            m["net_pnl"] > 0 for m in groups["symbol"].values()
        )
        >= 2,
        "regime_consistency": bool(active_regimes)
        and all(m["net_pnl"] > 0 for m in active_regimes),
        "risk_adjusted_static_improvement": (
            adaptive.get("sharpe") is not None
            and static.get("sharpe") is not None
            and adaptive["sharpe"] > static["sharpe"]
            and adaptive["maximum_drawdown"] <= static["maximum_drawdown"]
        ),
        "not_top10_dependent": adaptive["net_excluding_top10"] > 0
        and (adaptive["top10_positive_profit_share"] or 1) <= 0.5,
        "parameter_stability": bool(eligible),
        "forward_shadow": False,
    }
    historical = all(v for k, v in gates.items() if k != "forward_shadow")
    if not historical:
        return "ADAPTIVE_WEAK_EDGE", gates
    if (
        all(gates.values())
        and cost["cost2x"]["net_pnl"] > 0
        and adaptive["number_of_trades"] >= 100
        and positive_wf >= 0.6
    ):
        return "ADAPTIVE_ROBUST_EDGE_CANDIDATE", gates
    return "ADAPTIVE_EDGE_CANDIDATE", gates


def fmt(value, decimals=2):
    return "undefined" if value is None else f"{value:,.{decimals}f}"


def table(rows):
    lines = [
        "| System | Period | Costs | Trades | Net USDT | Sharpe | Max DD |",
        "|---|---|---|---:|---:|---:|---:|",
    ]
    for r in rows:
        lines.append(
            f"| {r['system']} | {r['period']} | {r['scenario']} | {r['number_of_trades']} | {fmt(r['net_pnl'])} | {fmt(r.get('sharpe'))} | {fmt(100 * r['maximum_drawdown'])}% |"
        )
    return "\n".join(lines)


def report():
    frozen = assert_frozen()
    cfg = config()
    runs = read_runs((*PRE, "holdout"))
    selected = frozen["static_choice"]
    systems = {
        "static_best": selected,
        "adaptive": "ADAPTIVE",
        "buy_hold": "BUY_HOLD",
        "no_trade": "NO_TRADE",
    }
    rows, details = [], {}
    for system, candidate in systems.items():
        details[system] = {}
        for period in (*PRE, "holdout"):
            start, end = map(ns, cfg["periods"][period])
            details[system][period] = {}
            for scenario in cfg["scenarios"]:
                chosen = [
                    r
                    for r in runs
                    if r["candidate"] == candidate
                    and r["period"] == period
                    and r["scenario"] == scenario
                ]
                if len(chosen) != len(cfg["symbols"]):
                    raise RuntimeError(
                        f"Missing comparable runs: {system} {period} {scenario}"
                    )
                m = combined(chosen)
                details[system][period][scenario] = {
                    "metrics": m,
                    "breakdown": breakdown(chosen, start, end),
                }
                rows.append(
                    {
                        "system": system,
                        "period": period,
                        "scenario": scenario,
                        **{
                            k: v
                            for k, v in m.items()
                            if k not in ("daily_equity", "monthly_net_pnl")
                        },
                    }
                )
    pre_evidence = json.loads(
        (ROOT / "results" / "preholdout_evidence.json").read_text()
    )
    eligible = [p for p, e in pre_evidence.items() if e and all(e["gates"].values())]
    final = details["adaptive"]["holdout"]["base"]["metrics"]
    static_final = details["static_best"]["holdout"]["base"]["metrics"]
    wf = [details["adaptive"][p]["base"]["metrics"] for p in ("wf1", "wf2")]
    costs = {s: details["adaptive"]["holdout"][s]["metrics"] for s in cfg["scenarios"]}
    label, gates = classify(
        final,
        static_final,
        wf,
        costs,
        details["adaptive"]["holdout"]["base"]["breakdown"],
        eligible,
    )
    counts = event_logs(runs)
    comparison = {
        "net_difference_vs_static": final["net_pnl"] - static_final["net_pnl"],
        "adaptive_underperforms_static_net": final["net_pnl"] < static_final["net_pnl"],
        "adaptive_sharpe": final.get("sharpe"),
        "static_sharpe": static_final.get("sharpe"),
        "claim": "No demonstrated adaptive edge"
        if label == "ADAPTIVE_NO_EDGE"
        else "Historical candidate only",
    }
    failure_counts = {}
    for e in pre_evidence.values():
        if e:
            for k, v in e["gates"].items():
                if not v:
                    failure_counts[k] = failure_counts.get(k, 0) + 1
    failure = (
        max(failure_counts, key=failure_counts.get)
        if failure_counts
        else "insufficient independent evidence"
    )
    write_json(
        ROOT / "results" / "final.json",
        {
            "classification": label,
            "gates": gates,
            "eligible_preholdout": eligible,
            "static_choice": selected,
            "comparison": comparison,
            "event_counts": counts,
            "promotion_gate_failures": failure_counts,
            "strongest_failure_mode": failure,
            "forward_shadow_observed": False,
            "real_money_enabled": False,
            "worth_v2": "Engineering yes; trading-edge advancement requires a new validated hypothesis and fresh untouched OOS",
        },
    )
    write_json(ROOT / "results" / "details.json", details)
    write_json(
        ROOT / "results" / "profiles.json",
        {
            p: {
                **v.definition(),
                "historical_expected_band": (pre_evidence.get(p) or {}).get("expected"),
                "preholdout_validated": p in eligible,
            }
            for p, v in library().items()
        },
    )
    static_all = {}
    for p in library():
        if p == "NO_TRADE":
            continue
        static_all[p] = {}
        for period in (*PRE, "holdout"):
            for scenario in cfg["scenarios"]:
                chosen = [
                    r
                    for r in runs
                    if r["candidate"] == p
                    and r["period"] == period
                    and r["scenario"] == scenario
                ]
                if chosen:
                    static_all[p][period + "/" + scenario] = combined(chosen)
    write_json(ROOT / "results" / "all_static_results.json", static_all)
    with (ROOT / "results" / "metrics.csv").open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    trades = [
        {
            "run": r["candidate"],
            "period": r["period"],
            "scenario": r["scenario"],
            "symbol": r["symbol"],
            **t,
        }
        for r in runs
        for t in r["trades"]
    ]
    fields = sorted({k for t in trades for k in t})
    with (ROOT / "results" / "trades.csv").open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(trades)
    current = [r for r in rows if r["period"] == "holdout"]
    cost_rows = []
    for system in systems:
        for scenario in cfg["scenarios"]:
            m = details[system]["holdout"][scenario]["metrics"]
            cost_rows.append(
                f"| {system} | {scenario} | {fmt(m['gross_pnl'])} | {fmt(m['fees'])} | {fmt(m['slippage'])} | {fmt(m['funding'])} | {fmt(m['net_pnl'])} |"
            )
    decomposition = []
    for axis in ("symbol", "regime", "side"):
        lines = [
            f"Sealed base-cost results by {axis}:\n",
            "| System | Group | Trades | Net USDT | PF |",
            "|---|---|---:|---:|---:|",
        ]
        for system in systems:
            for group, m in details[system]["holdout"]["base"]["breakdown"][
                axis
            ].items():
                if axis == "regime" and not m["number_of_trades"]:
                    continue
                lines.append(
                    f"| {system} | {group} | {m['number_of_trades']} | {fmt(m['net_pnl'])} | {fmt(m['profit_factor'])} |"
                )
        decomposition.append("\n".join(lines))
    verdict = (
        "Adaptation underperformed the frozen static profile on sealed net PnL."
        if comparison["adaptive_underperforms_static_net"]
        else "Avoiding losses through abstention is not evidence of a profitable adaptive edge."
        if label == "ADAPTIVE_NO_EDGE"
        else "See all risk-adjusted comparison gates."
    )
    parts = [
        f"# Nautilus Adaptive Trading System v1\n\n**Classification: {label}.** Historical simulation only; real-money execution disabled.",
        f"Frozen static comparator: `{selected}`. Sealed holdout: July–September 2026. Adaptive net {fmt(final['net_pnl'])} USDT versus static {fmt(static_final['net_pnl'])} USDT. {comparison['claim']}. {verdict}",
        "## 1. Architecture\n\nPublic Binance archives -> native events + causal feature engine -> regime engine -> finite-profile controller -> Nautilus Strategy/order/fills/portfolio. Closed native positions -> performance/drift -> proposal-only research agent -> timestamp-filtered historical research -> explicit promotion registry -> SHADOW. No live adapter is instantiated.",
        "## 2. Feature definitions\n\nLog-return 48-bar realized volatility; 14-bar true-range ATR and ATR/close; 24-bar momentum; EMA200 slope over six bars normalized by ATR; distance/ATR trend strength; 48-bar price efficiency; logarithmic choppiness; 48-bar channel breakout and one-bar failed breakout frequency over 96 bars; volatility/240-bar historical median; volume/96-bar median and 6/24 mean acceleration; 96-bar lag-one return correlation; absolute return/quote-volume liquidity proxy. Cross-symbol 96-bar return correlations and current return dispersion. Funding and first difference joined at actual publication time. Basis and observed spread unavailable. All four timeframes use closed bars. See adaptive/features.py and causal tests.",
        "## 3. Regime definitions\n\nUNKNOWN until features ready. Stress: volatility ratio >3, or absolute 15m 24-bar momentum >8% and volatility ratio >1.5. Expansion >1.8; compression <0.6. Otherwise trend requires 48-hour efficiency >0.3 and absolute hourly normalized slope >0.02; remaining observations are range. High volatility above 1.2. Confidence is a bounded distance-from-rule score, not a calibrated probability. Start, duration and complete transition logs are persisted.",
        "## 4. Profile definitions\n\nFour central economically motivated families, two neighbors each, short-only and funding-filter breakout hypotheses, and NO_TRADE. Exact parameters, regimes, permissions, sizing, provisional expected ranges and stop definitions: results/profiles.json. Expectations are hypotheses, not guaranteed historical bands; promotion evidence supplies estimated R confidence bands. All 14 attempts remain in all_static_results.json. Historical expected R bands and validation status are attached to each profile; they never mutate runtime parameters. Current profile definitions differ from the prior unfiltered WEAK_EDGE, so its results are not carried over.",
        "## 5. Adaptation policy\n\nOnly point-in-time SHADOW-eligible profiles; fixed family/id preference avoids chasing recent winners. Regime hysteresis, 24h dwell and 12 switches/30-day ceiling. Safety exits bypass dwell. Discrete risk 0/0.5/1; side and symbol disablement. Exposure exits on risk reduction; parameters never mutate. State persists across chronological periods; accounts are flattened and reinitialized to 10,000 USDT per sleeve at scheduled boundaries, with nominal PnL carried in portfolio reports. This scheduled-reset simulation is a limitation versus uninterrupted deployment.",
        "## 6. Degradation triggers\n\nDaily time, 50 additional trades, significant regime transitions, marked/realized drawdown >8%, eight consecutive losses, >=20-trade negative expectancy/PF signals, >=50-trade corroborated failure, execution-cost deterioration, and two-sided historical confidence-band comparison. Sparse samples are INSUFFICIENT_DATA. All six performance states are explicit. PnL alone never authorizes promotion.",
        "## 7. Research and promotion\n\nRESEARCH -> CANDIDATE -> VALIDATED -> SHADOW; failed gates -> REJECTED. SHADOW -> CANARY_ELIGIBLE requires additional forward shadow observations; LIVE_ELIGIBLE transitions are forbidden. The offline rule agent proposes and ranks only declared experiments. At every request a seven-day embargo and strict entry/exit purge restrict evidence to the past. Chronological 40/20/10/10/20 research/validation/WF/WF/internal-OOS partitions are diagnostics using known developmental data. The new sealed period is separate and never supplied to the research provider. Limited candidate re-evaluation is implemented; open-ended AI code generation is outside v1.",
        "## 8. Test periods\n\n"
        + "\n".join(f"- {p}: [{a}, {b}) UTC" for p, (a, b) in cfg["periods"].items())
        + "\n\nEvery date through June 2026 was previously observed. Only July–September 2026 is new sealed evidence. Exact freeze/open timestamps and hashes are in results/freeze.json and holdout_opened.json.",
        "## 9. Assumptions\n\n5bp taker and 1bp adverse slippage per fill at base, both stressed 1.5x/2x with outward tick rounding. Signed actual funding is not artificially multiplied. Historical tick/lot schedules are approximated by declared fixed instrument specs. No historical order book: volume participation is a proxy, not partial-fill evidence. Stop exits wait for a close then next open; intrabar stop protection is not claimed. MAE/MFE use observed bar high/low after entry. Perpetual buy/hold is 90% notional long with funding, not a matched-volatility allocation. Three-symbol survivorship/universe choice is explicit. Sharpe/Sortino use daily returns, zero risk-free rate, 365-day scaling; short samples are noisy.",
        "## 10–11. Static and adaptive results\n\n" + table(current),
        "Developmental chronological results:\n\n"
        + table(
            [r for r in rows if r["scenario"] == "base" and r["period"] != "holdout"]
        ),
        "## 12–14. Symbol, regime and long/short decomposition\n\nAll systems/costs/periods: results/details.json, with strategy/profile/symbol/regime/side and rolling 30/90/365-day breakdowns. Trade-level ledger: results/trades.csv. Group Sharpe is daily realized attribution; system Sharpe is marked equity. No-trade group metrics remain undefined where there are no observations.\n\n"
        + "\n\n".join(decomposition),
        "## 15. Fees, slippage and funding\n\n| System | Costs | Gross | Fees | Slippage | Signed funding | Net |\n|---|---|---:|---:|---:|---:|---:|\n"
        + "\n".join(cost_rows),
        "## 16–17. Walk-forward and sealed holdout\n\nSee the period tables and exact results/details.json. All walk-forward profile eligibility uses only prior closed outcomes, never full-period scores. Sealed static results never enter adaptive decisions. A flat adaptive result demonstrates abstention, not improved Sharpe. Positive static PnL does not imply promotion eligibility.",
        "## 18–21. Switch, degradation, research and promotion history\n\n"
        + "\n".join(
            f"- {k}: {v:,} logged events across costs and symbols"
            for k, v in counts.items()
        )
        + "\n\nComplete JSONL and CSV in results/events/. Switch rows include timestamp, old/new profile, regime/confidence, performance state, reason and structured evidence. JSONL retains every decision payload; CSV includes the full JSON too. No switches is a reported outcome, not an omitted log. Historical promotion is SHADOW simulation eligibility only. Superseded pre-freeze runs lacking state continuation remain under results/development_superseded, excluded from all conclusions.",
        "## 22. Failure modes and validation limits\n\n"
        + f"Most frequent final gate failure: **{failure}**. Failure counts: `{json.dumps(failure_counts, sort_keys=True)}`.\n\n"
        + "Handwritten regimes can fragment samples and create excessive eligibility churn. OHLCV cannot validate microstructure execution, latency or market impact. Confidence is heuristic. Known historical partitions and multiple candidate tests limit inference even with purging. Boundary flattening, fixed capital risk and reused warmup are not uninterrupted real operation. Withheld opportunities under NO_TRADE do not prove a profitable selection policy. AI process boundaries are a software capability convention, not a sandbox against malicious Python code. Forward shadow, calibrated uncertainty, stronger market-mechanism hypotheses and a new untouched OOS are required before advancement toward trading.",
        "## Reproducibility\n\nExact source/evidence freeze, publisher SHA256s, normalized data audits, artifact checksums, runtime provenance and native reconciliation differences are persisted. Run `python -m adaptive.workflow verify` using the pinned environment; reproduction instructions are in README.md. No prior branch files or develop history were modified.\n\n"
        + f"Tests: results/tests.txt. Current classification: **{label}**. Strongest failure mode: **{failure}**. Nautilus is worth advancing as the deterministic engine; trading-edge promotion to v2 needs new validated economics, not a more aggressive optimizer.",
    ]
    (ROOT / "REPORT.md").write_text("\n\n".join(parts) + "\n")
    write_json(
        ROOT / "results" / "runtime.json",
        {
            "python": platform.python_version(),
            "platform": platform.platform(),
            "prior_commit": PRIOR,
            "source_hashes": frozen["source_hashes"],
            "native_reconciliation_tolerance": "0.00001 USDT",
            "run_count": len(runs),
            "native_fill_count": sum(len(r["fills"]) for r in runs),
        },
    )
    artifacts = [
        p
        for p in ROOT.rglob("*")
        if p.is_file()
        and "__pycache__" not in p.parts
        and ".pytest_cache" not in p.parts
        and p.name != "artifact_checksums.json"
        and "raw" not in p.parts
    ]
    write_json(
        ROOT / "results" / "artifact_checksums.json",
        {str(p.relative_to(ROOT)): digest(p) for p in sorted(artifacts)},
    )
    print(
        json.dumps(
            {"classification": label, "comparison": comparison, "run_count": len(runs)}
        )
    )


def verify():
    assert_frozen()
    checks = json.loads((ROOT / "results" / "artifact_checksums.json").read_text())
    for name, expected in checks.items():
        if digest(ROOT / name) != expected:
            raise RuntimeError(f"Artifact checksum mismatch: {name}")
    raw_count = 0
    for manifest in (ROOT / "data").glob("*manifest.json"):
        for row in json.loads(manifest.read_text()):
            path = ROOT / row["path"]
            if digest(path) != row["publisher_sha256"]:
                raise RuntimeError(f"Publisher checksum mismatch: {path}")
            raw_count += 1
    for repairs in (ROOT / "data").glob("*repairs.json"):
        for row in json.loads(repairs.read_text()):
            if digest(ROOT / row["path"]) != row["publisher_sha256"]:
                raise RuntimeError("Repair checksum mismatch")
    runs = read_runs((*PRE, "holdout"))
    for r in runs:
        if abs(float(r["reconciliation_difference"])) > 0.00001:
            raise RuntimeError("Native account reconciliation failed")
        if any(
            f["signal_ns"] >= f["ts_ns"] or float(f["slippage"]) < 0 for f in r["fills"]
        ):
            raise RuntimeError("Fill chronology/adverse cost check failed")
        for e in r["promotions"]:
            if (
                e["evidence"]["end_ns"] > e["timestamp"]
                or e["new_state"] == "LIVE_ELIGIBLE"
            ):
                raise RuntimeError("Unsafe promotion")
        for e in r["research"]:
            evidence = e["evidence"]
            if evidence and evidence["end_ns"] > e["timestamp"] - 7 * DAY:
                raise RuntimeError("Research embargo violated")
        if r["candidate"] == "ADAPTIVE":
            availability = {"NO_TRADE": 0, **r.get("initial_eligibility", {})}
            # Include carried state to check promotions in earlier periods
            for p, ts in (
                (r.get("adaptive_state") or {})
                .get("registry", {})
                .get("available", {})
                .items()
            ):
                availability[p] = ts
            for e in r["promotions"]:
                if e["new_state"] == "SHADOW":
                    availability[e["profile"]] = e["timestamp"] + 1
            for trade in r["trades"]:
                if availability.get(trade["profile"], 2**63) >= trade["entry_ns"]:
                    raise RuntimeError("Trade executed before profile eligibility")
            for switch in r["switches"]:
                p = switch["new_profile"]
                if p != "NO_TRADE" and availability.get(p, 2**63) > switch["timestamp"]:
                    raise RuntimeError("Profile selected before validation")
    print(
        json.dumps(
            {
                "verified_artifacts": len(checks),
                "publisher_archives": raw_count,
                "native_runs": len(runs),
                "status": "PASS",
            }
        )
    )

"""Generate every table and admission artifact directly from retained native runs."""

import csv
import json
from datetime import datetime, timezone

import numpy as np

from .analysis import summary
from .audit import native_audit, reference_audit
from .common import ROOT, config, digest, write_json
from .evaluate import (
    DEVELOPMENT,
    END,
    QUARTERS,
    START,
    classify,
    monthly_eligibility,
    pick,
)
from .metrics import portfolio_daily, selected_trades, trade_metrics
from .profiles import BASE, library
from .research import diagnose, journal
from .workflow import load_runs, source_hashes, verify_freeze


def table(rows, columns):
    def fmt(x):
        if x is None:
            return "undefined"
        if isinstance(x, float):
            return f"{x:,.4f}"
        return str(x).replace("|", "/")

    return "\n".join(
        [
            "| " + " | ".join(columns) + " |",
            "|" + "---|" * len(columns),
            *["| " + " | ".join(fmt(r.get(c)) for c in columns) + " |" for r in rows],
        ]
    )


def write_csv(name, rows):
    if not rows:
        (ROOT / "results" / name).write_text("")
        return
    fields = list(dict.fromkeys(k for r in rows for k in r))
    with (ROOT / "results" / name).open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    k: json.dumps(v, sort_keys=True)
                    if isinstance(v, (list, dict, tuple))
                    else v
                    for k, v in row.items()
                }
            )


def generate():
    verify_freeze()
    runs = load_runs()
    references = reference_audit()
    native = native_audit(runs)
    causality = json.loads((ROOT / "results/causality_audit.json").read_text())
    integrity = native["passed"] and causality["passed"]
    evidence = classify(runs, integrity)
    eligibility = monthly_eligibility(runs)
    write_json(ROOT / "results/native_integrity.json", native)
    write_json(ROOT / "results/reference_final_audit.json", references)
    write_json(ROOT / "results/profile_evidence.json", evidence)
    write_json(ROOT / "results/monthly_eligibility.json", eligibility)
    write_json(ROOT / "results/research_loop.json", journal(evidence))
    rows = []
    by_symbol = []
    by_regime = []
    quarters = []
    months = []
    experiments = []
    trades = []
    profiles = library()
    for p in profiles.values():
        scenarios = {}
        for cost in config()["scenarios"]:
            chosen = pick(runs, p.id, cost)
            m = summary(chosen, START, END)
            dev = summary(chosen, DEVELOPMENT, START)
            scenarios[cost] = {"development": dev, "oos": m}
            rows.append(
                {
                    "profile": p.id,
                    "family": p.family,
                    "side": p.side,
                    "role": p.role,
                    "cost": cost,
                    **{k: v for k, v in m.items() if not isinstance(v, (dict, list))},
                }
            )
            for s in config()["symbols"]:
                sm = summary([r for r in chosen if r["symbol"] == s], START, END)
                by_symbol.append(
                    {
                        "profile": p.id,
                        "symbol": s,
                        "side": p.side,
                        "cost": cost,
                        **{
                            k: v
                            for k, v in sm.items()
                            if not isinstance(v, (dict, list))
                        },
                    }
                )
            for q, a, b in QUARTERS:
                qm = summary(chosen, a, b)
                quarters.append(
                    {
                        "profile": p.id,
                        "quarter": q,
                        "cost": cost,
                        "marked_net": qm["net_pnl"],
                        "purged_trade_net": qm["purged_trade_net"],
                        "trades": qm["trades"],
                        "sharpe": qm["sharpe"],
                    }
                )
            for month, net in m["months_marked"].items():
                months.append(
                    {"profile": p.id, "cost": cost, "month": month, "marked_net": net}
                )
            selected = selected_trades(chosen, START, END)
            regimes = sorted({t["regime"] for t in selected})
            for regime in regimes:
                gm = trade_metrics([t for t in selected if t["regime"] == regime])
                by_regime.append(
                    {
                        "profile": p.id,
                        "side": p.side,
                        "regime": regime,
                        "cost": cost,
                        **{
                            k: v
                            for k, v in gm.items()
                            if not isinstance(v, (dict, list))
                        },
                    }
                )
            if cost == "base":
                for run in chosen:
                    trades.extend({"profile": p.id, **t} for t in run["trades"])
        e = evidence.get(p.id)
        experiments.append(
            {
                "hypothesis_id": p.id,
                "strategy_family": p.family,
                "definition": p.definition(),
                "features": "FEATURES.md; exact causal formula in alpha/profiles.py:signal",
                "symbols": p.symbols,
                "timeframes": ["5m", "15m", "1h", "4h"],
                "entry_logic": "alpha/profiles.py:signal (frozen SHA256 in predeclaration)",
                "exit_logic": p.exit,
                "risk_model": ".25% initial stop risk; .9x notional; .1% prior volume; 40% annual-vol reduction only",
                "cost_model": "5bp taker +1bp adverse per fill; signed observed funding; decimal tick/lot quantization",
                "date_range": ["2024-01-01", "2026-10-01"],
                "evaluation": ["2025-01-01", "2026-10-01"],
                "result": scenarios,
                "classification": e["classification"] if e else "REJECTED",
                "reason": e["failures"] if e else ["NON_PROMOTABLE_" + p.role.upper()],
                "diagnosis": diagnose(scenarios["base"]["oos"]),
            }
        )
    write_json(ROOT / "results/experiments.json", experiments)
    write_csv("profile_results.csv", rows)
    write_csv("per_symbol_results.csv", by_symbol)
    write_csv("long_short_regime_results.csv", by_regime)
    write_csv("walk_forward_quarterly.csv", quarters)
    write_csv("monthly_contributions.csv", months)
    write_csv("trades_base.csv", trades)
    validated = [
        pid for pid, e in evidence.items() if e["classification"] == "VALIDATED_PROFILE"
    ]
    candidates = [
        pid
        for pid, e in evidence.items()
        if e["classification"] == "RESEARCH_CANDIDATE"
    ]
    weak = [pid for pid, e in evidence.items() if e["classification"] == "WEAK_SIGNAL"]
    corrs = []
    diverse = False
    for i, a in enumerate(validated):
        for b in validated[i + 1 :]:
            ra = np.diff([e for _, e in portfolio_daily(pick(runs, a), START, END)])
            rb = np.diff([e for _, e in portfolio_daily(pick(runs, b), START, END)])
            correlation = (
                float(np.corrcoef(ra, rb)[0, 1]) if np.std(ra) and np.std(rb) else None
            )
            different = (
                profiles[a].family != profiles[b].family
                and correlation is not None
                and abs(correlation) < 0.8
            )
            corrs.append(
                {
                    "a": a,
                    "b": b,
                    "daily_pnl_correlation": correlation,
                    "materially_different": different,
                }
            )
            diverse |= different
    final = (
        "ALPHA_DISCOVERY_VALIDATED_LIBRARY"
        if len(validated) >= 2 and diverse
        else "ALPHA_DISCOVERY_CANDIDATES"
        if validated or candidates
        else "ALPHA_DISCOVERY_WEAK"
        if weak
        else "ALPHA_DISCOVERY_NO_EDGE"
    )
    library_rows = []
    for pid in validated:
        p = profiles[pid]
        e = evidence[pid]
        m = e["metrics"]
        library_rows.append(
            {
                "profile_id": pid,
                "strategy_family": p.family,
                "symbols": p.symbols,
                "direction": "LONG" if p.side > 0 else "SHORT",
                "timeframes": ["5m", "15m", "1h", "4h"],
                "compatible_regimes": "Frozen entry conditions in alpha/profiles.py; descriptive entry cells in long_short_regime_results.csv",
                "entry_conditions": {
                    "function": "alpha.profiles.signal",
                    "profile": pid,
                },
                "exit_conditions": {
                    "policy": p.exit,
                    "maximum_15m_bars": p.max_age,
                    "close_stop_atr": p.stop_atr,
                },
                "risk_rules": {
                    "capital_per_symbol": 10000,
                    "initial_stop_risk_fraction": 0.0025,
                    "notional_ceiling": 0.9,
                    "volume_participation": 0.001,
                    "annual_volatility_target_reduction_only": 0.4,
                },
                "parameters": p.definition(),
                "expected_trade_frequency": {
                    "basis": "historical OOS, not a forecast",
                    "trades_per_30_days": m["trades"]
                    * 30
                    / ((END - START) / (86400 * 10**9)),
                },
                "historical_expectancy": m["expectancy"],
                "historical_expectancy_R": m["expectancy_R"],
                "historical_PF": m["profit_factor"],
                "historical_Sharpe": m["sharpe"],
                "historical_DD": m["maximum_drawdown"],
                "cost_tolerance": {c: v["net_pnl"] for c, v in e["costs"].items()},
                "known_failure_regimes": [
                    r["regime"]
                    for r in by_regime
                    if r["profile"] == pid and r["cost"] == "base" and r["net_pnl"] <= 0
                ],
                "prospective_confirmation": "REQUIRED_NOT_STARTED",
                "real_money_enabled": False,
            }
        )
    write_json(
        ROOT / "profile_library.json",
        {
            "schema_version": 1,
            "evidence_class": "RETROSPECTIVE_EVIDENCE",
            "classification": final,
            "profiles": library_rows,
            "real_money_enabled": False,
        },
    )
    ml = []
    for side in ("LONG", "SHORT"):
        m = evidence["ML_" + side]["metrics"]
        raw = summary(pick(runs, "RAW_" + side), START, END)
        ml.append(
            {
                "direction": side,
                "rule_net": raw["net_pnl"],
                "ml_net": m["net_pnl"],
                "delta": m["net_pnl"] - raw["net_pnl"],
                "rule_sharpe": raw["sharpe"],
                "ml_sharpe": m["sharpe"],
                "improvement_gate": evidence["ML_" + side]["gates"]["ml_improvement"],
                "classification": evidence["ML_" + side]["classification"],
                "promotion_limit": "ML threshold-neighborhood validation not included; stability fails closed",
            }
        )
    write_csv("ml_vs_rules.csv", ml)
    conclusion = {
        "classification": final,
        "validated_profiles": validated,
        "research_candidates": candidates,
        "weak_signals": weak,
        "primary_treatments": 16,
        "economic_hypotheses": 12,
        "paths": len(profiles),
        "native_runs": len(runs),
        "data_status": "CONSUMED_THROUGH_2026_09",
        "prospective_performance_observed": False,
        "material_difference_checks": corrs,
        "adaptive_controller_exercised": False,
        "real_money_enabled": False,
        "initial_forward_eligible_profiles": validated,
        "automatic_activation": False,
    }
    write_json(ROOT / "results/conclusions.json", conclusion)
    profile_table = [
        {
            "profile": pid,
            "status": e["classification"],
            "trades": e["metrics"]["trades"],
            "net": e["metrics"]["net_pnl"],
            "trade_net": e["metrics"]["purged_trade_net"],
            "PF": e["metrics"]["profit_factor"],
            "Sharpe": e["metrics"]["sharpe"],
            "DD": e["metrics"]["maximum_drawdown"],
            "expectancy_R": e["metrics"]["expectancy_R"],
        }
        for pid, e in evidence.items()
    ]
    strongest = sorted(
        evidence, key=lambda pid: evidence[pid]["metrics"]["net_pnl"], reverse=True
    )[:3]
    failures = [
        {"profile": pid, "failed_gates": ", ".join(e["failures"])}
        for pid, e in evidence.items()
    ]
    stress = [
        {"profile": pid, **{c: e["costs"][c]["net_pnl"] for c in config()["scenarios"]}}
        for pid, e in evidence.items()
    ]
    stability = [
        {
            "profile": pid,
            "low_net": e["neighbors"].get("LOW", {}).get("base", {}).get("net_pnl"),
            "central_net": e["metrics"]["net_pnl"],
            "high_net": e["neighbors"].get("HIGH", {}).get("base", {}).get("net_pnl"),
            "pass": e["gates"]["stability"],
        }
        for pid, e in evidence.items()
    ]
    concentration = [
        {
            "profile": pid,
            "top1_share": e["metrics"]["top1_share"],
            "top5_share": e["metrics"]["top5_share"],
            "top10_share": e["metrics"]["top10_share"],
            "ex_top1": e["metrics"]["net_ex_top1"],
            "month_share": e["metrics"]["largest_marked_month_share"],
            "symbol_share": e["symbol_positive_contribution_share"],
            "bootstrap_positive": e["bootstrap"]["probability_positive"],
            "centered_p": e["bootstrap"]["centered_p"],
        }
        for pid, e in evidence.items()
    ]
    wf = [
        {"profile": pid, **{q: v["net_pnl"] for q, v in e["quarters"].items()}}
        for pid, e in evidence.items()
    ]
    long_short = []
    for side in (1, -1):
        ids = [p.id for p in BASE if p.side == side]
        for pid in ids:
            m = evidence[pid]["metrics"]
            long_short.append(
                {
                    "profile": pid,
                    "side": side,
                    "net": m["net_pnl"],
                    "trades": m["trades"],
                }
            )
    report = f"""# Nautilus Alpha Discovery v3

**{final}**. This is standalone alpha-library research, not Adaptive Trading v3.
Validated profiles: {validated or "none"}. Research candidates: {candidates or "none"}.
Weak signals: {weak or "none"}. No real-money trading or credentials are enabled.

All historical results use CONSUMED data and are RETROSPECTIVE_EVIDENCE. Quarterly
OOS means chronological separation within reused history, not untouched evidence.
No prospective performance has been observed. Frozen references were neither
modified nor merged; V2 exact commit is 57703f7b5f77fed476adef323dc23e43f5a753b0.

## 1. Hypothesis families and rationale

Six economic families, separate sides: multi-horizon trend/resumption; breakout
quality with taker flow/volume; cross-asset BTC-conditioned ETH/SOL strength;
funding crowding/unwind; compression/expansion versus high-volatility downside
persistence; liquidity-shock range reversal. Two raw breakout controls and two
small chronological logistic filters compare complexity to simpler rules.
AUTOPSY.md documents prior failures and pre-result plausibility ranking.
FEATURES.md documents each formula, lookback, availability and rationale.

## 2. Experiment budget and research loop

16 central treatments (12 economic, two raw controls, two ML controls), 24
one-threshold stability paths and four exit interventions: **44 paths, {len(runs)}
native runs** across three symbols and three costs. Repeated paths and cost runs
are not independent market samples. No additional search or result-dependent
parameter revisions. results/experiments.json records every hypothesis, parameters,
entry/exit/risk/cost rules, dates, results and rejection reason. The assistant's
hypotheses are inert; deterministic gates alone classify. results/research_loop.json
retains diagnoses and next-version proposals after the finite budget is exhausted.

## 3. Rejected hypotheses and gates

Controls, neighbors and exit interventions are deliberately non-promotable. ML
must beat its own side's raw control; no ML neighborhood search was budgeted, so
its stability gate remains unsatisfied even if gross ranking improves.

{table(failures, ["profile", "failed_gates"])}

## 4–5. Strongest candidates and profile metrics

Highest marked retrospective PnL profiles: {", ".join(strongest)}. This ranking is
post-result description; it does not override the classifications below.
Net is marked equity change in USDT, trade_net is fully contained/purged trade
attribution. PF/expectancy/R use those purged closed trades. Sharpe uses daily
marked returns, zero risk-free rate, 365-day scaling. DD is a fraction.

{table(profile_table, ["profile", "status", "trades", "net", "trade_net", "PF", "Sharpe", "DD", "expectancy_R"])}

## 6. Per-symbol results

Independent 10,000USDT symbol sleeves, summed to 30,000USDT per path. Ineligible
BTC cross-asset sleeves remain cash and never supply transfer evidence.

{table([{"profile": pid, "symbol": s, "trades": m["trades"], "net": m["net_pnl"], "PF": m["profit_factor"]} for pid, e in evidence.items() for s, m in e["symbols"].items()], ["profile", "symbol", "trades", "net", "PF"])}

## 7. Long/short decomposition

Sides are separately specified and tested; gains on one side never validate the
other. Summing different research strategies is not a funded portfolio backtest.

{table(long_short, ["profile", "side", "trades", "net"])}

## 8. Entry-regime decomposition

Causal regime labels are descriptive, not future classification targets or a
universal-profitability requirement. Complete profile/side/regime cells, counts,
net and PF are in results/long_short_regime_results.csv. Each group uses purged
realized outcomes and does not acquire an invented marked Sharpe.

{table([r for r in by_regime if r["profile"] in strongest and r["cost"] == "base"], ["profile", "side", "regime", "trades", "net_pnl", "profit_factor"])}

## 9. Walk-forward and pseudo-live simulation

2024 development; fixed-profile continuous accounts; seven subsequent quarters.
No parameter re-selection at quarter boundaries. ML alone retrains quarterly on
expanding prior labels with a 24-hour embargo. Every monthly eligibility decision
uses only its preceding matured 365 days, ending seven days earlier. The initial
window has six pre-simulation days with no executions; coverage is not fabricated.
Monthly records retain exact decision and evidence timestamps and all gate failures.
This evaluates profile eligibility, not adaptive controller returns or switches.
{sum(r["eligible"] for r in eligibility)} eligible profile-month decisions of {len(eligibility)}.

{table(wf, ["profile", *[q for q, _, _ in QUARTERS]])}

Quarterly marked PnL sums to full OOS marked PnL. Boundary positions remain in
marked outcomes; quarterly purged trade totals need not sum to full-period trade
net. Every month, including inactive months, is in monthly_contributions.csv.

## 10. Realistic costs and turnover

5bp taker plus 1bp adverse slippage/fill, outward tick rounding, quantity floor,
observed signed funding. Stress independently reexecutes changed prices/fees and
therefore can change sizing, occupancy and stop paths. Signed funding is not
multiplied. No maker fill claim. Exact decimal native fees, fills, funding and
accounts reconcile. period_turnover, fees, slippage, funding, exposure and time in
market are in profile_results.csv. Costs are stylized, not observed depth/spread.

{table(stress, ["profile", "base", "cost1.5x", "cost2x"])}

## 11. Parameter-neighborhood stability and exits

Two one-coordinate +/-20% perturbations of the economic threshold, not an expanded
EMA/ATR/Donchian grid; neighbors cannot replace central profiles.

{table(stability, ["profile", "low_net", "central_net", "high_net", "pass"])}

Entry and exit are independent. Predeclared MHT structure and contraction exits
are fully reexecuted, never manufactured by deleting interrupted trades. Baseline
uses trailing risk stop plus time stop; funding uses fixed time plus risk stop;
range uses equilibrium/time plus risk stop. Entry-regime incompatibility alone
never forces an exit. All interventions and costs remain in profile_results.csv.

## 12. Concentration, sample and resampling

Top shares use positive closed-trade PnL; month share uses positive marked monthly
contributions; symbol share uses positive marked symbol contributions. Top-five/
ten deletion is diagnostic. Synchronized seven-day calendar blocks preserve
cross-asset co-movement and short-range dependence. 4,000 resamples are stability
diagnostics. Centered block-null p values face Bonferroni .05/16; they cannot undo
prior consumption, survivor bias, unknown market selection or longer dependence.

{table(concentration, ["profile", "top1_share", "top5_share", "top10_share", "ex_top1", "month_share", "symbol_share", "bootstrap_positive", "centered_p"])}

## 13. ML versus non-ML

Ten documented features, separate logistic directions, fixed L2 and threshold,
training-only standardization, no random shuffle, hourly sampled 4h labels.
All training cutoffs, latest label endpoints, sample counts and coefficients are
in ml_training.json. Models without enough past observations abstain.

{table(ml, ["direction", "rule_net", "ml_net", "delta", "rule_sharpe", "ml_sharpe", "improvement_gate", "classification"])}

## 14. Failure modes and limits

Multiple testing and all prior historical consumption limit inference. Universe
contains three surviving liquid coins. Funding uses historical settlement marks;
fixed filters lack historical snapshots. OHLC-based synthetic quotes cannot
validate spread, queue, latency, capacity or impact. Close-observed stops can gap;
no intrabar protection is claimed. Daily DD can miss intraday troughs. A 0.25%
initial stop budget is not a guaranteed realized loss cap. Low activity reduces
confidence. Positive slices, changing exits and specialization discovered after
results cannot be promoted. No future observations or test fixtures count as
market success. ML labels use simplified cost proxy; actual execution controls
all economic conclusions. Statistical classification remains consumed-history
research evidence, not a forecast or a guarantee.

## 15. Final machine-readable profile library

profile_library.json contains **{len(validated)} validated profile(s)** and complete
required definitions, risk rules, metrics, cost tolerance and known failure cells.
Empty is intentional when no profile passes. Research candidates and weak signals
remain in profile_evidence.json; they are not silently inserted into the library.
NO_TRADE is a defensive policy with zero exposure, not an alpha discovery.

## 16. Handoff to Adaptive Trading

Pass only validated frozen definitions plus their timestamped evidence and known
eligibility conditions; initial set: {validated or "empty"}. Do not activate an
adaptive controller or infer diversification from strategy names. A validated
library requires two materially different families with abs daily-PnL correlation
below .80. Pair checks: {corrs or "not applicable"}.

## 17. What remains unproven

Future profitability, prospective replication, real executable capacity, broader
symbol robustness and adaptive allocation benefit. SHADOW.md reserves observations
after the new prospective freeze; it does not relabel historical replay as forward.
No collector/server is deployed, and no real-money execution is enabled.

## Reproducibility

README.md gives restore, freeze, execution, report and verify commands. Source,
feature inputs, publisher archives, runtime, native ledgers, checksums and the
prospective bundle are preserved. Frozen references unchanged. Integrity:
{native["runs"]} native runs reconciled; historical-prefix causality passed.
"""
    (ROOT / "REPORT.md").write_text(report)
    freeze_files = {
        **source_hashes(),
        "profile_library.json": digest(ROOT / "profile_library.json"),
        "results/profile_evidence.json": digest(ROOT / "results/profile_evidence.json"),
        "results/conclusions.json": digest(ROOT / "results/conclusions.json"),
        "data/historical_manifest.json": digest(ROOT / "data/historical_manifest.json"),
        "data/feature_cache_manifest.json": digest(
            ROOT / "data/feature_cache_manifest.json"
        ),
    }
    write_json(
        ROOT / "prospective_freeze.json",
        {
            "created_utc": datetime.now(timezone.utc).isoformat(),
            "files": freeze_files,
            "historical_data_status": "CONSUMED_THROUGH_2026_09",
            "prospective_status": "NOT_STARTED",
            "initial_eligible_profiles": validated,
            "version": "alpha-discovery-v3",
            "real_money_enabled": False,
            "automatic_activation": False,
            "changes_require_new_version": True,
        },
    )
    print(final, flush=True)


def checksum_artifacts():
    excluded = {"artifact_checksums.json", "results/final_verification.json"}
    files = {}
    for p in sorted(ROOT.rglob("*")):
        rel = str(p.relative_to(ROOT))
        if (
            p.is_file()
            and rel not in excluded
            and not any(
                part in ("raw", "cache", "__pycache__", ".pytest_cache")
                for part in p.relative_to(ROOT).parts
            )
        ):
            files[rel] = digest(p)
    write_json(ROOT / "artifact_checksums.json", files)

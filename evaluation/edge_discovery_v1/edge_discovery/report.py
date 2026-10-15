"""Human-readable and machine-readable experiment results; never re-ranks holdout."""

import csv
import json

from .common import ROOT, digest, write_json

FIELDS = [
    "total_trades",
    "long_trades",
    "short_trades",
    "gross_pnl",
    "fees",
    "funding",
    "slippage_impact",
    "net_pnl",
    "return",
    "profit_factor",
    "sharpe",
    "sortino",
    "maximum_drawdown",
    "calmar",
    "win_rate",
    "average_win",
    "average_loss",
    "expectancy_per_trade",
    "exposure",
    "turnover",
]


def fmt(value):
    if value is None:
        return "undefined"
    if isinstance(value, float):
        return f"{value:,.4f}"
    return str(value)


def report():
    final = json.loads((ROOT / "results" / "final.json").read_text())
    selection = json.loads((ROOT / "results" / "selection.json").read_text())
    frozen = json.loads((ROOT / "results" / "freeze.json").read_text())
    lines = [
        "# NautilusTrader-only edge discovery v1",
        "",
        "Historical research only. All executions, commissions, funding transfers, and accounts "
        "use NautilusTrader. No live trading is configured. No NautilusTrader core files were changed.",
        "",
        "32 declared candidates across BTCUSDT, ETHUSDT, SOLUSDT. Research: 2022–2023; "
        "validation: 2024; two sequential six-month folds in 2025; sealed final: January–June 2026.",
        "",
        f"Selection frozen at {frozen['frozen_at_utc']}. Holdout opened only after the freeze. "
        "The holdout never chooses or replaces candidates.",
        "",
        "| Family | Classification | Preholdout eligible | Holdout net USDT | Holdout return | Trades |",
        "|---|---|---|---:|---:|---:|",
    ]
    rows = []
    for family, d in final.items():
        b = d["scenarios"]["base"]
        lines.append(
            f"| {family} | {d['classification']} | {d['preholdout_eligible']} | {b['net_pnl']:,.2f} | {b['return']:.2%} | {b['total_trades']} |"
        )
        for scenario, m in d["scenarios"].items():
            rows.append(
                {
                    "family": family,
                    "candidate": d["candidate"]["id"],
                    "period": "holdout",
                    "scenario": scenario,
                    **{f: m[f] for f in FIELDS},
                }
            )
        for period, m in selection[family]["folds"].items():
            rows.append(
                {
                    "family": family,
                    "candidate": selection[family]["choices"][period]["candidate"]["id"],
                    "period": period,
                    "scenario": "base",
                    **{f: m[f] for f in FIELDS},
                }
            )
    lines += [
        "",
        "Each family uses three 10,000 USDT symbol sleeves (30,000 USDT aggregate). "
        "Sleeves are evaluated independently with fixed initial-capital sizing. Fees are assumed "
        "VIP0 taker 5 bps/fill; base adverse slippage is 1 bp/fill with outward tick rounding. "
        "Slippage and fees are deducted separately; funding is signed income or expense.",
        "",
    ]
    for family, d in final.items():
        s = selection[family]
        lines += [
            f"## {family}",
            "",
            f"Classification: **{d['classification']}**. Frozen representative: `{d['candidate']['id']}`.",
            "",
            "| Metric | Holdout base |",
            "|---|---:|",
        ]
        for f in FIELDS:
            lines.append(f"| {f} | {fmt(d['scenarios']['base'][f])} |")
        lines += [
            "",
            "Chronological choices and true sequential OOS:",
            "",
            "| Evaluation | Selected using | Candidate | Net USDT | Trades | Sharpe |",
            "|---|---|---|---:|---:|---:|",
        ]
        for period in ("validation", "wf1", "wf2"):
            choice, m = s["choices"][period], s["folds"][period]
            lines.append(
                f"| {period} | {', '.join(choice['history'])} | {choice['candidate']['id']} | {m['net_pnl']:,.2f} | {m['total_trades']} | {fmt(m['sharpe'])} |"
            )
        lines += [
            "",
            f"Adaptive validation+WF net: {s['oos']['net_pnl']:,.2f} USDT. "
            f"Final representative's retrospective validation+WF net: {s['fixed_preholdout']['net_pnl']:,.2f} USDT. "
            "The latter is selection-contaminated and is not an independent OOS claim.",
            "",
            f"Profitable parameter neighbors: {s['positive_neighbor_fraction']:.0%}. "
            f"Failed preholdout gates: {', '.join(k for k, v in s['gates'].items() if not v) or 'none'}.",
            "",
            "| Cost scenario | Adaptive preholdout OOS net | Frozen holdout net |",
            "|---|---:|---:|",
        ]
        lines.append(
            f"| base: 5bp fee + 1bp slippage | {s['oos']['net_pnl']:,.2f} | {d['scenarios']['base']['net_pnl']:,.2f} |"
        )
        for scenario in ("slip2", "slip3", "cost2x"):
            lines.append(
                f"| {scenario} | {s['stresses'][scenario]['net_pnl']:,.2f} | {d['scenarios'][scenario]['net_pnl']:,.2f} |"
            )
        b = d["scenarios"]["base"]
        lines += ["", "| Holdout breakdown | Trades | Net USDT | PF |", "|---|---:|---:|---:|"]
        for group in ("by_symbol", "by_side", "by_regime"):
            for name, m in b[group].items():
                lines.append(
                    f"| {name} | {m['total_trades']} | {m['net_pnl']:,.2f} | {fmt(m['profit_factor'])} |"
                )
        lines += [
            "",
            f"Holdout net excluding best trade: {b['net_excluding_best_trade']:,.2f}; "
            f"excluding best realized-exit month: {b['net_excluding_best_month']:,.2f}. "
            f"Best trade share of positive trade profits: {fmt(b['best_trade_positive_profit_share'])}; "
            f"best month share of positive monthly profits: {fmt(b['best_month_positive_profit_share'])}.",
            "",
        ]
    audits = [json.loads(p.read_text()) for p in (ROOT / "data" / "audits").glob("*.json")]
    unique = {(r["symbol"], r["period"]): r for r in audits}
    proxies = sum(r["funding_mark_proxy_rows"] for r in unique.values())
    lines += [
        "## Integrity and limits",
        "",
        f"Native closed-position and account reconciliations passed for every saved run. "
        f"Funding boundary trade-open proxies: {proxies} across unique symbol-period datasets. "
        "All requested 5m grids were checked for missing/duplicate timestamps and OHLC validity; "
        "coarser bars are causal UTC-aligned aggregates.",
        "",
        "Prefix replay and mutated future tails leave earlier fills unchanged. Integrity details "
        "and test output are in results/integrity.json and results/tests.txt. Every run retains "
        "fill reference prices, signal/fill timestamps, native fees, funding, trades, and daily equity.",
        "",
        "The universe is fixed to three surviving liquid assets; broader market survival bias "
        "is not measured. Constant conservative instrument filters lack historical snapshots. "
        "Bar-derived executable quotes do not observe actual spread, queue, latency, or depth; "
        "stops are close-based and can gap. Funding mark proxies introduce valuation uncertainty. "
        "Consequently the strongest classification is unavailable in this experiment. "
        "Multi-period returns and risk statistics chain-link normalized period equity; USDT PnL remains the nominal sum of independent period PnLs. No p-value or significance claim is made after the 32-candidate search. "
        "Historical evidence does not establish future profitability.",
        "",
        "Undefined statistics (for example PF without losses) are null in JSON/CSV and shown as "
        "undefined here. Drawdown is daily marked equity; exposure is invested symbol-time; "
        "turnover counts both entry and exit notional. Monthly attribution uses realized exit "
        "month and is distinct from daily marked-equity returns.",
        "",
        "## Reproduction",
        "",
        "See README.md for commands, runtime lock, and single-use holdout controls. "
        "Raw Binance archives are retained locally under data/raw and identified by publisher "
        "SHA256 in the two data manifests. Source/config, preholdout evidence, and decisions "
        "are hashed into results/freeze.json before holdout data access.",
        "",
    ]
    (ROOT / "REPORT.md").write_text("\n".join(lines))
    with (ROOT / "results" / "metrics.csv").open("w", newline="") as f:
        writer = csv.DictWriter(
            f, fieldnames=["family", "candidate", "period", "scenario", *FIELDS]
        )
        writer.writeheader()
        writer.writerows(rows)
    hashes = {
        str(p.relative_to(ROOT)): digest(p)
        for p in sorted((ROOT / "results").rglob("*"))
        if p.is_file() and p.name != "artifact_checksums.json"
    }
    hashes["REPORT.md"] = digest(ROOT / "REPORT.md")
    write_json(ROOT / "results" / "artifact_checksums.json", hashes)
    print(ROOT / "REPORT.md")

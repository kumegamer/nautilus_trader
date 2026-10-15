"""Fail-closed deterministic classifications; research proposals cannot set gates."""

import pandas as pd

from .analysis import bootstrap, concentration, summary
from .common import DAY, config, ns
from .metrics import selected_trades, trade_metrics
from .profiles import BASE, library

START = ns("2025-01-01")
END = ns("2026-10-01")
DEVELOPMENT = ns("2024-01-01")
QUARTERS = tuple(
    (str(q), ns(str(q.start_time.date())), ns(str((q + 1).start_time.date())))
    for q in pd.period_range("2025Q1", "2026Q3", freq="Q")
)


def pick(runs, pid, cost="base"):
    return [runs[(pid, s, cost)] for s in config()["symbols"]]


def classify(runs, integrity):
    out = {}
    for p in [*BASE, library()["ML_LONG"], library()["ML_SHORT"]]:
        base = pick(runs, p.id)
        m = summary(base, START, END)
        costs = {
            c: summary(pick(runs, p.id, c), START, END) for c in config()["scenarios"]
        }
        quarters = {q: summary(base, a, b) for q, a, b in QUARTERS}
        b = bootstrap(base, START, END)
        neighbors = {}
        if p.role == "primary":
            for suffix in ("LOW", "HIGH"):
                neighbors[suffix] = {
                    c: summary(pick(runs, p.id + "_" + suffix, c), START, END)
                    for c in config()["scenarios"]
                }
        positive_neighbors = sum(
            v["base"]["net_pnl"] > 0 and v["base"]["purged_trade_net"] > 0
            for v in neighbors.values()
        )
        stable_2x = any(
            v["cost2x"]["net_pnl"] > 0 and v["cost2x"]["purged_trade_net"] > 0
            for v in neighbors.values()
        )
        symbols = {
            s: summary([r for r in base if r["symbol"] == s], START, END)
            for s in config()["symbols"]
        }
        eligible = {s: v for s, v in symbols.items() if s in p.symbols}
        positive_symbols = [v["net_pnl"] for v in eligible.values() if v["net_pnl"] > 0]
        symbol_share = (
            max(positive_symbols) / sum(positive_symbols) if positive_symbols else None
        )
        yearly = {
            str(y): len(
                selected_trades(base, ns(f"{y}-01-01"), min(END, ns(f"{y + 1}-01-01")))
            )
            for y in (2025, 2026)
        }
        cost_ok = all(
            v["net_pnl"] > 0 and v["purged_trade_net"] > 0 for v in costs.values()
        )
        gates = {
            "integrity": integrity,
            "economics": m["net_pnl"] > 0
            and m["purged_trade_net"] > 0
            and (m["profit_factor"] or 0) >= 1.10,
            "sample": m["trades"] >= 100
            and min(yearly.values()) >= 20
            and sum(v["trades"] >= 10 for v in quarters.values()) >= 4,
            "chronology": sum(v["net_pnl"] > 0 for v in quarters.values()) >= 4
            and quarters["2026Q3"]["net_pnl"] > 0,
            "risk": m["maximum_drawdown"] <= 0.15,
            "cost": cost_ok,
            "stability": positive_neighbors == 2 and stable_2x,
            "resampling": b["probability_positive"] >= 0.95,
            "multiple_testing": b["centered_p"] <= 0.05 / 16,
            "concentration": concentration(m),
            "symbol_transfer": sum(
                v["net_pnl"] > 0 and v["trades"] >= 20 for v in eligible.values()
            )
            >= 2
            and (symbol_share or 1) <= 0.75,
        }
        if p.role == "ml":
            baseline = summary(
                pick(runs, "RAW_LONG" if p.side > 0 else "RAW_SHORT"), START, END
            )
            increments = [
                v["net_pnl"]
                - summary(pick(runs, "RAW_LONG" if p.side > 0 else "RAW_SHORT"), a, z)[
                    "net_pnl"
                ]
                for (_, a, z), v in zip(QUARTERS, quarters.values())
            ]
            gates["ml_improvement"] = (
                m["net_pnl"] > baseline["net_pnl"]
                and (m["sharpe"] or -1e9) > (baseline["sharpe"] or -1e9)
                and sum(x > 0 for x in increments) >= 4
            )
        candidate = (
            integrity
            and cost_ok
            and m["trades"] >= 60
            and gates["chronology"]
            and gates["risk"]
            and positive_neighbors >= 1
            and b["probability_positive"] >= 0.8
        )
        weak = (
            integrity
            and m["net_pnl"] > 0
            and m["purged_trade_net"] > 0
            and m["trades"] >= 20
        )
        status = (
            "VALIDATED_PROFILE"
            if all(gates.values())
            else "RESEARCH_CANDIDATE"
            if candidate
            else "WEAK_SIGNAL"
            if weak
            else "REJECTED"
        )
        if p.role == "ml" and not gates["ml_improvement"]:
            status = "REJECTED"
        out[p.id] = {
            "classification": status,
            "gates": gates,
            "failures": [k for k, v in gates.items() if not v],
            "metrics": m,
            "costs": costs,
            "quarters": quarters,
            "neighbors": neighbors,
            "symbols": symbols,
            "symbol_positive_contribution_share": symbol_share,
            "yearly_trade_counts": yearly,
            "bootstrap": b,
        }
    return out


def monthly_eligibility(runs):
    rows = []
    for decision in pd.date_range("2025-01-01", "2026-10-01", freq="MS", tz="UTC"):
        t = decision.as_unit("ns").value
        end = t - 7 * DAY
        begin = end - 365 * DAY
        for p in BASE:
            base = pick(runs, p.id)
            m = summary(base, begin, end)
            thirds = [
                trade_metrics(
                    selected_trades(
                        base,
                        begin + i * (end - begin) // 3,
                        begin + (i + 1) * (end - begin) // 3,
                    )
                )["net_pnl"]
                for i in range(3)
            ]
            costs = {
                c: summary(pick(runs, p.id, c), begin, end)
                for c in config()["scenarios"]
            }
            neighbors = {
                s: summary(pick(runs, p.id + "_" + s), begin, end)["purged_trade_net"]
                for s in ("LOW", "HIGH")
            }
            boot = bootstrap(base, begin, end)
            gates = {
                "economics": m["net_pnl"] > 0
                and m["purged_trade_net"] > 0
                and (m["profit_factor"] or 0) >= 1.1,
                "sample": m["trades"] >= 60,
                "chronology": sum(x > 0 for x in thirds) >= 2 and thirds[-1] > 0,
                "cost": all(
                    v["net_pnl"] > 0 and v["purged_trade_net"] > 0
                    for v in costs.values()
                ),
                "risk": m["maximum_drawdown"] <= 0.15,
                "concentration": concentration(m),
                "stability": any(v > 0 for v in neighbors.values()),
                "resampling": boot["probability_positive"] >= 0.8,
            }
            rows.append(
                {
                    "decision_ns": int(t),
                    "available_ns": int(t),
                    "evidence_end_ns": int(end),
                    "window_start_ns": int(begin),
                    "profile": p.id,
                    "eligible": all(gates.values()),
                    "failures": [k for k, v in gates.items() if not v],
                    "gates": gates,
                    "third_net": thirds,
                    "metrics": m,
                    "neighbors": neighbors,
                    "bootstrap": boot,
                }
            )
    return rows

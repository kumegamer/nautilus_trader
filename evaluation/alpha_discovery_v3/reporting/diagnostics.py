"""Post-experiment diagnostics only; no candidate generation or promotion authority."""

import json

import pandas as pd
from alpha.common import ROOT, config, write_json
from alpha.evaluate import END, START, pick
from alpha.metrics import portfolio_daily
from alpha.profiles import BASE, library
from alpha.workflow import load_runs, verify_freeze


def enrich_registry():
    """Expose the exact already-frozen input dependencies, without changing rules."""
    from alpha.ml import FEATURES

    shared = ["close", "atr", "annual_vol", "volume"]
    families = {
        "multi_horizon_trend": [
            "mom_240",
            "mom_60",
            "efficiency",
            "ret_15",
            "ret_5",
            "pullback",
            "vol_ratio",
        ],
        "breakout_quality": [
            "high_prev",
            "low_prev",
            "mom_240",
            "mom_60",
            "volume_ratio",
            "range_ratio",
            "taker_ratio",
            "vol_percentile",
            "false_frequency",
        ],
        "cross_asset_strength": [
            "relative_strength",
            "btc_mom",
            "mom_60",
            "ret_15",
            "ret_5",
            "btc_correlation",
            "efficiency",
        ],
        "funding_crowding": [
            "funding",
            "funding_age_hours",
            "ret_15",
            "ret_5",
            "ret_1h",
            "vol_ratio",
        ],
        "liquidity_reversal": [
            "efficiency",
            "vol_ratio",
            "shock_prev",
            "ret_15",
            "ret_5",
            "deviation",
            "volume_ratio",
        ],
        "raw_breakout": ["high_prev", "low_prev"],
        "logistic_quality": ["high_prev", "low_prev", *FEATURES],
    }
    profiles = library()
    rows = json.loads((ROOT / "results/experiments.json").read_text())
    for row in rows:
        p = profiles[row["hypothesis_id"]]
        row["parameters"] = p.definition()
        if p.family == "volatility_regime":
            entry = (
                [
                    "compression_recent",
                    "range_ratio",
                    "high_12h",
                    "mom_240",
                    "volume_ratio",
                ]
                if p.side > 0
                else [
                    "vol_ratio",
                    "efficiency",
                    "mom_240",
                    "mom_60",
                    "low_12h",
                    "taker_ratio",
                ]
            )
        else:
            entry = families[p.family]
        if p.family == "logistic_quality":
            entry = [*entry, f"ml_{p.side}"]
        exits = {
            "equilibrium": ["equilibrium"],
            "structure": ["exit_high", "exit_low"],
            "contraction": ["vol_ratio"],
        }.get(p.exit, [])
        row["features"] = {
            "entry": sorted(set(entry)),
            "exit": ["close", "atr", *exits],
            "risk": shared,
            "availability_dictionary": "FEATURES.md",
            "readiness": [
                "vol_percentile",
                "mom_240",
                "volume_ratio",
                "taker_ratio",
                "funding",
            ],
        }
        row["execution_parameters"] = {
            k: config()[k]
            for k in (
                "capital_per_symbol",
                "risk_per_trade",
                "notional_cap_fraction",
                "minimum_notional",
                "participation_cap",
                "taker_fee",
                "scenarios",
                "instrument_specs",
            )
        }
    write_json(ROOT / "results/experiments.json", rows)


def main():
    verify_freeze()
    enrich_registry()
    runs = load_runs()
    series = {}
    for p in BASE:
        daily = portfolio_daily(pick(runs, p.id), START, END)
        series[p.id] = pd.Series({t: e for t, e in daily}).diff() / 30000
    pd.DataFrame(series).corr().to_csv(ROOT / "results/primary_daily_correlations.csv")
    rows = []
    for p in BASE:
        for cost in config()["scenarios"]:
            for suffix in ("LOW", "HIGH"):
                common = 0
                union = 0
                identical = True
                for s in p.symbols:

                    def signature(pid, symbol=s, scenario=cost):
                        return {
                            tuple(
                                f[k]
                                for k in ("ts_ns", "side", "quantity", "price", "fee")
                            )
                            for f in runs[(pid, symbol, scenario)]["fills"]
                            if START <= f["ts_ns"] < END
                        }

                    a, b = signature(p.id), signature(p.id + "_" + suffix)
                    common += len(a & b)
                    union += len(a | b)
                    identical &= a == b
                rows.append(
                    {
                        "profile": p.id,
                        "cost": cost,
                        "neighbor": suffix,
                        "identical_OOS_fill_path": identical,
                        "fill_jaccard": common / union if union else None,
                        "note": "Equal paths show local insensitivity, not independent replication.",
                    }
                )
    pd.DataFrame(rows).to_csv(ROOT / "results/neighbor_path_changes.csv", index=False)
    evidence = json.loads((ROOT / "results/profile_evidence.json").read_text())
    lines = [
        "# Research interpretation",
        "",
        "All observations below are retrospective on consumed history. No next-version proposal",
        "is executed, and no additional strategy is admitted by this diagnostic script.",
        "",
    ]
    for p in BASE:
        e = evidence[p.id]
        m = e["metrics"]
        positive = sum(q["net_pnl"] > 0 for q in e["quarters"].values())
        cost = e["costs"]["cost2x"]["net_pnl"]
        gross = m["purged_trade_net"] + m["fees"] + m["slippage"] - m["funding"]
        friction = m["fees"] + m["slippage"]
        diagnosis = (
            "Insufficient activity to assess a repeatable edge; zero exposure is not a loss estimate."
            if m["trades"] < 20
            else "The price mechanism itself lost before execution friction."
            if gross < 0
            else "Execution friction exceeded the positive price mechanism."
            if m["purged_trade_net"] <= 0
            else "Positive aggregate economics still need the failed gates listed below."
        )
        lines += [
            f"## {p.id}: {e['classification']}",
            "",
            (
                f"OOS marked PnL {m['net_pnl']:.2f} USDT; 2x-cost PnL {cost:.2f}; "
                f"{m['trades']} purged trades; {positive}/7 positive quarters."
            ),
            (
                f"Purged reference-price gross {gross:.2f}, fees plus slippage {friction:.2f}, "
                f"signed funding {m['funding']:.2f} USDT. {diagnosis}"
            ),
            "Unpassed gates: " + ", ".join(e["failures"]) + ".",
            "",
        ]
    lines += [
        "## Stability and diversity",
        "",
        "primary_daily_correlations.csv compares every central economic profile on synchronized",
        "daily marked PnL. Different family names alone do not establish different payoff sources.",
        "neighbor_path_changes.csv reports when a changed threshold leaves the entire eligible",
        "symbol fill path unchanged. Such a plateau is not independent confirmation. No neighbor",
        "is substituted for a central hypothesis. Repeated cost runs are the same market sample.",
        "",
        "## Next experiment proposals, currently inert",
        "",
        "For sparse funding and high-volatility hypotheses, collect unchanged forward observations",
        "rather than relax sample gates. For negative gross mechanisms, reconsider the economic",
        "entry hypothesis in a new version; exit optimization cannot establish missing entry alpha.",
        "For positive gross but negative net outcomes, a new version should test an economically",
        "justified lower-turnover mechanism or actual executable spread/depth evidence, without",
        "assuming maker fills. For unstable temporal or symbol transfer, request a new independent",
        "period before choosing a specialized cell. Every such change needs a new finite protocol.",
        "",
        "Only the frozen validated library may be handed to future adaptive research. Neither these",
        "proposals nor attractive hindsight slices activate trading or modify frozen rules.",
    ]
    (ROOT / "RESEARCH_INTERPRETATION.md").write_text("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()

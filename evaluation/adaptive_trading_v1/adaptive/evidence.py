"""Point-in-time evidence assembled from predeclared native historical experiments."""

from itertools import pairwise

import numpy as np

from .common import DAY, config, ns
from .performance import trade_metrics
from .profiles import library


class EvidenceProvider:
    def __init__(self, runs):
        self.runs = runs
        self.cfg = config()
        self.profiles = library()

    def __call__(self, profile, timestamp):
        # Daily snapshots and seven-day embargo bound repeated research computation
        cutoff = timestamp - 7 * DAY
        begin = ns(self.cfg["periods"]["research"][0])
        if cutoff - begin < 365 * DAY:
            return None
        duration = cutoff - begin
        bounds = [
            begin,
            begin + int(duration * 0.4),
            begin + int(duration * 0.6),
            begin + int(duration * 0.7),
            begin + int(duration * 0.8),
            cutoff,
        ]
        known = [r for r in self.runs if r["candidate"] == profile]

        def selected(scenario, lo, hi, candidate=profile):
            return [
                t
                for r in self.runs
                if r["candidate"] == candidate and r["scenario"] == scenario
                for t in r["trades"]
                if lo <= t["entry_ns"] < t["exit_ns"] < hi
            ]

        validation = selected("base", bounds[1], bounds[2])
        wf = [
            selected("base", bounds[2], bounds[3]),
            selected("base", bounds[3], bounds[4]),
        ]
        sealed = selected("base", bounds[4], bounds[5])
        all_oos = validation + wf[0] + wf[1] + sealed
        metrics = trade_metrics(all_oos, 30000)
        stressed = selected("cost2x", bounds[1], cutoff)
        stressed = [
            t
            for t in stressed
            if any(
                lo <= t["entry_ns"] < t["exit_ns"] < hi
                for lo, hi in pairwise(bounds[1:])
            )
        ]
        p = self.profiles[profile]
        central = next(
            (
                k
                for k, v in self.profiles.items()
                if v.family == p.family and "_" not in k and k != "NO_TRADE"
            ),
            None,
        )
        neighbors = [central + "_STOP", central + "_WINDOW"] if central else []
        neighbors_positive = [
            sum(float(t["net_pnl"]) for t in selected("base", bounds[1], cutoff, n)) > 0
            for n in neighbors
        ]
        by_symbol = {
            s: trade_metrics([t for t in all_oos if t["symbol"] == s])
            for s in self.cfg["symbols"]
        }

        def positive(trades):
            return len(trades) >= 10 and sum(float(t["net_pnl"]) for t in trades) > 0

        policy = self.cfg["policy"]
        gates = {
            "sample": len(all_oos) >= policy["minimum_trades"],
            "validation_positive": positive(validation),
            "walk_forward": all(positive(fold) for fold in wf),
            "sealed_oos": positive(sealed),
            "cost_stress": positive(stressed),
            "neighbors": bool(neighbors_positive)
            and sum(neighbors_positive) / len(neighbors_positive)
            >= policy["minimum_positive_neighbor_fraction"],
            "symbols": sum(
                m["net_pnl"] > 0
                and m["number_of_trades"] >= policy["minimum_symbol_trades"]
                for m in by_symbol.values()
            )
            >= policy["minimum_positive_symbols"],
            "drawdown": metrics["maximum_drawdown"] <= policy["maximum_drawdown"],
            "concentration": (
                metrics["top10_positive_profit_share"] is not None
                and metrics["top10_positive_profit_share"]
                <= policy["maximum_top10_positive_profit_share"]
                and metrics["net_excluding_top10"] > 0
            ),
        }
        # Marked drawdown includes intratrade losses; only known daily closes contribute
        changes = {}
        for run in known:
            if run["scenario"] != "base":
                continue
            previous = 10000.0
            for t, equity in run.get("daily", []):
                if t >= cutoff:
                    break
                if t >= begin:
                    changes[t] = changes.get(t, 0.0) + float(equity) - previous
                previous = float(equity)
        if changes:
            curve = np.r_[
                30000.0, 30000 + np.cumsum([v for _, v in sorted(changes.items())])
            ]
            marked_drawdown = float(np.max(1 - curve / np.maximum.accumulate(curve)))
            metrics["marked_maximum_drawdown"] = marked_drawdown
            gates["drawdown"] &= marked_drawdown <= policy["maximum_drawdown"]
        gates["profit_factor"] = (
            metrics["profit_factor"] is not None
            and metrics["profit_factor"] >= policy["minimum_profit_factor"]
        )
        by_regime = {
            regime: trade_metrics([t for t in all_oos if t["regime"] == regime])
            for regime in p.compatible_regimes
        }
        gates["regimes"] = bool(by_regime) and all(
            m["number_of_trades"] >= 10 and m["net_pnl"] > 0 for m in by_regime.values()
        )
        sides = ([1] if p.allow_long else []) + ([-1] if p.allow_short else [])
        by_side = {
            str(side): trade_metrics([t for t in all_oos if t["side"] == side])
            for side in sides
        }
        gates["sides"] = bool(by_side) and all(
            m["number_of_trades"] >= 10 and m["net_pnl"] > 0 for m in by_side.values()
        )
        r_values = np.array(
            [float(t["net_pnl"]) / float(t["initial_risk"]) for t in all_oos]
        )
        mean = float(r_values.mean()) if len(r_values) else 0
        se = (
            float(r_values.std(ddof=1) / np.sqrt(len(r_values)))
            if len(r_values) > 1
            else 0
        )
        return {
            "end_ns": cutoff,
            "requested_ns": timestamp,
            "profile": profile,
            "gates": gates,
            "bounds_ns": bounds,
            "purge": "entry and exit must both fall strictly within one chronological split",
            "metrics": metrics,
            "by_symbol": by_symbol,
            "by_regime": by_regime,
            "by_side": by_side,
            "validation": trade_metrics(validation),
            "walk_forward": [trade_metrics(t) for t in wf],
            "internal_sealed": trade_metrics(sealed),
            "cost2x": trade_metrics(stressed),
            "neighbors": dict(zip(neighbors, neighbors_positive)),
            "expected": {
                "expectancy_lower": mean - 1.96 * se,
                "expectancy_upper": mean + 1.96 * se,
            },
            "experiment_count": len(
                [r for r in known if ns(self.cfg["periods"][r["period"]][0]) < cutoff]
            ),
            "note": "All periods before July 2026 are reused developmental evidence",
        }

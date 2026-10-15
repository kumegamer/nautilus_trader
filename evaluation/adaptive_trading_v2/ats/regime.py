"""Causal raw labels, hourly hysteresis, persistence and stable regime history."""

from .common import HOUR, config


def raw_v1(f):
    if not f.get("ready", False):
        return "UNKNOWN", 0.0
    v, e = f["vol_ratio_60"], f["efficiency_60"]
    if v > 3 or abs(f["momentum_15"]) > 0.08 and v > 1.5:
        return "MARKET_STRESS", min(0.95, 0.6 + 0.1 * v)
    if v > 1.8:
        return "VOLATILITY_EXPANSION", min(0.95, 0.55 + (v - 1.8) * 0.2)
    if v < 0.6:
        return "VOLATILITY_COMPRESSION", min(0.95, 0.55 + (0.6 - v) * 0.5)
    trending = e > 0.3 and abs(f["slope_60"]) > 0.02
    return ("TREND" if trending else "RANGE") + (
        "_HIGH_VOL" if v > 1.2 else "_LOW_VOL"
    ), min(0.9, 0.55 + abs(e - 0.3))


class RegimeEngine:
    def __init__(self):
        self.regime = "UNKNOWN"
        self.started = None
        self.candidate = "UNKNOWN"
        self.persistence = 0
        self.confidence = 0.0
        self.transitions = []

    def update(self, timestamp, f):
        raw, raw_confidence = raw_v1(f)
        if self.started is None:
            self.started = timestamp
        if f.get("new_hour", False) or raw == "MARKET_STRESS":
            candidate = raw
            if raw not in ("MARKET_STRESS", "UNKNOWN"):
                v, e, slope = f["vol_ratio_60"], f["efficiency_60"], abs(f["slope_60"])
                if v > (1.6 if self.regime == "VOLATILITY_EXPANSION" else 1.8):
                    candidate = "VOLATILITY_EXPANSION"
                elif v < (0.7 if self.regime == "VOLATILITY_COMPRESSION" else 0.6):
                    candidate = "VOLATILITY_COMPRESSION"
                else:
                    trend = e > (
                        0.24 if self.regime.startswith("TREND") else 0.32
                    ) and slope > (0.015 if self.regime.startswith("TREND") else 0.02)
                    high = v > (1.10 if self.regime.endswith("HIGH_VOL") else 1.25)
                    candidate = ("TREND" if trend else "RANGE") + (
                        "_HIGH_VOL" if high else "_LOW_VOL"
                    )
            self.persistence = (
                self.persistence + int(f.get("new_hour", False))
                if candidate == self.candidate
                else 1
            )
            self.candidate = candidate
            self.confidence = raw_confidence if candidate == raw else 0.55
            rules = config()["regime"]
            mature = self.persistence >= rules["persistence_hours"]
            dwell = timestamp - self.started >= rules["minimum_dwell_hours"] * HOUR
            if candidate != self.regime and (
                candidate == "MARKET_STRESS" or mature and dwell
            ):
                self.transitions.append(
                    {
                        "timestamp": timestamp,
                        "old": self.regime,
                        "new": candidate,
                        "confidence": self.confidence,
                        "persistence_hours": self.persistence,
                        "previous_duration_ns": timestamp - self.started,
                    }
                )
                self.regime, self.started = candidate, timestamp
        entry_confidence = self.confidence if self.candidate == self.regime else 0.0
        return {
            "regime": self.regime,
            "confidence": entry_confidence,
            "transition_confidence": self.confidence,
            "candidate": self.candidate,
            "persistence_hours": self.persistence,
            "dwell_ns": timestamp - self.started,
            "raw_regime": raw,
            "raw_confidence": raw_confidence,
        }


def attach_regimes(frame):
    import pandas as pd

    engine = RegimeEngine()
    states = [
        engine.update(int(f["available_ns"]), f) for f in frame.to_dict("records")
    ]
    return pd.concat(
        [frame.reset_index(drop=True), pd.DataFrame(states)], axis=1
    ), engine.transitions


def invalidated(policy, p, f, incompatible_hours):
    if policy == "ENTRY_ONLY":
        return False
    if policy == "V1_IMMEDIATE":
        return f["raw_regime"] not in p.compatible_regimes
    if policy == "PERSIST_4":
        return incompatible_hours >= 4
    if policy == "CONFIDENT_80":
        return (
            f["regime"] not in p.compatible_regimes
            and f["transition_confidence"] >= 0.8
            and f["persistence_hours"] >= 2
        )
    raise ValueError(f"Unknown exit policy: {policy}")

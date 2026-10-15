"""Predeclared economic hypotheses; neighbors and interventions cannot be promoted."""

from dataclasses import asdict, dataclass, replace


@dataclass(frozen=True)
class Profile:
    id: str
    family: str
    side: int
    threshold: float
    exit: str = "trailing"
    max_age: int = 96
    stop_atr: float = 3.0
    role: str = "primary"
    parent: str | None = None
    symbols: tuple = ("BTCUSDT", "ETHUSDT", "SOLUSDT")
    minutes: int = 15
    lookback: int = 96

    def definition(self):
        return asdict(self)


BASE = (
    Profile("MHT_LONG", "multi_horizon_trend", 1, 0.5),
    Profile("MHT_SHORT", "multi_horizon_trend", -1, 0.7, max_age=64),
    Profile("BQ_LONG", "breakout_quality", 1, 1.3),
    Profile("BQ_SHORT", "breakout_quality", -1, 1.5, max_age=64),
    Profile(
        "CROSS_LONG", "cross_asset_strength", 1, 0.01, symbols=("ETHUSDT", "SOLUSDT")
    ),
    Profile(
        "CROSS_SHORT",
        "cross_asset_strength",
        -1,
        0.015,
        symbols=("ETHUSDT", "SOLUSDT"),
        max_age=64,
    ),
    Profile("FUND_LONG", "funding_crowding", 1, 0.0001, exit="time", max_age=32),
    Profile("FUND_SHORT", "funding_crowding", -1, 0.0003, exit="time", max_age=32),
    Profile("VOL_LONG", "volatility_regime", 1, 0.7),
    Profile("VOL_SHORT", "volatility_regime", -1, 1.4, max_age=64),
    Profile("RANGE_LONG", "liquidity_reversal", 1, 2.0, exit="equilibrium", max_age=16),
    Profile(
        "RANGE_SHORT", "liquidity_reversal", -1, 2.5, exit="equilibrium", max_age=12
    ),
)
CONTROLS = (
    Profile("RAW_LONG", "raw_breakout", 1, 0, role="control"),
    Profile("RAW_SHORT", "raw_breakout", -1, 0, role="control", max_age=64),
    Profile("ML_LONG", "logistic_quality", 1, 0.55, role="ml"),
    Profile("ML_SHORT", "logistic_quality", -1, 0.55, role="ml", max_age=64),
)


def library():
    out = [*BASE, *CONTROLS]
    for p in BASE:
        for scale, name in ((0.8, "LOW"), (1.2, "HIGH")):
            out.append(
                replace(
                    p,
                    id=p.id + "_" + name,
                    threshold=p.threshold * scale,
                    role="neighbor",
                    parent=p.id,
                )
            )
    for p in BASE[:2]:
        for policy in ("structure", "contraction"):
            out.append(
                replace(
                    p,
                    id=p.id + "_" + policy.upper(),
                    exit=policy,
                    role="exit_diagnostic",
                    parent=p.id,
                )
            )
    return {p.id: p for p in out}


def signal(p, f, symbol):
    if not f["ready"] or symbol not in p.symbols:
        return False
    s, q, fam = p.side, p.threshold, p.family
    trend = s * f["mom_240"] > 0 and s * f["mom_60"] > 0
    resume = s * f["ret_15"] > 0 and s * f["ret_5"] > 0
    breakout = f["close"] > f["high_prev"] if s > 0 else f["close"] < f["low_prev"]
    if fam == "multi_horizon_trend":
        return (
            trend
            and f["efficiency"] > 0.25
            and resume
            and s * f["pullback"] < -q
            and f["vol_ratio"] < 2.5
        )
    if fam in ("raw_breakout", "logistic_quality", "breakout_quality"):
        if not breakout:
            return False
        if fam == "raw_breakout":
            return True
        if fam == "logistic_quality":
            return f[f"ml_{s}"] >= q
        return (
            trend
            and f["volume_ratio"] > q
            and f["range_ratio"] > 1.2
            and s * (f["taker_ratio"] - 0.5) > (0.04 if s > 0 else 0.06)
            and 0.3 < f["vol_percentile"] < 0.95
            and f["false_frequency"] < 0.10
        )
    if fam == "cross_asset_strength":
        return (
            s * f["relative_strength"] > q
            and s * f["btc_mom"] > 0
            and s * f["mom_60"] > 0
            and resume
            and f["btc_correlation"] > 0.3
            and f["efficiency"] > 0.2
        )
    if fam == "funding_crowding":
        crowded = f["funding"] < -q if s > 0 else f["funding"] > q
        return (
            crowded
            and f["funding_age_hours"] < 12
            and resume
            and s * f["ret_1h"] > 0
            and f["vol_ratio"] < 2.5
        )
    if fam == "volatility_regime":
        if s > 0:
            return (
                f["compression_recent"] < q
                and f["range_ratio"] > 1.5
                and f["close"] > f["high_12h"]
                and f["mom_240"] > 0
                and f["volume_ratio"] > 1.2
            )
        return (
            f["vol_ratio"] > q
            and f["efficiency"] > 0.35
            and trend
            and f["close"] < f["low_12h"]
            and f["taker_ratio"] < 0.48
        )
    if fam == "liquidity_reversal":
        return (
            f["efficiency"] < 0.2
            and f["vol_ratio"] < 1.5
            and s * f["shock_prev"] < -q
            and resume
            and s * f["deviation"] < -1
            and f["volume_ratio"] > 0.8
        )
    raise ValueError(f"Unknown family {fam}")

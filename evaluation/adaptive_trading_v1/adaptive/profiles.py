"""Immutable economically motivated profiles, never mutable optimizer outputs."""

from dataclasses import asdict, dataclass, replace

REGIMES = (
    "TREND_LOW_VOL",
    "TREND_HIGH_VOL",
    "RANGE_LOW_VOL",
    "RANGE_HIGH_VOL",
    "VOLATILITY_EXPANSION",
    "VOLATILITY_COMPRESSION",
    "MARKET_STRESS",
    "UNKNOWN",
)


@dataclass(frozen=True)
class Profile:
    id: str
    family: str
    minutes: int = 60
    lookback: int = 48
    stop_atr: float = 2.0
    band_k: float = 2.5
    pullback_atr: float = 1.0
    compression: float = 0.8
    compatible_regimes: tuple = ()
    risk_allocation: float = 0.0025
    risk_bounds: tuple = (0.0, 0.5, 1.0)
    allow_long: bool = True
    allow_short: bool = True
    expected_trades_per_symbol_month: tuple = (2, 50)
    expected_net_r_band: tuple = (-0.5, 0.5)
    stop_methodology: str = (
        "close-observed ATR trailing stop, next-open exit; 96 signal bars max"
    )
    sizing: str = (
        "fixed initial capital risk / stop; 90% notional; 0.1% last closed volume cap"
    )
    maximum_age: int = 96
    funding_filter: bool = False

    @property
    def incompatible_regimes(self):
        return tuple(r for r in REGIMES if r not in self.compatible_regimes)

    def definition(self):
        return {
            **asdict(self),
            "incompatible_regimes": self.incompatible_regimes,
            "expected_range_status": "provisional hypothesis; calibrated only by validation",
        }


NO_TRADE = Profile(
    "NO_TRADE",
    "no_trade",
    risk_allocation=0,
    allow_long=False,
    allow_short=False,
    compatible_regimes=REGIMES,
)
BASE = (
    Profile(
        "TB48", "trend_breakout", compatible_regimes=("TREND_LOW_VOL", "TREND_HIGH_VOL")
    ),
    Profile(
        "TP24",
        "trend_pullback",
        lookback=24,
        stop_atr=2.5,
        compatible_regimes=("TREND_LOW_VOL",),
    ),
    Profile(
        "MR48",
        "mean_reversion",
        minutes=15,
        compatible_regimes=("RANGE_LOW_VOL", "VOLATILITY_COMPRESSION"),
    ),
    Profile(
        "VB48",
        "volatility_breakout",
        minutes=15,
        stop_atr=2.5,
        compatible_regimes=("VOLATILITY_EXPANSION", "TREND_HIGH_VOL"),
    ),
)


def library():
    # One adjacent stop and one adjacent lookback per family, not a combinatorial grid
    profiles = list(BASE)
    for p in BASE:
        profiles += [
            replace(p, id=p.id + "_STOP", stop_atr=p.stop_atr * 1.25),
            replace(p, id=p.id + "_WINDOW", lookback=int(p.lookback * 1.25)),
        ]
    profiles += [
        replace(BASE[0], id="TB48_SHORT", allow_long=False),
        replace(BASE[0], id="TB48_FUNDING", funding_filter=True),
    ]
    return {p.id: p for p in [NO_TRADE, *profiles]}


def signal(profile, f):
    if profile.id == "NO_TRADE" or not f.get("ready", False):
        return 0
    prefix = f"{profile.minutes}_{profile.lookback}_"
    c, atr, trend, eq = (f[prefix + k] for k in ("close", "atr", "trend", "eq"))
    family = profile.family
    side = 0
    if family == "trend_breakout":
        side = (
            1
            if c > f[prefix + "high_prev"]
            else -1
            if c < f[prefix + "low_prev"]
            else 0
        )
    elif family == "trend_pullback":
        if c > trend and eq > trend and c < eq - profile.pullback_atr * atr:
            side = 1
        elif c < trend and eq < trend and c > eq + profile.pullback_atr * atr:
            side = -1
    elif family == "mean_reversion":
        if f[prefix + "efficiency"] <= 0.2 and abs(c - trend) <= 3 * atr:
            side = (
                1
                if c < f[prefix + "mean"] - profile.band_k * f[prefix + "std"]
                else -1
                if c > f[prefix + "mean"] + profile.band_k * f[prefix + "std"]
                else 0
            )
    elif f[prefix + "compressed_recent"] and f[prefix + "width_expanding"]:
        side = (
            1
            if c > f[prefix + "high_prev"]
            else -1
            if c < f[prefix + "low_prev"]
            else 0
        )
    if side == 1 and not profile.allow_long or side == -1 and not profile.allow_short:
        return 0
    if profile.funding_filter and side * f.get("funding_rate", 0) > 0.0003:
        return 0
    return side

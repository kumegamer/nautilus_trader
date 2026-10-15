"""Six directional profiles, two stability neighbors each, and explicit cash."""

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
POLICIES = ("ENTRY_ONLY", "PERSIST_4", "CONFIDENT_80", "V1_IMMEDIATE")


@dataclass(frozen=True)
class Profile:
    id: str
    family: str
    side: int
    minutes: int
    lookback: int
    stop_atr: float
    compatible_regimes: tuple
    maximum_age: int = 96

    def definition(self):
        return asdict(self)


BASE = (
    Profile("TB_SHORT", "trend_breakout", -1, 60, 48, 2.0, ("TREND_LOW_VOL",)),
    Profile("TB_LONG", "trend_breakout", 1, 60, 48, 2.0, ("TREND_LOW_VOL",)),
    Profile(
        "VB_SHORT", "volatility_breakout", -1, 15, 48, 2.5, ("VOLATILITY_EXPANSION",)
    ),
    Profile(
        "VB_LONG", "volatility_breakout", 1, 15, 48, 2.5, ("VOLATILITY_EXPANSION",)
    ),
    Profile(
        "VST_SHORT",
        "volatility_scaled_trend",
        -1,
        60,
        96,
        3.0,
        ("TREND_LOW_VOL", "TREND_HIGH_VOL"),
    ),
    Profile(
        "VST_LONG",
        "volatility_scaled_trend",
        1,
        60,
        96,
        3.0,
        ("TREND_LOW_VOL", "TREND_HIGH_VOL"),
    ),
)
NO_TRADE = Profile("NO_TRADE", "no_trade", 0, 15, 48, 2.0, REGIMES)


def library(neighbors=True):
    profiles = [NO_TRADE, *BASE]
    if neighbors:
        for p in BASE:
            profiles += [
                replace(p, id=p.id + "_STOP", stop_atr=p.stop_atr * 1.25),
                replace(p, id=p.id + "_WINDOW", lookback=int(p.lookback * 1.25)),
            ]
    return {p.id: p for p in profiles}


def signal(p, f):
    if not f.get("ready", False) or not p.side:
        return 0
    prefix = f"{p.minutes}_{p.lookback}_"
    c = f[prefix + "close"]
    breakout = c > f[prefix + "high_prev"] if p.side > 0 else c < f[prefix + "low_prev"]
    if p.family == "volatility_breakout":
        breakout &= bool(
            f[prefix + "compressed_recent"] and f[prefix + "width_expanding"]
        )
    if p.family == "volatility_scaled_trend":
        breakout &= p.side * (c - f[prefix + "trend"]) > 0
    return p.side if breakout else 0

"""Causal multi-timeframe features, with backward joins on closed bar timestamps."""

import numpy as np
import pandas as pd

from .profiles import library


def aggregate(bars, minutes):
    b = bars.set_index(pd.to_datetime(bars.t, utc=True))
    result = b.resample(f"{minutes}min", closed="left", label="left").agg(
        {
            "t": "first",
            "open": "first",
            "high": "max",
            "low": "min",
            "close": "last",
            "volume": "sum",
        }
    )
    counts = b.close.resample(f"{minutes}min", closed="left", label="left").count()
    result = result[counts == minutes // 5].copy()
    result["t"] = result.t.astype("int64")
    result["available_ns"] = result.t + minutes * 60 * 10**9 - 10**6
    return result.reset_index(drop=True)


def timeframe(b, minutes):
    c, h, l, v = b.close, b.high, b.low, b.volume
    r = np.log(c).diff()
    tr = pd.concat([h - l, (h - c.shift()).abs(), (l - c.shift()).abs()], axis=1).max(
        axis=1
    )
    atr = tr.rolling(14).mean()
    rv = r.rolling(48).std()
    ratio = rv / rv.rolling(240).median()
    efficiency = (c - c.shift(48)).abs() / c.diff().abs().rolling(48).sum()
    trend = c.ewm(span=200, adjust=False, min_periods=200).mean()
    out = pd.DataFrame(
        {
            "available_ns": b.available_ns,
            f"rv_{minutes}": rv,
            f"atr_{minutes}": atr,
            f"natr_{minutes}": atr / c,
            f"vol_ratio_{minutes}": ratio,
            f"momentum_{minutes}": c.pct_change(24),
            f"trend_strength_{minutes}": (c - trend).abs() / atr,
            f"slope_{minutes}": (trend - trend.shift(6)) / (6 * atr),
            f"efficiency_{minutes}": efficiency,
            f"choppiness_{minutes}": np.log10(
                tr.rolling(48).sum() / (h.rolling(48).max() - l.rolling(48).min())
            )
            / np.log10(48),
            f"volume_regime_{minutes}": v / v.rolling(96).median(),
            f"volume_acceleration_{minutes}": v.rolling(6).mean()
            / v.rolling(24).mean(),
            f"autocorrelation_{minutes}": r.rolling(96).corr(r.shift()),
            f"liquidity_proxy_{minutes}": r.abs() / (c * v).replace(0, np.nan),
        }
    )
    breakout = (c > h.rolling(48).max().shift()) | (c < l.rolling(48).min().shift())
    false = (
        breakout.shift(1).fillna(False)
        & (c < h.rolling(48).max().shift(2))
        & (c > l.rolling(48).min().shift(2))
    )
    out[f"breakout_frequency_{minutes}"] = breakout.rolling(96).mean()
    out[f"false_breakout_frequency_{minutes}"] = false.rolling(96).mean()
    for n in sorted({p.lookback for p in library().values() if p.minutes == minutes}):
        width = c.rolling(n).std() / c
        compressed = width.shift() <= 0.8 * width.shift().rolling(96).mean()
        prefix = f"{minutes}_{n}_"
        values = {
            "close": c,
            "atr": atr,
            "trend": trend,
            "eq": c.ewm(span=n, adjust=False).mean(),
            "mean": c.rolling(n).mean(),
            "std": c.rolling(n).std(ddof=0),
            "high_prev": h.rolling(n).max().shift(),
            "low_prev": l.rolling(n).min().shift(),
            "exit_high": h.rolling(n // 2).max().shift(),
            "exit_low": l.rolling(n // 2).min().shift(),
            "efficiency": efficiency,
            "compressed_recent": compressed.rolling(6).max().fillna(0),
            "width_expanding": width > width.shift(),
        }
        for k, value in values.items():
            out[prefix + k] = value
    return out


def build_features(raw, rates):
    result, returns = {}, {}
    for symbol, bars in raw.items():
        b = aggregate(bars, 15)
        f = b[["available_ns", "t", "open", "high", "low", "close", "volume"]].copy()
        for minutes in (5, 15, 60, 240):
            z = timeframe(aggregate(bars, minutes), minutes)
            f = pd.merge_asof(f, z, on="available_ns", direction="backward")
        funding = rates[symbol][["original_ms", "rate"]].copy()
        funding["available_ns"] = funding.original_ms.astype("int64") * 10**6
        funding["funding_acceleration"] = funding.rate.diff()
        funding = funding.rename(columns={"rate": "funding_rate"})
        f = pd.merge_asof(
            f,
            funding.drop(columns="original_ms"),
            on="available_ns",
            direction="backward",
        )
        f["basis"] = np.nan
        f["spread"] = np.nan
        f["ready"] = (
            f[["rv_60", "vol_ratio_60", "efficiency_60", "slope_240"]]
            .notna()
            .all(axis=1)
        )
        f["new_hour"] = (f.available_ns + 10**6) % (3600 * 10**9) == 0
        result[symbol] = f
        returns[symbol] = pd.Series(
            np.log(f.close).diff().to_numpy(), index=f.available_ns
        )
    cross = pd.DataFrame(returns)
    extras = pd.DataFrame(index=cross.index)
    extras["cross_sectional_dispersion"] = cross.std(axis=1)
    for a, b in (
        ("BTCUSDT", "ETHUSDT"),
        ("BTCUSDT", "SOLUSDT"),
        ("ETHUSDT", "SOLUSDT"),
    ):
        if a in cross and b in cross:
            extras[f"correlation_{a}_{b}"] = cross[a].rolling(96).corr(cross[b])
    for symbol, frame in result.items():
        result[symbol] = frame.merge(
            extras,
            left_on="available_ns",
            right_index=True,
            how="left",
            validate="one_to_one",
        )
    return result


class RegimeEngine:
    def __init__(self):
        self.regime = "UNKNOWN"
        self.started = None
        self.transitions = []

    def update(self, timestamp, f):
        if not f.get("ready", False):
            regime, confidence = "UNKNOWN", 0.0
        else:
            vol, efficiency = f["vol_ratio_60"], f["efficiency_60"]
            stress = abs(f["momentum_15"]) > 0.08 and vol > 1.5
            if stress or vol > 3:
                regime, confidence = "MARKET_STRESS", min(0.95, 0.6 + 0.1 * vol)
            elif vol > 1.8:
                regime, confidence = (
                    "VOLATILITY_EXPANSION",
                    min(0.95, 0.55 + (vol - 1.8) * 0.2),
                )
            elif vol < 0.6:
                regime, confidence = (
                    "VOLATILITY_COMPRESSION",
                    min(0.95, 0.55 + (0.6 - vol) * 0.5),
                )
            else:
                trending = efficiency > 0.3 and abs(f["slope_60"]) > 0.02
                regime = ("TREND" if trending else "RANGE") + (
                    "_HIGH_VOL" if vol > 1.2 else "_LOW_VOL"
                )
                margin = abs(efficiency - 0.3)
                confidence = min(0.9, 0.55 + margin)
        relevant = {
            k: float(f[k])
            for k in ("vol_ratio_60", "efficiency_60", "slope_60", "momentum_15")
            if k in f and pd.notna(f[k])
        }
        if self.started is None or regime != self.regime:
            self.transitions.append(
                {
                    "timestamp": timestamp,
                    "old": self.regime,
                    "new": regime,
                    "confidence": confidence,
                    "features": relevant,
                    "start_ns": timestamp,
                    "previous_duration_ns": timestamp - self.started
                    if self.started is not None
                    else 0,
                }
            )
            self.regime, self.started = regime, timestamp
        return {
            "regime": regime,
            "confidence": confidence,
            "start_ns": self.started,
            "duration_ns": timestamp - self.started,
            "features": relevant,
        }

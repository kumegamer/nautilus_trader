"""Completed-bar features; all alignment is on timestamp of actual availability."""

import numpy as np
import pandas as pd

MINUTE = 60 * 10**9


def aggregate(bars, minutes):
    b = bars.set_index(pd.to_datetime(bars.t, unit="ns", utc=True))
    rules = {
        "t": "first",
        "open": "first",
        "high": "max",
        "low": "min",
        "close": "last",
        "volume": "sum",
        "quote_volume": "sum",
        "taker_buy": "sum",
    }
    result = b.resample(f"{minutes}min", closed="left", label="left").agg(rules)
    counts = b.close.resample(f"{minutes}min", closed="left", label="left").count()
    result = result[counts == minutes // 5].copy()
    result["t"] = result.t.astype("int64")
    result["available_ns"] = result.t + minutes * MINUTE - 10**6
    return result.reset_index(drop=True)


def build(raw, rates):
    result = {}
    for symbol, bars in raw.items():
        f = aggregate(bars, 15)
        c, h, l = f.close, f.high, f.low
        ret = np.log(c).diff()
        tr = pd.concat(
            [h - l, (h - c.shift()).abs(), (l - c.shift()).abs()], axis=1
        ).max(axis=1)
        f["atr"] = tr.rolling(14).mean()
        f["rv"] = ret.rolling(96).std()
        f["vol_ratio"] = f.rv / f.rv.rolling(96 * 20).median()
        f["vol_percentile"] = f.rv.rolling(96 * 30).rank(pct=True)
        f["vol_of_vol"] = f.rv.rolling(96).std() / f.rv.rolling(96).mean()
        f["annual_vol"] = f.rv * np.sqrt(96 * 365)
        f["ret_15"] = ret
        f["ret_1h"] = np.log(c / c.shift(4))
        f["mom_24h"] = np.log(c / c.shift(96))
        f["efficiency"] = (c - c.shift(96)).abs() / c.diff().abs().rolling(96).sum()
        f["persistence"] = np.sign(ret).rolling(96).mean()
        f["choppiness"] = np.log10(
            tr.rolling(96).sum() / (h.rolling(96).max() - l.rolling(96).min())
        ) / np.log10(96)
        f["pullback"] = (c.shift() - c.shift().rolling(8).mean()) / f.atr.shift()
        f["volume_ratio"] = f.volume / f.volume.shift().rolling(96).median()
        f["volume_percentile"] = f.volume.rolling(96 * 20).rank(pct=True)
        f["taker_ratio"] = f.taker_buy / f.volume.replace(0, np.nan)
        f["range_ratio"] = (h - l) / (h - l).shift().rolling(96).median()
        f["high_prev"] = h.shift().rolling(96).max()
        f["low_prev"] = l.shift().rolling(96).min()
        f["high_12h"] = h.shift().rolling(48).max()
        f["low_12h"] = l.shift().rolling(48).min()
        f["exit_high"] = h.shift().rolling(16).max()
        f["exit_low"] = l.shift().rolling(16).min()
        f["distance_high"] = (c - f.high_prev) / f.atr
        f["distance_low"] = (c - f.low_prev) / f.atr
        failed = ((c.shift() > f.high_prev.shift()) & (c < f.high_prev.shift())) | (
            (c.shift() < f.low_prev.shift()) & (c > f.low_prev.shift())
        )
        f["false_frequency"] = failed.rolling(48).mean()
        f["compression_recent"] = f.vol_ratio.shift().rolling(16).min()
        f["shock_prev"] = (ret / ret.shift().rolling(96).std()).shift()
        f["equilibrium"] = (c * f.volume).rolling(96).sum() / f.volume.rolling(96).sum()
        f["deviation"] = (c - f.equilibrium) / f.atr
        five = aggregate(bars, 5)
        five["ret_5"] = np.log(five.close / five.close.shift())
        f = pd.merge_asof(
            f,
            five[["available_ns", "ret_5"]],
            on="available_ns",
            direction="backward",
            tolerance=5 * MINUTE,
        )
        for minutes, n in ((60, 12), (240, 6)):
            a = aggregate(bars, minutes)
            a[f"mom_{minutes}"] = np.log(a.close / a.close.shift(n))
            a[f"slope_{minutes}"] = (a.close - a.close.shift(n)) / (
                n * (a.high - a.low).rolling(14).mean()
            )
            f = pd.merge_asof(
                f,
                a[["available_ns", f"mom_{minutes}", f"slope_{minutes}"]],
                on="available_ns",
                direction="backward",
                tolerance=minutes * MINUTE,
            )
        funding = rates[symbol][["original_ms", "rate"]].copy()
        funding["funding_available_ns"] = (
            funding.original_ms.astype("int64") * 10**6 + 10**9
        )
        funding["funding_change"] = funding.rate.diff()
        funding = funding.rename(columns={"rate": "funding"})
        f = pd.merge_asof(
            f,
            funding.drop(columns="original_ms"),
            left_on="available_ns",
            right_on="funding_available_ns",
            direction="backward",
        )
        f["funding_age_hours"] = (f.available_ns - f.funding_available_ns) / (
            60 * MINUTE
        )
        f["regime"] = np.select(
            [f.vol_ratio > 2.5, f.vol_ratio < 0.7, f.efficiency > 0.3],
            ["STRESS", "COMPRESSION", "TREND"],
            default="RANGE",
        )
        f["regime"] = f.regime + np.where(f.vol_ratio > 1.3, "_HIGH_VOL", "_LOW_VOL")
        f["ready"] = (
            f[["vol_percentile", "mom_240", "volume_ratio", "taker_ratio", "funding"]]
            .notna()
            .all(axis=1)
        )
        result[symbol] = f
    btc = result["BTCUSDT"].set_index("available_ns")
    for symbol, f in result.items():
        # Exact availability joins require all three synchronized completed bars
        f["btc_mom"] = f.available_ns.map(btc.mom_24h)
        f["relative_strength"] = f.mom_24h - f.btc_mom
        btc_ret = f.available_ns.map(btc.ret_15)
        f["btc_correlation"] = f.ret_15.rolling(96 * 7).corr(btc_ret)
        f["cross_rank"] = np.nan
    cross = pd.DataFrame(
        {s: f.set_index("available_ns").mom_24h for s, f in result.items()}
    ).rank(axis=1, pct=True)
    for s, f in result.items():
        f["cross_rank"] = f.available_ns.map(cross[s])
    return result

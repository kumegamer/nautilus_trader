"""Public Binance Vision archives; no private endpoints or trading clients."""

import concurrent.futures
import io
import time
import urllib.request
import zipfile
from functools import lru_cache

import numpy as np
import pandas as pd

from .common import ROOT, assert_frozen, config, digest, ns, write_json

BASE = "https://data.binance.vision/data/futures/um/monthly"


def archive_info(symbol, month, kind):
    if kind == "fundingRate":
        name = f"{symbol}-fundingRate-{month}.zip"
        relative = f"{kind}/{symbol}/{name}"
    else:
        name = f"{symbol}-5m-{month}.zip"
        relative = f"{kind}/{symbol}/5m/{name}"
    return BASE + "/" + relative, ROOT / "data" / "raw" / relative


def fetch(url):
    for attempt in range(4):
        try:
            with urllib.request.urlopen(url, timeout=60) as response:
                return response.read()
        except Exception:
            if attempt == 3:
                raise
            time.sleep(0.5 * (attempt + 1))


def download_one(item):
    symbol, month, kind = item
    if month >= "2026-01":
        assert_frozen()
    url, path = archive_info(symbol, month, kind)
    path.parent.mkdir(parents=True, exist_ok=True)
    sidecar = path.with_suffix(".zip.CHECKSUM")
    if not sidecar.exists():
        sidecar.write_bytes(fetch(url + ".CHECKSUM"))
    expected = sidecar.read_text().split()[0]
    if not path.exists():
        content = fetch(url)
        temporary = path.with_suffix(".part")
        temporary.write_bytes(content)
        temporary.replace(path)
    actual = digest(path)
    if actual != expected:
        raise ValueError(f"Publisher checksum mismatch: {path}")
    return {
        "symbol": symbol,
        "month": month,
        "kind": kind,
        "url": url,
        "path": str(path.relative_to(ROOT)),
        "sha256": actual,
        "publisher_sha256": expected,
        "bytes": path.stat().st_size,
    }


def download(holdout=False):
    if holdout:
        assert_frozen()
    first, last = ("2026-01", "2026-06") if holdout else ("2021-12", "2025-12")
    months = pd.period_range(first, last, freq="M").astype(str)
    jobs = [
        (s, m, k)
        for s in config()["symbols"]
        for m in months
        for k in ("klines", "markPriceKlines", "fundingRate")
    ]
    rows = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
        for i, row in enumerate(pool.map(download_one, jobs), 1):
            rows.append(row)
            if i % 30 == 0:
                print(f"Verified {i}/{len(jobs)} archives", flush=True)
    name = "holdout_manifest.json" if holdout else "preholdout_manifest.json"
    write_json(ROOT / "data" / name, rows)
    repair_klines(holdout)


def repair_klines(holdout=False):
    """Use daily publisher archives only for missing monthly kline timestamps."""
    first, last = ("2026-01", "2026-06") if holdout else ("2021-12", "2025-12")
    rows = []
    for symbol in config()["symbols"]:
        for month in pd.period_range(first, last, freq="M"):
            frame = read_archive(symbol, str(month), "klines")
            present = pd.to_datetime(frame.iloc[:, 0].astype("int64"), unit="ms", utc=True)
            begin = pd.Timestamp(str(month), tz="UTC")
            end = begin + pd.offsets.MonthBegin(1)
            expected = pd.date_range(begin, end, freq="5min", inclusive="left")
            missing = expected.difference(present)
            for day in sorted(set(missing.strftime("%Y-%m-%d"))):
                if day >= "2026-01-01":
                    assert_frozen()
                name = f"{symbol}-5m-{day}.zip"
                url = BASE.replace("monthly", "daily") + f"/klines/{symbol}/5m/{name}"
                path = ROOT / "data" / "raw" / "daily" / symbol / name
                path.parent.mkdir(parents=True, exist_ok=True)
                sidecar = path.with_suffix(".zip.CHECKSUM")
                if not sidecar.exists():
                    sidecar.write_bytes(fetch(url + ".CHECKSUM"))
                if not path.exists():
                    path.write_bytes(fetch(url))
                expected_hash = sidecar.read_text().split()[0]
                if digest(path) != expected_hash:
                    raise ValueError(f"Daily repair checksum mismatch: {path}")
                rows.append(
                    {
                        "symbol": symbol,
                        "day": day,
                        "url": url,
                        "path": str(path.relative_to(ROOT)),
                        "sha256": digest(path),
                        "publisher_sha256": expected_hash,
                        "bytes": path.stat().st_size,
                    }
                )
    name = "holdout_repairs.json" if holdout else "preholdout_repairs.json"
    write_json(ROOT / "data" / name, rows)


def read_archive(symbol, month, kind):
    _, path = archive_info(symbol, month, kind)
    if not path.exists():
        raise FileNotFoundError(f"Run download first: {path}")
    sidecar = path.with_suffix(".zip.CHECKSUM")
    if digest(path) != sidecar.read_text().split()[0]:
        raise ValueError(f"Archive changed: {path}")
    with zipfile.ZipFile(path) as z:
        content = z.read(z.namelist()[0])
    header = 0 if not content.splitlines()[0].split(b",")[0].isdigit() else None
    return pd.read_csv(io.BytesIO(content), header=header)


def read_klines(symbol, month):
    frame = read_archive(symbol, month, "klines")
    for path in sorted((ROOT / "data" / "raw" / "daily" / symbol).glob(f"*-{month}-*.zip")):
        if digest(path) != path.with_suffix(".zip.CHECKSUM").read_text().split()[0]:
            raise ValueError("Daily repair archive changed")
        with zipfile.ZipFile(path) as z:
            content = z.read(z.namelist()[0])
        header = 0 if not content.splitlines()[0].split(b",")[0].isdigit() else None
        daily = pd.read_csv(io.BytesIO(content), header=header)
        daily.columns = frame.columns
        daily = daily[~daily.iloc[:, 0].isin(frame.iloc[:, 0])]
        frame = pd.concat([frame, daily], ignore_index=True)
    return frame.sort_values(frame.columns[0]).reset_index(drop=True)


@lru_cache(maxsize=12)
def load(symbol, period, minutes):
    cfg = config()
    start, end = map(ns, cfg["periods"][period])
    if period == "holdout":
        assert_frozen()
    warm = start - cfg["warmup_days"] * 86400 * 10**9
    months = pd.period_range(
        pd.Timestamp(warm, tz="UTC").strftime("%Y-%m"),
        pd.Timestamp(end - 1, tz="UTC").strftime("%Y-%m"),
        freq="M",
    )
    bars, rates, marks = [], [], []
    for month in months.astype(str):
        b = read_klines(symbol, month)
        b = b.iloc[:, :6].copy()
        b.columns = ["t", "open", "high", "low", "close", "volume"]
        bars.append(b)
        r = read_archive(symbol, month, "fundingRate")
        r.columns = ["original_ms", "interval", "rate"]
        rates.append(r)
        m = read_archive(symbol, month, "markPriceKlines").iloc[:, :2].copy()
        m.columns = ["t", "mark"]
        marks.append(m)
    b = pd.concat(bars, ignore_index=True).astype(float)
    b["t"] = b.t.astype("int64") * 10**6
    b = b[(b.t >= warm) & (b.t < end)].copy()
    if b.t.duplicated().any() or not b.t.is_monotonic_increasing:
        raise ValueError("Duplicate or nonmonotonic bars")
    if not np.isfinite(b.to_numpy()).all() or (b.iloc[:, 1:5] <= 0).any().any():
        raise ValueError("Nonfinite or nonpositive prices")
    if (
        (b.high < b[["open", "close", "low"]].max(axis=1))
        | (b.low > b[["open", "close", "high"]].min(axis=1))
        | (b.volume < 0)
    ).any():
        raise ValueError("Invalid OHLCV")
    gaps = int((b.t.diff().dropna() != 300 * 10**9).sum())
    expected = (end - warm) // (300 * 10**9)
    if len(b) != expected or gaps:
        raise ValueError(f"Incomplete 5m bars: {symbol} {period}, {len(b)}/{expected}, gaps={gaps}")
    trade_opens = b[["t", "open"]].copy()
    b.index = pd.to_datetime(b.t, utc=True)
    if minutes != 5:
        b = b.resample(f"{minutes}min", closed="left", label="left").agg(
            {
                "t": "first",
                "open": "first",
                "high": "max",
                "low": "min",
                "close": "last",
                "volume": "sum",
            }
        )
    b["t"] = b.t.astype("int64")
    r = pd.concat(rates, ignore_index=True)
    r["t"] = (r.original_ms.astype("int64") // 60000) * 60 * 10**9
    jitter = r.original_ms.astype("int64") % 60000
    if (r.original_ms.astype("int64") % 3600000 >= 60000).any() or (r.interval <= 0).any():
        raise ValueError("Invalid funding reporting jitter/interval")
    r = r[(r.t >= start) & (r.t < end)].copy()
    if r.t.duplicated().any() or not r.t.is_monotonic_increasing:
        raise ValueError("Invalid funding sequence")
    intervals = np.maximum(r.interval.to_numpy()[1:], r.interval.to_numpy()[:-1])
    if (r.t.diff().dropna().to_numpy() > intervals * 3600 * 10**9).any():
        raise ValueError("Missing funding interval")
    if len(r) < (end - start) / (86400 * 10**9) * 2.9:
        raise ValueError("Incomplete funding coverage")
    m = pd.concat(marks, ignore_index=True)
    m["t"] = m.t.astype("int64") * 10**6
    if m.t.duplicated().any():
        raise ValueError("Duplicate marks")
    r = r.merge(m, on="t", how="left", validate="one_to_one")
    r["mark_source"] = "mark_open"
    r = r.merge(trade_opens, on="t", how="left", validate="one_to_one")
    missing = r.mark.isna()
    r.loc[missing, "mark_source"] = "trade_open_proxy"
    r.loc[missing, "mark"] = r.loc[missing, "open"]
    if r.mark.isna().any():
        raise ValueError("Missing funding boundary marks and trade open proxies")
    audit = {
        "symbol": symbol,
        "period": period,
        "minutes": minutes,
        "bar_rows": len(b),
        "expected_5m_rows": int(expected),
        "gaps": gaps,
        "funding_rows": len(r),
        "funding_mark_proxy_rows": int(missing.sum()),
        "max_reporting_jitter_ms": int(jitter.max()),
        "first_bar_ns": int(b.t.iloc[0]),
        "last_bar_ns": int(b.t.iloc[-1]),
    }
    write_json(ROOT / "data" / "audits" / f"{symbol}_{period}_{minutes}.json", audit)
    return b.reset_index(drop=True), r.reset_index(drop=True)

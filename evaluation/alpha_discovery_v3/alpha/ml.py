"""Small deterministic regularized logistic comparator, trained on past labels only."""

import numpy as np
import pandas as pd

from .common import DAY, ns

FEATURES = [
    "mom_60",
    "mom_240",
    "vol_percentile",
    "volume_ratio",
    "taker_ratio",
    "range_ratio",
    "false_frequency",
    "efficiency",
    "relative_strength",
    "funding",
]


def attach(frames):
    records = []
    for f in frames.values():
        for side in (1, -1):
            f[f"ml_{side}"] = np.nan
    for quarter in pd.period_range("2024Q1", "2026Q3", freq="Q"):
        begin = ns(str(quarter.start_time.date()))
        end = ns(str((quarter + 1).start_time.date()))
        cutoff = begin - DAY
        for side in (1, -1):
            xs, ys = [], []
            max_label_ns = None
            for f in frames.values():
                future = f.close.shift(-16)
                label_end = f.available_ns.shift(-16)
                breakout = (
                    (f.close > f.high_prev) if side > 0 else (f.close < f.low_prev)
                )
                mask = (
                    (f.available_ns < cutoff)
                    & (label_end < cutoff)
                    & f.ready
                    & breakout
                )
                mask &= (f.available_ns + 10**6) % (3600 * 10**9) == 0
                mask &= np.isfinite(f[FEATURES]).all(axis=1) & future.notna()
                xs.append(f.loc[mask, FEATURES].to_numpy())
                ys.append(
                    (side * np.log(future[mask] / f.close[mask]) > 0.0012)
                    .to_numpy()
                    .astype(float)
                )
                if mask.any():
                    last = int(label_end[mask].max())
                    max_label_ns = (
                        last if max_label_ns is None else max(last, max_label_ns)
                    )
            x, y = np.concatenate(xs), np.concatenate(ys)
            record = {
                "quarter": str(quarter),
                "side": side,
                "decision_ns": begin,
                "training_cutoff_ns": cutoff,
                "latest_label_end_ns": max_label_ns,
                "samples": len(y),
                "features": FEATURES,
                "status": "INSUFFICIENT_TRAINING",
            }
            if len(y) >= 40 and len(np.unique(y)) == 2:
                mean = x.mean(axis=0)
                scale = np.maximum(x.std(axis=0), 1e-8)
                z = np.clip((x - mean) / scale, -10, 10)
                w = np.zeros(z.shape[1])
                intercept = 0.0
                for _ in range(200):
                    prob = 1 / (1 + np.exp(-np.clip(z @ w + intercept, -30, 30)))
                    w -= 0.05 * (z.T @ (prob - y) / len(y) + w / len(y))
                    intercept -= 0.05 * (prob - y).mean()
                for f in frames.values():
                    mask = (f.available_ns >= begin) & (f.available_ns < end)
                    z = np.clip(
                        (f.loc[mask, FEATURES].to_numpy() - mean) / scale, -10, 10
                    )
                    f.loc[mask, f"ml_{side}"] = 1 / (
                        1 + np.exp(-np.clip(z @ w + intercept, -30, 30))
                    )
                record.update(
                    status="FITTED",
                    mean=mean.tolist(),
                    scale=scale.tolist(),
                    coefficients=w.tolist(),
                    intercept=float(intercept),
                )
            records.append(record)
    return frames, records

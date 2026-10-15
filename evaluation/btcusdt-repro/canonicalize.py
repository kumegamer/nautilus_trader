"""Explicit NEW canonical schema; not the unavailable historical implementation.

Keeps ALL economic outputs without projection or rounding. Includes raw engine
orders, order events, archived positions, and account events after identity-only
normalization. UUIDs map to labels in deterministic first-encounter order so that
cross-references remain testable. Trade IDs similarly map to stable labels;
their generated hash prefix is not an execution price or economic value.
No sorting of event/array order; no removal of timestamps, prices, fees or PnL.
Runtime versions and assertion counts remain part of the canonical payload.
JSON: UTF-8, sorted dictionary keys, compact separators, no NaN, no trailing LF.
"""
import argparse
import hashlib
import json
import re
from pathlib import Path

UUID = re.compile(r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}")
TRADE_ID = re.compile(r"^T-[0-9a-f]+-[0-9]+$")


def canonicalize(raw):
    uuids, trades = {}, {}

    def normalize(value):
        if isinstance(value, dict):
            return {key: normalize(value[key]) for key in sorted(value)}
        if isinstance(value, list):
            return [normalize(x) for x in value]
        if isinstance(value, str):
            if TRADE_ID.fullmatch(value):
                if value not in trades:
                    trades[value] = f"TRADE-{len(trades) + 1:04d}"
                return trades[value]

            def replace_uuid(match):
                key = match.group().lower()
                if key not in uuids:
                    uuids[key] = f"UUID-{len(uuids) + 1:06d}"
                return uuids[key]

            return UUID.sub(replace_uuid, value)
        return value

    # Economics is preserved verbatim, including exact decimal strings and EMA hex values.
    output = {"canonical_schema": "btc-ema-replay-canonical-v1",
              "economics": raw["economics"], "engine": normalize(raw["engine"]),
              "runtime": raw["runtime"], "validation": raw["validation"]}
    return json.dumps(output, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("raw", type=Path)
    parser.add_argument("canonical", type=Path)
    args = parser.parse_args()
    data = canonicalize(json.loads(args.raw.read_text()))
    args.canonical.write_bytes(data)
    print(hashlib.sha256(data).hexdigest())


if __name__ == "__main__":
    main()

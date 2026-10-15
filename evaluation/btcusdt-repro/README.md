# BTCUSDT January 2025 reproducibility evaluation

This directory preserves the completed evaluation as five files. The three Python
scripts are unchanged copies of the scripts used for the two successful replays.
NautilusTrader source, its native extension, and its environment are unchanged.
No dataset or generated replay output is committed.

The result is `REPRODUCIBILITY_PARTIAL`: both new replays are identical, and all
supplied historical economic metrics match. The historical canonicalization code
was unavailable, so the historical byte-level hash cannot be verified. Counts and
monetary values match exactly; historical ratios match at their reported precision.
Original historical event-level outputs and unrounded ratios were not supplied.

## Dataset and checksums

Binance USD-M Futures perpetual BTCUSDT, five-minute OHLCV bars, January 2025 UTC:

```text
https://data.binance.vision/data/futures/um/monthly/klines/BTCUSDT/5m/BTCUSDT-5m-2025-01.zip
```

The archive's companion `.CHECKSUM` file was checked against its contents.
The pinned SHA-256 values are:

```text
ZIP: 0c99422d64fa3cc58564cf77969fc5a96d6f44783c79ecfcf94b103753bf7570
CSV: 42041de841ce900c8209dec3524f70bb57bededef7923f4ac8bfa444f9a5f508
```

There are 8,928 bars, from January 1 at 00:00 through January 31 at 23:55 UTC.
Their open times are strictly increasing at 300,000 ms intervals, without missing
or duplicate bars. Each Binance close timestamp is open time plus 299,999 ms;
the bar becomes available at the next interval boundary. OHLC ordering and
nonnegative volume were validated.

## Verified runtime

| Component | Version |
| --- | --- |
| Python | 3.13.16 |
| NautilusTrader | 2.0.0rc7 |
| Checkout commit | `de794053685c3a3b7ae74eb995e2b31215786b25` |
| Earlier experiment's Python | 3.13.5 |

Use the existing interpreter at `python/.venv/bin/python` relative to the
repository root. No installation, rebuild, or repair is part of these commands.
The canonical payload includes runtime versions, so a different Python or
NautilusTrader version can change its hash even if economic results agree.

## Fixed assumptions

- EMA20/EMA50 use only completed closes. Each EMA is seeded with the SMA of its
  first N closes, then updated recursively with alpha `2 / (N + 1)`.
- Fifty bars provide warm-up. The first entry requires a subsequent strict
  crossover; EMA ordering at warm-up completion does not open a position.
- Every order has fixed size 0.010 BTC. There is at most one open position.
  A reversal's closing order must fill before its opening order is submitted.
- Signals execute at the next bar's open. Initial balance is 10,000 USDT.
- Every fill pays a 0.05% taker fee. Funding is zero.
- Every fill receives 1 bp adverse slippage: BUY prices round up and SELL prices
  round down to a 0.1 USDT tick, using Decimal arithmetic.
- The final open exposure is forcibly closed from the last completed bar close
  with the same fee and slippage rules. The final short's exit is a modeled BUY
  at 102,390.0 USDT, from the last close of 102,379.7, with a 0.511950 USDT fee.
  No February market observation is used.
- Synthetic zero-spread quotes from historical opens provide execution reference
  prices. They do not represent observed bid/ask quotes. Native bar execution is
  disabled, so historical high/low values do not drive fills.
- At each boundary, the completed bar is consumed first; a one-nanosecond offset
  orders the next-open reference afterward. Final liquidation uses a two-nanosecond
  offset. These offsets specify event ordering in an idealized zero-latency model.
- Equity is marked at every completed close. The final equity sample is replaced
  with post-liquidation equity. Drawdown uses an initial high-water mark of 10,000
  USDT and these bar-close samples, rather than intrabar equity.
- Profit factor is positive net closed-trade PnL divided by the absolute sum of
  negative net closed-trade PnL. No strategy parameters were optimized.

## Expected results

| Metric | Expected |
| --- | ---: |
| Closed trades | 172: 86 long, 86 short |
| Orders / fills | 344 / 344 |
| Winning trades | 39 |
| Final balance | 9,810.296225 USDT |
| Gross PnL after slippage | -17.874000 USDT |
| Commissions | 171.829775 USDT |
| Net realized PnL | -189.703775 USDT |
| Win rate | 22.6744% |
| Maximum drawdown | 233.238054 USDT / 2.327584% |
| Profit factor | 0.737767 |
| Final exposure | 0 BTC |

`expected_result.json` preserves full computed precision, source checksums,
runtime versions, validation counts, and checksums of the three saved scripts.

Both new canonical outputs have SHA-256:

```text
ff16ab490258a4e6f7fa5e33207351432f25e786fc243e19a450c98ade15c201
```

The unavailable earlier canonicalization produced this historical reference:

```text
7aecf9ac5050a5eb6c08ca36a32cd5bd29edf82c4c26d3df51799ea750f60814
```

These hashes differ. The new hash establishes future replay expectations for the
explicit `btc-ema-replay-canonical-v1` schema; it does not reproduce the old bytes.

## Canonicalization and validation

`canonicalize.py` preserves all economic outputs, including exact decimal strings,
EMA floating-point hex states, timestamps, and array order. It includes engine
orders, order events, archived NETTING position cycles, account events, versions,
and validation counts. Generated UUIDs and trade IDs map to stable labels in
deterministic traversal order while retaining cross-references. This includes
event UUIDs, initialization UUIDs, and archived-position snapshot UUIDs. There is
no rounding or removal of economic values. Serialization is UTF-8 JSON with
sorted keys, compact separators, no NaN, and no trailing newline.

`compare_runs.py` checks exact economic and normalized engine equality, recomputes
signals independently, audits all 344 fills and 172 closed trades, reconstructs
all 8,928 equity points, and perturbs future closes at seven cutoffs to check
earlier signal invariance. Each successful engine run also checks engine balances
against its Decimal ledger at 8,929 checkpoints and checks every archived trade's
realized PnL. The final gate below checks the persisted full metrics and canonical
hash, in addition to the historical report comparisons built into that script.

## Replay commands

Run from the repository root in Bash. Data and generated outputs stay in a
separate temporary directory. The saved scripts expect a `btcusdt-repro` data
directory beside them, so copy them to the replay directory first:

```bash
REPO_ROOT="$PWD"
EVALUATION_DIR="$REPO_ROOT/evaluation/btcusdt-repro"
PYTHON_EXE="$REPO_ROOT/python/.venv/bin/python"
REPLAY_DIR="$(mktemp -d "${TMPDIR:-/tmp}/btcusdt-repro.XXXXXX")"
mkdir -p "$REPLAY_DIR/btcusdt-repro"
cp "$EVALUATION_DIR/btc_experiment.py" "$REPLAY_DIR/"
cp "$EVALUATION_DIR/compare_runs.py" "$REPLAY_DIR/"
cp "$EVALUATION_DIR/canonicalize.py" "$REPLAY_DIR/"
```

Download and verify the pinned public archive using the existing Python standard
library and the environment's configured networking. Keep TLS verification and
the configured proxy in place:

```bash
"$PYTHON_EXE" -B - "$REPLAY_DIR/btcusdt-repro" <<'PY'
import hashlib
import io
import sys
import urllib.request
import zipfile
from pathlib import Path

out = Path(sys.argv[1])
name = "BTCUSDT-5m-2025-01.zip"
url = "https://data.binance.vision/data/futures/um/monthly/klines/BTCUSDT/5m/" + name
with urllib.request.urlopen(url, timeout=30) as response:
    archive = response.read()
with urllib.request.urlopen(url + ".CHECKSUM", timeout=30) as response:
    published = response.read().decode()
digest = hashlib.sha256(archive).hexdigest()
assert digest == published.split()[0]
assert digest == "0c99422d64fa3cc58564cf77969fc5a96d6f44783c79ecfcf94b103753bf7570"
with zipfile.ZipFile(io.BytesIO(archive)) as zipped:
    csv_data = zipped.read("BTCUSDT-5m-2025-01.csv")
assert hashlib.sha256(csv_data).hexdigest() == (
    "42041de841ce900c8209dec3524f70bb57bededef7923f4ac8bfa444f9a5f508"
)
(out / name).write_bytes(archive)
(out / (name + ".CHECKSUM")).write_text(published)
(out / "BTCUSDT-5m-2025-01.csv").write_bytes(csv_data)
PY
```

Execute the same script twice, then compare all outputs and audit the economics:

```bash
"$PYTHON_EXE" -B "$REPLAY_DIR/btc_experiment.py" \
  --output "$REPLAY_DIR/btcusdt-repro/run1" > "$REPLAY_DIR/run1.log" 2>&1
"$PYTHON_EXE" -B "$REPLAY_DIR/btc_experiment.py" \
  --output "$REPLAY_DIR/btcusdt-repro/run2" > "$REPLAY_DIR/run2.log" 2>&1
"$PYTHON_EXE" -B "$REPLAY_DIR/compare_runs.py" --root "$REPLAY_DIR/btcusdt-repro"
```

Finally verify both full metric dictionaries and canonical hashes against the
persisted expectations. This gate fails on any differing saved metric or hash:

```bash
"$PYTHON_EXE" -B - "$EVALUATION_DIR/expected_result.json" "$REPLAY_DIR/btcusdt-repro" <<'PY'
import hashlib
import json
import sys
from pathlib import Path

expected = json.loads(Path(sys.argv[1]).read_text())
root = Path(sys.argv[2])
for run in ("run1", "run2"):
    raw = json.loads((root / run / "raw.json").read_text())
    assert raw["economics"]["metrics"] == expected["metrics"], run
    assert raw["runtime"] == expected["runtime"], run
    digest = hashlib.sha256((root / run / "canonical.json").read_bytes()).hexdigest()
    assert digest == expected["expected_canonical_sha256"], (run, digest)
print("EXPECTED_RESULT_MATCH: both runs")
PY
```

To canonicalize a raw output separately:

```bash
"$PYTHON_EXE" -B "$EVALUATION_DIR/canonicalize.py" \
  "$REPLAY_DIR/btcusdt-repro/run1/raw.json" "$REPLAY_DIR/standalone-canonical.json"
```

Preserving a local commit does not publish it to a remote. No push, merge, pull
request, or update to `develop` is part of this evaluation.

# Persisted Edge Discovery v1

This directory preserves the completed NautilusTrader-only experiment. The original
code, configuration, native execution records, reports, interactive charts, source
manifests, selection decisions and one-use holdout marker are retained unchanged.
The branch is `evaluation/edge-discovery-v1`; no live trading is enabled.

| Family | Final classification |
| --- | --- |
| Trend breakout | WEAK_EDGE |
| Trend pullback | NO_EDGE |
| Mean reversion | NO_EDGE |
| Volatility breakout | NO_EDGE |

Read `REPORT.md` for the findings and limitations, and open `CHARTS.html` locally for
the offline charts. `results/freeze.json` seals the pre-holdout decisions and evidence.
`results/holdout_opened.json` records the single holdout opening. The holdout has
already been consumed; a replay is a reproduction check, not another unseen test.

## Restore a fresh checkout

Run these commands from this directory. The restoration utility uses only the Python
standard library. It downloads the 500 original public archives from the four saved
manifests and rejects bytes that differ from the recorded publisher SHA256 hashes.
It does not regenerate manifests, rerun selection, or change frozen evidence.

```bash
sha256sum --check PERSISTENCE_SHA256SUMS
python restore_data.py
python restore_data.py --verify-only
```

Raw archives and derived caches remain ignored by Git. The manifests preserve their
public URLs, byte sizes and both observed and publisher checksums, including the five
daily repairs. Checksums establish the exact inputs; future public source availability
is outside this repository's control. The compressed files under `results/runs/` are
research execution evidence, not copies of the raw Binance datasets.

Follow `REPRODUCTION.md` for the pinned NautilusTrader revision, dependency locks,
native build and replay instructions. `runtime-requirements.txt` records the original
environment; its editable `/workspace/nautilus_trader/python` entry refers to this
checkout's Python package and must be adjusted to the new checkout path when rebuilding.
`verify_artifacts.py` additionally checks the original native binary checksum, which
only matches the original compiled environment; a rebuild uses numerical replay for
comparison as described in `REPRODUCTION.md`.

`restore_data.py`, this note and `PERSISTENCE_SHA256SUMS` were added for Git persistence
after the completed experiment. They do not alter its original freeze. The supplemental
checksum list covers every committed experiment file except itself. Preserve the
original evidence when reproducing in a separate working copy. `.gitattributes`
disables Git line-ending conversion here so sealed file bytes survive checkout.

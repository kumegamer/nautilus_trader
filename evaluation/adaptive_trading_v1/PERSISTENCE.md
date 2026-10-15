# Adaptive Trading v1 persistence

Only evaluation/adaptive_trading_v1/ is added to evaluation/adaptive-trading-v1.
The development baseline, NautilusTrader core and frozen prior research are unchanged.
No merge or pull request is part of this persistence operation. Real-money execution stays disabled.

## Committed scope

The branch includes the implementation, protocol/configuration, tests, corrected and original reports,
complete JSONL/CSV event logs, all 501 native result runs, superseded developmental runs, test/replay/
financial-audit output, execution console logs, dependency locks, environment provenance, data audits,
public download manifests and SHA256 checksums. Developmental failures and reporting corrections remain
visible. results/repository_refs.json records the experiment's original baseline, not the later
persistence commit. Obtain the persistence commit with `git rev-parse HEAD`.

All committed artifacts retain exact bytes through the local .gitattributes rule, including CSV CRLF.
The frozen source, config, protocol, tests, freeze manifest and preholdout evidence are not rewritten.
README/storage metadata and the aggregate artifact checksum inventory reflect persistence packaging.

## Excluded data

Only data/raw/, Python/test caches and partial downloads are excluded. No raw Binance market ZIPs,
credentials, toolchains, native extension binaries or unrelated repository files are committed.
The raw dataset is reproducibly downloadable from the committed publisher URLs and SHA256s.
Small data/audits/ JSON files are metadata and are committed.

## Verification after cloning

Use the baseline's uv-managed python/.venv environment and its matching built Nautilus extension.
The required dependency versions and extension/lock hashes are in results/environment.json.

Before downloading data, all committed artifact hashes and frozen evidence can be checked offline:

```bash
export PYTHONPATH=evaluation/adaptive_trading_v1
python/.venv/bin/python - <<'PY'
import json
from adaptive.common import ROOT, assert_frozen, digest
assert_frozen()
checks = json.loads((ROOT / "results/artifact_checksums.json").read_text())
for name, expected in checks.items():
    assert digest(ROOT / name) == expected, name
print("Committed artifact and frozen evidence checks passed")
PY
```

Restore the public raw inputs and run the complete publisher/experiment verification:

```bash
python/.venv/bin/python -m adaptive.reproduce restore
python/.venv/bin/python -m adaptive.workflow verify
python/.venv/bin/python -m pytest -q evaluation/adaptive_trading_v1/tests
python/.venv/bin/python evaluation/adaptive_trading_v1/verify_financial_ledger.py
python/.venv/bin/python -m adaptive.reproduce replay --profile ADAPTIVE --period holdout
```

The financial ledger check recomputes identities from saved native outputs without rerunning trading.
The independent holdout replay compares fills, trades, daily balances and complete adaptive decisions.
See results/persistence_checks.json for packaging checks performed before committing.

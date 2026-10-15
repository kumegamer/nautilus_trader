"""Re-execute published frozen strategies; this is reproduction, never new OOS selection."""

import argparse
import gzip
import json
import platform

import nautilus_trader

from edge_discovery.common import ROOT, assert_frozen, config, write_json
from edge_discovery.data import load
from edge_discovery.engine import run
from edge_discovery.metrics import metrics


def replay(family=None, scenario=None):
    frozen = assert_frozen()
    if not (ROOT / "results/holdout_opened.json").exists():
        raise RuntimeError(
            "Use the one-time holdout stage first; replay is only for published evidence"
        )
    if nautilus_trader.__version__ != frozen["runtime"]["nautilus_trader"]:
        raise RuntimeError("NautilusTrader version differs from frozen runtime")
    published = json.loads((ROOT / "results/final.json").read_text())
    comparisons = []
    for name, candidate in frozen["representatives"].items():
        if family is not None and family != name:
            continue
        for cost in config()["scenarios"]:
            if scenario is not None and cost != scenario:
                continue
            runs = []
            for symbol in config()["symbols"]:
                bars, rates = load(symbol, "holdout", candidate["minutes"])
                result = run(candidate, symbol, "holdout", bars, rates, cost)
                path = ROOT / "work/replay" / cost / f"{candidate['id']}__{symbol}.json.gz"
                path.parent.mkdir(parents=True, exist_ok=True)
                with gzip.open(path, "wt") as f:
                    json.dump(result, f, sort_keys=True, allow_nan=False)
                runs.append(result)
            actual = metrics(runs)
            original = published[name]["scenarios"][cost]
            assert actual["total_trades"] == original["total_trades"]
            for metric in ["gross_pnl", "fees", "funding", "slippage_impact", "net_pnl"]:
                assert abs(actual[metric] - original[metric]) < 0.00001, (name, cost, metric)
            comparisons.append({"family": name, "scenario": cost, "matches_published": True})
    if not comparisons:
        raise RuntimeError("No matching frozen family/scenario")
    write_json(
        ROOT / "work/replay/comparison.json",
        {
            "purpose": "Reproduction of already-opened evidence; not an independent OOS experiment",
            "platform": platform.platform(),
            "comparisons": comparisons,
        },
    )
    print(json.dumps(comparisons, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--family", choices=list(config()["grids"]))
    parser.add_argument("--scenario", choices=list(config()["scenarios"]))
    args = parser.parse_args()
    replay(args.family, args.scenario)

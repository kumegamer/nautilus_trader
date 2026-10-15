from decimal import Decimal as D

from adaptive.common import ROOT, write_json
from adaptive.workflow import PRE, read_runs

runs = read_runs((*PRE, "holdout"))
assert len(runs) == 501, len(runs)
trade_count = 0
maximum_trade_error = D(0)
maximum_account_error = D(0)
for r in runs:
    total = D(0)
    for t in r["trades"]:
        total += D(str(t["net_pnl"]))
        identity = (
            D(str(t["gross_pnl"]))
            - D(str(t["fees"]))
            - D(str(t["slippage"]))
            + D(str(t["funding"]))
        )
        error = abs(identity - D(str(t["net_pnl"])))
        maximum_trade_error = max(error, maximum_trade_error)
        assert error < D("0.00001"), (r["candidate"], error)
        trade_count += 1
    discrepancy = abs(D(r["native_balance"]) - D(10000) - total)
    maximum_account_error = max(discrepancy, maximum_account_error)
    assert discrepancy < D("0.00001"), (r["candidate"], discrepancy)
    assert all(
        f["signal_ns"] < f["ts_ns"] and D(f["slippage"]) >= 0 for f in r["fills"]
    )
    for e in r["research"]:
        assert (
            e["evidence"] is None
            or e["evidence"]["end_ns"] <= e["timestamp"] - 7 * 86400 * 10**9
        )
write_json(
    ROOT / "results/independent_validation.json",
    {
        "status": "PASS",
        "native_runs": len(runs),
        "closed_trades": trade_count,
        "maximum_trade_identity_error": str(maximum_trade_error),
        "maximum_account_error": str(maximum_account_error),
        "tolerance_USDT": "0.00001",
        "checks": [
            "gross-fees-slippage+funding = net",
            "native final balance-initial balance = sum closed net PnL",
            "signal before execution",
            "adverse slippage",
            "seven-day research embargo",
        ],
    },
)
print("INDEPENDENT FINANCIAL AUDIT PASS", len(runs), trade_count)

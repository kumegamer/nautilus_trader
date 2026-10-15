# Prospective shadow runner

This package never creates a live execution client or calls a Binance order endpoint.
It needs public USD-M market data only. Trading API credentials are neither required
nor read. Nautilus BacktestEngine handles hypothetical orders, fills, positions,
commissions and funding. The same frozen profiles, regime rules, controller, risk
budget and performance monitor are imported by retrospective and shadow runners.

## Operation

Use this repository baseline and its built `python/.venv`. Preserve the Python/Rust
locks and pinned runtime snapshot supplied with the bundle. From repository root:

```bash
PYTHONPATH=evaluation/adaptive_trading_v2 python/.venv/bin/python -m ats.shadow verify
PYTHONPATH=evaluation/adaptive_trading_v2 python/.venv/bin/python -m ats.shadow poll --state /path/to/persistent/v2-state
PYTHONPATH=evaluation/adaptive_trading_v2 python/.venv/bin/python -m ats.shadow replay --state /path/to/persistent/v2-state
```

Schedule one non-overlapping poll every minute using a desktop scheduler or systemd
timer. `deployment/shadow.service` and `shadow.timer` are templates. Replace their
repository/state paths before enabling a user service. No server deployment is
performed by this experiment. Back up SQLite database and WAL consistently using
SQLite backup tooling; do not copy only the database while a writer is active.

The first poll records a forward-start timestamp and exact freeze SHA256, then
downloads at least 40 days of closed 5m bars for indicator warmup. For later
deployments it also backfills the gap from October 2026 for monthly evaluation;
funding is paginated over the same interval. All pre-start data are WARMUP_ONLY,
not prospective performance. The trading replay uses only the fixed 40-day
indicator warmup before the recorded start. All subsequently observed responses are
immutable rows in `market.sqlite`: payload checksum, venue timestamp, observation
timestamp and evidence class. A changed historical candle raises an error and
preserves the original. Gaps block execution until public backfill completes.

Each successful poll replays the complete local journal from the original forward
start. This reconstructs open positions and controller state without a native
pickle or hidden runtime state. No scheduled end liquidation occurs. Pending entries are rechecked for current
eligibility and regime compatibility at the actual observed execution quote. Output files
are replaced atomically only after a successful native accounting reconciliation.
The journal is authoritative; deleting a checkpoint or restarting cannot reset
losses, switch counters or position occupancy. Replay cost grows with history;
archive/checkpoint acceleration is future engineering, not a changed trading rule.

## Forward execution model and availability

Signals are made from completed bars, with forward bar availability delayed to
actual receipt; host clocks must be synchronized. Catch-up bars are processed in causal order at receipt, never
backdated to manufacture fills during an outage. Quotes are the publicly observed
best bid/ask, plus the frozen adverse slippage and taker fee assumptions. Fill
depth remains synthetic, with frozen size/volume caps: top-of-book quantity is
recorded but does not reconstruct queues or partial fills. Stop decisions remain
close-observed and execute at the next observed quote; polling latency is part
of the forward evidence. Open equity marks use the latest completed bar close.

Public funding settlements are recorded with settlement and receipt timestamps;
native shadow funding is applied at receipt to avoid future-information insertion.
Delayed funding can differ from exact exchange boundary-holder accounting. Report
that limitation and observed delays. The journal retains enough evidence for a
separate reconciliation. Warmup funding features are neutral, but no V2 signal or
regime rule uses funding as an input. No spread/latency/partial-fill claim is made.

## Monthly validation and frozen eligibility

The initial eligibility snapshot is the final matured retrospective evaluation.
Each record expires at the next monthly boundary. This runner fails closed when
a fresh gate record is missing. It does not silently extend a stale profile's
permission, waive gates or admit AI proposals. Existing positions retain their
frozen management policy; expired profiles cannot open new positions.

Run the separate monthly validation command after the first collection of a month:

```bash
PYTHONPATH=evaluation/adaptive_trading_v2 python/.venv/bin/python -m ats.shadow validate --state /path/to/persistent/v2-state
```

It reexecutes all frozen central/neighbor profiles and cost scenarios continuously
from the original January 2024 start through the matured cutoff, then purges trades
to the rolling evaluation window. It does not restart flat at each window or
liquidate open positions at the cutoff. It applies the same frozen gates and records new eligibility
in the immutable journal. It requires the checksum-verified historical archives
and prepared rates cache as well as complete collected forward data. Use a separate
monthly job so the minute collector remains responsive. Missing bars or funding
block admission. No retrospective month is backdated: new eligibility is available
only from actual validation completion time and expires at the next month boundary.
The current monthly boundary may precede the first deployment timestamp; this
permits a mid-month start without backdating permission. Boundaries before the
consumed-history cutoff cannot replace the frozen historical evidence.
The evaluator may update evidence for unchanged frozen profiles; it cannot add
profiles, alter parameters or consume research proposals. Changing rules requires
a new version and prospective freeze. Monthly gate evidence derived partly from
consumed training is labeled separately from untouched forward trade performance.

## Prospective assessment

No prospective trading performance is claimed by packaging or testing the runner.
Track forward start, downtime, complete-day coverage, trade count, side/symbol/
regime coverage, costs, funding delays, risk metrics, drawdown, MAE/MFE, decisions,
switches, research triggers and NO_TRADE time separately from all reused history.
Review on elapsed 30/90/180-day milestones and every material risk/execution event;
do not wait for a fixed 50 trades or infer an edge from a sparse winning sample.
At least six months and 100 independent-enough closed trades across two symbols
are necessary descriptive review targets, not proof of a robust edge. Missing
execution evidence or rule changes preclude a stronger conclusion. Every rule
change starts a new version and an untouched forward period.

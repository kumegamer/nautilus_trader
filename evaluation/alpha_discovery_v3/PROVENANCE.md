# Source and data provenance

All new material belongs to evaluation/alpha_discovery_v3. Repository core and
locks are unchanged. Reference objects are inspected by exact commit through git
archive/show/ls-tree; they are never checked out as a work branch or merged.

Read-only evidence:
- Edge v1: 3c669f91dd195266107a2f5b77c5c991565840a8.
- Adaptive v1: 8acc5c4c3138b8057dc1da9f853b9a3a4bb9c4e9.
- Adaptive v2: 57703f7b5f77fed476adef323dc23e43f5a753b0 (user-verified).

The V3 execution-local native.py copies V2's decimal quantization, instrument,
quote-event, market-order, fill, funding and reconciliation mechanics. The old
signal grid and adaptive controller are removed; strategy_factory is mandatory.
strategy.py implements only the new hypotheses. No reuse is called a new edge.
common.py reuses atomic artifacts and timestamp helpers. metrics.py reuses daily
risk and purged closed-trade attribution. data.py/restore.py reuse archive checks,
complete-grid audits and funding handling; V3 additionally retains quote volume
and taker-buy volume. New features, models, strategies, gates, research workflow,
reporting and tests live locally and import no mutable reference package.

All 315 raw archives use exact V2 publisher/frozen hashes, including historical
funding rates and mark-price klines. Funding normalization assumes settlement on
the reported minute; original publication jitter is retained. Signals wait until
original_ms +1 second. Native funding is applied at normalized settlement minute;
no post-open signal can exploit reporting jitter. When a settlement mark-open is
missing, the loader records trade-open proxy valuation explicitly in data/audits.
These uncertainties are reported rather than mistaken for tick-accurate history.

Fixed tick/lot/minimum filters are conservative assumptions and not historical
exchange filter snapshots. Synthetic quotes model adverse fills without observing
historical spread or depth. Decimal native calculations precede floating-point
statistical reporting. Exact financial strings are retained alongside reports.

Runtime dependency locks remain those of the baseline; versions and native binary
identity are recorded in results/runtime_snapshot.json. Feature files are bound
by SHA256 in data/feature_cache_manifest.json. Fixtures are engineering checks,
not market observations. No result-dependent engineering revision was made after
candidate scoring started; any necessary correction must be disclosed separately.

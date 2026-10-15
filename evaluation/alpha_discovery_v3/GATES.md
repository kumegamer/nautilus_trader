# Deterministic profile gates

Frozen before scoring. Missing evidence fails closed. No gate waiver.

VALIDATED_PROFILE requires all of:
- Native accounting, point-in-time data, prefix/future-tail causality and chronological fills pass.
- Positive purged OOS net and PF >=1.10; positive marked OOS PnL; <=15% daily marked DD.
- >=100 purged OOS trades, >=20 in 2025 and >=20 in 2026, >=10 in each of >=4 quarters.
- >=4 of 7 positive OOS quarters, final quarter positive (marked portfolio PnL).
- Independently rerun 1.5x and 2x costs positive, both marked and purged outcomes.
- Both one-coordinate neighbors positive in OOS at base and at least one positive at 2x.
- >=95% positive totals from 4,000 circular seven-calendar-day blocks of synchronized
  daily marked PnL; centered one-sided block test <=.05/16 (Bonferroni, conservative).
- Top trade <=25% of positive trade PnL; largest positive month <=60% of positive
  monthly marked gains; ex-top-one trade net positive. Top5/10 deletion is diagnostic.
- Broad hypotheses: >=2 positive symbols, >=20 trades each, largest symbol <=75%
  positive symbol contributions. CROSS is predefined ETH/SOL specialization and
  still requires both positive. No universal direction/regime profitability rule.
- No opaque rationale, fragile threshold, unexplained leakage, or single-month dependence.
- ML additionally improves marked OOS PnL and Sharpe against the same-side raw control,
  with positive incremental PnL in >=4/7 quarters; otherwise reject ML promotion.

RESEARCH_CANDIDATE requires integrity, positive base/1.5x/2x marked and purged
outcomes, >=60 trades, >=4/7 positive quarters, final quarter positive, <=15% DD,
one positive neighbor and >=80% positive block totals. It may fail stronger gates.
WEAK_SIGNAL requires positive base marked/purged economics and >=20 trades.
Otherwise REJECTED. Controls and exit diagnostics are never promoted.

VALIDATED_PROFILE means historically research-validated on consumed data, never
prospective proof. A VALIDATED_LIBRARY requires >=2 validated profiles from
materially different economic families and absolute daily-return correlation <.80.
One validated profile produces ALPHA_DISCOVERY_CANDIDATES, never a validated library.
No research candidates but weak signals => ALPHA_DISCOVERY_WEAK; no positive adequate
sample signal => ALPHA_DISCOVERY_NO_EDGE. Integrity failure blocks all promotion.

Monthly pseudo-live admission is stricter about time: same core positive economics,
cost/risk/concentration checks, >=60 matured trades, positive last chronological
third and >=2/3 positive thirds, one positive neighbor and >=80% positive blocks.
It never uses OOS full-period classifications to make a past decision. These
eligibility records are not adaptive trading PnL.

# Prospective confirmation reserved, not started

Future confirmation starts strictly after prospective_confirmation_freeze.json's actual UTC
creation time and the chosen observation start, whichever is later. History and
warmup never count as prospective performance. No retrospective replay is forward.

Freeze code, data interpretation, profile definitions, gates, cost/risk model,
dependency versions and initial validated-profile library together. Verify SHA256
before any future run. Future observations must preserve exchange event time and
actual receive time, missing/out-of-order data, hypothetical fills, fees, funding,
sizing and rejections in an append-only local journal. Decisions must use only
information actually received. Reconcile hypothetical accounting independently.
No private credentials or real orders. No collector or server is deployed here.

Initial eligible definitions are exactly those in the frozen library. An empty
library permits observation-only collection; cash is not an alpha validation.
Before collecting, fix a minimum six-calendar-month observation period and 60
closed trades per profile, whichever is later, with a maximum 12-month budget.
At the maximum, insufficient sample fails closed. Apply frozen cost, concentration,
chronology and stability gates to new observations separately from historical data.
Do not repeatedly peek until a profile passes. Report funding, executions and
gaps, and preserve failed observations. A future controller needs its own separate
experiment; this project does not authorize deployment or real-money activation.

Any model, threshold, universe, feature, exit, gate or code change after observing
forward results requires a new version and fresh forward observations. AI proposals
remain inert; they cannot overwrite this bundle, relax gates or activate profiles.

# Effective gate specification

The authoritative gates are the pre-scoring frozen GATES.md and
alpha/evaluate.py. The saved per-profile evidence records every actually enforced
boolean and its supporting counts. No threshold changed after scoring began.

config.json was derived from the execution reference. Its validation dictionary
retains some unused V2 metadata: minimum_symbol_trades=10 and
minimum_positive_neighbors=1 do not control VALIDATED_PROFILE classification.
The actual stricter V3 final gates require two positive symbols with >=20 trades
each and both threshold neighbors positive at base costs, with at least one
neighbor positive at 2x. The one-neighbor rule applies only to the weaker research
candidate / monthly eligibility tier. Final, candidate and rolling sample rules
are deliberately different and are specified explicitly in GATES.md.

The evaluation code uses fixed literal gates so that a configuration edit cannot
silently relax admission. Runtime-changing configuration edits also fail the
source freeze. Future integration must consume the validated profile library and
its full frozen evaluator, not infer promotion rules from unused config fields.
The copied common.assert_specification helper belongs to the earlier reference
format and is not a V3 entry point; V3 uses alpha.workflow.verify_freeze and the
published verification commands. These compatibility leftovers affect neither
native paths nor classifications and should be removed only in a separately
versioned engineering cleanup with equivalence checks.

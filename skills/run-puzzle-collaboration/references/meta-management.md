# Feeder and Meta dependency management

Represent each feeder as a versioned record containing feeder ID/title, answer/language, length definition, source/evidence, status/confidence, transformation, extraction, downstream consumers, version, and last-change reason.

## Dependency rules

1. Use only `已锁定` feeders in final extraction.
2. Keep candidates in a separate exploration column.
3. Mark every Meta claim with the exact feeder versions it consumes.
4. On feeder change, invalidate all downstream results before new reasoning.
5. Reconcile expected feeder count, used count, answer lengths, and extraction length with formulas.
6. Keep missing feeders visible; never silently treat them as irrelevant.

## Failure containment

If a Meta output is readable but depends on an unlocked feeder, use it only to rank candidates. It cannot serve as a local proof. Require every feeder to retain an independent reproducible mechanism.

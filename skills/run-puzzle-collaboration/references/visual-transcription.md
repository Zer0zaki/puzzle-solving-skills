# Visual transcription protocol

Use this protocol only for a full audited transcription or when a final claim depends on exhaustive visual coverage. For readable images or localized uncertainty, inspect directly or transcribe only the relevant regions and continue reasoning with explicit confidence labels.

## Inventory

Assign each image an immutable ID. Record full-image dimensions, orientation, crop relationship, interaction state, and whether colors are original or screenshot-altered.

Create one row per visible unit with image ID and coordinate, literal text or glyph, object type, color/line/direction/layer, OCR or manual source, confidence, user confirmation, and unresolved alternatives.

## Confidence

- `锁定`: user-confirmed or independently reproduced.
- `高`: clear at native resolution.
- `中`: plausible but has a competing reading.
- `低`: blurred, occluded, color-ambiguous, or inferred from context.

Do not use `中` or `低` readings as hard constraints without branching the solve.

## Coverage gate

Before locking a claim that depends on the complete image, confirm every relevant panel and legend is inventoried, every depended-on repeated symbol has a count, ordering is preserved, color and direction categories are explicit, missing material is listed, and interaction changes are separate states.

Do not use the coverage gate to block early observation, localized hypothesis testing, or a candidate that is explicitly independent of uncovered regions.

## Mechanism testing

Share a mechanism-shaping observation before completing the transcript. Test a surviving hypothesis against every row it claims to explain and record counterexamples. A neat fit to a few examples is evidence for a candidate, not a lock.

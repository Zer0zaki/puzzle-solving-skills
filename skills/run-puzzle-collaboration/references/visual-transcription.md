# Visual transcription protocol

Use this protocol before interpreting a dense image puzzle.

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

Before mechanism search, confirm every panel and legend is inventoried, every repeated symbol has a count, ordering is preserved, color and direction categories are explicit, missing material is listed, and interaction changes are separate states.

## Mechanism testing

Test a hypothesis against every transcribed row. Record unexplained rows and counterexamples. A neat fit to a few examples is evidence for a candidate, not a lock.

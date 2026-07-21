# Coverage and lock gate

## Coverage definition

An expected region is covered when it comes from an independently reviewed, image-hash-matched inventory manifest, has a matching detected region row, and has one of these statuses:

- `已转录`: reliable text, confirmed blank, or an explicitly inventoried non-text object;
- `不确定`: observed and recorded, but one or more readings remain unresolved.

`未处理` does not count as covered. Uncertainty is counted as coverage because the evidence is inventoried, but it remains visible and may block downstream claims that depend on that reading. Automatically generated cells do not count as reviewed coverage on the first run.

## Minimum lock requirements

The workbook may display `允许` only when all conditions pass:

1. coverage is at least the configured threshold, default 95%;
2. inventory verification is `是`, with reviewer, timestamp, accepted grid review, and matching image SHA-256;
3. there are no untracked panels or regions;
4. text-bearing material has at least two successful OCR engines, unless the operator records a justified exception;
5. the lock request concerns only evidence covered by the reviewed inventory.

Automatic grid detection or an external region manifest never confirms the inventory by itself and may not define its own coverage denominator. A whole-image fallback is useful for evidence collection but must remain blocked until manually reviewed.

## Two-stage review

1. The automatic run writes `inventory_review_template.json` and reports zero reviewed coverage.
2. The reviewer adds missing panels/legends, marks every expected region `已转录` or `不确定`, accepts or rejects the detected structure, and signs the manifest.
3. `apply_transcription_review.py` validates the image hash, imports decisions without overwriting raw OCR fields, recalculates the gate, and writes a new output directory.

## Status discipline

- Below threshold: only `转录中`.
- Threshold passed but inventory unconfirmed: at most `候选`.
- Inventory confirmed but a depended-on reading is uncertain: at most `高置信`.
- `已锁定`: coverage gate passed, depended-on readings resolved or explicitly branched, and an independent mechanism check succeeded.

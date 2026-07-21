# Output schema

## report.json

- `input`: original image path, dimensions, SHA-256 image identifier, pipeline code hash, and optional after-state path/hash.
- `perspective`: whether correction was applied, detected corners, forward/inverse matrices, output dimensions, and confidence.
- `grid`: detection mode, x/y boundaries or externally supplied region polygons, rows, columns, detector provenance, confidence, and verification state.
- `engines`: requested OCR engines and success/error details.
- `cells`: one record per immutable region ID such as `R03C07`, including pixel bounds, per-engine OCR, fused text, colors, geometry counts, transcription status, and review note.
- `uncertain`: OCR disagreements, single-engine readings, ambiguous glyphs, and visually complex regions with no reliable reading.
- `colors`: clustered RGB/hex samples and proportions per region.
- `geometry`: lines, arrows, intersections, and region associations.
- `difference`: image-alignment method and changed components for before/after inputs.
- `gate`: threshold, independently reviewed expected/covered IDs, missing and unreviewed IDs, manifest validity, inventory confirmation, OCR evidence, permission, and blocking reasons.

## Review manifest

`inventory_review_template.json` contains the immutable image hash, detected structure, expected regions, per-region review status, missing-region queue, reviewer, review time, and inventory confirmation. Importing it creates `inventory_review_applied.json`; raw OCR readings remain unchanged while reviewed/effective text is stored in separate fields.

## CSV outputs

`逐格转录.csv` is the canonical row-wise observation table. `不确定字符.csv` is a filtered queue for manual review. Other CSV files keep color, geometry, difference, and engine evidence separate from interpretation.

Pixel coordinates use the normalized image with a top-left origin. The original image and normalized image are both retained for audit.

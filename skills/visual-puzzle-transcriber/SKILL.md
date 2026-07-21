---
name: visual-puzzle-transcriber
description: Transcribe visual puzzle images before solving them with multi-engine OCR, automatic grid segmentation and coordinates, color sampling and clustering, line/arrow/intersection detection, perspective correction, before/after image difference analysis, uncertainty preservation, and an Excel coverage gate. Use for screenshots, grids, maps, diagrams, symbol panels, colored paths, click-state puzzles, dense image riddles, or any puzzle where visual evidence must be inventoried before inference.
---

# Visual Puzzle Transcriber

Apply the non-negotiable order: **transcribe first, solve second**. Never use context to silently repair OCR output.

## Run the pipeline

Use system Python on macOS because the bundled runtime may not include OpenCV:

```bash
python3 scripts/transcribe_visual_puzzle.py INPUT_IMAGE --output OUTPUT_DIR
```

Apple Vision may fail inside a restricted sandbox with a `CVPixelBuffer` error or `nilError`. If either appears, rerun the same local pipeline with sandbox escalation; do not mark Vision successful unless its engine row actually says `是` and its item count is nonzero for a text-bearing puzzle.

Useful options:

```bash
# Known grid dimensions
python3 scripts/transcribe_visual_puzzle.py puzzle.png --output out --rows 8 --cols 8

# Before/after interaction states
python3 scripts/transcribe_visual_puzzle.py before.png --after after.png --output out

# Import regions produced by an external detector or puzzle-specific adapter
python3 scripts/transcribe_visual_puzzle.py puzzle.png --output out --regions-manifest regions.json

# After reviewing inventory_review_template.json, apply it without rerunning OCR
python3 scripts/apply_transcription_review.py out/report.json reviewed_inventory.json --output reviewed-out
```

Run `python3 scripts/transcribe_visual_puzzle.py --help` for all controls. If the workbook builder cannot resolve `@oai/artifact-tool`, create a `node_modules` symlink at the skill root pointing to the workspace dependency path before retrying.

## Required operating sequence

1. Run the pipeline without interpreting the puzzle. The first run must remain blocked and creates `inventory_review_template.json`.
2. Inspect `annotated_regions.png`, cell crops, OCR engine status, perspective result, and any diff overlay.
3. Open `visual_transcription.xlsx` and review `逐格转录` plus `不确定字符`.
4. Correct uncertain rows without deleting the raw engine candidates.
5. Complete the review manifest only after every panel, legend, repeated mark, color class, direction, and interaction state has a row. Add missing regions instead of silently accepting the detected grid.
6. Run `apply_transcription_review.py`; it writes a new reviewed report and preserves the original automatic evidence.
7. Read the reviewed workbook's `锁定门` result. When it says `禁止`, every pattern remains `候选` or `阶段结论`.
8. Start mechanism search only after the coverage requirement passes. “Fits several cells” is never enough to call a mechanism locked.

## Evidence rules

- Preserve immutable image IDs, region IDs, coordinates, raw OCR candidates, confidence, and engine source.
- Treat OCR disagreement as an uncertainty record, not an invitation to choose the best-looking word.
- Automatic rows can never serve as their own coverage denominator. Coverage is zero until an image-hash-matched review manifest is imported.
- The deprecated `--inventory-verified` shortcut is forbidden; confirmation requires reviewer identity, review time, accepted grid review, and explicit expected regions.
- A whole-image fallback region means grid inventory failed; it must block locking until manually verified.
- Keep perspective-corrected and original images so coordinates remain auditable.
- Keep click states separate; only the diff table may assert a change between them.
- Do not treat automatic arrow heuristics or color names as user-confirmed facts.
- Keep puzzle-specific thresholds, semantic labels, layout assumptions, and extraction rules outside this skill. Specialized adapters may only enter through the generic `--regions-manifest` protocol and are never run by default.

Read `references/output-schema.md` when integrating the JSON/CSV outputs. Read `references/region-manifest.md` before connecting any external detector. Read `references/coverage-gate.md` before changing thresholds or status labels.

## Completion contract

Deliver the following before puzzle solving begins:

- annotated full image and cell crops;
- `逐格转录.csv`;
- `不确定字符.csv`;
- detector evidence tables and `report.json`;
- `visual_transcription.xlsx` with the coverage and lock gate;
- `inventory_review_template.json` on the automatic run and `inventory_review_applied.json` on the reviewed run;
- an explicit list of remaining unverified regions or engine failures.

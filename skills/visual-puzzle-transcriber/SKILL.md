---
name: visual-puzzle-transcriber
description: Read and, when necessary, transcribe puzzle images using manual inspection, targeted OCR, or a full audited pipeline with coordinates, colors, geometry, uncertainty, and coverage tracking. Use only when unclear or exact visual evidence materially affects the requested solve or the user requests a full transcription; do not invoke merely because a puzzle includes an image or because the current workspace is puzzle-related.
---

# Visual Puzzle Transcriber

Extract the smallest amount of reliable visual evidence needed for the current decision. Do not make OCR or artifact production a universal prerequisite for reasoning.

## 1. Pass the necessity gate

Inspect the supplied image before running tools.

- If the relevant content is human-readable, report the observation and continue solving without OCR.
- If only a few regions are unclear, use targeted inspection or OCR on those regions.
- Use the full audited pipeline only when exhaustive coverage, exact coordinates, subtle colors, interaction states, or a durable transcription record materially affects the answer.
- Do not start any visual workflow for a simple non-solving question, status request, feedback, or workspace administration.

The presence of an image is not itself a reason to run OCR.

## 2. Share observations immediately

Tell the user as soon as a visual observation changes the likely mechanism, identifies a candidate, rejects a route, or exposes one precise uncertainty. Do not wait for all cells, files, or engines to finish.

Use a compact update such as:

`[观察/候选] 关键区域显示……；目前不确定的是……；下一步只核验……。`

Communication comes before workbook creation or repair.

## 3. Choose one transcription level

### Level A — direct observation

Use native-resolution viewing, zooming, or a simple crop. Record the literal observation and confidence in chat. Do not create a workbook, manifest, or coverage gate.

### Level B — targeted verification

Inspect or OCR only regions that can change the active hypothesis. Preserve raw readings and competing alternatives. A single reliable engine, clear manual reading, or user confirmation may be sufficient for a working candidate.

Do not require full-image inventory, two-engine agreement, or reviewed coverage for a localized claim. Keep any mechanism that depends on unresolved readings labeled `候选` or branch the alternatives.

### Level C — full audited transcription

Use when the extraction depends on most or all visual units, the layout itself is the mechanism, small color or line differences matter, several interaction states must be compared, or the user explicitly requests exhaustive transcription. Run the pipeline and coverage gate described below.

## 4. Apply an OCR circuit breaker

Use at most one broad OCR attempt and one targeted retry by default.

- If an engine fails, note the failure and use the successful evidence; do not repair every engine unless the missing engine is essential.
- If OCR remains poor, stop troubleshooting and switch to manual zoom/crops, another already-available lightweight reader, or one precise user question.
- Do not spend more time repairing OCR infrastructure than the visual uncertainty is worth to the solve.
- Never stay silent during retries; share the current observation and blocker first.

Context may guide where to inspect, but never silently rewrite raw OCR to fit a hypothesis.

## 5. Run the full pipeline only for Level C

Use system Python on macOS:

```bash
python3 scripts/transcribe_visual_puzzle.py INPUT_IMAGE --output OUTPUT_DIR
```

Useful options:

```bash
# Known grid dimensions
python3 scripts/transcribe_visual_puzzle.py puzzle.png --output out --rows 8 --cols 8

# Before/after interaction states
python3 scripts/transcribe_visual_puzzle.py before.png --after after.png --output out

# Puzzle-specific regions from an external detector or adapter
python3 scripts/transcribe_visual_puzzle.py puzzle.png --output out --regions-manifest regions.json

# Apply a reviewed inventory without rerunning OCR
python3 scripts/apply_transcription_review.py out/report.json reviewed_inventory.json --output reviewed-out
```

Apple Vision may fail in a restricted sandbox. Count Vision only when its engine row reports success and a nonzero item count. Treat one sandbox retry as the targeted retry; if it fails again, continue with other evidence unless Vision is essential.

## 6. Complete Level C proportionally

For a full audited transcription:

1. run the pipeline and retain the automatic evidence;
2. inspect annotated regions, relevant crops, OCR status, perspective output, and diff overlays;
3. review `逐格转录` and `不确定字符`;
4. correct uncertain rows without deleting raw candidates;
5. inventory panels, legends, repeated marks, color classes, directions, and interaction states that the final extraction depends on;
6. apply the review manifest and read the resulting `锁定门`;
7. keep final claims dependent on uncovered or uncertain regions provisional.

Full coverage is required only for claims that depend on the full visual inventory. It does not block unrelated observations, targeted candidates, or early mechanism exploration.

## 7. Preserve evidence at the chosen level

- Keep region coordinates, raw readings, confidence, source, and unresolved alternatives for the regions actually used.
- Treat OCR disagreement as uncertainty, not permission to choose the desired word.
- Keep interaction states separate; use a diff only to assert changes between them.
- Do not treat automatic arrow, color, or geometry heuristics as user-confirmed facts.
- Keep puzzle-specific semantic labels and extraction rules outside the generic OCR pipeline.

Read `references/output-schema.md` when integrating full JSON or CSV outputs. Read `references/region-manifest.md` before connecting an external detector. Read `references/coverage-gate.md` only for Level C or a final claim requiring exhaustive coverage.

## 8. Deliver only what the level needs

For Level A, deliver the observation, confidence, and any uncertainty.

For Level B, deliver the targeted readings or crops, raw alternatives, confidence, and the resulting candidate or next test.

For Level C, deliver the audited evidence needed by the task, normally including annotated images, transcription tables, uncertainty records, the report, the reviewed workbook or manifest, and an explicit list of unresolved regions. Do not generate unused artifacts merely to satisfy a fixed checklist.

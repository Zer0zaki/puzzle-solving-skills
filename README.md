# Puzzle Solving Skills

Private Codex skill collection for high-accuracy puzzle collaboration. The repository contains one authoritative collaboration workflow, its visual-transcription dependency, and a legacy compatibility alias.

## Included skills

### `puzzle-solving`

Legacy compatibility alias. It activates only when the old skill name is explicitly invoked and immediately delegates to `run-puzzle-collaboration`; it contains no independent solving workflow.

### `run-puzzle-collaboration`

Maintains an Excel-first source of truth, separates observations from hypotheses, manages feeder and Meta dependencies, preserves rejected routes, enforces answer verification, and applies the agreed network-research boundary.

### `visual-puzzle-transcriber`

Implements the discipline **transcribe first, solve second** with multi-engine OCR, grid segmentation, coordinate IDs, color analysis, geometry detection, perspective correction, before/after image differencing, uncertainty tables, and an Excel coverage gate.

`run-puzzle-collaboration` invokes `visual-puzzle-transcriber` for image-heavy puzzles. Install all three folders to preserve old prompts without retaining two competing workflows.

## Install locally

Copy the three skill directories into the Codex skills directory:

```bash
rsync -a skills/puzzle-solving/ ~/.codex/skills/puzzle-solving/
rsync -a skills/run-puzzle-collaboration/ ~/.codex/skills/run-puzzle-collaboration/
rsync -a skills/visual-puzzle-transcriber/ ~/.codex/skills/visual-puzzle-transcriber/
```

Restart or open a new Codex session after installation so the skills are rediscovered.

## Usage

For a full puzzle-solving session:

```text
Use $run-puzzle-collaboration to structure, solve, verify, and track this puzzle.
```

For visual transcription only:

```text
Use $visual-puzzle-transcriber to transcribe this image before solving it.
```

## Operating boundaries

- Use the internet for topic knowledge, factual verification, and relevant public databases.
- Do not search for the puzzle source, original instance, write-up, solution, or answer.
- Do not inspect the user's contest browser or authenticated contest interface for material the user has not supplied.
- Keep puzzle-specific adapters and thresholds outside the generic transcription pipeline.
- Treat formal non-visual solvers as an optional fallback, not a default workflow.

## Runtime notes

- The collaboration packet validator requires Node.js.
- The visual pipeline requires Python 3, OpenCV, and NumPy.
- OCR support is opportunistic: macOS Vision uses Swift; RapidOCR and Tesseract require their corresponding local dependencies.
- Excel workbook generation uses the Codex workspace dependency `@oai/artifact-tool` when available.

## Privacy and licensing

This is a private repository. It intentionally excludes contest source material, answer histories, browser data, credentials, caches, and local dependency directories. No public-use license is granted at this stage.

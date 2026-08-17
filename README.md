# Puzzle Solving Skills

Open-source Codex skill collection for fast, evidence-disciplined puzzle collaboration. The repository contains one authoritative collaboration workflow, its on-demand visual-transcription dependency, and a legacy compatibility alias.

## Validation and version

This skill workflow has been tested in two puzzle-hunt competitions: **PnKU3** and **CCBC17**. After each competition, its real-world performance was reviewed and the workflow was further optimized. The current release is **version 1.2**.

## Included skills

### `puzzle-solving`

Legacy compatibility alias. It activates only when the old skill name is explicitly invoked and immediately delegates to `run-puzzle-collaboration`; it contains no independent solving workflow.

### `run-puzzle-collaboration`

Shares testable observations and candidates immediately, distinguishes ordinary questions from real solving requests, and escalates to OCR, workbooks, feeder tracking, or formal verification only when the task requires them. It preserves the agreed network-research boundary and final-answer gate without letting process artifacts block live collaboration.

### `visual-puzzle-transcriber`

Uses a three-level visual workflow: direct observation, targeted verification, or full audited transcription. Full mode retains multi-engine OCR, grid segmentation, coordinate IDs, color and geometry analysis, perspective correction, before/after differencing, uncertainty tables, and an Excel coverage gate; readable or localized evidence no longer requires the full pipeline.

`run-puzzle-collaboration` invokes `visual-puzzle-transcriber` only when unclear or exhaustive visual evidence materially affects the solve. Install all three folders to preserve old prompts without retaining two competing workflows.

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
Use $visual-puzzle-transcriber to inspect this image at the lightest sufficient level and fully transcribe it only if necessary.
```

## Operating boundaries

- A puzzle workspace or image does not by itself trigger a solving or OCR workflow; simple questions receive direct answers.
- Share mechanism-shaping observations, candidates, rejections, and blockers before updating workbooks or repairing tools.
- Use one broad OCR attempt and at most one targeted retry by default, then switch to manual inspection or a precise user question.
- Use the internet for topic knowledge, factual verification, and relevant public databases.
- Do not search for the puzzle source, original instance, write-up, solution, or answer.
- Do not inspect the user's contest browser or authenticated contest interface for material the user has not supplied.
- Keep puzzle-specific adapters and thresholds outside the generic transcription pipeline.
- Treat formal non-visual solvers as an optional fallback, not a default workflow.

## Runtime notes

- The collaboration packet validator requires Node.js.
- The visual pipeline requires Python 3, OpenCV, and NumPy.
- OCR support is optional and opportunistic: macOS Vision uses Swift; RapidOCR and Tesseract require their corresponding local dependencies.
- Excel workbook generation uses the Codex workspace dependency `@oai/artifact-tool` when available.

## Privacy and licensing

This is a public repository released under the [MIT License](LICENSE). It intentionally excludes contest source material, answer histories, browser data, credentials, caches, and local dependency directories.

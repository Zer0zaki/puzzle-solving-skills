---
name: run-puzzle-collaboration
description: Run a high-accuracy, Excel-first puzzle collaboration workflow that separates observations from hypotheses, transcribes visual material before inference, manages feeder and Meta dependencies, preserves rejected routes, and blocks premature final answers with an eight-point verification gate. Use for puzzle hunts, visual or word puzzles, paper puzzles, multi-stage riddles, feeder/Meta structures, repeated corrections, or any solve where incomplete materials and changing assumptions can contaminate downstream reasoning.
---

# Run Puzzle Collaboration

Treat the shared workbook as the live source of truth. Do not let chat prose outrank a confirmed workbook entry.

## 1. Intake before solving

1. Copy `assets/problem-packet-template.md` and fill every required section.
2. Run `scripts/validate_puzzle_packet.mjs <packet.md>`.
3. Stop and request only the missing information marked `BLOCKING` by the validator.
4. Record non-blocking ambiguity as an explicit assumption; never silently normalize it.

Lock the required deliverable, hard constraints, confirmed facts, material inventory, allowed tools, proof level, answer language/length, and time strategy before substantial inference.

## 2. Enforce the network research firewall

Use the internet freely for topic-related knowledge, factual verification, and relevant public databases. Never search for the puzzle's source, original instance, write-up, solution, or answer. Do not query exact titles, distinctive wording, full puzzle text, or puzzle images in ways intended to identify the puzzle.

Never control or inspect the user's browser, authenticated session, contest page, DOM, screenshots, network traffic, or hidden interface state to obtain material the user has not provided. For interactive puzzles, tell the user what action or observation is needed and wait for the user to perform it and return the result.

Keep web-derived background facts separate from puzzle-provided evidence. If a search result unexpectedly appears to reveal the original puzzle or its solution, do not open or use it; record the contamination risk and tell the user. Read `references/network-research-boundary.md` before any online research for a live puzzle.

## 3. Transcribe visual material first

For any image with small text, colors, lines, grids, arrows, layers, or interaction states, invoke `$visual-puzzle-transcriber` and run its local pipeline before proposing a mechanism. Use its Excel `锁定门` as the authoritative coverage check, then copy the reviewed rows into the live collaboration workbook. Read `references/visual-transcription.md` for the evidence discipline.

Do not start mechanism search while the visual workbook reports coverage below threshold. Do not call a mechanism locked until every relevant region is inventoried, uncertain glyphs and colors are marked, the mechanism explains all regions or excludes them with evidence, and at least one independent check succeeds.

## 4. Maintain layered evidence

Keep observations, interpretations, mechanisms, and conclusions in separate workbook columns. Assign every route one status:

- `已锁定`: reproducible and independently checked;
- `高置信`: strong, bounded missing proof;
- `候选`: plausible but not established;
- `争议`: a specific conflict remains;
- `已否定`: tested and retained with the rejection reason.

Never delete rejected routes. Never reuse a rejected route without new evidence.

## 5. Solve at the requested proof level

Use the lightest method that can satisfy the user's requested proof level. If one verified route is enough, return it without building a general model or running an exhaustive search.

Do not load the non-visual formal-solving toolkit by default. Read `references/nonvisual-fallback-toolkit.md` only when two substantive direct routes have stalled, interacting constraints can no longer be tracked reliably, or the user explicitly requires minimum, uniqueness, optimality, or all-solution proof. Stop using the toolkit as soon as a lighter check is sufficient.

## 6. Manage feeder and Meta dependencies

For feeder/Meta tasks, read `references/meta-management.md`. Treat each feeder answer as a versioned dependency with source, language, length, status, transformation, and downstream consumers.

Only `已锁定` feeder answers may support a final Meta claim. Candidates may be used for exploration but must remain visibly provisional. When a feeder changes, invalidate and recompute every dependent extraction.

## 7. Enforce the answer verification gate

Before emitting a final answer, read `references/answer-gate.md` and record evidence for all eight checks. A submission-style answer requires no blocking material gap, complete constraint coverage, matching format, title/hint fit, candidate comparison, an independent check, a reproducible mechanism, and complete delivery.

If any required check fails, label the output `候选` or `阶段结论`; do not present it as final.

## 8. Update after every meaningful round

After each discovery, correction, rejection, or regrouping:

1. update the workbook;
2. propagate affected dependencies;
3. recalculate counts and extraction;
4. report what changed, what is locked, and what remains uncertain;
5. continue solving only after the workbook is current.

Use `assets/feedback-template.md` when the user judges an answer. Record the concrete contradiction even if the official answer is unknown.

## 9. Final response contract

Return, in this order:

1. `最终答案` on its own line, or an explicit candidate/stage label;
2. three to five decisive verification points;
3. remaining risk, if any;
4. the updated collaboration workbook.

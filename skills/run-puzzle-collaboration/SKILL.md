---
name: run-puzzle-collaboration
description: Solve puzzle-hunt, word, visual, feeder, or Meta tasks with rapid hypothesis sharing, proportional evidence, and optional durable tracking. Use only when the user is actually asking to solve, analyze, continue, or formally verify a puzzle; a puzzle workspace, casual question, status request, feedback, or administrative request alone must not trigger this skill.
---

# Run Puzzle Collaboration

Optimize for the earliest testable candidate shared with the user. Preserve evidence and final-answer reliability without letting OCR, workbooks, validators, or polish block useful reasoning.

## 0. Pass the intent gate

Decide whether the current message actually requests puzzle solving.

- Invoke the workflow for an explicit request to solve, analyze, continue, extract, or formally verify a puzzle, or when the user supplies material and clearly asks what it means.
- Do not invoke it for simple questions, explanations, status checks, feedback, workspace administration, or casual conversation merely because they occur in a puzzle workspace.
- If the intent is ambiguous, answer the ordinary question directly. Do not silently upgrade it into a puzzle project.
- If the skill was invoked unnecessarily, stop and answer normally. Do not create files or run tools.

The workspace provides context, not authorization to expand the task.

## 1. Select the lightest sufficient mode

Use `闪答模式` for a self-contained clue, a straightforward observation, a quick candidate check, or any task that can be answered from the supplied material without durable state. Reply directly. Do not create a packet, workbook, dashboard, or formal transcript.

Use `快速协作模式` by default for an active live solve. Keep compact working notes, test the strongest routes, and share useful observations immediately. Reuse an existing workbook only when it already contains relevant state; do not create one by default.

Use `持久协作模式` only for cross-chat handoff, repeated corrections, multiple interacting stages, feeder/Meta dependencies, large state spaces, or a user request for exhaustive or uniqueness proof. In this mode, check for an existing packet and workbook before creating anything. Create or validate a packet only when missing material or durable coordination makes it useful.

Mode upgrades must be justified by task complexity, not by the workspace name or the mere presence of an image.

## 2. Communicate before documenting

Share a core observation as soon as it can change the solve, even if it is provisional. Do not wait for a complete theory, workbook update, OCR run, or polished final response.

Immediately report:

- a mechanism-shaping observation;
- a strong candidate or uniform extraction rule;
- confirmation or rejection of a substantive route;
- a correction that invalidates downstream work;
- a precise blocker or a small fact the user can verify quickly.

Use one or two lines when possible:

`[观察/候选/已验证] 发现了什么；它为什么重要；下一步验证什么。`

User communication precedes workbook maintenance. Never stay silent while troubleshooting tools or building artifacts.

## 3. Run the fast solving pass

Use this order:

1. answer direct clues or identify literal visual structure;
2. identify the likely theme or entity class;
3. inspect awkward, unusually specific, repeated, or unnecessary details;
4. test whether they encode metadata, ordering, indices, or transformations;
5. apply enumeration, title, and hint constraints;
6. broaden to external facts or formal search only when a concrete hypothesis needs it.

Before extracting, state one uniform selector, index, ordering, or transformation rule. Reject routes that require unrelated row-by-row choices or choosing letters after seeing the desired phrase.

Use hard stop-loss rules during live work:

- after roughly 3–5 minutes without traction, share the strongest observations and current route;
- test at most three substantive direct routes before regrouping;
- after roughly 10–15 minutes without a reproducible candidate, report the blocker and change method;
- do not keep working a route merely because much time has already been spent on it.

## 4. Use visual evidence proportionally

Inspect the image manually before launching OCR. Choose one level:

1. `直接观察`: use when the relevant text, structure, colors, or symbols are human-readable. Solve immediately without OCR.
2. `局部核验`: crop or inspect only the unclear regions that can change the current hypothesis. Record competing readings and confidence; no workbook or coverage gate is required.
3. `完整转录`: invoke `$visual-puzzle-transcriber` only when the solution or final extraction materially depends on exhaustive cells, exact geometry, subtle colors, interaction states, or a durable audited record.

OCR is an aid, not a prerequisite for reasoning. Use one broad attempt and at most one targeted retry by default. If OCR or its dependencies still fail, stop troubleshooting, inspect manually, ask the user one precise micro-question, or continue with explicit uncertainty.

Do not lock a final claim that depends on unresolved visual evidence. This restriction does not prevent sharing observations or candidates.

## 5. Apply a lightweight working gate

Before investing in broad research or formal machinery, prefer a route that has:

1. bounded clue or region coverage relevant to the route;
2. one deterministic and reproducible mechanism;
3. exact format or enumeration agreement;
4. one independent semantic, identity, or consistency check.

Passing this gate creates a strong candidate, not necessarily a final answer. Failing it does not justify silence: report the current observation or candidate with its uncertainty.

## 6. Research only when it changes the decision

Use the internet just in time to test a specific hypothesis or verify a surviving candidate. Prefer one authoritative or canonical source sufficient to accept or reject the route.

Never search for the puzzle source, original instance, write-up, solution, answer, exact title, distinctive wording, full puzzle text, or puzzle image. Never inspect the user's contest browser, authenticated session, DOM, network traffic, or hidden state. For interactive puzzles, request the exact user-visible action or observation needed.

Keep web-derived facts separate from puzzle-provided evidence. If a result unexpectedly reveals the source or solution, stop using it, record the contamination risk, and tell the user. Read `references/network-research-boundary.md` before online research for a live puzzle.

## 7. Maintain only useful evidence

Keep observations, interpretations, mechanisms, and conclusions distinct. Mark routes as `已锁定`, `高置信`, `候选`, `争议`, or `已否定`, and preserve a rejected route with its rejection reason when durable tracking is active.

For simple or single-turn work, chat is sufficient. Do not create artifacts for their own sake.

For durable collaboration, batch workbook updates after a meaningful solving round. A meaningful round is a discovery, correction, rejection, regrouping, feeder change, or answer-gate decision. Share the discovery with the user first, then update affected dependencies. Delay styling, dashboards, and full rendering until final delivery or a layout-dependent check.

## 8. Escalate formal solving only when required

Use the lightest method that satisfies the requested proof. Read `references/nonvisual-fallback-toolkit.md` only after two substantive direct routes stall, interacting constraints no longer fit compact notes, or the user explicitly requires uniqueness, minimum, optimality, or all-solution proof. Stop formal tooling once a lighter verification is sufficient.

## 9. Manage feeder and Meta dependencies strictly

For feeder/Meta tasks, read `references/meta-management.md`. Track feeders as versioned dependencies. Candidates may support exploration, but only `已锁定` feeders may support a submission-style final Meta claim. When a feeder changes, invalidate and recompute dependent extraction.

Dependency discipline must not delay reporting the changed feeder or its immediate consequences.

## 10. Use the full answer gate only at finalization

Before presenting a submission-style final answer, read `references/answer-gate.md` and record evidence for all eight checks. Do not apply the eight-point gate to early observations, working hypotheses, or candidates.

If required proof is incomplete, label the result `候选`, `高置信候选`, or `阶段结论`. Do not withhold a useful candidate merely because it is not yet final.

## 11. Process corrections as dependency changes

When the user corrects an answer, record the concrete contradiction if durable tracking is active, preserve unaffected facts, retract dependent hypotheses, and propagate invalidation. Do not defend sunk work.

## 12. Response contracts

For live intermediate collaboration, lead with:

`[观察/候选/已验证] 核心内容 — 置信度 — 下一步。`

For a final response, return:

1. `最终答案`, `候选`, or `阶段结论` plus the answer on the first line;
2. the decisive mechanism or verification points;
3. remaining risk, if any;
4. the collaboration workbook only when one was actually created or changed.

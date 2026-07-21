# Non-visual fallback toolkit

This is optional weak guidance, not part of the default workflow. Do not load it for ordinary solving, require its artifacts in the problem packet, or turn it into an answer gate.

## Activation boundary

Use this reference only when at least one condition holds:

- two substantive direct approaches have stalled without a checkable advance;
- the number of interacting rules or cases makes informal tracking unreliable;
- the user explicitly asks for minimum, uniqueness, optimality, impossibility, or all solutions;
- a correction invalidates several dependent conclusions and selective recomputation is unsafe.

Do not activate it merely because a puzzle contains numbers, words, paths, or multiple clues. Deactivate it once a direct argument or small local check is enough.

## Smallest sufficient escalation

Choose only the minimum layer needed. Do not automatically perform all layers.

1. **Constraint note:** write only the objects, domains, hard rules, goal, permitted operations, and unresolved ambiguities that affect the current blockage.
2. **State/search model:** encode only the relevant state and legal transitions. Prefer a small enumerator over a general solver when the search space is bounded.
3. **Independent checker:** verify a candidate with logic or code that does not repeat the generator's assumptions verbatim.
4. **Proof certificate:** retain the path, explored bound, counterexample, solution count, or optimality comparison needed for the requested claim.

## Method routing hints

Treat these as suggestions, not prescriptions:

| Structure actually blocking progress | Possible fallback |
|---|---|
| unweighted path or state reachability | BFS |
| weighted shortest path | Dijkstra or A* with an admissible heuristic |
| assignment, ordering, or scheduling constraints | backtracking or CP-SAT |
| Boolean or symbolic constraints | SAT or SMT |
| bounded expressions, partitions, or recurrences | enumeration or dynamic programming |
| graph connectivity, matching, flow, or coloring | the corresponding graph algorithm |
| exact-cover structure | exact-cover search such as DLX |

Before searching, make operation permissions explicit only where they change reachability: repetition, inverse operations, division, leading zeros, rotation, reflection, component integrity, reuse, and order.

## Proof-level discipline

- **Feasible:** stop at the first independently verified solution.
- **All solutions:** state the finite search boundary and retain the complete result set.
- **Unique:** produce one solution and show that no second solution exists under the same rules.
- **Optimal:** define the objective, produce a candidate, and show no better candidate exists.
- **Impossible:** show exhaustive coverage, a valid invariant, or a contradiction; lack of discovery is not proof.

## Word and knowledge fallbacks

When a word answer remains ambiguous, check full clue coverage, form and length, standalone dictionary meaning, and corpus or database evidence as needed. Use web sources only within `network-research-boundary.md`: background knowledge and public databases are allowed; searching for the puzzle's source or solution is not.

For feeder and Meta structures, model only the dependencies affected by the blockage. If an upstream answer changes, invalidate and recompute its downstream consumers; do not rebuild unrelated branches.

## Efficiency guardrails

- Estimate the state space and setup cost before coding or invoking a solver.
- Prefer a local calculation, short script, or manual table when it is sufficient.
- Do not create a schema, workbook sheet, solver model, or reusable program unless it is likely to save more time than it costs.
- Time-box exploratory formalization and return to direct reasoning when the model is not reducing uncertainty.
- Never force a puzzle into SAT, CP-SAT, or exhaustive enumeration just because the tool is available.

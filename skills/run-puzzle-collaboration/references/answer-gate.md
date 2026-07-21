# Eight-point answer verification gate

Record evidence, not only pass/fail.

1. **Material completeness** — no missing input can materially change the answer.
2. **Constraint coverage** — every hard constraint is used or intentionally excluded.
3. **Format match** — language, length, count, ordering, and output type match.
4. **Title and hint fit** — the mechanism explains the title and hints without extra inventions.
5. **Candidate competition** — serious alternatives are tested and rejected or bounded.
6. **Independent check** — a second method, source, reverse construction, exhaustive search, or user confirmation agrees.
7. **Reproducibility** — another solver can reproduce the answer from recorded local steps.
8. **Delivery completeness** — every requested sub-answer, route, proof, or minimum claim is included.

## Decision

- 8/8 and no blocking conflict: `最终答案`.
- 6–7/8 with bounded missing proof: `高置信候选`.
- 3–5/8: `候选`.
- 0–2/8 or missing material: `阶段结论`.

Minimum or uniqueness claims require an exhaustive certificate even if all other checks pass.

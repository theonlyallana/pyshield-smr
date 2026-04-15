# tasks/playbook.md — Orchestrator playbook

How the PyShield-SMR Orchestrator plans, routes and verifies work.

## 1. Planning

- Restate the user request in one sentence.
- Decide the smallest valid output (a test? a patch? a full example?).
- Choose the process pattern:
  - *tool use* for a one-off fix,
  - *prompt chaining* for multi-step implementations,
  - *routing* across specialists when the work crosses physics / workflow / QA,
  - *orchestrator-workers* for parallel verification of independent changes,
  - *evaluator-optimizer* when UQ or ALARP tuning is involved.
- Write the plan into `tasks/todo.md` with checkable items.

## 2. Routing

- Physics / numerics → `physics-governor`.
- Transport kernel / MC / point-kernel → `transport-author`.
- Workflow / CLI / HPC → `workflow-author`.
- Report / docs / external-facing text → `technical-author`.
- Tests / CI / audits → `qa-governor`.

For a change that crosses two specialists, pick the one whose invariants are most at risk and assign verification to the other.

## 3. Verification heuristics

- Every physics change: a unit test *and* a regression-value comparison against `tests/integration/regression_values.yaml`.
- Every workflow change: an integration test that runs one example end-to-end.
- Every docs change: `docs-link-check` in CI, plus a peer review if external-facing.
- Never merge a change that only touches physics without running the relevant examples.

## 4. Communication

- When the user asks "will this affect my dose numbers?" — always answer with:
  - a yes / no,
  - the magnitude (from the regression test),
  - the reason,
  - a pointer to the relevant `PHYSICS_CHANGELOG.md` entry.
- Never paraphrase uncertainty. State 95% bounds, or say "no UQ performed."

## 5. Escalation

- If a specialist produces results that disagree with the regression values beyond tolerance, stop and re-plan; do not push through.
- If two specialists disagree on the physics, escalate to `first-principles-analyst` (spawn if not yet registered).

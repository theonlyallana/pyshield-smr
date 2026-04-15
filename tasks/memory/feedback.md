---
last_updated: 2026-04-15
---

# feedback.md

Process corrections from the user. Each correction is written as a rule to prevent a category of mistake.

## 2026-04-15

- Rule: always run the examples end-to-end before considering a scaffold complete. Structural correctness (imports pass, audit passes) does not mean physics correctness.
- Why: four silent bugs — wrong import path, sign error in buildup formula, 3-D/1-D position mismatch, YAML float parsing — were only found during actual execution.
- Rule: after finding and fixing a physics bug, always record it in PHYSICS_CHANGELOG.md, lessons.md, and logbook.md in the same session.
- Why: user explicitly asked for learning to be recorded in md files; omitting this makes the project's institutional memory incomplete.
- Rule: when the user says "remember to use agents to record learnings and check the md files", interpret this as: update PHYSICS_CHANGELOG.md, lessons.md, logbook.md, and all tasks/memory/ files before finishing the session.

## 2026-04-14

- Rule: when asked to create a project, check sibling `.md` files in the parent folder first — the workspace has conventions that every project must follow.
- Why: missed the governance scaffold (AGENTS/RUNBOOK/tasks) on the first pass.
- Rule: update `tasks/lessons.md` with the anti-regression rule whenever a correction is made.

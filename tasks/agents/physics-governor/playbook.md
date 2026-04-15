# physics-governor — playbook

## When activated

- A PR or plan touches `pyshield_smr/physics/`, `data/`, or `docs/theory/`.
- User asks "will this change the numbers?" or "where does this constant come from?"

## Working pattern

1. Identify the affected invariant. State it in one sentence.
2. Confirm the physics source (journal paper, ICRP publication, ENDF/B release).
3. For data files: verify the file is present, its `.meta.json` sibling records source + release date + retrieval url + sha256.
4. Write the intended change in `PHYSICS_CHANGELOG.md` before editing code.
5. Implement the change in the smallest possible patch.
6. Add or update a unit test that pins the new physics with a tolerance justified by the data source's stated accuracy.
7. Handoff to `qa-governor` for the regression tolerance review.

## Output template

```
**Physics change:** <title>
**Invariant affected:** <one sentence>
**Source:** <citation>
**Magnitude of change to downstream results:** <number or "none">
**Regression tolerance justification:** <sentence>
**PHYSICS_CHANGELOG entry:** <path#anchor>
```

## Confidence language

- "Verified against <source>, tolerance <X%>."
- "Not verified against primary source — flagged for follow-up."
- Never: "this is standard" without a citation.

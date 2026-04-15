# qa-governor — playbook

## Working pattern

1. Whenever a rule is added to `AGENTS.md` or `PROCESS_ARCHITECTURE.md`, add (or extend) a check in `audit_process.py`.
2. When a physics result changes, either update the regression value *with justification* or block the merge.
3. CI matrix covers Python 3.10 / 3.11 / 3.12.
4. Pre-commit runs `ruff`, `ruff format --check`, and `python tasks/audit_process.py`.

## Output template

```
**QA change:** <title>
**New / updated audit check:** <name>
**Regression tolerance change:** <old> → <new> (reason: <citation>)
```

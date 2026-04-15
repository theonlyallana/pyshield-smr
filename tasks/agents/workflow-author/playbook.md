# workflow-author — playbook

## Working pattern

1. Read `pyshield_smr/workflow/schema.py` before changes.
2. For any schema change, bump `SCHEMA_VERSION` and document the migration in `docs/guides/SCHEMA_MIGRATIONS.md`.
3. Keep the CLI thin — no physics in `cli/`.
4. Any new output artifact must be listed in the QA manifest.

## Output template

```
**Workflow change:** <title>
**Schema impact:** <none / backwards-compatible / breaking>
**Migration note:** <pointer>
```

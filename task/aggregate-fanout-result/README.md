# aggregate-fanout-result

Aggregate aligned Matrix result arrays inline with Python. No source
artifact, repository script, workspace, or credentials are required.

SKIPPED legs are excluded. Empty input succeeds. Every evaluated leg must report
SUCCESS; malformed JSON, duplicate identifiers, or mismatched arrays fail closed.
`fail-on-non-success=true` fails the Task after writing the aggregate result.

## Parameters

| Parameter | Default | Purpose |
|---|---|---|
| `changed-skills` | `[]` | Skill identifiers aligned with eval-outcomes. |
| `eval-outcomes` | `[]` | Per-skill TEST_OUTPUT JSON values. |
| `fail-on-non-success` | false | Fail the task after writing a non-success result. |

## Results and usage

`TEST_OUTPUT` contains the standardized aggregate result. Use this task for
Tier 1, Tier 2, or publication results, selecting the appropriate Matrix result:

```yaml
- name: gate-tier1
  taskRef:
    name: aggregate-fanout-result
  params:
    - name: changed-skills
      value: $(tasks.catalog.results.skills[*])
    - name: eval-outcomes
      value: $(tasks.evaluate.results.TEST_OUTPUT_TIER_A[*])
    - name: fail-on-non-success
      value: "true"
```

Version 1.0.0 removes `SOURCE_ARTIFACT`, `aggregate-script-path`, and
`should-evaluate`. No application image parameter is required. See [migration](../../docs/migration-cli.md).

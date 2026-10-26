# update-registered-shas

Version 1.0.0 registers only eligible skill IDs from a CLI batch summary, after
the evaluation task has passed its static and required-publication gates.

The single `source` workspace contains discovery's full-history clone at `repo/`
and the evaluation task's evidence under `runs/`.
`batch-manifest` is relative to that workspace and normally comes from
`$(tasks.evaluate-skill.results.batch-manifest)`. `changed-skills` supplies the
expected IDs and `current-sha` supplies the evaluated revision. `should-evaluate`
must be true to perform any registration; false skips the entire task.

The registration script must accept `--current-sha`, `--changed-skills`, and
`--batch-manifest`. It must validate the summary schema, revision, gates, and
exact set of IDs, correlating results by ID. Completed Tier 2 SUCCESS, WARNING,
and FAILURE results are eligible; runtime ERROR, unexecuted, and malformed items
are not. Only the explicit eligible inclusion set is updated. A malformed batch
fails closed. No positional result arrays are accepted.

Git remote, push branch, token Secret/key, bot name/email, TLS behavior, and
registration script path retain their existing parameters. The script runs
against the discovery clone, and the task commits once with `[skip-evaluation]`.
The caller must suppress that marker to avoid recursive evaluation. Registry and
workload credentials are not needed by registration.

```yaml
- name: register
  runAfter: [evaluate-skill]
  taskRef:
    name: update-registered-shas
  params:
    - name: current-sha
      value: $(params.revision)
    - name: should-evaluate
      value: 'true'
    - name: changed-skills
      value: $(tasks.discover.results.changed-skills[*])
    - name: batch-manifest
      value: $(tasks.evaluate-skill.results.batch-manifest)
  workspaces:
    - name: source
      workspace: evaluation-evidence
```

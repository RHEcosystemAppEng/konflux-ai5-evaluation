# Sequential skill evaluation pipeline

Discover changed IDs once, then pass the array to one batch task. There is no
Matrix. The evaluation task emits results before enforcing static and required
publication gates. Trial results remain informational; registration excludes
runtime failures. Separate pipeline runs may execute concurrently.

```yaml
apiVersion: tekton.dev/v1
kind: Pipeline
metadata:
  name: skills-evaluation
spec:
  params:
    - name: revision
      type: string
    - name: source-artifact
      type: string
  workspaces:
    - name: evaluation
  tasks:
    - name: discover
      taskRef:
        name: discover-changed-skills
      params:
        - name: current-sha
          value: $(params.revision)
      workspaces:
        - name: source
          workspace: evaluation
    - name: evaluate
      timeout: 22h
      taskRef:
        name: aeh-skill-eval
      params:
        - name: changed-skills
          value: $(tasks.discover.results.changed-skills[*])
        - name: source-artifact
          value: $(params.source-artifact)
        - name: submission-revision
          value: $(params.revision)
        - name: tiers
          value: '1,2'
        - name: persist
          value: postgres,s3
        - name: timeout-retries
          value: '1'
      workspaces:
        - name: source
          workspace: evaluation
    - name: register
      runAfter: [evaluate]
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
          value: $(tasks.evaluate.results.batch-manifest)
      workspaces:
        - name: source
          workspace: evaluation
```

In production, resolve published bundles by digest: evaluation `2.1.3`,
registration `1.0.0`, and discovery `0.1.0`. The default images use
`v1.0.5-runner` (CLI 0.5.0) and `v1.0.2-trial`, pinned by digest. PostgreSQL
publication requires a fresh evidence schema v2 database. Supply existing Secrets and a trusted source artifact as documented by
the task. Add component `image-url`/`image-digest` to require OCI attachment.
PipelineRun timeouts must exceed the evaluation task's batch duration; the
agentic-plugins pipelines use a 24-hour overall budget, 23-hour tasks budget,
and a 22-hour evaluation task cap. Adjust these budgets for workload size.
Do not configure whole-batch automatic retries.

# Pipeline and task parameters

Expose `tiers` and `persist` as Pipeline parameters and forward them to the
shared task. Defaults below run static checks with no persistence. Set
`tiers=1,2` to add trials, `tiers=2` for trials alone, and `persist=postgres,s3`
to enable those destinations. `image-url` and `image-digest` independently enable OCI evidence.

```yaml
apiVersion: tekton.dev/v1
kind: Pipeline
metadata:
  name: evaluate-skills
spec:
  params:
    - name: tiers
      type: string
      default: "1"
    - name: persist
      type: string
      default: ""
    - name: skills
      type: array
    - name: revision
      type: string
    - name: source-artifact
      type: string
    - name: evaluation-image
      type: string
      default: quay.io/ecosystem-appeng/agent-eval-harness:v1.0-runner@sha256:c4b1f29e5eef8adab45e7d2c9d640af31f82d2b962179f3438a17d0d7065c781
    - name: trial-image
      type: string
      default: quay.io/ecosystem-appeng/agent-eval-harness:v1.0-trial@sha256:c497b4f57d17aa7cfba98a97a1b2d4eca330268a38270a99e39cb77ce71cb226
    - name: image-url
      type: string
      default: ""
    - name: image-digest
      type: string
      default: ""
  workspaces:
    - name: evaluation
  tasks:
    - name: evaluate
      taskRef:
        name: aeh-skill-eval
      matrix:
        params:
          - name: submission-dir
            value: $(params.skills[*])
      params:
        - name: tiers
          value: $(params.tiers)
        - name: persist
          value: $(params.persist)
        - name: submission-revision
          value: $(params.revision)
        - name: source-artifact
          value: $(params.source-artifact)
        - name: evaluation-image
          value: $(params.evaluation-image)
        - name: aeh-image
          value: $(params.trial-image)
        - name: image-url
          value: $(params.image-url)
        - name: image-digest
          value: $(params.image-digest)
      workspaces:
        - name: source
          workspace: evaluation
    - name: gate-static
      taskRef:
        name: aggregate-fanout-result
      params:
        - name: changed-skills
          value: $(params.skills[*])
        - name: eval-outcomes
          value: $(tasks.evaluate.results.TEST_OUTPUT_TIER_A[*])
        - name: fail-on-non-success
          value: "true"
```

Use immutable bundle/image references in deployed pipelines; local task names
are shown for readability. Pass an upstream clone task's trusted artifact result
when composing this with the build pipeline. Model endpoints, workload access,
and persistence Secrets are configured through the shared task's parameters.

Repeat aggregation for `TEST_OUTPUT_TIER_B` and `TEST_OUTPUT_PUBLICATION` when
those results should gate the pipeline. Unrequested tiers report SKIPPED and
are excluded by aggregation. Arrays must contain matching identifiers/outcomes.

GitLab label checks, catalog discovery, and registered-SHA updates remain
separate tasks. The calling pipeline uses their results to choose skills and
parameters. If different skill groups need different tiers, use separate Matrix
invocations with explicit `tiers` values. The evaluation task does not silently
add, remove, or downgrade requested tiers.

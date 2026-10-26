# create-namespace task

Creates an ephemeral namespace `mcp-eval-<run-id>` on the remote target
cluster and grants pipeline ServiceAccount access via a RoleBinding.
Intended to be cleaned up by
[teardown-namespace](../teardown-namespace/README.md) in the pipeline's
`finally` block.

## Parameters

| name | description | default value | required |
|---|---|---|---|
| pipeline-run-id | Pipeline run ID, used to generate a unique namespace name | | true |
| backend-endpoints | Retained for compatibility, not used | `""` | false |

## Results

| name | description |
|---|---|
| namespace-name | Name of the created ephemeral namespace (`mcp-eval-<run-id>`). |

## Workspaces

| name | description |
|---|---|
| target-kubeconfig | Kubeconfig for the target cluster. |

## Usage

```yaml
- name: create-namespace
  taskRef:
    resolver: bundles
    params:
    - name: name
      value: create-namespace
    - name: bundle
      value: "quay.io/ecosystem-appeng/konflux-skill-evaluation/create-namespace:0.1.0@sha256:1f2e332a73461850dee78f4cb79a0185b634548890af8f1fefd298e8ed0197d4"
    - name: kind
      value: task
  params:
  - name: pipeline-run-id
    value: $(context.pipelineRun.name)
  workspaces:
  - name: target-kubeconfig
    workspace: target-kubeconfig
```

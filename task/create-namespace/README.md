# create-namespace task

Creates an ephemeral namespace `mcp-eval-<run-id>` on the remote target
cluster and grants pipeline ServiceAccount access via a RoleBinding.
Intended to be cleaned up by
[teardown-namespace](../teardown-namespace/README.md) in the pipeline's
`finally` block.

## Prerequisites

The ClusterRole `mcp-eval-ephemeral-access` **must already exist** on the
target cluster before this task runs. The RoleBinding created by this task
references it; `oc apply` will not create the ClusterRole automatically and
the step will fail if it is missing.

The ClusterRole must be configured by the target cluster maintainers with
whatever permissions the pipeline ServiceAccount needs inside the ephemeral
namespace.

## Parameters

| name | description | default value | required |
|---|---|---|---|
| pipeline-run-id | Pipeline run ID, used to generate a unique namespace name | | true |
| backend-endpoints | Retained for compatibility, not used | `""` | false |
| pipeline-sa-name | ServiceAccount name to grant access in ephemeral namespace | `mcp-eval-pipeline` | false |
| pipeline-sa-namespace | Namespace of the pipeline ServiceAccount | `default` | false |

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
      value: "quay.io/ecosystem-appeng/konflux-skill-evaluation/create-namespace:0.1.0@sha256:e13fe13e07c8cef435949f929de28478848ad2a9bae4c8ad77e527142625fc9e"
    - name: kind
      value: task
  params:
  - name: pipeline-run-id
    value: $(context.pipelineRun.name)
  workspaces:
  - name: target-kubeconfig
    workspace: target-kubeconfig
```

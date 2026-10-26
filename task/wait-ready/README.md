# wait-ready task

Waits for all Deployments and StatefulSets in the target namespace to
complete rollout, then verifies every pod is Ready. Fails if no workloads
appear, rollout doesn't complete within the timeout, or pods are in an
error state.

Migrated from [agentic_eval_flow](https://github.com/RHEcosystemAppEng/agentic_eval_flow).

## Parameters

| name | description | default value | required |
|---|---|---|---|
| namespace-name | Namespace where the MCP server is deployed | | true |
| readiness-timeout | Maximum seconds to wait for readiness | `120` | false |

## Results

| name | description |
|---|---|
| ready-status | `ready` if all workloads are healthy; not written on failure. |

## Workspaces

| name | description |
|---|---|
| target-kubeconfig | Kubeconfig for the target cluster. |

## Usage

```yaml
- name: wait-ready
  runAfter: [deploy-mcp]
  taskRef:
    resolver: bundles
    params:
    - name: name
      value: wait-ready
    - name: bundle
      value: "quay.io/ecosystem-appeng/konflux-skill-evaluation/wait-ready:0.1.0"
    - name: kind
      value: task
  params:
  - name: namespace-name
    value: $(tasks.create-namespace.results.namespace-name)
  workspaces:
  - name: target-kubeconfig
    workspace: target-kubeconfig
```

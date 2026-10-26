# teardown-namespace task

Deletes the ephemeral evaluation namespace. Runs in the pipeline's
`finally` block to clean up after evaluation completes (success or
failure). Safety check: only deletes namespaces matching the `mcp-eval-*`
prefix. Gracefully handles non-existent namespaces.

Migrated from [agentic_eval_flow](https://github.com/RHEcosystemAppEng/agentic_eval_flow).

## Parameters

| name | description | default value | required |
|---|---|---|---|
| namespace-name | Ephemeral namespace to delete | | true |

## Workspaces

| name | description |
|---|---|
| target-kubeconfig | Kubeconfig for the target cluster. |

## Usage

```yaml
finally:
- name: teardown-namespace
  taskRef:
    resolver: bundles
    params:
    - name: name
      value: teardown-namespace
    - name: bundle
      value: "quay.io/ecosystem-appeng/konflux-skill-evaluation/teardown-namespace:0.1.0"
    - name: kind
      value: task
  params:
  - name: namespace-name
    value: $(tasks.create-namespace.results.namespace-name)
  workspaces:
  - name: target-kubeconfig
    workspace: target-kubeconfig
```

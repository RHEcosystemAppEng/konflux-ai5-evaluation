# teardown-namespace task

Deletes the ephemeral evaluation namespace. Runs in the pipeline's
`finally` block to clean up after evaluation completes (success or
failure). Safety check: only deletes namespaces matching the `mcp-eval-*`
prefix. Gracefully handles non-existent namespaces.

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
      value: "quay.io/ecosystem-appeng/konflux-skill-evaluation/teardown-namespace:0.1.0@sha256:0fb1163f5959263dcc1f95f18aee8f0e12e06cf8eb3298791fc21f74a9f06fb1"
    - name: kind
      value: task
  params:
  - name: namespace-name
    value: $(tasks.create-namespace.results.namespace-name)
  workspaces:
  - name: target-kubeconfig
    workspace: target-kubeconfig
```

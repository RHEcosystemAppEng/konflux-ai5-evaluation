# deploy-mcp task

Deploys an MCP server into an ephemeral namespace on the target cluster
using a Helm chart and test values. The MCP server source repository must
be pre-cloned into the workspace at `_mcp-server-repo`. Copies required
image pull and credential Secrets from the pipeline namespace to the
ephemeral namespace before deployment.

Migrated from [agentic_eval_flow](https://github.com/RHEcosystemAppEng/agentic_eval_flow).

## Parameters

| name | description | default value | required |
|---|---|---|---|
| namespace-name | Ephemeral namespace to deploy into | | true |
| component-image | Built container image from Konflux Snapshot | | true |
| helm-chart-path | Path to Helm chart in the MCP server repo | `chart` | false |
| values-test-path | Path to test values file | `values-test.yaml` | false |
| service-name | K8s Service name for the deployed MCP server | `mcp-server` | false |
| service-port | Port the MCP server listens on | `8080` | false |
| credentials-secrets | Comma-separated Secret names to copy to ephemeral namespace | `""` | false |
| image-key | Helm value key for image repository | `image.repository` | false |
| image-ref-key | Helm value key for image ref | `image.ref` | false |
| image-pull-secret | Image pull Secret name | `image-pull-secret` | false |

## Results

| name | description |
|---|---|
| mcp-url | Internal service URL of the deployed MCP server. |
| release-name | Helm release name. |

## Workspaces

| name | description |
|---|---|
| source | Contains the pre-cloned MCP server repo at `_mcp-server-repo`. |
| target-kubeconfig | Kubeconfig for the target cluster. |

## Secrets

| Secret (param) | Purpose |
|---|---|
| `image-pull-secret` (default `image-pull-secret`) | Image pull credentials, copied from pipeline namespace to ephemeral namespace. |
| `credentials-secrets` (comma-separated) | Additional credential Secrets copied to ephemeral namespace for MCP server use. |

## Usage

```yaml
- name: deploy-mcp
  runAfter: [create-namespace]
  taskRef:
    resolver: bundles
    params:
    - name: name
      value: deploy-mcp
    - name: bundle
      value: "quay.io/ecosystem-appeng/konflux-skill-evaluation/deploy-mcp:0.1.0"
    - name: kind
      value: task
  params:
  - name: namespace-name
    value: $(tasks.create-namespace.results.namespace-name)
  - name: component-image
    value: $(tasks.parse-snapshot.results.component-image)
  workspaces:
  - name: source
    workspace: shared-workspace
  - name: target-kubeconfig
    workspace: target-kubeconfig
```

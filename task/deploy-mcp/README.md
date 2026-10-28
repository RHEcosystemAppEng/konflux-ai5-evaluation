# deploy-mcp task

Deploys an MCP server into an ephemeral namespace on the target cluster
using a Helm chart and test values. The MCP server source repository must
be pre-cloned into the workspace at the `repo-subdir` location (default
`mcp-server-repo`). Copies required
image pull and credential Secrets from the pipeline namespace to the
ephemeral namespace before deployment.

## Parameters

| name | description | default value | required |
|---|---|---|---|
| namespace-name | Ephemeral namespace to deploy into | | true |
| component-image | Built container image from Konflux Snapshot | | true |
| mcp-eval-image | MCP eval image with Helm and pipeline tooling | `quay.io/ecosystem-appeng/abevalflow-mcp-eval:0.1` | false |
| repo-subdir | Subdirectory in workspace for the cloned MCP server repo | `mcp-server-repo` | false |
| service-name | K8s Service name for the deployed MCP server | `mcp-server` | false |
| service-port | Port the MCP server listens on | `8080` | false |
| helm-chart-path | Path to Helm chart in the MCP server repo | `chart` | false |
| values-test-path | Path to test values file | `values-test.yaml` | false |
| image-helm-key | Helm value key for image repository | `image.repository` | false |
| image-ref-helm-key | Helm value key for image ref | `image.ref` | false |
| image-pull-secret-helm-key | Helm value key for image pull secret name | `imagePullSecrets[0].name` | false |
| image-pull-secret | Image pull Secret name | `image-pull-secret` | false |
| credentials-secrets | Comma-separated Secret names to copy to ephemeral namespace | `""` | false |

## Results

| name | description |
|---|---|
| mcp-url | Internal service URL of the deployed MCP server. |
| release-name | Helm release name. |

## Workspaces

| name | description |
|---|---|
| source | Contains the pre-cloned MCP server repo at `repo-subdir` (default `mcp-server-repo`). |
| target-kubeconfig | Kubeconfig for the target cluster. |

## Secrets

Secrets are read from the **Konflux pipeline namespace** (where the
Tekton task pod runs) and copied to the ephemeral namespace on the
target test cluster.

| Secret (param) | Source | Purpose |
|---|---|---|
| `image-pull-secret` (default `image-pull-secret`) | Konflux pipeline namespace | Image pull credentials for the MCP server container image. |
| `credentials-secrets` (comma-separated) | Konflux pipeline namespace | Additional credential Secrets (e.g. backend API keys) needed by the MCP server at runtime. |

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
      value: "quay.io/ecosystem-appeng/konflux-skill-evaluation/deploy-mcp:0.1.0@sha256:497dd68018844303b9e98b245e98b74a727cc9738be9a128f8639c3bec57b898"
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

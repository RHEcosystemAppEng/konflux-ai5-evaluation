# mcp-conformance-eval task

Black-box deterministic conformance probe against a deployed MCP server.
No LLM. Probes the server over Streamable HTTP for protocol, schema, and
HTTP conformance using a three-state model (pass/fail/not_evaluated). Runs
probes as a Kubernetes Job on the target cluster.

Migrated from [agentic_eval_flow](https://github.com/RHEcosystemAppEng/agentic_eval_flow).

## Parameters

| name | description | default value | required |
|---|---|---|---|
| mcp-eval-image | MCP eval image with probe dependencies | `quay.io/ecosystem-appeng/abevalflow-mcp-eval:0.1` | false |
| namespace-name | Ephemeral namespace where MCP server is deployed | | true |
| service-name | K8s Service name of deployed MCP server | `mcp-server` | false |
| service-port | Port MCP server listens on | `8080` | false |
| mode | Gate enforcement mode -- block, warn, or disabled | `block` | false |
| timeout | Per-request HTTP timeout (seconds) | `30` | false |
| job-timeout | Timeout for probe Job (seconds) | `300` | false |
| openapi-url | Explicit OpenAPI contract URL | `""` | false |
| compass-secret | Secret name for Compass SoundCheck credentials | `mcp-eval-compass` | false |
| job-template | Path to K8s Job template inside the image | `/opt/templates/mcp-conformance-eval-job.yaml` | false |

## Results

| name | description |
|---|---|
| conformance-eval-passed | `true` if all conformance probes passed, `false` otherwise. |
| report-path | Workspace-relative path to the generated reports directory. |

## Workspaces

| name | description |
|---|---|
| source | Report output directory. |
| target-kubeconfig | Kubeconfig for the target cluster where the MCP server is deployed. |

## Secrets

| Secret (param) | Keys | Purpose |
|---|---|---|
| `compass-secret` (default `mcp-eval-compass`) | `api-key`, `compass-url`, `entity-ref` | Compass SoundCheck credentials, copied into the ephemeral namespace for probe use. |

## Usage

```yaml
- name: mcp-conformance-eval
  runAfter: [wait-ready]
  taskRef:
    resolver: bundles
    params:
    - name: name
      value: mcp-conformance-eval
    - name: bundle
      value: "quay.io/ecosystem-appeng/konflux-skill-evaluation/mcp-conformance-eval:0.1.0"
    - name: kind
      value: task
  params:
  - name: namespace-name
    value: $(tasks.create-namespace.results.namespace-name)
  workspaces:
  - name: source
    workspace: shared-workspace
  - name: target-kubeconfig
    workspace: target-kubeconfig
```

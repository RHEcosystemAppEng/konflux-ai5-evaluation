# mcp-behavioral-eval task

LLM-driven behavioral evaluation using mcpchecker against a deployed MCP
server. Runs as a Kubernetes Job on the target cluster. Tests tool
correctness, edge-case handling, and sensitive data redaction using
configurable task suites.

## Parameters

| name | description | default value | required |
|---|---|---|---|
| namespace-name | Ephemeral namespace where MCP server is deployed | | true |
| service-name | K8s Service name of deployed MCP server | `mcp-server` | false |
| service-port | Port MCP server listens on | `8080` | false |
| job-timeout | Timeout for mcpchecker Job (seconds) | `1800` | false |
| llm-agent-secret | Secret name for LLM agent credentials | `mcp-eval-llm-agent` | false |
| llm-judge-secret | Secret name for judge LLM model | `mcp-eval-llm-judge` | false |
| llm-ca-secret | Secret name for CA cert bundle for internal LLM endpoints | `mcp-eval-llm-ca` | false |
| mcp-eval-image | MCP eval image with mcpchecker and pipeline code | `quay.io/ecosystem-appeng/abevalflow-mcp-eval:0.1` | false |
| job-template | Path to Job template inside the image | `/opt/templates/mcp-behavioral-eval-job.yaml` | false |
| secrets-namespace | Namespace on the target cluster where LLM secrets are stored | `default` | false |
| pipeline-run-id | Pipeline run ID for provenance | | true |
| submission-name | Component name being evaluated | | true |

## Results

| name | description |
|---|---|
| eval-passed | `true` if behavioral eval passed the pass threshold, `false` otherwise, `error` on failure. |
| report-path | Workspace-relative path to the generated reports directory. |

The pass threshold is currently hardcoded to **0.7** (70%) inside the
`abevalflow` library and is not yet configurable per task. A configurable
`pass-threshold` parameter will be added in a future version.

## Workspaces

| name | description |
|---|---|
| source | Results output directory. |
| target-kubeconfig | Kubeconfig for the target cluster where the MCP server is deployed. |

## Secrets

Secrets are read from the **target test cluster** (in the namespace
specified by `secrets-namespace`, default `default`) and copied into the
ephemeral evaluation namespace.

| Secret (param) | Keys | Source | Purpose |
|---|---|---|---|
| `llm-agent-secret` (default `mcp-eval-llm-agent`) | `openai-api-key`, `openai-base-url`, `anthropic-api-key`, `anthropic-base-url`, `model-name` | Target cluster (`secrets-namespace`) | LLM agent credentials for mcpchecker. |
| `llm-judge-secret` (default `mcp-eval-llm-judge`) | `model` | Target cluster (`secrets-namespace`) | Judge LLM model name. |
| `llm-ca-secret` (default `mcp-eval-llm-ca`) | `ca.crt` | Target cluster (`secrets-namespace`) | CA certificate bundle for internal LLM endpoints. |

## Usage

```yaml
- name: mcp-behavioral-eval
  runAfter: [mcp-conformance-eval]
  taskRef:
    resolver: bundles
    params:
    - name: name
      value: mcp-behavioral-eval
    - name: bundle
      value: "quay.io/ecosystem-appeng/konflux-skill-evaluation/mcp-behavioral-eval:0.1.0@sha256:d351effabf4f6e6bde44feec370eae8abec13d81cdc13bf5104b6d247c1040ee"
    - name: kind
      value: task
  params:
  - name: namespace-name
    value: $(tasks.create-namespace.results.namespace-name)
  - name: pipeline-run-id
    value: $(context.pipelineRun.name)
  - name: submission-name
    value: $(tasks.parse-snapshot.results.component-name)
  workspaces:
  - name: source
    workspace: shared-workspace
  - name: target-kubeconfig
    workspace: target-kubeconfig
```

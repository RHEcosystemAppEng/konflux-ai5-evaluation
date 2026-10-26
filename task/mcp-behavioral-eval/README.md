# mcp-behavioral-eval task

LLM-driven behavioral evaluation using mcpchecker against a deployed MCP
server. Runs as a Kubernetes Job on the target cluster. Tests tool
correctness, edge-case handling, and sensitive data redaction using
configurable task suites.

Migrated from [agentic_eval_flow](https://github.com/RHEcosystemAppEng/agentic_eval_flow).

## Parameters

| name | description | default value | required |
|---|---|---|---|
| namespace-name | Ephemeral namespace where MCP server is deployed | | true |
| service-name | K8s Service name of deployed MCP server | `mcp-server` | false |
| service-port | Port MCP server listens on | `8080` | false |
| job-timeout | Timeout for mcpchecker Job (seconds) | `1800` | false |
| pass-threshold | Minimum score for pass (0.0--1.0) | `0.7` | false |
| llm-agent-secret | Secret name for LLM agent credentials | `mcp-eval-llm-agent` | false |
| llm-judge-secret | Secret name for judge LLM model | `mcp-eval-llm-judge` | false |
| llm-ca-secret | Secret name for CA cert bundle for internal LLM endpoints | `mcp-eval-llm-ca` | false |
| mcp-eval-image | MCP eval image with mcpchecker and pipeline code | `quay.io/ecosystem-appeng/abevalflow-mcp-eval:0.1` | false |
| job-template | Path to Job template inside the image | `/opt/templates/mcp-behavioral-eval-job.yaml` | false |
| pipeline-run-id | Pipeline run ID for provenance | | true |
| submission-name | Component name being evaluated | | true |

## Results

| name | description |
|---|---|
| eval-passed | `true` if behavioral eval passed threshold, `false` otherwise, `error` on failure. |
| report-path | Workspace-relative path to the generated reports directory. |

## Workspaces

| name | description |
|---|---|
| source | Results output directory. |
| target-kubeconfig | Kubeconfig for the target cluster where the MCP server is deployed. |

## Secrets

| Secret (param) | Keys | Purpose |
|---|---|---|
| `llm-agent-secret` (default `mcp-eval-llm-agent`) | `openai-api-key`, `openai-base-url`, `anthropic-api-key`, `anthropic-base-url`, `model-name` | LLM agent credentials for mcpchecker. |
| `llm-judge-secret` (default `mcp-eval-llm-judge`) | `model` | Judge LLM model name. |
| `llm-ca-secret` (default `mcp-eval-llm-ca`) | `ca.crt` | CA certificate bundle for internal LLM endpoints. |

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
      value: "quay.io/ecosystem-appeng/konflux-skill-evaluation/mcp-behavioral-eval:0.1.0"
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

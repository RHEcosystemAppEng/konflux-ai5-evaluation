# mcp-static-eval task

Runs three static checks against MCP server source before deployment:
secrets management (gitleaks), no user-provided code execution (semgrep),
and license compliance (licensee). Resolves to pass/fail only -- no LLM,
no deployment required.

Migrated from [agentic_eval_flow](https://github.com/RHEcosystemAppEng/agentic_eval_flow).

## Parameters

| name | description | default value | required |
|---|---|---|---|
| mcp-eval-image | MCP eval image with scanners and pipeline code | `quay.io/ecosystem-appeng/abevalflow-mcp-eval:0.1` | false |
| source-subdir | Path of MCP server source within workspace to scan | `.` | false |
| mode | Gate enforcement mode -- block, warn, or disabled | `block` | false |
| allowed-licenses | Space-separated approved SPDX ids overriding built-in allow-list | `""` | false |

## Results

| name | description |
|---|---|
| static-eval-passed | `true` if all static checks passed, `false` otherwise. |
| report-path | Workspace-relative path to the generated reports directory. |

## Workspaces

| name | description |
|---|---|
| source | Contains the MCP server source to scan. |

## Usage

```yaml
- name: mcp-static-eval
  taskRef:
    resolver: bundles
    params:
    - name: name
      value: mcp-static-eval
    - name: bundle
      value: "quay.io/ecosystem-appeng/konflux-skill-evaluation/mcp-static-eval:0.1.0"
    - name: kind
      value: task
  params:
  - name: source-subdir
    value: "."
  workspaces:
  - name: source
    workspace: shared-workspace
```

# mcp-static-eval task

Runs three static checks against MCP server source before deployment:
secrets management (gitleaks), no user-provided code execution (semgrep),
and license compliance (licensee). Resolves to pass/fail only -- no LLM,
no deployment required.

## Parameters

| name | description | default value | required |
|---|---|---|---|
| mcp-eval-image | MCP eval image with scanners and pipeline code | `quay.io/ecosystem-appeng/konflux-skill-evaluation/abevalflow-mcp-eval:0.1` | false |
| source-subdir | Path of MCP server source within workspace to scan | `mcp-server-repo` | false |
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
      value: "quay.io/ecosystem-appeng/konflux-skill-evaluation/mcp-static-eval:0.1.0@sha256:5ee89b25e0a4f09cbd7d0fe64f6d170a3f4f1f64c3d3b3f471df4295973a27ca"
    - name: kind
      value: task
  params:
  - name: source-subdir
    value: "."
  workspaces:
  - name: source
    workspace: shared-workspace
```

# mcp-static-eval task

Runs three static checks against MCP server source before deployment:
secrets management (gitleaks), no user-provided code execution (semgrep),
and license compliance (licensee). Resolves to pass/fail only -- no LLM,
no deployment required.

## Parameters

| name | description | default value | required |
|---|---|---|---|
| mcp-eval-image | MCP eval image with scanners and pipeline code | `quay.io/ecosystem-appeng/konflux-skill-evaluation/abevalflow-mcp-eval:0.1` | false |
| source-subdir | Path of MCP server source within workspace to scan | `"."` | false |
| allowed-licenses | Space-separated approved SPDX ids overriding built-in allow-list | `""` | false |

## Results

| name | description |
|---|---|
| report-path | Workspace-relative path to the static evaluation summary JSON (`reports/static-eval-summary.json`). |

## Workspaces

| name | description |
|---|---|
| source | Contains the MCP server source to scan. |
| reports | Persistent workspace for report and result output. |

## Trusted Artifacts variant

A generated OCI Trusted Artifacts variant (`mcp-static-eval-oci-ta`) is
available. It replaces the `source` workspace with a `SOURCE_ARTIFACT`
parameter, pulling the source from OCI instead of a PVC.  Use this
variant in pipelines where a TA-aware git-clone task produces source as
a Trusted Artifact.

## Usage

### Workspace-based (base task)

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
  - name: reports
    workspace: shared-workspace
```

### Trusted Artifacts (oci-ta variant)

```yaml
- name: mcp-static-eval
  taskRef:
    resolver: bundles
    params:
    - name: name
      value: mcp-static-eval-oci-ta
    - name: bundle
      value: "quay.io/ecosystem-appeng/konflux-skill-evaluation/mcp-static-eval-oci-ta:0.1.0"
    - name: kind
      value: task
  params:
  - name: SOURCE_ARTIFACT
    value: $(tasks.git-clone.results.SOURCE_ARTIFACT)
  - name: source-subdir
    value: "."
  workspaces:
  - name: reports
    workspace: shared-workspace
```

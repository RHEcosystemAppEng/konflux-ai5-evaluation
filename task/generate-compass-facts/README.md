# generate-compass-facts task

Generates Compass SoundCheck check-level fact payload files from the static,
conformance, and optional behavioral MCP evaluation phase summaries in a
shared workspace. Each fact file contains data for a single check result.
Phase-level and evaluation-level facts are not generated.

The task validates phase summary JSON files against the schema and produces
fact files with `factRef` and check data. This task does not contact Compass.

## Parameters

| name | description | default value | required |
|---|---|---|---|
| mcp-eval-image | MCP evaluation image containing the fact generator and schemas | `quay.io/ecosystem-appeng/konflux-skill-evaluation/abevalflow-mcp-eval:0.1` | false |
| summary-dir | Workspace-relative directory containing phase summary JSON files | `reports` | false |
| facts-dir | Workspace-relative output directory for generated fact JSON files | `facts` | false |
| component-name | Component name for the Compass entity ref (e.g. my-mcp-server) | | true |
| scorecard-config | Path to the scorecard YAML config file, relative to the task module | `config/scorecard.yaml` | false |

## Results

| name | description |
|---|---|
| facts-dir | Absolute path to the generated facts directory in the workspace. |

## Workspaces

| name | description |
|---|---|
| source | Shared workspace containing evaluation summaries and receiving fact files. |

## Secrets

This task does not read Secrets.

## Usage

```yaml
- name: generate-compass-facts
  runAfter: [mcp-static-eval, mcp-conformance-eval, mcp-behavioral-eval]
  taskRef:
    resolver: bundles
    params:
    - name: name
      value: generate-compass-facts
    - name: bundle
      value: quay.io/ecosystem-appeng/konflux-skill-evaluation/generate-compass-facts:0.1.0@sha256:dcd2fbb53956d5673fb1424ecca3d5fbf3c10e7323fbc002fe06afce3a3cedfe
    - name: kind
      value: task
  params:
  - name: component-name
    value: $(tasks.parse-snapshot.results.component-name)
  workspaces:
  - name: source
    workspace: shared-workspace
```

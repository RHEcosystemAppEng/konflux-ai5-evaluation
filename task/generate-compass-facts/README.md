# generate-compass-facts task

Generates Compass SoundCheck fact payload files from the static,
conformance, and optional behavioral MCP evaluation phase summaries in a
shared workspace. Its runtime assets contain only summary interpretation and
fact generation code plus the phase-summary schema. This task does not contact
Compass.

## Parameters

| name | description | default value | required |
|---|---|---|---|
| mcp-eval-image | MCP evaluation image containing the fact generator and schemas | `quay.io/ecosystem-appeng/abevalflow-mcp-eval:0.1` | false |
| summary-dir | Workspace-relative directory containing phase summary JSON files | `reports` | false |
| facts-dir | Workspace-relative output directory for generated fact JSON files | `facts` | false |

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
      value: quay.io/ecosystem-appeng/konflux-skill-evaluation/generate-compass-facts:0.1.0
    - name: kind
      value: task
  workspaces:
  - name: source
    workspace: shared-workspace
```

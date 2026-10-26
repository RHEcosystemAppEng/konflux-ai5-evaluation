# parse-snapshot task

Parses a Konflux Snapshot JSON to extract the component image, git URL,
revision, and component name. Bridges the Konflux Snapshot model with
parameter-based pipeline tasks.

Migrated from [agentic_eval_flow](https://github.com/RHEcosystemAppEng/agentic_eval_flow).

## Parameters

| name | description | default value | required |
|---|---|---|---|
| SNAPSHOT | Konflux Snapshot JSON string | | true |
| component-name | Specific component to extract (empty = first component) | `""` | false |

## Results

| name | description |
|---|---|
| component-image | Container image reference for the component. |
| git-url | Git repository URL. |
| git-revision | Git commit SHA. |
| component-name | Name of the extracted component. |

## Usage

```yaml
- name: parse-snapshot
  taskRef:
    resolver: bundles
    params:
    - name: name
      value: parse-snapshot
    - name: bundle
      value: "quay.io/ecosystem-appeng/konflux-skill-evaluation/parse-snapshot:0.1.0"
    - name: kind
      value: task
  params:
  - name: SNAPSHOT
    value: $(params.SNAPSHOT)
```

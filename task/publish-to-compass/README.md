# publish-to-compass task

Publishes pre-built fact payload JSON files to Compass SoundCheck. The task
copies Compass credentials into the ephemeral evaluation namespace, mounts
the fact files through a temporary ConfigMap, and runs the publisher as a Job
on the target cluster. The task owns its Compass fact validator and fact
schema; it does not import generation code. Publishing defaults to dry-run
mode.

## Parameters

| name | description | default value | required |
|---|---|---|---|
| mcp-eval-image | Image containing the publisher code and Job template | `quay.io/ecosystem-appeng/konflux-skill-evaluation/abevalflow-mcp-eval:0.1` | false |
| facts-dir | Workspace-relative directory containing fact payload JSON files | `facts` | false |
| namespace-name | Ephemeral namespace on the target cluster | | true |
| compass-secret | Secret containing `api-key`, `compass-url`, and `entity-ref` | `mcp-eval-compass` | false |
| secrets-namespace | Target-cluster namespace containing the Compass Secret | `default` | false |
| configmap-name | Temporary ConfigMap used to mount fact files | `compass-facts` | false |
| dry-run | Set to `false` to publish; otherwise only report intended POSTs | `true` | false |
| job-timeout | Publisher Job timeout in seconds | `120` | false |
| job-template | Publisher Job template path inside the image | `/opt/templates/mcp-compass-publish-job.yaml` | false |

## Results

| name | description |
|---|---|
| publish-status | One of `dry-run`, `published`, `failed`, or `skipped`. |

## Workspaces

| name | description |
|---|---|
| source | Shared workspace containing generated fact files. |
| target-kubeconfig | Kubeconfig Secret workspace for the target cluster. |

## Secrets

| Secret (param) | Keys | Source | Purpose |
|---|---|---|---|
| `compass-secret` | `api-key`, `compass-url`, `entity-ref` | Target cluster (`secrets-namespace`) | Authenticates and identifies the Compass fact destination. |

## Usage

```yaml
- name: publish-to-compass
  runAfter: [generate-compass-facts]
  taskRef:
    resolver: bundles
    params:
    - name: name
      value: publish-to-compass
    - name: bundle
      value: quay.io/ecosystem-appeng/konflux-skill-evaluation/publish-to-compass:0.1.0@sha256:0c5b0b38b69e3384ad94adbf780ec5aec17245dd8db988c0de5fbd0cb3b71d58
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

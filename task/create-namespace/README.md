# create-namespace task

Creates an ephemeral namespace `mcp-eval-<run-id>` on the remote target
cluster, grants pipeline ServiceAccount access via a RoleBinding, and
installs default-deny ingress and egress NetworkPolicies before deployment.
Intended to be cleaned up by
[teardown-namespace](../teardown-namespace/README.md) in the pipeline's
`finally` block.

## Prerequisites

The ClusterRole `mcp-eval-ephemeral-access` **must already exist** on the
target cluster before this task runs. The RoleBinding created by this task
references it; `oc apply` will not create the ClusterRole automatically and
the step will fail if it is missing.

The ClusterRole must be configured by the target cluster maintainers with
whatever permissions the pipeline ServiceAccount needs inside the ephemeral
namespace.

## Parameters

| name | description | default value | required |
|---|---|---|---|
| pipeline-run-id | Pipeline run ID, used to generate a unique namespace name | | true |
| backend-endpoints | Comma-separated sandbox backend IP:port destinations (TCP) | `""` | false |
| llm-endpoints | IP:port destinations allowed only for behavioral Jobs | `""` | false |
| compass-endpoints | IP:port destinations allowed only for conformance/publisher Jobs | `""` | false |
| openapi-endpoints | External OpenAPI IP:port destinations allowed only for conformance Jobs | `""` | false |
| service-port | MCP pod port allowed from evaluator Jobs; match deploy-mcp | `8080` | false |
| dns-namespace | Namespace of the cluster DNS resolver | `openshift-dns` | false |
| dns-port | UDP/TCP DNS endpoint port, after Service translation | `5353` | false |
| pipeline-sa-name | ServiceAccount name to grant access in ephemeral namespace | `mcp-eval-pipeline` | false |
| pipeline-sa-namespace | Namespace of the pipeline ServiceAccount | `default` | false |

## Results

| name | description |
|---|---|
| namespace-name | Name of the created ephemeral namespace (`mcp-eval-<run-id>`). |

## Workspaces

| name | description |
|---|---|
| target-kubeconfig | Kubeconfig for the target cluster. |

## Network access

Endpoint lists use comma-separated literal IP:port pairs (TCP), for example
`192.0.2.10:443,[2001:db8::10]:8443`. Hostnames and URLs are rejected because
standard NetworkPolicy cannot match them. Addresses and ports must match the
destination after Service translation. Empty lists add no external access.
DNS is allowed separately over UDP and TCP.

| Pods | Allowed outgoing traffic beyond DNS |
|---|---|
| MCP/chart pods | Declared sandbox backends only |
| Conformance Job pods | MCP port, declared Compass and external OpenAPI endpoints |
| Behavioral Job pods | MCP port and declared LLM endpoints |
| Publisher Job pods | Declared Compass endpoints only |

Ingress is an explicit pipeline choice beyond the ADR's egress requirement:
only same-namespace conformance and behavioral pods may initiate connections
to MCP/chart pods on `service-port`. Other new application connections are
denied. Replies and node-originated probes follow Kubernetes NetworkPolicy
semantics.

A CNI that enforces NetworkPolicy is required. DNS defaults match OpenShift;
for Kind, set `dns-namespace` to `kube-system` and `dns-port` to `53`.

The target credentials need permission to manage NetworkPolicies in the
created namespace. Install the updated namespace, deployment, conformance,
behavioral, and publishing Task definitions together: the Job Tasks apply
the pod labels selected by these policies.

## Usage

For local testing, install the updated Task YAML directly. Before bundle-based
use, the normal release process must publish the revised bundles and refresh
the digest pins in the usage examples.

```yaml
- name: create-namespace
  taskRef:
    resolver: bundles
    params:
    - name: name
      value: create-namespace
    - name: bundle
      value: "quay.io/ecosystem-appeng/konflux-skill-evaluation/create-namespace:0.1.0@sha256:e13fe13e07c8cef435949f929de28478848ad2a9bae4c8ad77e527142625fc9e"
    - name: kind
      value: task
  params:
  - name: pipeline-run-id
    value: $(context.pipelineRun.name)
  - name: backend-endpoints
    value: $(params.BACKEND_ENDPOINTS)
  - name: llm-endpoints
    value: $(params.LLM_ENDPOINTS)
  - name: compass-endpoints
    value: $(params.COMPASS_ENDPOINTS)
  - name: service-port
    value: $(params.SERVICE_PORT)
  workspaces:
  - name: target-kubeconfig
    workspace: target-kubeconfig
```

The consumer Pipeline must declare and pass these endpoint parameters. If an
external `openapi-url` is configured, also pass its destination through
`openapi-endpoints`. Namespace teardown removes all policies with the namespace.

# aeh-skill-eval

Version 2.0.0 evaluates an explicit array of changed skills through one installed
`abeval batch` invocation. The CLI runs the existing single-skill workflow in
sequence; configured plugin trees, MCP fixtures, tiers, policy, reporting, and
PostgreSQL/S3/Compass persistence are unchanged. Separate pipeline runs may run
concurrently. An empty list is a successful no-op.

## Steps

1. Retrieve the trusted source artifact once.
2. Run `abeval batch`, retaining its manifest and every skill's evidence even
   when one skill fails. Only timed-out AEH arms are retried (default one retry).
3. Package the batch manifest and per-skill reports through `batch-package`.
4. Attach one OCI archive to the component digest using Konflux registry auth
   and the existing task-runner/ORAS image.
5. Validate evidence and emit bounded aggregate results with `batch-results`,
   then fail when static or required-publication gates fail. Tier 2 is informational.

Timeout retries stop the local process group and await cleanup of that
invocation's recorded trial pods before starting another attempt. Other pipeline
runs' pods are never swept. Unconfirmed cleanup prevents further batch trials.
No shell skill loop, new controller, queue, or whole-batch automatic retry is used.

## Parameters

| Parameter | Default | Purpose |
|---|---|---|
| `changed-skills` | `[]` | Ordered catalog skill identifiers; an empty list is a successful no-op. |
| `submission-revision` | `Required` | Evaluated source commit SHA. |
| `source-artifact` | `Required` | Trusted source artifact for the evaluated revision. |
| `evaluation-image` | `quay.io/ecosystem-appeng/agent-eval-harness:v1.0.1-runner@sha256:5ef9d0b539ba19de003362fef8b4dda33c1b077905e700b46442963830a1544e` | Complete CLI image with both scanners, unchanged AEH runtime, model clients, and storage clients. |
| `tiers` | `1` | Evaluation tiers passed directly to the CLI: 1, 2, or 1,2. |
| `aeh-image` | `quay.io/ecosystem-appeng/agent-eval-harness:v1.0-trial@sha256:c497b4f57d17aa7cfba98a97a1b2d4eca330268a38270a99e39cb77ce71cb226` | Trial image pullable by the workload cluster; used for Tier 2. |
| `persist` | `Disabled` | Optional evaluation persistence: postgres,s3,compass. OCI evidence attachment is controlled by image-url and image-digest. |
| `persistence-required` | `true` | Treat selected publication failures as errors. |
| `image-url` | `Disabled` | Built component image repository for OCI report attachment. |
| `image-digest` | `Disabled` | Built component image digest for OCI report attachment. |
| `llm-secret` | `llm-credentials` | Konflux Secret containing api-key for local review and suite-level judging. |
| `llm-api-base` | `Disabled` | OpenAI-compatible review and judge endpoint, normally ending in /v1. |
| `llm-model` | `gemini-2.5-flash` | Submission and optional skill review model. |
| `agent-api-base` | `Disabled` | Agent provider endpoint; for Claude through LiteLLM use the gateway root. |
| `skill-review` | `false` | Enable advisory LLM skill review for every leg. |
| `submission-review` | `auto` | auto honors submission metadata; also accepts on or off. |
| `continue-on-tier1-failure` | `false` | Run selected trials despite blocking static findings. |
| `aeh-model-override` | `Disabled` | Override submission agent model. |
| `aeh-judge-model-override` | `Disabled` | Override submission judge model. |
| `aeh-kubeconfig-secret` | `agentic-plugins-konflux-sa-kubeconfig` | Konflux Secret containing workload kubeconfig under key kubeconfig. |
| `workload-namespace` | `agentic-plugins-evaluation` | Namespace on the workload cluster. |
| `workload-credentials-secret` | `llm-credentials` | Existing workload Secret with native provider SDK environment keys. |
| `workload-service-account` | `Disabled` | Trial service account; empty uses native AEH defaults. |
| `database-secret` | `ab-eval-db-credentials` | Konflux Secret with database-url and optional database-tls-route-host. |
| `s3-secret` | `minio-credentials` | Konflux Secret with endpoint-url, root-user, root-password, optional insecure-skip-tls-verify. |
| `s3-bucket` | `ab-eval-reports` | S3 publication bucket. |
| `compass-secret` | `compass-facts-api` | Konflux Secret containing token. |
| `ca-bundle-configmap` | `trusted-ca-bundle` | Optional Konflux ConfigMap with trusted CA bundle at ca-bundle.crt. |
| `otel-exporter-endpoint` | `Disabled` | Optional OTLP/gRPC collector endpoint. |
| `command-timeout` | `7200` | Timeout in seconds for each external AEH command. |
| `timeout-retries` | `1` | Additional attempts for a timed-out AEH arm; 0-5, never retry verdict failures. |
| `fail-on-non-success` | `true` | Fail after emission when static or required-publication gates fail. |

## Results and workspaces

| Result | Meaning |
|---|---|
| `TEST_OUTPUT_TIER_A` | Aggregate static result; unrequested tiers are excluded. |
| `TEST_OUTPUT_TIER_B` | Aggregate informational trial result. |
| `TEST_OUTPUT_PUBLICATION` | Aggregate application publication plus required OCI attachment. |
| `batch-manifest` | Workspace-relative path to validated `summary.json`. |
| `skill-reports-ARTIFACT_OUTPUTS` | Batch OCI referrer `{uri,digest}`; empty when not requested. |

The `source` workspace holds `runs/<taskrun-name>/batch.json`, `summary.json`,
and isolated per-skill run directories. Detailed outcomes remain in files to
avoid Tekton result limits. Share this workspace with discovery and registration as their
`source` workspace; keep the clone under `repo/` and batch evidence under `runs/`. The source input still comes from the trusted artifact,
not the discovery clone. Allocate batch storage and task/pipeline timeouts for
all selected skills and their bounded timeout retries.

Secrets and ConfigMap names are parameters. The workload kubeconfig is mounted
read-only; workload credentials must already exist in that cluster with native
SDK names. Konflux review, storage, and registry credentials retain their existing
contracts. The optional CA bundle is mounted from `ca-bundle-configmap`.

## Usage

```yaml
- name: evaluate-skills
  taskRef:
    name: aeh-skill-eval
  params:
    - name: changed-skills
      value: $(tasks.discover.results.changed-skills[*])
    - name: submission-revision
      value: $(params.revision)
    - name: source-artifact
      value: $(tasks.clone.results.SOURCE_ARTIFACT)
    - name: tiers
      value: '1,2'
    - name: persist
      value: postgres,s3
  workspaces:
    - name: source
      workspace: evaluation-evidence
```

Build and publish the 0.4.0 CLI runner image before publishing the 2.0.0 task
bundle. Upgrade both pipelines and the 1.0.0 registration task together. Existing
published 1.0.0 evaluation bundles retain their old interface.

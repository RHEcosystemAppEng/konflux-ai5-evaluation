# aeh-skill-eval

Run a skill evaluation with explicit `tiers` and optional `persist` task
parameters. A calling pipeline can expose the same parameters and forward them.
The task passes them directly to one `abeval run` invocation.

## Steps and ownership

| Step | Responsibility |
|---|---|
| `use-trusted-artifact` | Retrieve the pipeline's trusted source snapshot. |
| `evaluate` | Run `abeval run --tiers ... --persist ...`. The CLI stages source, validates, scans, reviews, runs AEH, reports, and persists. |
| `package-oci-reports` | Archive reports and the run manifest using a standard Python image. |
| `attach-oci-reports` | Reuse the existing Konflux task-runner with registry auth, retry, and ORAS. |
| `emit-results` | Convert saved evidence inline using a standard Python image. |

There are no per-phase evaluation steps. The CLI owns operation ordering,
dependencies, failure handling, reporting, and database/S3/Compass publication.
Konflux owns source retrieval, workload credentials, image references, fanout,
and the OCI subject and registry credentials used for evidence attachment.

## Tier and persistence parameters

- `tiers=1` runs static structure, security, and quality checks.
- `tiers=2` runs AEH submission validation/review and trials.
- `tiers=1,2` runs both tiers sequentially.
- `persist=postgres,s3,compass` enables the selected application destinations;
  empty disables them. Credentials alone do not enable publication.
- `image-url` plus `image-digest` independently enable Konflux OCI evidence
  attachment. Leave both empty to skip it.

No label or changed-skill selection is hidden in the task or CLI. The pipeline
selects which skills run and passes their requested tiers. A requested Tier 2
without a submission is an error. Submission metadata owns single/pairwise mode,
review policy, config filenames, models, thresholds, fixtures, and Compass facts.

## Runtime images

`evaluation-image` contains the CLI, both scanners in isolated Python environments,
unchanged upstream AEH, Harbor/Kubernetes, and model/storage clients. `aeh-image`
is required only for Tier 2 trial pods. These are the two project-owned images.

Evidence packaging, result conversion, and aggregation use the standard Red Hat
Python image. OCI attachment reuses the existing digest-pinned Konflux task-runner
and its `select-oci-auth`, `retry`, and `oras` tools. There is no utility image or
OCI client in the CLI. No packages are installed at TaskRun startup.

## Parameters

| Parameter | Default | Purpose |
|---|---|---|
| `submission-dir` | Required | Catalog skill identifier: <pack>/<skill>. |
| `submission-revision` | Required | Evaluated source commit SHA. |
| `source-artifact` | Required | Trusted source artifact for the evaluated revision. |
| `evaluation-image` | Required | Complete CLI image with both scanners, unchanged AEH runtime, model clients, and storage clients. |
| `tiers` | 1 | Evaluation tiers passed directly to the CLI: 1, 2, or 1,2. |
| `aeh-image` | Unset / disabled | Trial image pullable by the workload cluster; required for Tier 2. |
| `persist` | Unset / disabled | Optional evaluation persistence: postgres,s3,compass. OCI evidence attachment is controlled by image-url and image-digest. |
| `persistence-required` | true | Treat selected publication failures as errors. |
| `image-url` | Unset / disabled | Built component image repository for OCI report attachment. |
| `image-digest` | Unset / disabled | Built component image digest for OCI report attachment. |
| `llm-secret` | llm-credentials | Konflux Secret containing api-key for local review and suite-level judging. |
| `llm-api-base` | Unset / disabled | OpenAI-compatible review and judge endpoint, normally ending in /v1. |
| `llm-model` | gemini-2.5-flash | Submission and optional skill review model. |
| `agent-api-base` | Unset / disabled | Agent provider endpoint; for Claude through LiteLLM use the gateway root. |
| `skill-review` | false | Enable advisory LLM skill review for every leg. |
| `submission-review` | auto | auto honors submission metadata; also accepts on or off. |
| `continue-on-tier1-failure` | false | Run selected trials despite blocking static findings. |
| `aeh-model-override` | Unset / disabled | Override submission agent model. |
| `aeh-judge-model-override` | Unset / disabled | Override submission judge model. |
| `aeh-kubeconfig-secret` | agentic-plugins-konflux-sa-kubeconfig | Konflux Secret containing workload kubeconfig under key kubeconfig. |
| `workload-namespace` | agentic-plugins-evaluation | Namespace on the workload cluster. |
| `workload-credentials-secret` | llm-credentials | Existing workload Secret with native provider SDK environment keys. |
| `workload-service-account` | Unset / disabled | Trial service account; empty uses native AEH defaults. |
| `database-secret` | ab-eval-db-credentials | Konflux Secret with database-url and optional database-tls-route-host. |
| `s3-secret` | minio-credentials | Konflux Secret with endpoint-url, root-user, root-password, optional insecure-skip-tls-verify. |
| `s3-bucket` | ab-eval-reports | S3 publication bucket. |
| `compass-secret` | compass-facts-api | Konflux Secret containing token. |
| `ca-bundle-configmap` | trusted-ca-bundle | Optional Konflux ConfigMap with trusted CA bundle at ca-bundle.crt. |
| `otel-exporter-endpoint` | Unset / disabled | Optional OTLP/gRPC collector endpoint. |

## Results and workspace

| Result | Meaning |
|---|---|
| `TEST_OUTPUT_TIER_A` | Tier 1 SUCCESS, FAILURE, or ERROR; SKIPPED when not requested. |
| `TEST_OUTPUT_TIER_B` | Tier 2 SUCCESS, FAILURE, or ERROR; SKIPPED when not requested. |
| `TEST_OUTPUT_PUBLICATION` | Independent status of selected persistence and OCI attachment. |
| `skill-reports-ARTIFACT_OUTPUTS` | `{uri,digest,skill}` for the OCI referrer; empty uri/digest when absent. |

Task steps allow result emission after a failure; gate result content rather
than TaskRun success. Missing selected evidence produces ERROR. Aggregate the
publication result when those destinations are required.
The `source` workspace stores isolated runs at `runs/<taskrun-name>`. Matrix legs
can share it. Source copies and kubeconfigs are excluded from report uploads.

## Credentials

| Parameter | Secret keys / location |
|---|---|
| `llm-secret` | Konflux `api-key` for local review and suite judging. |
| `aeh-kubeconfig-secret` | Konflux `kubeconfig` for workload access. |
| `workload-credentials-secret` | Existing workload-namespace Secret with native SDK keys, such as `ANTHROPIC_API_KEY` and `OPENAI_API_KEY`. |
| `database-secret` | Konflux `database-url`; optional `database-tls-route-host`. |
| `s3-secret` | Konflux `endpoint-url`, `root-user`, `root-password`; optional `insecure-skip-tls-verify`. |
| `compass-secret` | Konflux `token`. |

Registry authentication is selected by the existing Konflux `select-oci-auth`
helper. No registry Secret or file is configured through the application.
The optional CA ConfigMap supplies
`ca-bundle.crt`, including public and private roots for controller clients.
Workload CAs must separately exist in the trial image or workload configuration.
TLS verification remains enabled. Selecting a destination without credentials
records a publication error.

See [pipeline parameter forwarding](../../docs/examples/skills-evaluation-usage.md)
and [migration](../../docs/migration-cli.md).

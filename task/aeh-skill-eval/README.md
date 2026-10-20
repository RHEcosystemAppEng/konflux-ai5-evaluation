# aeh-skill-eval task

Runs a single catalog item's full evaluation as one Task, so a Tekton
`Matrix` can fan out over it natively -- one `TaskRun` per item in the
Matrix source array.

- **Tier A** (`materialize-source`/`security-scan`/`skillmd-scan`) always runs,
  regardless of any opt-in flag -- a non-LLM security + `SKILL.md` quality
  scan over the real on-disk item.
- **Tier B** (`validate`/`quality-review`/`run-eval`) runs for a changed,
  opted-in skill that has an AEH submission. Quality review is advisory.
- **Persistence** (`analyze-and-scorecard`, OCI attachment, `store`) is
  independently gated by `enable-persistence` and can persist Tier A-only
  results when evaluation does not apply.

This Task is already fully generic -- it needs purpose-specific images, params,
and Secrets, with no coupling to any particular source repository (unlike
`check-pr-label`/`discover-changed-skills`/`update-registered-shas`, which
are GitLab-project-specific). It consumes its caller's trusted Source
Artifact via `source-artifact`, never performs its own `git clone`.

**No Trusted Artifacts (`-oci-ta`) variant**: this Task's `source` workspace
is a Matrix-shared scratch PVC (every concurrent leg computes its own
`legs/<slug>` subdirectory under it), not a hand-off of build artifacts
between sequential pipeline Tasks -- see
[.ta-ignore.yaml](../../.ta-ignore.yaml) in the repo root for the full
rationale.

Emits two independent `TEST_OUTPUT` results so a caller can gate on Tier A
(hard, always applicable) separately from Tier B (informational, "SKIPPED"
when not applicable this run) -- see
[aggregate-fanout-result](../aggregate-fanout-result/README.md) for
aggregating these across every Matrix leg. One final `emit-results` step
writes both result files.

Safe for concurrent Matrix legs sharing one workspace: every step except
the final `emit-results` uses `onError: continue` plus a cascading
skip-guard, so one leg's runtime failure never fails that leg's `TaskRun`
(and so never disrupts sibling legs or downstream aggregator Tasks).
`quality-review` also writes the token metrics checkpoint consumed by
`store`, avoiding a standalone bookkeeping step.

When persistence is enabled and the caller supplies a built image URL and
digest, `package-oci-reports` prepares the same report objects uploaded to
MinIO and `attach-oci-reports` attaches them as an OCI artifact to that image
digest before `store` writes to Postgres/MinIO. The OCI archive uses the
`application/vnd.agentic-eval.reports.v1` artifact type. Persistence-disabled
callers (including pull request builds) skip this upload.

Each Matrix leg emits `skill-reports-ARTIFACT_OUTPUTS`, an object with
`uri`, `digest`, and `skill` fields. When a report is attached, `uri` is the
image repository and `digest` is the manifest digest printed by `oras attach`;
combine them as `${uri}@${digest}` to pull the report archive:

```sh
oras pull --registry-config /path/to/auth.json -o ./report \
  "${uri}@${digest}"
```

The object result uses Tekton Chains' `*ARTIFACT_OUTPUTS` type hint, allowing
Chains to record the attached report artifact for the individual skill's
TaskRun. The `skill` field identifies the Matrix leg. The result is emitted
only when an archive was successfully attached; legs that skip attachment
have no report artifact result.

## Parameters

| name | description | default value | required |
|---|---|---|---|
| submission-dir | Catalog item identifier in `submission_dir` form (e.g. `rh-sre/cve-impact`). The real on-disk pack directory is mechanically derived from this. | | true |
| submission-revision | Commit SHA of the repo being evaluated. | | true |
| source-artifact | The caller's own trusted Source Artifact for `submission-revision`, consumed via `use-trusted-artifact` since this Task's pod has no git credentials of its own. | | true |
| image-url | Built component image repository to which this leg's OCI report artifact is attached. | `""` | false |
| image-digest | Digest of the built component image to which this leg's OCI report artifact is attached. | `""` | false |
| should-evaluate | Pipeline-wide (same value for every leg): `"true"` only when the Tier B (LLM) chain is opted in for this run. | `"false"` | false |
| changed-skills | `array`. Full changed-skills array (same value for every leg, NOT a Matrix param); this leg's own `is-changed` flag is derived by membership check against this array. | `[]` | false |
| enable-persistence | Independent of `should-evaluate`/`is-changed`: whether this leg should attempt `analyze-and-scorecard` (Compass Facts), OCI report attachment, and `store` (Postgres/MinIO). | `"false"` | false |
| harness-eval-version | Pinned `harness-eval` version for deterministic `SKILL.md` scanning. | `"7.9.0"` | false |
| llm-api-key | API key for the LLM used by `quality-review`/`run-eval`. | `"sk-dummy"` | false |
| llm-api-base | Base URL of the LLM API. | `""` | false |
| llm-model | LLM model name for `quality-review`. | `"gemini-2.5-flash"` | false |
| aeh-mode | AEH evaluation mode: `single` or `pairwise`. | `"single"` | false |
| task-image | Source preparation, validation, review, reporting, persistence, and result steps. | `"quay.io/ecosystem-appeng/agent-eval-harness:v4.0-task@sha256:f94faf30857634ef9307bf43b5c355fbb286c228747e438366cb60c168e49df5"` | false |
| runner-image | AEH orchestration image for `run-eval`. | `"quay.io/ecosystem-appeng/agent-eval-harness:v4.0-runner@sha256:5fb940342c3c56cd25b5e80ae9684e4ad383bd62bb268083fa3840818a1ef76e"` | false |
| security-scan-image | Cisco deterministic scanner image. | `"quay.io/ecosystem-appeng/agent-eval-harness:v4.0.1-security-scan@sha256:98d0d70e69f5a8d812c9730adaf8ce9a8b1018b4c17b1f0ac027d90718d14b09"` | false |
| skillmd-scan-image | Deterministic SKILL.md scanner image. | `"quay.io/ecosystem-appeng/agent-eval-harness:v4.0-skillmd-scan@sha256:5c35e22bfb5709941d93a88f1f0ecf4393779a9b77204be8ca26132d78311ad9"` | false |
| aeh-image | Trial pod image containing Claude Code, the MCP mock server, and AEH's reward verifier. | `"quay.io/ecosystem-appeng/agent-eval-harness:v4.0-trial@sha256:c8fdca4740c811ea4e4d3dcd411c4d98161374934799df5a0370e06a4635e0b1"` | false |
| aeh-model-override | Explicit model override for `run-eval` (auto-derived from the item's own eval config when empty). | `""` | false |
| aeh-judge-model-override | Explicit judge-model override for `run-eval`. | `""` | false |
| aeh-runner | AEH runner backend (`harbor`). | `"harbor"` | false |
| aeh-control-config | Filename (within the submission) of the control eval config. | `"eval-control.yaml"` | false |
| aeh-treatment-config | Filename (within the submission) of the treatment eval config. | `"eval-treatment.yaml"` | false |
| aeh-kubeconfig-secret | Name of an optional Secret holding a kubeconfig for a remote evaluation cluster. | `"agentic-plugins-konflux-sa-kubeconfig"` | false |
| workload-namespace | Kubernetes namespace on the (remote or in-cluster) evaluation cluster to run the workload in. | `"agentic-plugins-evaluation"` | false |
| otel-exporter-endpoint | Optional OTLP gRPC endpoint for tracing (Tier B chain only); inert when empty. | `""` | false |
| mock-mcp-binary | Path to the generic mock-MCP-server entrypoint baked into the trial image, used by the `swap-mock-mcp` step for per-skill fixture-backed MCP mocking. | `"/opt/mock-mcp/src/server.py"` | false |

## Results

| name | description |
|---|---|
| TEST_OUTPUT_TIER_A | Standardized Konflux test output derived only from `materialize-source`/`security-scan`/`skillmd-scan` -- the hard gate. |
| TEST_OUTPUT_TIER_B | Standardized Konflux test output derived from the Tier B (LLM) chain when it actually ran this leg; `{"result": "SKIPPED", ...}` otherwise. |
| skill-reports-ARTIFACT_OUTPUTS | Per-skill OCI report artifact object (`uri`, `digest`, `skill`), type-hinted for automatic Tekton Chains collection. |

## Workspaces

| name | description |
|---|---|
| source | Shared across ALL concurrent Matrix legs (one leg per item). Each step computes its own `legs/<slug>` subdirectory first. |

## Secrets

| Secret (param) | Key | Required | Purpose |
|---|---|---|---|
| `aeh-kubeconfig-secret` (default `agentic-plugins-konflux-sa-kubeconfig`) | `kubeconfig` | optional | Kubeconfig for a remote evaluation cluster (`run-eval`); when absent, evaluation runs against the Task's own in-cluster credentials. |
| `compass-facts-api` | `token` | optional | API token for pushing Compass Facts (`analyze-and-scorecard`). |
| `ab-eval-db-credentials` | `database-url`, `database-tls-route-host` | optional | Postgres connection string / TLS tunnel route host for persisting results (`store`). |
| `minio-credentials` | `endpoint-url`, `root-user`, `root-password`, `insecure-skip-tls-verify` (optional key) | optional | MinIO/S3 credentials for publishing report artifacts (`store`). Set `insecure-skip-tls-verify: "1"` when `endpoint-url` is only reachable through a Route/Ingress with a self-signed or internal-CA certificate. |
| `llm-credentials` *(indirect)* | n/a | n/a | Not a `secretKeyRef` on this Task -- `run-eval` sets `AGENT_EVAL_K8S_CREDENTIALS_SECRET=llm-credentials` so the harness's own remote-workload runner knows which Secret name to use on the target evaluation cluster. |

No ConfigMaps are used by this Task.

## Image release and usage

Version `0.8.1` is published with the five runtime images listed in the parameter
table. They share `quay.io/ecosystem-appeng/agent-eval-harness`, using the
`v4.0` prefix and one purpose suffix per image, except for the patched Cisco
scanner, which uses `v4.0.1-security-scan`. Each reference is pinned to its
verified registry digest. The scanner accepts space-separated `allowed-tools`
without changing the HIGH severity gate. Callers overriding
`AEH_IMAGE` must select the `-trial` image. Remove the obsolete
`workload-credentials-secret` task argument when upgrading; the runtime
continues to use the target cluster's `llm-credentials` secret.

The existing Konflux trusted-artifact and ORAS steps use their own images.
Runtime steps do not install Python dependencies. `aeh-image` is the trial
image; `runner-image` is the image executing the orchestration step.

The example below resolves the published `0.8.1` bundle by digest.

```yaml
- name: evaluate-skill
  runAfter:
  - discover-changed-skills
  - build-image-index
  matrix:
    params:
    - name: submission-dir
      value: $(tasks.discover-changed-skills.results.changed-skills[*])
  taskRef:
    resolver: bundles
    params:
    - name: name
      value: aeh-skill-eval
    - name: bundle
      value: quay.io/ecosystem-appeng/konflux-skill-evaluation/aeh-skill-eval:0.8.1@sha256:aaf5d06843a90c93be5a9bce79526540b9083d4315905ae1dcf3a2c123e3bea5
    - name: kind
      value: task
  params:
  - name: submission-revision
    value: $(params.revision)
  - name: source-artifact
    value: $(tasks.clone-repository.results.SOURCE_ARTIFACT)
  - name: image-url
    value: $(tasks.build-image-index.results.IMAGE_URL)
  - name: image-digest
    value: $(tasks.build-image-index.results.IMAGE_DIGEST)
  - name: should-evaluate
    value: $(tasks.check-pr-label.results.should-evaluate)
  - name: changed-skills
    value: $(tasks.discover-changed-skills.results.changed-skills[*])
  - name: enable-persistence
    value: "true"
  workspaces:
  - name: source
    workspace: shared-workspace
```

Then aggregate every leg's results with
[aggregate-fanout-result](../aggregate-fanout-result/README.md) -- see
[docs/examples/skills-evaluation-usage.md](../../docs/examples/skills-evaluation-usage.md)
for the full end-to-end wiring.

# aeh-skill-eval task

Runs a single catalog item's full evaluation as one Task, so a Tekton
`Matrix` can fan out over it natively -- one `TaskRun` per item in the
Matrix source array.

- **Tier A** (`clone-repo`/`security-scan`/`skillmd-scan`) always runs,
  regardless of any opt-in flag -- a non-LLM security + `SKILL.md` quality
  scan over the real on-disk item.
- **Tier B** (`validate`/`quality-review`/`aeh-eval-check`/
  `write-metrics-checkpoint`/`run-eval`/`analyze-and-scorecard`/`store`),
  the LLM-cost evaluation chain, only runs for a leg that is both changed
  (per `changed-skills`) and opted in (`should-evaluate`) this run.

This Task is already fully generic -- it needs only its own image, params,
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
aggregating these across every Matrix leg.

Safe for concurrent Matrix legs sharing one workspace: every step except
the final `emit-tier-a`/`emit-tier-b` uses `onError: continue` plus a
cascading skip-guard, so one leg's runtime failure never fails that leg's
`TaskRun` (and so never disrupts sibling legs or downstream aggregator
Tasks).

## Parameters

| name | description | default value | required |
|---|---|---|---|
| submission-dir | Catalog item identifier in `submission_dir` form (e.g. `rh-sre/cve-impact`). The real on-disk pack directory is mechanically derived from this. | | true |
| submission-revision | Commit SHA of the repo being evaluated. | | true |
| source-artifact | The caller's own trusted Source Artifact for `submission-revision`, consumed via `use-trusted-artifact` since this Task's pod has no git credentials of its own. | | true |
| should-evaluate | Pipeline-wide (same value for every leg): `"true"` only when the Tier B (LLM) chain is opted in for this run. | `"false"` | false |
| changed-skills | `array`. Full changed-skills array (same value for every leg, NOT a Matrix param); this leg's own `is-changed` flag is derived by membership check against this array. | `[]` | false |
| enable-persistence | Independent of `should-evaluate`/`is-changed`: whether this leg should attempt `analyze-and-scorecard` (Compass Facts) and `store` (Postgres/MinIO) at all. | `"false"` | false |
| harness-eval-version | Pinned `harness-eval` version for deterministic `SKILL.md` scanning. | `"7.9.0"` | false |
| llm-api-key | API key for the LLM used by `quality-review`/`run-eval`. | `"sk-dummy"` | false |
| llm-api-base | Base URL of the LLM API. | `""` | false |
| llm-model | LLM model name for `quality-review`. | `"gemini-2.5-flash"` | false |
| aeh-mode | AEH evaluation mode: `single` or `pairwise`. | `"single"` | false |
| aeh-image | Container image AEH uses for the evaluation workload. | `"quay.io/ecosystem-appeng/agent-eval-harness:v1.2.1"` | false |
| aeh-model-override | Explicit model override for `run-eval` (auto-derived from the item's own eval config when empty). | `""` | false |
| aeh-judge-model-override | Explicit judge-model override for `run-eval`. | `""` | false |
| aeh-runner | AEH runner backend (e.g. `harbor`). | `"harbor"` | false |
| aeh-control-config | Filename (within the submission) of the control eval config. | `"eval-control.yaml"` | false |
| aeh-treatment-config | Filename (within the submission) of the treatment eval config. | `"eval-treatment.yaml"` | false |
| aeh-kubeconfig-secret | Name of an optional Secret holding a kubeconfig for a remote evaluation cluster. | `"agentic-plugins-konflux-sa-kubeconfig"` | false |
| workload-namespace | Kubernetes namespace on the (remote or in-cluster) evaluation cluster to run the workload in. | `"agentic-plugins-evaluation"` | false |
| workload-credentials-secret | Name of a Secret the harness runner provisions for the evaluation workload (consumed indirectly by the harness image itself, not by this Task's own script -- see Secrets below). | `"workload-cluster-credentials"` | false |
| enable-aeh-eval-check | When `"true"`, runs the advisory AEH harness-inventory scan (no gate consumes its output). | `"false"` | false |
| otel-exporter-endpoint | Optional OTLP gRPC endpoint for tracing (Tier B chain only); inert when empty. | `""` | false |
| mock-mcp-binary | Path to the generic mock-MCP-server entrypoint baked into this Task's image, used by the `swap-mock-mcp` step for per-skill fixture-backed MCP mocking. | `"/opt/mock-mcp/src/server.py"` | false |

## Results

| name | description |
|---|---|
| TEST_OUTPUT_TIER_A | Standardized Konflux test output derived only from `clone-repo`/`security-scan`/`skillmd-scan` -- the hard gate. |
| TEST_OUTPUT_TIER_B | Standardized Konflux test output derived from the Tier B (LLM) chain when it actually ran this leg; `{"result": "SKIPPED", ...}` otherwise. |

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

## Usage

```yaml
- name: evaluate-skill
  runAfter:
  - discover-changed-skills
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
      value: "quay.io/ecosystem-appeng/konflux-skill-evaluation/aeh-skill-eval:0.2.0@sha256:67dd9be7e223322b1101810fdcbc4020f469ffaf95ec4323507f3de76718d90b"
    - name: kind
      value: task
  params:
  - name: submission-revision
    value: $(params.revision)
  - name: source-artifact
    value: $(tasks.clone-repository.results.SOURCE_ARTIFACT)
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

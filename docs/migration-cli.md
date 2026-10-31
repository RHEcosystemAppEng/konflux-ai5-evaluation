# CLI task migration (1.0.0)

## Score summaries, evidence schema, and trial concurrency (evaluation 2.1.3, CLI 0.5.0)

Use `v1.0.5-runner` with the existing `v1.0.2-trial` image, both pinned by
digest. Upgrade the evaluation task bundle to `2.1.3`; discovery, label checking,
and registration retain their existing interfaces and versions.
The task exposes `n-concurrent` for maximum concurrent AEH trial cases; the
agentic-plugins pipelines set it to `2`.

Configure PostgreSQL publication against a fresh evidence schema v2 database.
The CLI rejects the old schema and does not delete or migrate it. Evaluation
records include plugin/skill identity, commit SHA, the built content image,
linked arm/case/judge scores, pairwise outcomes, severity counts, and S3 evidence
references. The task passes `image-url@image-digest` as `ABEVAL_BUILT_IMAGE_REF`
for each evaluated skill whenever a built component image is available.

S3 report keys now include the plugin: `<plugin>/<skill>/<run-id>/reports/`.
Publication status remains in `run.json`. Skill loading, trial execution, and
the registration contract are unchanged.

## Sequential batch upgrade (evaluation 2.0.0, registration 1.0.0)

Use the `v1.0.1-runner` image with CLI 0.4.0 and the versioned batch evaluation
task. Replace the pipeline's Matrix and `submission-dir` with an ordinary
`changed-skills` array parameter. Remove the three `aggregate-fanout-result`
callers: the task now emits small aggregate Tier A, Tier B, and publication
results, then enforces static and required-publication gates. Tier B remains
informational. Per-skill evidence is in `batch.json`, child `run.json` files,
and validated `summary.json`, avoiding large Tekton arrays.

Upgrade registration together: replace `eval-outcomes` with `batch-manifest`
and share one workspace across discovery, evaluation, and registration.
Keep the mutable clone under `repo/` and trusted-source evaluation evidence under
`runs/`; registration mounts only one PVC workspace. Register
only explicit eligible skill IDs with matching source revisions; errors and
unexecuted skills keep their previous SHAs. Suppress the new `[skip-evaluation]`
bot marker; retaining suppression of historical `[skip-fanout]` commits is safe.

The CLI owns sequential orchestration and bounded timeout-only AEH arm retries.
Single-skill `abeval run`, plugin loading, scoring, reports, persistence, and
per-tier policies remain unchanged. No PipelineRun concurrency limit is added.
OCI now attaches one batch archive. The runner/trial images retain the same AEH
pin. Rebuild/publish images and bundles, then update consumers to verified digests.
See the [current example](examples/skills-evaluation-usage.md).

The 1.0.0 migration below describes the previous release and its old interface.


Use the CLI-based runtime images with the 1.0.0 evaluation and aggregation tasks.
Older published bundles retain their existing interfaces. Do not mix the new
images with script-based bundles: the compatibility scripts have been removed.
Build and publish the runtime images and bundles, then update pipeline references
together. No image tags or digests in this document imply a published release.

## Pipeline changes

| Existing input | CLI task input |
|---|---|
| Per-phase task, runner, and scanner image inputs | `evaluation-image` for the complete workflow; existing upstream images handle OCI/results. |
| `should-evaluate`, `changed-skills` | Pipeline selects skills and forwards `tiers=1`, `2`, or `1,2`. |
| `enable-persistence=true` | Explicit `persist=postgres,s3,compass`, selecting required destinations. |
| `image-url` and `image-digest` | Retained as `image-url` and `image-digest` for the existing Konflux attachment step. |
| `llm-api-key` | `llm-secret` with `api-key`. |
| `llm-api-base` | Review/judge endpoint, normally ending in `/v1`. |
| Agent reused review URL | `agent-api-base`, normally gateway root for Claude/LiteLLM. |
| Mode and control/treatment config parameters | Submission `metadata.yaml`. |
| `aeh-runner`, `mock-mcp-binary`, `harness-eval-version` | Removed; runtime image owns installed tools and versions. |
| Aggregator source artifact and script parameters | Removed; aggregation is inline Python with no application image. |

Expose `tiers` and `persist` in the Pipeline and forward them to the Task as in
[the example](examples/skills-evaluation-usage.md). A direct TaskRun can set them
without a Pipeline. Defaults are Tier 1 and no application persistence.
Only one task step runs evaluation, through `abeval run`. Trusted source
retrieval, evidence packaging, OCI attachment, and inline result projection remain separate.

The existing Tier A/B result names represent CLI Tiers 1/2. Either can be
SKIPPED when not requested. Aggregate `TEST_OUTPUT_PUBLICATION` to gate required
storage and OCI attachment. OCI attachment uses the existing Konflux task-runner and stays outside CLI
persistence. Its outcome is combined with application storage status in the task.

Tier 2 stops after blocking Tier 1 findings by default. Set
`continue-on-tier1-failure=true` to collect trials despite those findings. A
requested Tier 2 without a submission is an error; no silent fallback applies.

## Credentials and storage

OCI registry authentication uses the existing Konflux `select-oci-auth` helper.
No application OCI flags, registry settings, or utility image are required.

The workload Secret must already exist on the workload cluster with native SDK
keys. A Konflux Secret containing only `api-key` provides the controller's
review/judge credential and does not populate workload pods. Set
`workload-credentials-secret` and `workload-service-account` explicitly where
needed. No production MCP servers are registered: trials use submission fixtures.

Provide trusted private CA roots through `ca-bundle-configmap`; verification is
enabled for model, database route, and storage clients. The PostgreSQL Secret's
optional `database-tls-route-host` works through the CLI; its database URL must
use a loopback host. The CLI creates a private ephemeral tunnel port.

CLI report storage uses `<skill>/<run-id>/reports/` plus `run.json`, replacing the
old timestamp prefix and hand-selected upload paths. OCI archives use the same
report evidence, including native AEH artifacts under `reports/`. Run directories
are `source/runs/<taskrun-name>`, replacing `source/legs/<skill-slug>`.

## Validation

Run `make yamllint`, `make versioning-check`, and `make ta-check` for local checks.
Tekton integration tests under `task/*/tests/` accept the new image
references as Pipeline parameters and require a cluster. Build bundles separately
when ready to release.

The shared integration runner accepts image parameters from a JSON file:

```json
{
  "evaluation-image": "registry.example/evaluator:runner"
}
```

```sh
TASK_TEST_PARAMS_FILE=/path/to/images.json .github/scripts/test_tekton_tasks.sh \
  task/aeh-skill-eval task/aggregate-fanout-result
```

Only parameters declared by each test Pipeline are forwarded. The file contains
runtime image references, not model credentials. The CI task-test job can supply
`TASK_TEST_PARAMS_FILE` through its environment when testing a published runtime.

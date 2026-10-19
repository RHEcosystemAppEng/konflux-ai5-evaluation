# Changelog

## Unreleased

### AEH runtime image refresh (0.8.0)

- Build and publish the five AEH runtime images as `v4.0` purpose-specific
  tags, and pin the Task defaults to their registry digests.
- Republish the `aeh-skill-eval` bundle as `0.8.0` with the refreshed images.

### AEH-only runtime cleanup (0.7.0)

- Split task utilities, Cisco scanning, SKILL.md scanning, AEH orchestration,
  and trial execution into separately selectable images. `aeh-image` selects
  the trial image; new step-image parameters select the other four purposes.
- Use AEH report rendering directly and remove the classic Harbor analysis,
  MCPChecker report, scaffold generation, and image-promotion branches.
- Remove runtime OTLP dependency installation; dependencies are baked into
  the task image. Read kubeconfig namespaces with the Kubernetes Python client.
- Remove the unused `workload-credentials-secret` task input,
  `security_scan_use_llm` metadata field, and unused
  metadata-derived scan flags; enforce the baked harness-eval version.
- Published test images in the original `agent-eval-harness` repository with
  prefix `v3.0-test-20261019-021235` and five purpose suffixes; bundle `0.7.0`
  pins every image digest. Updated both agentic-plugins pipeline bundle pins.

### Changed

- Pass the selected eval configuration into report aggregation so integer
  scores on declared numeric ranges are normalized correctly.
- Update the AEH image to `agent-eval-harness:v2.3`; its pinned config loader
  no longer emits a numeric score-range warning for the categorical A/B/tie
  pairwise judge, while retaining the warning for numeric judges.
- Bump the task bundle version to `0.6.3`.
- Added an OCI report persistence stage before the existing Postgres/MinIO
  store. It packages the same object paths published to MinIO and attaches
  the archive to the caller's built image digest with ORAS. The push pipeline
  now waits for the image build and passes its URL and digest to each matrix
  leg; persistence-disabled callers skip the attachment. The archive is
  passed to ORAS by a relative filename to satisfy ORAS path validation.
- Bumped the task bundle version to `0.6.1`.
- Fixed the ORAS attach step to define its archive directory and filename in
  its own step scope; Tekton steps do not share shell variables.
- Bumped the task bundle version to `0.6.2`.
- Simplified the per-skill task flow: renamed the trusted-artifact copy step
  to `materialize-source`, merged symlink resolution into that preparation
  step, and combined Tier A/Tier B result serialization into one final
  `emit-results` step while preserving both result fields and their distinct
  gate semantics.
- Moved metrics-checkpoint writing into `quality-review`; the checkpoint
  remains available to `store` for Postgres observability metrics.
- Removed the optional AEH harness-inventory scan and its unused output.
- Updated the task to use `agent-eval-harness:v2.2`.

### Fixed

- `validate` step no longer crashes with `FileNotFoundError` on
  `metadata.yaml` for a changed-and-opted-in skill that never committed an
  AEH submission at all (no `submissions/<pack>/<skill>/` directory --
  true for most skills in the catalog, e.g. plain `rh-basic` skills with
  no `eval.yaml`/`cases`/mock-mcps). Previously, `validate`'s
  `EFFECTIVE_AEH_MODE`/`EFFECTIVE_AEH_CONTROL_CONFIG`/
  `EFFECTIVE_AEH_TREATMENT_CONFIG` preamble opened
  `$SUBMISSION_PATH/metadata.yaml` directly, before ever calling
  `scripts/validate.py` (which already handles a missing `metadata.yaml`
  gracefully) -- so any such skill crashed as soon as it was both changed
  and opted into evaluation (`should-evaluate=true` + `is-changed=true`),
  surfacing only as `FileNotFoundError: ... /submissions/<pack>/<skill>/
  metadata.yaml` with no actionable message. `validate` now checks for
  `metadata.yaml` first and, when absent, writes a new per-leg
  `has-aeh-submission=false` flag and exits 0 cleanly instead -- treated
  identically to an unmet `should-evaluate`/`is-changed` gate. Every other
  Tier B step (`quality-review`, `aeh-eval-check`,
  `write-metrics-checkpoint`, `run-eval`, `emit-tier-b`) now also checks
  this flag before touching any of `validate`'s per-leg baked vars, so
  none of them error out trying to read files `validate` never wrote.
  `analyze-and-scorecard`/`store` are unaffected -- they already degrade
  to a Tier-A-only scorecard when no AEH submission/report exists for a
  leg.

### Fixed

- `run-eval` step now sets `AEH_INSECURE_SSL=1` (already used by
  `quality-review`/`analyze-and-scorecard`). In `aeh-mode: pairwise`, the
  final `score.py pairwise` A/B comparison call runs as a plain subprocess
  of this step's own container, never spawned through
  `OpenShiftEnvironment` -- which auto-injects this flag into Harbor trial
  pods via `_pod_manifest`'s `env.setdefault`, so per-case judge calls
  inside trial pods were unaffected. Without it on `run-eval` itself, that
  one pairwise comparison call hit the cluster's self-signed ingress
  certificate on the internal LiteLLM route and failed SSL verification,
  surfacing only as a generic `"AB failed: Connection error."` per case
  (`wins_a=wins_b=0`, `errors=2`) -- driving AEH's evaluation gate to
  "fail" even when both arms' own judges scored well.

### Added

- New `resolve-symlinks` step, right after `clone-repo`. `clone-repo`'s own
  symlink handling only repairs *flattened* symlink stubs -- one-line text
  files left behind when a `core.symlinks=false` git client mangled a
  symlink somewhere in the trusted-artifact round trip -- and explicitly
  skips anything that is still a real OS symlink. But `run-eval`/Harbor
  only ever stage the ONE skill or `runner.plugin_dirs` tree being
  evaluated into a trial pod, so a surviving symlink pointing outside that
  tree (e.g. a skill's `references/` doc symlinked into a sibling skill)
  resolved fine on the Task's own disk but uploaded as a dangling link once
  the pod only received that single directory. This step walks the leg's
  checkout with `find -type l` (skipping `.git`) and replaces every real
  symlink found with a real `cp -a` copy of its dereferenced target before
  any later step -- `security-scan`, `skillmd-scan`, `swap-mock-mcp`,
  `validate`, `run-eval` -- reads these trees.

- New optional `minio-credentials` key `insecure-skip-tls-verify` -- maps
  to a new `MINIO_INSECURE_SSL` env var on the `store` step, read by
  `agentic_eval_flow/scripts/publish.py`'s new `_minio_client()` helper
  (`cert_check=False` on the `Minio()` client when set). Needed when the
  MinIO endpoint is only reachable through a Route/Ingress presenting a
  self-signed or internal-CA certificate -- the existing `AEH_INSECURE_SSL`
  flag doesn't help here since it only patches httpx/httpx2/requests/
  aiohttp (judge HTTP calls) and has no effect on the `minio` SDK, which
  builds its own `urllib3.PoolManager` directly. Also refactored
  `publish.py`'s 7 near-identical `Minio(...)` construction call sites
  (one per `upload_*` function) down to this single shared helper.

### Changed

- `swap-mock-mcp` step now calls a new, unit-tested
  `agentic_eval_flow/scripts/swap_mock_mcp.py` (baked into the
  `agent-eval-harness` image the same way as `scripts/validate.py`) instead
  of its previous untested inline Python heredoc. Behavior for the existing
  real-pack swap is unchanged. New: it also auto-generates and swaps a
  pairwise control arm's `"<real-pack>-mcp-only"` `runner.plugin_dirs`
  sibling (e.g. `rh-sre-mcp-only/`, never committed to git) by copying the
  real pack's own `mcps.json` into it, so that arm gets the same mocked MCP
  tool access as treatment with zero hand-authored/duplicated mcps.json
  content. `scripts/run_aeh.py`'s own `_prepare_enriched_tasks` now calls
  the same function, so local dev runs get this for free too -- no separate
  "remember to run the pipeline step first" footgun.
- Bumped every step's pinned `quay.io/ecosystem-appeng/agent-eval-harness`
  image from `v1.2.6` to `v1.2.6` (rebuilt from `agentic_eval_flow`) to pick
  up the new `scripts/swap_mock_mcp.py` and the `abevalflow/harbor_extensions/
  aeh_task_enrichment.py` docstring note on why a flag-based approach to
  this same problem doesn't work (confirmed empirically against a real
  trial pod -- `agent_eval/harbor/run.py`'s `_resolve_harbor_skill_roots`
  does its own independent, per-plugin_dirs-entry `SKILL.md` filesystem
  check with no flag-based override).

## 0.3.0

### Fixed

- Bumped every step's pinned `quay.io/ecosystem-appeng/agent-eval-harness`
  image from `v1.2.1` to `1.2.3` (rebuilt from `agentic_eval_flow`), which
  fixes `scripts/run_aeh.py`'s `HarborRunner._execute()` passing
  `--regenerate` to `python -m agent_eval.harbor.run` right after it had
  just generated+enriched the same `tasks_dir` itself. `--regenerate`
  unconditionally purges and re-generates Harbor task packages via bare
  upstream `generate_tasks()`, which has no knowledge of AEH's own
  enrichment (mock-MCP `schema.json`/`fixture.json` staging, `skills/`,
  `annotations.yaml`, reward injection) -- silently wiping every one of
  those files before Harbor ever uploaded the task to a trial pod. Any
  skill depending on a mocked (or real) stdio MCP server therefore failed
  to connect 100% of the time, with no infra-error signal (the agent still
  completed its turn and wrote a degraded "connection failed" report), one
  level of indirection away from quietly zeroing out judges like
  `used_mcp_tool` in a pairwise AEH comparison. Confirmed root cause via a
  live trial pod's own `/workspace/.cache/claude-cli-nodejs/-workspace/
  mcp-logs-<server>/*.jsonl` connection log (`FileNotFoundError: ... mcp-
  servers/<server>/schema.json`), and confirmed the fix end-to-end against
  a real OpenShift trial pod.

## 0.2.0

### Added

- Per-submission AEH mode override: the `validate` step now reads
  `metadata.yaml`'s own `aeh_mode` / `aeh_control_config` /
  `aeh_treatment_config` fields (when present) and uses them in place of
  this Task's pipeline-wide `aeh-mode` / `aeh-control-config` /
  `aeh-treatment-config` params for that one Matrix leg, baking the
  resolved values to `.baked-vars/` for `run-eval` to read. Lets one
  submission opt into `AEH_MODE=pairwise` (vanilla-vs-skilled control/
  treatment lift comparison) without the calling pipeline's own
  `AEH_MODE` param -- shared by every skill's Matrix leg -- having to
  flip for the whole catalog. No change in behavior for a submission that
  omits these `metadata.yaml` fields: it still inherits the pipeline
  param exactly as before.
- Bumped every step's pinned `quay.io/ecosystem-appeng/agent-eval-harness`
  image from `v1.2.0` to `v1.2.1` (rebuilt from `agentic_eval_flow`).

## 0.1.0

### Added

- Initial version, extracted from agentic-plugins' `.tekton/tasks/aeh-skill-eval.yaml`.
- Runs a single catalog item's full Tier A (security/SKILL.md scan, always)
  and Tier B (LLM evaluation, opt-in) evaluation chain as one Task, so a
  Tekton `Matrix` can fan out over it natively.
- No behavior change from the agentic-plugins original: this version only
  threads existing `$(params.*)` usages through step-level `env:` entries
  (required by this repo's Tekton Security Task Lint) and adds the
  `app.kubernetes.io/version` label / `tekton.dev/tags` annotation.

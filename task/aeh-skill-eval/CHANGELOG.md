# Changelog

## Unreleased

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

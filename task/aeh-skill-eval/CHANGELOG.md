# Changelog

## Unreleased

*Nothing yet.*

## 0.3.0

### Fixed

- Bumped every step's pinned `quay.io/ecosystem-appeng/agent-eval-harness`
  image from `v1.2.1` to `v1.2.2` (rebuilt from `agentic_eval_flow`), which
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

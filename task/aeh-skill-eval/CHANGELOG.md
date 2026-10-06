# Changelog

## Unreleased

*Nothing yet.*

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

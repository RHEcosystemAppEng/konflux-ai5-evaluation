# Changelog

## 1.0.0

### Changed

- Aggregate results inline with structured JSON validation on a standard Python image.
- Remove source extraction and caller-provided aggregation scripts.
- Remove `SOURCE_ARTIFACT`, `aggregate-script-path`, and `should-evaluate` inputs;
  no application image is required.


## Unreleased

*Nothing yet.*

## 0.1.0

### Added

- Initial version, extracted from agentic-plugins' `.tekton/tasks/aggregate-fanout-result.yaml`.
- Aggregates an array of per-item evaluation outcomes into one standardized
  Konflux `TEST_OUTPUT`, optionally hard-failing the pipeline.
- No behavior change from the agentic-plugins original: this version adds
  the `aggregate-script-path` param (defaulted to the previously-hardcoded
  `scripts/aggregate_fanout_result.py`) plus the `app.kubernetes.io/version`
  label / `tekton.dev/tags` annotation.

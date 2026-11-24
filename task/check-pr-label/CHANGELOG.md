# Changelog

## 0.3.0

- Select the label provider and repository from `source-url` in automatic mode.
- Support `mirror-source` as the only repository to query for a mirrored build.
- Preserve the existing provider settings for callers that omit both URLs.

## 0.2.3

- Support GitHub-only builds through `source-provider: github`, with no GitLab API token required.
- Keep GitLab as the default, with the optional GitHub fallback for mirrored commits.

## 0.2.2

- Add an optional GitHub repository lookup for mirrored commits without a matching GitLab MR.
- Support anonymous lookup for public repositories and an optional read token for authenticated requests.

## 0.2.1

- Default to the native `trusted-ca` ConfigMap and report actionable GitLab connection errors.

## 0.2.0

- Add explicit `tiers` input and resolved `tiers` output; explicit selections skip GitLab.
- Resolve auto against the exact merged/squash/fast-forward commit and destination branch.
- Verify GitLab TLS and fail on API errors or ambiguous matches.
- Support additional CA trust and pin the selector runtime image.
- Preserve existing 0.1.0 published bundles for legacy consumers.

## 0.1.0

### Added

- Initial version, extracted from agentic-plugins' `.tekton/tasks/check-pr-label.yaml`.
- Checks whether the merged MR for a commit SHA on a GitLab project carries
  a given label.
- No behavior change from the agentic-plugins original: this version adds
  `label-name`/`gitlab-server-url`/`gitlab-project-path`/
  `git-token-secret-name`/`git-token-secret-key` params (all defaulted to
  the previously-hardcoded values) so the Task is reusable by other
  GitLab-hosted projects, plus the `app.kubernetes.io/version` label /
  `tekton.dev/tags` annotation.

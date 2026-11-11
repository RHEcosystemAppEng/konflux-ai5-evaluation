# Changelog

## Unreleased

*Nothing yet.*

## 0.1.0

### Added

- Check GitHub PRs and GitLab MRs for a caller-specified label and optional status.
- Select requests by explicit PR/MR number, caller-provided metadata, or commit SHA when no number is available.
- Return the `has-label` result without falling back to commit lookup after a direct lookup failure.
- Read Git credentials from a configurable Secret name and key.

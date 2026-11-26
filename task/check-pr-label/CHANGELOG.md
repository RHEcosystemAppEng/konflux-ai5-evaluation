# Changelog

## Unreleased

*Nothing yet.*

## 0.1.0

### Added

- Check GitHub PRs and GitLab MRs for a caller-specified label and optional status.
- Select requests by explicit PR/MR number, caller-provided metadata, or commit SHA when no number is available.
- Return the `has-label` result without falling back to commit lookup after a direct lookup failure.
- Read Git credentials from a configurable Secret name and key.
- Select only the most recently created associated PR/MR during commit lookup and warn when multiple candidates exist.
- Apply the optional status filter after selecting the PR/MR.
- Fail without writing a result when credentials are missing, lookup or response validation fails, or no associated PR/MR exists.

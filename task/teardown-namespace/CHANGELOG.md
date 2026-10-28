# Changelog

## Unreleased

*Nothing yet.*

## 0.1.0

### Added

- Initial version.
- Deletes the ephemeral evaluation namespace created by create-namespace.
- Safety check: refuses to delete any namespace that does not match the
  `mcp-eval-*` prefix.
- Designed for the pipeline `finally` block; gracefully handles cases
  where the namespace does not exist.

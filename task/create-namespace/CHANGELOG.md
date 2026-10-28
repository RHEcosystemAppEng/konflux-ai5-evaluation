# Changelog

## Unreleased

*Nothing yet.*

## 0.1.0

### Added

- Initial version.
- Creates an `mcp-eval-<run-id>` ephemeral namespace on the target cluster
  for isolated MCP server evaluation.
- Grants the pipeline ServiceAccount access via a RoleBinding to the
  `mcp-eval-ephemeral-access` ClusterRole, with configurable SA name
  and namespace.

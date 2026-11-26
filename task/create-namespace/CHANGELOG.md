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
- Enforce default-deny ingress/egress with separate DNS, sandbox backend, evaluator-to-MCP, LLM, Compass, and external OpenAPI allow rules. Validate IP:port inputs and reject hostnames. Ingress permits only same-namespace evaluator pods on the configured MCP port.

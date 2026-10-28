# Changelog

## Unreleased

*Nothing yet.*

## 0.1.0

### Added

- Initial version.
- LLM-driven behavioral evaluation using mcpchecker against a deployed
  MCP server. Tests tool correctness, edge-case handling, and sensitive
  data redaction using configurable task suites.
- Runs mcpchecker as a Kubernetes Job on the target cluster.
- Copies LLM secrets (agent, judge, CA) from the target cluster's default
  namespace (configurable) into the target cluster's ephemeral namespace.
- Aggregates mcpchecker results with pass / fail / not_evaluated recommendation; threshold
  is hardcoded in the `abevalflow` library and is not yet configurable
  per task.

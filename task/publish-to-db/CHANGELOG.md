# Changelog

## Unreleased

*Nothing yet.*

## 0.1.0

### Added

- Initial MCP evaluation result publishing Task.
- PostgreSQL tables and writer for components, evaluations, phases, and checks.
- Compass `entity_ref` and `fact_ref` identifiers read from generated fact files.
- `mcp_evaluation_history` view with a calculated `is_latest` flag per component.
- PipelineRun `started_at` timestamp used to identify latest evaluations.

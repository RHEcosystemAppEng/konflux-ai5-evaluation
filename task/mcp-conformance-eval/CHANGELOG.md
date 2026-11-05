# Changelog

## Unreleased

*Nothing yet.*

## 0.1.0

### Added

- Initial version.
- Black-box deterministic conformance probe against a deployed MCP server
  over Streamable HTTP — no LLM required.
- Three-state evaluation model: pass / fail / not_evaluated.
- Configurable MCP endpoint path.
- Optional Compass integration for SoundCheck-consumed checks; secret
  copied from the target cluster's default namespace (configurable).
- Gate enforcement modes: block, warn, or disabled.
- Runs as a Job on the target cluster.

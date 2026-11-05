# Changelog

## Unreleased

*Nothing yet.*

## 0.1.0

### Added

- Initial version.
- Runs three language-agnostic static checks against MCP server source
  before deployment: secrets management (gitleaks), no user-provided code
  execution (semgrep), and license compliance (licensee).
- Gate enforcement modes: block, warn, or disabled.
- Configurable allowed SPDX license IDs.

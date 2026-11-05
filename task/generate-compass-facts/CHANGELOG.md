# Changelog

## Unreleased

*Nothing yet.*

## 0.1.0

### Added

- Initial version.
- Generates validated Compass SoundCheck check-level fact payload files from
  MCP evaluation phase summaries.
- Validates phase summary JSON files against the schema.
- Fact format includes `factRef`, `entityRef` (empty), and check data. The
  `entityRef` is populated by the publishing step.

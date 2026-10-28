# Changelog

## Unreleased

*Nothing yet.*

## 0.1.0

### Added

- Initial version.
- Deploys an MCP server into the ephemeral namespace using its Helm chart
  and test values from the pre-cloned MCP server repo.
- Copies image pull and MCP credential Secrets from the Konflux cluster's pipeline namespace
  to the target cluster's ephemeral namespace before deployment.
- Configurable Helm value keys for image repository, image ref, and
  image pull secret.

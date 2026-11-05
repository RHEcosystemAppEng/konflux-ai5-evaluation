# prepare-plugin-oci-ta

Consumes `SOURCE_ARTIFACT` from the trusted clone task, packages `plugin-id`
through the digest-pinned `tools-image`, and returns `SOURCE_ARTIFACT` containing
the original source plus `.konflux/package`. `SKILLS` is the full plugin inventory.
Pass that inventory to `aeh-skill-eval`, with
`component-manifest: .konflux/package/manifest.json`. Do not select only changed
skills for a release candidate. The Component Containerfile copies only the
prepared installable payload and its manifest.

The managed EC policy must approve this task bundle and its tools-image parameter.
All parameters are passed as argument arrays, never interpolated into shell code.
Intermediate source is immutable OCI data; the task has no workspaces.

All steps run as UID 1001 with `HOME=/tekton/home`. Restoring and packaging
as the same non-root user keeps the extracted source writable without changing
source permissions or granting additional privileges. The TaskRun's volume
group must allow access to its emptyDir, as provided by the tenant's SCC.

Version 1.1.0 also emits the complete canonical manifest as `PLUGIN_PACKAGE`.
Official EC policies compare its inventory with the signed evaluation and
verification results. The approved tools runtime must support that result.

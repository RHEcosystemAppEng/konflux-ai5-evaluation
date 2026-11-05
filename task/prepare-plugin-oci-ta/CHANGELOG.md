# Changelog

## 1.1.0

- Emit the complete canonical `PLUGIN_PACKAGE` manifest for native EC policies.
- Preserve trusted source transport, deterministic packaging and full `SKILLS` inventory.

## 1.0.1

- Restore, package and archive source as UID 1001, matching the tools image.
- Set a writable Tekton HOME for registry credentials in the non-root steps.

## 1.0.0

- Package one plugin using approved tools, preserving trusted source identity.
- Emit the complete skill inventory and a prepared source trusted artifact.

# Changelog

## Unreleased

*Nothing yet.*

## 0.1.0

### Added

- Initial version.
- Waits for all Deployments and StatefulSets created by the Helm release
  to complete their rollout with a configurable timeout.
- Final pod-level readiness sweep catches standalone pods, Jobs, and
  sidecars not managed by a Deployment or StatefulSet.
- Fails on error states such as CrashLoopBackOff and ImagePullBackOff.

# Reusable Konflux plugin build Tasks

These versioned Tekton Tasks produce build evidence for native, per-plugin
Konflux Components. Official Enterprise Contract policies make market decisions.
The managed release team owns its ECP, RPA, release pipeline and credentials.

## Supported Task catalog

| Task | Version | Responsibility |
|---|---|---|
| [prepare-plugin-oci-ta](task/prepare-plugin-oci-ta/README.md) | 1.1.0 | Package every skill in one plugin; emit trusted source and `PLUGIN_PACKAGE` |
| [aeh-skill-eval](task/aeh-skill-eval/README.md) | 3.1.0 | Evaluate the package; emit schema-2 signed scores and attach complete reports |
| [verify-plugin-evidence](task/verify-plugin-evidence/README.md) | 1.0.0 | Bind actual image, package inventory, report hashes and score evidence |
| [collect-plugin-context](task/collect-plugin-context/README.md) | 1.0.0 | Collect ownership, lifecycle and requested Compass observations |
| [check-pr-label](task/check-pr-label/README.md) | 0.2.1 | Select optional Tier 2 for a merged GitLab MR carrying `evaluate` |

Tier 1 is always selected. The label is not required for redhat-only. Missing
behavior stays unavailable. Task success records evidence collection/execution;
it does not grant market eligibility. Tekton Chains includes the declared results
in signed image provenance. Native EC checks approved producers and every skill.

Start with [onboarding](docs/onboarding.md). Task READMEs describe interfaces,
Secrets and workspaces. The native reference build is
[agentic-plugins](https://gitlab.cee.redhat.com/ai5-marketplace/agentic-plugins/-/blob/per-plugin-componnent/konflux/pipelines/plugin-component-build.yaml).

## Publication and validation

Bundles are published manually under
`quay.io/ecosystem-appeng/konflux-skill-evaluation/<task-name>:<version>`:

```sh
hack/build-and-push-bundles.sh TASK_NAME
make test
hack/checkton-local.sh
hack/missing-ta-tasks.sh
```

Pin the returned digest in consumers and their managed producer allowlists.
Task changes require a version bump and CHANGELOG entry; see
[shared CI standards](SHARED-CI.md). Executable local smokes use `ABEVAL_TEST_CLI`.
Registry access and cluster integration are separate from local validation.

Legacy Matrix aggregation, catalog-SHA discovery/registration Tasks and their
onboarding examples have been removed. Plugin coverage comes from the immutable
package inventory; publication is governed by native Snapshots, EC and managed
ReleasePlans/Admissions. Historical implementations remain in Git history.

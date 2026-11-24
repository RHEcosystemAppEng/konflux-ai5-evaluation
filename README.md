# Reusable Konflux plugin builds

The Tekton build Pipeline and its versioned Tasks produce signed build evidence
for native, per-plugin Konflux Components. `plugin-pipeline` owns Enterprise
Contract integration scenarios, policies, and managed release wiring.

Task layout, versioning, linting, and integration tests follow `task-repo-shared-ci`.
[Shared CI setup](SHARED-CI.md)

## Build Pipeline

[`plugin-component-build`](pipelines/plugin-component-build/plugin-component-build.yaml)
packages and evaluates one plugin, then produces the image and evidence for EC.
Its PipelineRun supplies the Task bundle and runtime image digests as parameters.
Build the Pipeline bundle using `tekton-bundle-builder-oci-ta` with
`pipelines/plugin-component-build` as the Component source context. Set the
generated PipelineRun's `path-context` to
`pipelines/plugin-component-build/plugin-component-build.yaml`.
Pull requests targeting `main` build a temporary bundle tagged `on-pr-<sha>`.
Pushes to `main` that change the Pipeline or its publish configuration publish
a bundle tagged with the commit SHA. Pin that bundle's digest in consumers.

For a GitHub repository mirrored to GitLab, pass `tiers: auto` and set
`github-repository` to the upstream GitHub.com `owner/repo`. With a
`check-pr-label` bundle at version 0.2.2 or later, the Pipeline checks GitHub
when GitLab finds no matching merged MR. The mirror must preserve the merge
commit SHA and target branch.

## Supported Task catalog

| Task | Version | Responsibility |
|---|---|---|
| [aeh-skill-eval](task/aeh-skill-eval/README.md) | 3.1.0 | Evaluate the package; emit schema-2 signed scores and attach complete reports |
| [verify-plugin-evidence](task/verify-plugin-evidence/README.md) | 1.0.0 | Bind actual image, package inventory, report hashes and score evidence |
| [collect-plugin-context](task/collect-plugin-context/README.md) | 1.0.0 | Collect ownership, lifecycle and requested Compass observations |
| [check-pr-label](task/check-pr-label/README.md) | 0.2.3 | Select optional Tier 2 from the `evaluate` label on a GitHub PR or GitLab MR, including mirrored builds |

Tier 1 is always selected. The label is not required for redhat-only. Missing
behavior stays unavailable. Task success records evidence collection/execution;
it does not grant market eligibility. Tekton Chains includes the declared results
in signed image provenance. Native EC checks approved producers and every skill.

Start with [onboarding](docs/onboarding.md). Task READMEs describe interfaces,
Secrets and workspaces.

Preparation uses the official Konflux `run-script-oci-ta` Task and the approved
`plugin-pipeline` tools image. The build Pipeline owns the command and result
wiring.

## Publication and validation

Task bundles can also be published manually under
`quay.io/ecosystem-appeng/konflux-skill-evaluation/<task-name>:<version>`:

```sh
hack/build-and-push-bundles.sh TASK_NAME
```

Pin the returned digest in consumers and their managed producer allowlists.
Task changes require a version bump and CHANGELOG entry; see
[shared CI standards](SHARED-CI.md).

Run the local checks with the commands below. The shared CI workflow discovers
Tekton test Pipelines under each Task's `tests/` directory.
[Task validation and integration tests](SHARED-CI.md#task-validation-and-integration-tests)

```sh
hack/checkton-local.sh
hack/missing-ta-tasks.sh
python3 hack/check-plugin-component-build.py
```

Legacy Matrix aggregation, catalog-SHA discovery/registration Tasks and their
onboarding examples have been removed. Plugin coverage comes from the immutable
package inventory; publication is governed by native Snapshots, EC and managed
ReleasePlans/Admissions. Historical implementations remain in Git history.

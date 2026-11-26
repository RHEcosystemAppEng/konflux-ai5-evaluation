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

Automatic tier selection uses `check-pr-label` version 0.3.0 or later. With
`tiers: auto`, the Pipeline looks up labels in the repository specified by
`git-url`. Set the optional `mirror-source` to the repository URL where the
PRs or MRs are merged when building from a mirror. Only that repository is
queried for labels. GitHub.com and GitLab are supported in either direction.
Mirrors must preserve the upstream merge commit SHA and target branch.

## Compass publication

The [Compass publication PipelineRun](pipelines/compass-publication/compass-publication.yaml)
verifies the push Snapshot's build evidence and publishes the evaluator's facts.
Its workspace passes the Conforma report to the publisher. The
`pipeline-compass-publication` Component uses the same Tekton bundle builder
as the build Pipeline. The IntegrationTestScenario resolves the PipelineRun
from its digest-pinned bundle with `resourceKind: pipelinerun`.

## Supported Task catalog

| Task | Version | Responsibility |
|---|---|---|
| [aeh-skill-eval](task/aeh-skill-eval/README.md) | 4.0.0 | Evaluate the package, emit schema-2 signed scores and attach complete reports |
| [verify-plugin-evidence](task/verify-plugin-evidence/README.md) | 1.0.0 | Bind actual image, package inventory, report hashes and score evidence |
| [collect-plugin-context](task/collect-plugin-context/README.md) | 1.0.0 | Collect ownership, lifecycle and requested Compass observations |
| [check-pr-label](task/check-pr-label/README.md) | 0.3.0 | Select optional Tier 2 from the `evaluate` label on a GitHub PR or GitLab MR, including mirrored builds |
| [parse-snapshot](task/parse-snapshot/README.md) | 0.1.0 | Parses a Konflux Snapshot JSON to extract component image, git URL, revision, and name |
| [create-namespace](task/create-namespace/README.md) | 0.1.0 | Creates an ephemeral namespace on a remote cluster for MCP server evaluation |
| [deploy-mcp](task/deploy-mcp/README.md) | 0.1.0 | Deploys an MCP server into the ephemeral namespace via Helm chart |
| [deploy-mcp-oci-ta](task/deploy-mcp/README.md#trusted-artifacts-variant) | 0.1.0 | OCI Trusted Artifacts variant of deploy-mcp |
| [wait-ready](task/wait-ready/README.md) | 0.1.0 | Waits for all Deployments/StatefulSets in the namespace to complete rollout |
| [mcp-static-eval](task/mcp-static-eval/README.md) | 0.1.0 | Static checks (secrets, code execution, license) against MCP server source |
| [mcp-static-eval-oci-ta](task/mcp-static-eval/README.md#trusted-artifacts-variant) | 0.1.0 | OCI Trusted Artifacts variant of mcp-static-eval |
| [mcp-conformance-eval](task/mcp-conformance-eval/README.md) | 0.1.0 | Deterministic conformance probes against a deployed MCP server (no LLM) |
| [mcp-behavioral-eval](task/mcp-behavioral-eval/README.md) | 0.1.0 | LLM-driven behavioral evaluation using mcpchecker against a deployed MCP server |
| [generate-compass-facts](task/generate-compass-facts/README.md) | 0.1.0 | Generates Compass SoundCheck fact payloads from MCP evaluation summaries |
| [publish-to-compass](task/publish-to-compass/README.md) | 0.1.0 | Publishes generated fact payloads to Compass SoundCheck |
| [teardown-namespace](task/teardown-namespace/README.md) | 0.1.0 | Deletes the ephemeral evaluation namespace (`finally` block) |

Tier 1 is always selected. The label is not required for redhat-only. Missing
behavior stays unavailable. Task success records evidence collection/execution;
it does not grant market eligibility. Tekton Chains includes the declared results
in signed image provenance. Native EC checks approved producers and every skill.

Start with [onboarding](docs/onboarding.md). Task READMEs describe interfaces,
Secrets and workspaces.

Preparation uses the official Konflux `run-script-oci-ta` Task and the approved
`plugin-pipeline` tools image. The build Pipeline owns the command and result
wiring.

`publish-to-compass` creates a temporary ConfigMap on the target cluster to
mount generated fact files into its publishing Job. The task deletes that
ConfigMap after the Job finishes.

## Publication and validation

Task bundles can also be published manually under
`quay.io/ecosystem-appeng/konflux-skill-evaluation/<task-name>:<version>`:

```sh
hack/build-and-push-bundles.sh TASK_NAME
```

Pin the returned digest in consumers and their managed producer allowlists.
You can also re-resolve a published digest with
`skopeo inspect docker://quay.io/ecosystem-appeng/konflux-skill-evaluation/<task-name>:<version>`.
Task changes require a version bump and CHANGELOG entry; see
[shared CI standards](SHARED-CI.md).

Run the local checks with the commands below. The shared CI workflow discovers
Tekton test Pipelines under each Task's `tests/` directory.
[Task validation and integration tests](SHARED-CI.md#task-validation-and-integration-tests)

```sh
hack/checkton-local.sh
hack/missing-ta-tasks.sh
python3 hack/check-plugin-component-build.py
python3 hack/check-compass-publication.py
```

Legacy Matrix aggregation, catalog-SHA discovery/registration Tasks and their
onboarding examples have been removed. Plugin coverage comes from the immutable
package inventory; publication is governed by native Snapshots, EC and managed
ReleasePlans/Admissions. Historical implementations remain in Git history.

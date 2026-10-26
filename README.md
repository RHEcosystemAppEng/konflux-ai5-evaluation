# konflux-shared-tasks

Reusable [Konflux](https://konflux-ci.dev/) Tekton Tasks, originally built for
and used by [agentic-plugins](https://gitlab.cee.redhat.com/ai5-marketplace/agentic-plugins)'
`on-push`/`on-pull-request` build pipelines, extracted here so any Konflux
pipeline can consume them as versioned Tekton bundles instead of a
repo-pinned `git` resolver.

This repo follows the structure, versioning, linting, and testing standards
from [konflux-ci/task-repo-shared-ci](https://github.com/konflux-ci/task-repo-shared-ci) --
see [SHARED-CI.md](SHARED-CI.md) for the full standard this repo is onboarded
to.

## Task catalog

| Task | Purpose | Version |
|---|---|---|
| [aeh-skill-eval](task/aeh-skill-eval/README.md) | Per-item security/quality (Tier A) + opt-in LLM (Tier B) evaluation, designed to be `Matrix`-fanned-out over a catalog. | 0.1.0 |
| [aggregate-fanout-result](task/aggregate-fanout-result/README.md) | Aggregates a `Matrix`'s per-item `TEST_OUTPUT`s into one standardized, optionally hard-gating result. | 0.1.0 |
| [check-pr-label](task/check-pr-label/README.md) | Fail-closed check of whether the merged MR for a commit carries an opt-in label (GitLab). | 0.1.0 |
| [discover-changed-skills](task/discover-changed-skills/README.md) | Diffs a catalog's registered SHAs against the current SHA to find what changed (GitLab). | 0.1.0 |
| [update-registered-shas](task/update-registered-shas/README.md) | Bumps a catalog's registered SHAs and pushes the bookkeeping commit (GitLab). | 0.1.0 |
| [parse-snapshot](task/parse-snapshot/README.md) | Parses a Konflux Snapshot JSON to extract component image, git URL, revision, and name. | 0.1.0 |
| [create-namespace](task/create-namespace/README.md) | Creates an ephemeral namespace on a remote cluster for MCP server evaluation. | 0.1.0 |
| [deploy-mcp](task/deploy-mcp/README.md) | Deploys an MCP server into the ephemeral namespace via Helm chart. | 0.1.0 |
| [wait-ready](task/wait-ready/README.md) | Waits for all Deployments/StatefulSets in the namespace to complete rollout. | 0.1.0 |
| [mcp-static-eval](task/mcp-static-eval/README.md) | Static checks (secrets, code execution, license) against MCP server source. | 0.1.0 |
| [mcp-conformance-eval](task/mcp-conformance-eval/README.md) | Deterministic conformance probes against a deployed MCP server (no LLM). | 0.1.0 |
| [mcp-behavioral-eval](task/mcp-behavioral-eval/README.md) | LLM-driven behavioral evaluation using mcpchecker against a deployed MCP server. | 0.1.0 |
| [teardown-namespace](task/teardown-namespace/README.md) | Deletes the ephemeral evaluation namespace (`finally` block). | 0.1.0 |

Every task's own `README.md` documents its full Parameters/Results/
Workspaces/**Secrets** tables and a copy-pasteable usage snippet. See
[docs/examples/skills-evaluation-usage.md](docs/examples/skills-evaluation-usage.md)
for how all five compose together in a real pipeline (the exact wiring
agentic-plugins itself uses).

## Reusability scope

- `aeh-skill-eval` and `aggregate-fanout-result` are **fully generic**: they
  depend only on their own image, params, and Secrets -- no coupling to any
  particular source repository.
- `check-pr-label`, `discover-changed-skills`, and `update-registered-shas`
  are **GitLab-specific by design** (they call the GitLab REST API / do
  their own `git clone`+`push`), but every GitLab project detail
  (server URL, project path, clone/push URL, branch, bot identity, token
  Secret name/key) is a parameter -- defaulted to the values
  agentic-plugins itself uses, so its own pipelines need zero behavior
  change, but any other GitLab-hosted Konflux project can point them at its
  own repository. They additionally expect that repository to carry its
  own `detect-script-path`/`register-script-path`/`aggregate-script-path`
  scripts implementing the small CLI contracts documented in each task's
  `README.md` -- these three tasks implement a *bookkeeping pattern*, not a
  fully self-contained integration.

No task in this repo uses a ConfigMap.

## Getting bundle images

Each `task/<name>/<name>.yaml` is built and pushed as a Tekton bundle image
via `hack/build-and-push-bundles.sh` (see that script and the `make bundles`
target), to:

```text
quay.io/ecosystem-appeng/konflux-skill-evaluation/<task-name>:<version>
```

All 0.1.0 bundles are published. Pin the digest `make bundles` prints
(or re-resolve it with `skopeo inspect docker://quay.io/ecosystem-appeng/konflux-skill-evaluation/<task-name>:0.1.0`)
in your pipeline's `taskRef.params[bundle]` -- see each task's own
`README.md` for a ready-to-use, already-pinned snippet, and
agentic-plugins' own `.tekton/skills-evaluation-*.yaml` for a real
consumer.

## Repository layout

```text
task/<name>/<name>.yaml       Task definition
task/<name>/CHANGELOG.md      Required by the versioning check (hack/versioning.py)
task/<name>/README.md         Params/Results/Workspaces/Secrets + usage snippet
task/<name>/tests/            Integration test Pipeline(s), tests-workspace convention
.ta-ignore.yaml                Trusted Artifacts exemptions (with rationale)
hack/, .github/                Shared CI tooling (from task-repo-shared-ci)
docs/examples/                 End-to-end usage walkthroughs
```

## Versioning

Every task starts at `0.1.0` in this repo (the "initial version, extracted
from agentic-plugins" baseline -- see each `CHANGELOG.md`). Future changes
follow [SHARED-CI.md's versioning rules](SHARED-CI.md#versioning): bump
`app.kubernetes.io/version` and update `CHANGELOG.md` for any change you
want released as a new bundle.

## Validating locally

```bash
# Lint embedded shell scripts
hack/checkton-local.sh

# Check versioning requirements for anything changed vs. main
hack/versioning.py check

# Check that workspace-using Tasks have a Trusted Artifacts variant or a
# documented .ta-ignore.yaml exemption
hack/missing-ta-tasks.sh

# yamllint
yamllint .
```

Running the actual integration tests under `task/*/tests/` requires a
Kubernetes cluster with Konflux's Tekton bits installed and `tkn` -- see
[SHARED-CI.md](SHARED-CI.md#task-validation-and-integration-tests). The
`run-task-tests` GitHub Actions workflow runs these automatically on every
PR once this repo has a GitHub remote.

## Open follow-ups

- **Enable the shared-ci GitHub Actions workflows** on the
  [GitHub remote](https://github.com/RHEcosystemAppEng/konflux-skills-evaluation)
  (they're already onboarded locally under `.github/workflows/` and will run
  automatically on the next PR) plus the
  [Shared CI Updater](SHARED-CI.md#shared-ci-updater) (needs its GitHub App
  secrets configured, see that section).
- **Re-run `make bundles` and update every pinned digest** whenever a task
  changes and its `app.kubernetes.io/version` is bumped -- digests are not
  automatically kept in sync with source changes.

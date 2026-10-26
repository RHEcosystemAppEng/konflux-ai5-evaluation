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
| [aeh-skill-eval](task/aeh-skill-eval/README.md) | One sequential CLI batch with per-skill evidence, timeout retries, and aggregate gates. | 2.0.1 |
| [aggregate-fanout-result](task/aggregate-fanout-result/README.md) | Legacy Matrix result aggregation; unused by sequential batch pipelines. | 1.0.0 |
| [check-pr-label](task/check-pr-label/README.md) | Fail-closed check of whether the merged MR for a commit carries an opt-in label (GitLab). | 0.1.0 |
| [discover-changed-skills](task/discover-changed-skills/README.md) | Diffs a catalog's registered SHAs against the current SHA to find what changed (GitLab). | 0.1.0 |
| [update-registered-shas](task/update-registered-shas/README.md) | Registers eligible skills from a revision-bound batch summary (GitLab). | 1.0.0 |

Every task's own `README.md` documents its full Parameters/Results/
Workspaces/**Secrets** tables and a copy-pasteable usage snippet. See
[docs/examples/skills-evaluation-usage.md](docs/examples/skills-evaluation-usage.md)
for pipeline wiring and the CLI migration. Sequential pipelines no longer use the legacy aggregator.

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
  own `detect-script-path`/`register-script-path`
  scripts implementing the small CLI contracts documented in each task's
  `README.md` -- the two catalog tasks implement a *bookkeeping pattern*, not a
  fully self-contained integration.

The evaluation task accepts an optional trusted CA ConfigMap.

## Getting bundle images

Each `task/<name>/<name>.yaml` is built and pushed as a Tekton bundle image
via `hack/build-and-push-bundles.sh` (see that script and the `make bundles`
target), to:

```text
quay.io/ecosystem-appeng/konflux-skill-evaluation/<task-name>:<version>
```

The batch evaluation task is `2.0.1`, and batch registration is `1.0.0`.
Discovery and label tasks remain `0.1.0`; the legacy aggregator remains available
for older consumers. Runtime images use `v1.0.2-runner` and `v1.0.2-trial`, both pinned by digest. Evaluation/trial runtime images are explicit task parameters. Result adaptation
uses standard Python images; OCI attachment reuses the existing Konflux task-runner. Build and publish them before updating
pipeline bundle references. See [migration](docs/migration-cli.md).

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
# Local task contracts; optionally set ABEVAL_TEST_CLI for executable smoke tests
make test

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

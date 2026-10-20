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
| [aeh-skill-eval](task/aeh-skill-eval/README.md) | Per-item security/quality (Tier A) + opt-in LLM (Tier B) evaluation, designed to be `Matrix`-fanned-out over a catalog. | 0.8.1 |
| [aggregate-fanout-result](task/aggregate-fanout-result/README.md) | Aggregates a `Matrix`'s per-item `TEST_OUTPUT`s into one standardized, optionally hard-gating result. | 0.1.0 |
| [check-pr-label](task/check-pr-label/README.md) | Fail-closed check of whether the merged MR for a commit carries an opt-in label (GitLab). | 0.1.0 |
| [discover-changed-skills](task/discover-changed-skills/README.md) | Diffs a catalog's registered SHAs against the current SHA to find what changed (GitLab). | 0.1.0 |
| [update-registered-shas](task/update-registered-shas/README.md) | Bumps a catalog's registered SHAs and pushes the bookkeeping commit (GitLab). | 0.1.0 |

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

The `aeh-skill-eval` bundle is published as `0.8.1`; the other four bundles
remain `0.1.0`. Its five runtime images share the original
`quay.io/ecosystem-appeng/agent-eval-harness` repository with the test prefix
`v4.0` and purpose-specific tags, with the patched Cisco scanner at
`v4.0.1-security-scan`. Image and bundle
references are digest-pinned. See the evaluation task's
[image parameters and published usage](task/aeh-skill-eval/README.md#image-release-and-usage).

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

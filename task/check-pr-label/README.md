# check-pr-label

Version 0.3.0 resolves evaluation tiers for GitHub.com and GitLab Component
builds, including mirrors in either direction.

| `tiers` | Behavior |
|---|---|
| `1` | Tier 1 with no API lookup |
| `1,2` | Both tiers with no API lookup |
| `auto` | Both tiers when a matching merge has `evaluate`. Otherwise Tier 1. |

Pass `current-sha` from the trusted clone result and `target-branch` from the
configured Component branch. In `auto` mode, pass the build repository URL as
`source-url`. The shared Pipeline supplies it from `git-url`. If
`mirror-source` is set, the Task queries that repository exclusively.
`label-name` defaults to `evaluate`.

| Build repository | `mirror-source` | Label lookup |
|---|---|---|
| GitHub.com | Empty | Build repository on GitHub |
| GitLab | Empty | Build repository on GitLab |
| GitLab mirror | Upstream GitHub.com repository URL | Upstream repository on GitHub |
| GitHub mirror | Upstream GitLab repository URL | Upstream repository on GitLab |

The Task accepts HTTPS repository URLs and Git SSH clone URLs. Mirrors between
repositories on the same provider also work. Configure the sync to preserve
commit SHAs and use the same target branch on both sides.

For GitLab lookups, set `gitlab-server-url` to the selected GitLab server. The
server defaults to `https://gitlab.cee.redhat.com`. This setting also scopes
where the Task sends the read-API token from `git-token-secret-name` and
`git-token-secret-key`. Public GitHub.com repositories work anonymously.
For authenticated GitHub lookups, pass a pull request read token via
`github-token-secret-name` and `github-token-secret-key`, which default to
`github-pr-read-token` and `token`.

Callers that omit both repository URLs continue to use the previous
`source-provider`, `gitlab-project-path`, and `github-repository` settings.

The Task matches only merged changes for the exact build SHA and target branch.
GitLab supports merge, squash and fast-forward commit identities, with a short
retry while a push webhook can precede the MR state update. A GitHub PR must
target the configured repository. A lookup with no matching change selects
Tier 1. API and TLS errors, invalid responses, and ambiguous matches fail the
Task. `ca-bundle-configmap` (default `trusted-ca`) optionally adds trust from
`ca-bundle.crt`.

Results are `tiers` (`1` or `1,2`) and `should-evaluate` (`true` when Tier 2 was
selected). The pipeline passes the resolved tiers into the evaluator and records
them in signed results. The label requests execution; managed qualification
policy still decides which evidence and outcomes are required for release.

Apply the label before merging the final relevant MR or PR. The evaluation covers the
entire affected plugin at that merged revision, including earlier merged changes.
An unrelated plugin's path does not start this Component. For later evaluation
without a new relevant merge, use an explicit `tiers=1,2` build for the selected
Component and immutable revision. Rechecking ITS evidence alone does not run
missing trials.

The [Tekton integration test](tests/test-check-pr-label.yaml) checks explicit
Tier 1 against an unreachable endpoint without requiring a token.

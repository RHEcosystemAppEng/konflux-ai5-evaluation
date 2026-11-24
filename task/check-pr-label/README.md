# check-pr-label

Version 0.2.3 resolves evaluation tiers for GitHub.com and GitLab Component
builds, including GitHub commits mirrored to GitLab.

| `tiers` | Behavior |
|---|---|
| `1` | Tier 1 with no API lookup |
| `1,2` | Both tiers with no API lookup |
| `auto` | Both tiers when a matching merge has `evaluate`. Otherwise Tier 1. |

Pass `current-sha` from the trusted clone result and `target-branch` from the
configured Component branch. In `auto` mode, use these Pipeline parameters to
select the lookup. `label-name` defaults to `evaluate`.

| Build source | `source-provider` | `github-repository` |
|---|---|---|
| GitHub.com | `github` | Build repository as `owner/repo` |
| GitLab | `gitlab` (default) | Leave empty |
| GitHub mirrored to GitLab | `gitlab` (default) | Upstream GitHub.com repository as `owner/repo` |

GitLab lookups use `gitlab-server-url`, the URL-encoded `gitlab-project-path`,
and a read-API token from `git-token-secret-name` and `git-token-secret-key`.
GitHub-only builds use the GitHub API directly. Public GitHub repositories work
anonymously. For authenticated GitHub lookups, supply a token with pull request
read access via `github-token-secret-name` and `github-token-secret-key`, which
default to `github-pr-read-token` and `token`.

For mirrored builds, a matching GitLab MR decides the result, even when it has
no evaluation label. The Task queries GitHub after a successful GitLab lookup
finds no matching MR. Configure this for a sync that preserves commit SHAs and
uses the same target branch on both platforms.

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

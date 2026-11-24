# check-pr-label

Version 0.2.2 resolves evaluation tiers for GitLab Component builds, including
commits mirrored from an upstream GitHub repository. Existing
0.1.0 bundles retain their previous interface and behavior.

| `tiers` | Behavior |
|---|---|
| `1` | Tier 1 with no API lookup |
| `1,2` | Both tiers with no API lookup |
| `auto` | Both tiers when a matching merge has `evaluate`. Otherwise Tier 1. |

Pass `current-sha` from the trusted clone result and `target-branch` from the
configured Component branch. `auto` uses `gitlab-server-url`, URL-encoded
`gitlab-project-path`, `label-name` (default `evaluate`), and a read-API token
from `git-token-secret-name` / `git-token-secret-key`. The Secret reference is
optional for explicit selections, but a token is required for `auto`.

Merge, squash and fast-forward identities are supported. Other branches, older
commits and open MRs do not request Tier 2. A short bounded retry handles the
push/merge-state race. API/TLS errors, invalid responses and ambiguous matches
fail the task instead of silently skipping requested evaluation. TLS verification
is enabled; `ca-bundle-configmap` (default `trusted-ca`) optionally adds trust from `ca-bundle.crt`.

### GitHub fallback for mirrored commits

Set `github-repository` to the upstream GitHub.com `owner/repo` in the Task's
Pipeline parameters. The fallback runs in `auto` mode after a successful GitLab
lookup finds no matching merged MR. Any matching GitLab MR decides the result,
including an MR without the label. The GitHub PR must have merged into the
configured repository and `target-branch` at the exact build SHA. Configure
this for a sync that preserves commit SHAs and uses the same target branch on
both platforms.

Public repositories work anonymously. For authenticated requests, supply a
GitHub read-only pull requests token in the optional Secret selected by
`github-token-secret-name` and `github-token-secret-key`. They default to
`github-pr-read-token` and `token`. A successful lookup with no matching PR,
including a GitHub response that the commit is absent, selects Tier 1.
Permission errors, rate limits, invalid responses, and ambiguous matches fail
the Task.

Results are `tiers` (`1` or `1,2`) and `should-evaluate` (`true` when Tier 2 was
selected). The pipeline passes the resolved tiers into the evaluator and records
them in signed results. The label requests execution; managed qualification
policy still decides which evidence and outcomes are required for release.

Apply the label before merging the final relevant MR. The evaluation covers the
entire affected plugin at that merged revision, including earlier merged changes.
An unrelated plugin's path does not start this Component. For later evaluation
without a new relevant MR, use an explicit `tiers=1,2` build for the selected
Component and immutable revision. Rechecking ITS evidence alone does not run
missing trials.

Run `python -m unittest discover -s tests -v` for the executable GitLab and
GitHub selector fixtures. The native smoke pipeline checks explicit
Tier 1 against an unreachable endpoint without requiring a token.

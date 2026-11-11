# update-registered-shas task

Bumps every evaluated catalog item's registered SHA to `current-sha`,
except ones that hit a runtime error this run, via a caller-supplied
registration script (default `scripts/register_evaluation_results.py`), in
a single batched commit + push. Skipped entirely when `should-evaluate` is
not `"true"`. The commit message carries a `[skip-fanout]` marker so the
caller pipeline can avoid re-triggering itself on this Task's own
bookkeeping push.

Must run against the same `source` workspace that
[discover-changed-skills](../discover-changed-skills/README.md) already
cloned (this Task does not clone on its own) -- the checkout needs to still
be authenticated/writable so this Task can push back. This is also why it
has no Trusted Artifacts (`-oci-ta`) variant -- see
[.ta-ignore.yaml](../../.ta-ignore.yaml) in the repo root.

Reusable across any GitLab-hosted repository that follows the same
"registered SHA" bookkeeping convention as agentic-plugins. The
registration script itself is **not** bundled in this Task -- it must exist
in the repository at `register-script-path`.

## Parameters

| name | description | default value | required |
|---|---|---|---|
| current-sha | Commit SHA under evaluation. | | true |
| should-evaluate | When not `"true"`, this Task is a no-op. | | true |
| changed-skills | `array`. Identifiers, same order as `eval-outcomes`. Forwarded verbatim to `register-script-path`. | `[]` | false |
| eval-outcomes | `array`. Per-item `TEST_OUTPUT` JSON strings, same order/length as `changed-skills`. Forwarded verbatim to `register-script-path`. | `[]` | false |
| register-script-path | Path, relative to the repository root, of the registration script to run. | `"scripts/register_evaluation_results.py"` | false |
| git-remote-url | HTTPS URL to push the registration commit to. | `"https://gitlab.cee.redhat.com/ai5-marketplace/agentic-plugins.git"` | false |
| git-push-branch | Branch to push the registration commit to. | `"main"` | false |
| git-ssl-no-verify | When `"true"`, disables TLS certificate verification for the git push. | `"true"` | false |
| git-bot-name | `git user.name` for the registration commit. | `"agentic-plugins-bot"` | false |
| git-bot-email | `git user.email` for the registration commit. | `"agentic-plugins-bot@redhat.com"` | false |
| git-token-secret-name | Name of the Secret containing a GitLab access token with push access to the repository. | `"agentic-plugins-gitlab-sa"` | false |
| git-token-secret-key | Key within `git-token-secret-name` holding the GitLab access token. | `"password"` | false |

## Workspaces

| name | description |
|---|---|
| source | Must already contain an authenticated, checked-out clone at `./repo` (e.g. produced by `discover-changed-skills` sharing this same workspace). |

## Secrets

| Secret (param) | Key (param) | Required | Purpose |
|---|---|---|---|
| `git-token-secret-name` (default `agentic-plugins-gitlab-sa`) | `git-token-secret-key` (default `password`) | yes | GitLab access token with push access, used both for the credential store and the push URL. |

No ConfigMaps are used by this Task.

## Usage

```yaml
- name: update-registered-shas
  runAfter: [evaluate-skill]
  taskRef:
    resolver: bundles
    params:
    - name: name
      value: update-registered-shas
    - name: bundle
      value: "quay.io/ecosystem-appeng/konflux-skill-evaluation/update-registered-shas:0.1.0@sha256:de91b167f45481b8de74641e5abeeb82f2c7cb16f602ee6bcddfa8ff496ad316"
    - name: kind
      value: task
  params:
  - name: current-sha
    value: $(params.revision)
  - name: should-evaluate
    value: $(tasks.check-pr-label.results.has-label)
  - name: changed-skills
    value: $(tasks.discover-changed-skills.results.changed-skills[*])
  - name: eval-outcomes
    value: $(tasks.evaluate-skill.results.TEST_OUTPUT_TIER_B[*])
  - name: git-remote-url
    value: "https://gitlab.cee.redhat.com/my-group/my-project.git"
  - name: git-token-secret-name
    value: "my-gitlab-sa"
  workspaces:
  - name: source
    workspace: orchestrator-workspace
```

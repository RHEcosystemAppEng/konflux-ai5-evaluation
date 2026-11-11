# check-pr-label task

Checks whether a specific pull request or merge request, or one associated with
a commit, has a target label. Supports GitHub, GitHub Enterprise, and GitLab hosts.
Returns a string result that can gate an optional evaluation task.

For the skills evaluation gate, set `target-label: evaluate` and
`pr-status-is: merged` so an open request cannot enable the evaluation.

## Parameters

| name | description | default value | required |
|---|---|---|---|
| git-url | HTTPS repository URL; its host selects the GitHub or GitLab API | | true |
| git-revision | Commit SHA used to find associated pull or merge requests | | true |
| pr-number | Repository-scoped GitHub PR number or GitLab MR IID | `""` | false |
| target-label | Label to look for | | true |
| pr-status-is | Request status: `open`, `merged`, `closed`, or empty for any status | `""` | false |
| git-token-secret-name | Secret containing the Git access token | `git-secret` | false |
| git-token-secret-key | Key containing the token in that Secret | `password` | false |

## Results

| name | description |
|---|---|
| has-label | `true` if an associated request matches the label and optional status; `false` otherwise. |

The task returns `false` if no token is available, no request matches, or
the API lookup fails, including malformed JSON responses. Invalid status
values and unsupported hosts with a token fail the task.

The task uses the existing Python image and installs no packages at runtime.

Request selection uses explicit `pr-number` first, then the optional
`CONTEXT_PR_NUMBER` environment variable injected by the calling PipelineRun.
When both are empty, the existing commit lookup is used. A direct lookup failure
returns `false` without falling back to another request associated with the SHA.
Commit lookup retains its existing behavior: any matching associated request
can return `true`.

## Workspaces

None.

## Secrets

| Secret (param) | Keys | Source | Purpose |
|---|---|---|---|
| `git-token-secret-name` | `git-token-secret-key` (optional) | Namespace running the Task | Read pull or merge requests from the Git API. |

The task sends the token through the GitHub `Authorization` header or GitLab
`PRIVATE-TOKEN` header. Hostnames must contain `github` or `gitlab`, matching
the source task's platform detection.

## Usage

Publish this new task bundle before use and pin its resolved digest in the
consuming pipeline. The tag below illustrates the bundle location.

```yaml
- name: check-pr-label
  taskRef:
    resolver: bundles
    params:
    - name: name
      value: check-pr-label
    - name: bundle
      value: quay.io/ecosystem-appeng/konflux-skill-evaluation/check-pr-label:0.1.0
    - name: kind
      value: task
  params:
  - name: git-url
    value: $(tasks.parse-snapshot.results.git-url)
  - name: git-revision
    value: $(tasks.parse-snapshot.results.git-revision)
  - name: target-label
    value: evaluate
  - name: pr-status-is
    value: merged
```

Use `$(tasks.check-pr-label.results.has-label)` in a downstream task's `when`
expression to run it only when the result is `true`.

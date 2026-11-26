# publish-to-db task

Stores MCP evaluation phase summaries and their checks in PostgreSQL. The task
reads the summary files from a shared workspace and uses the PipelineRun name
as the unique evaluation ID. Repeating a run does not insert duplicate rows.

Apply [sql/001_create_mcp_tables.sql](sql/001_create_mcp_tables.sql) to the
destination database once before running this task. The task inserts results;
it does not create tables. The destination is planned to be the `public`
schema of the existing `abevalflow` database, applied through that database's
migration process; the owner of that process is still to be confirmed.

## Stored data

Every run adds new rows; earlier runs are kept as history. The
`latest_mcp_evaluations` view returns the most recently started evaluation for
each component, whatever its status, ordered by `started_at` and then `run_id`.
`started_at` is the PipelineRun's `status.startTime`; `stored_at` is the database
insertion time.

The `mcp_evaluation_history` view returns all evaluations with a calculated
`is_latest` flag per component, using the same ordering as the latest view.

To correlate results with Compass, the task stores the identifiers taken from
the generated fact files:

- `mcp_evaluations.entity_ref`: the `entityRef` used for that run.
- `mcp_check_results.fact_ref`: the `factRef` generated for that check.

`fact_ref` is NULL for checks that produce no fact, such as `not_evaluated` or
consumed checks. A stored identifier does not prove that the fact was
published; `publish-to-compass` may have run in dry-run mode.

## Parameters

| name | description | default value | required |
|---|---|---|---|
| mcp-eval-image | MCP evaluation image containing the database writer | | true |
| summary-dir | Workspace-relative directory containing phase summary JSON files | `reports` | false |
| facts-dir | Workspace-relative directory containing generated Compass fact files | `facts` | false |
| scorecard-config | Scorecard path relative to the generate-compass-facts module; use the same value as that Task | `config/scorecard.yaml` | false |
| component-name | MCP component name from the Snapshot | | true |
| git-url | MCP component source repository URL | | true |
| commit-sha | MCP component source revision | | true |
| pipeline-run-id | Name of the evaluation PipelineRun | | true |
| database-secret | Secret containing the database connection | | true |

## Results

This task declares no Tekton results. It fails if no phase summaries are found
or if the database write fails.

## Workspaces

| name | description |
|---|---|
| source | Shared workspace containing `reports/<phase>-summary.json` and the generated `facts/` directory. |

The supported phases are `static-eval`, `conformance-eval`, and optional
`behavioral-eval`. Each summary contains a `checks` array. Missing optional
phases are omitted; a run with no summaries fails. The task also fails if the
fact files contain more than one `entityRef`, or a `factRef` that does not
match a stored check through the scorecard.

## Secrets

| Secret (param) | Keys | Source | Purpose |
|---|---|---|---|
| `database-secret` | `database-url`, optional `database-tls-route-host` | Konflux namespace running the Task | Connect to PostgreSQL. |

When `database-tls-route-host` is present, the task opens a local TLS tunnel
to that host on port 443. In that case, `database-url` must use
`127.0.0.1:5432`. The current tunnel does not verify the Route certificate;
review that setting before using a production database.

## Usage

The evaluator image must include this task's writer script. Publish the task
bundle and pin its digest before using it in a production PipelineRun.

The Task's service account needs `get` access to `pipelineruns.tekton.dev` in
its namespace to read the PipelineRun's start time.

```yaml
- name: publish-to-db
  runAfter: [generate-compass-facts]
  taskRef:
    resolver: bundles
    params:
      - name: name
        value: publish-to-db
      - name: bundle
        value: quay.io/ecosystem-appeng/konflux-skill-evaluation/publish-to-db:0.1.0
      - name: kind
        value: task
  params:
    - name: mcp-eval-image
      value: $(params.MCP_EVAL_IMAGE)
    - name: facts-dir
      value: $(tasks.generate-compass-facts.results.facts-dir)
    - name: component-name
      value: $(tasks.parse-snapshot.results.component-name)
    - name: git-url
      value: $(tasks.parse-snapshot.results.git-url)
    - name: commit-sha
      value: $(tasks.parse-snapshot.results.git-revision)
    - name: pipeline-run-id
      value: $(context.pipelineRun.name)
    - name: database-secret
      value: $(params.MCP_DB_SECRET)
  workspaces:
    - name: source
      workspace: shared-workspace
```

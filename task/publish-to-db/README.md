# publish-to-db task

Stores MCP evaluation phase summaries and their checks in PostgreSQL. The task
reads the summary files from a shared workspace and uses the PipelineRun name
as the unique evaluation ID. Repeating a run does not insert duplicate rows.

Apply [sql/001_create_mcp_tables.sql](sql/001_create_mcp_tables.sql) to the
destination database once before running this task. The task inserts results;
it does not create tables.

## Parameters

| name | description | default value | required |
|---|---|---|---|
| mcp-eval-image | MCP evaluation image containing the database writer | | true |
| summary-dir | Workspace-relative directory containing phase summary JSON files | `reports` | false |
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
| source | Shared workspace containing `reports/<phase>-summary.json`. |

The supported phases are `static-eval`, `conformance-eval`, and optional
`behavioral-eval`. Each summary contains a `checks` array. Missing optional
phases are omitted; a run with no summaries fails.

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

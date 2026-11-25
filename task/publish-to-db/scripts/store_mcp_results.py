"""Store MCP evaluation phase summaries in Postgres."""

import argparse
import json
import os
from datetime import datetime
from pathlib import Path
from uuid import uuid4

import yaml
from sqlalchemy import create_engine, text


PHASES = ("static-eval", "conformance-eval", "behavioral-eval")
SOURCES = {
    "static-eval": "pipeline",
    "conformance-eval": "probe",
    "behavioral-eval": "mcpchecker",
}


def load_compass_identifiers(
    facts_dir: Path, scorecard_path: Path
) -> tuple[str | None, dict[tuple[str, str], str]]:
    """Return the entityRef and (phase, check) -> factRef of generated facts."""
    if not facts_dir.is_dir():
        print(f"No facts directory at {facts_dir}; storing without Compass identifiers")
        return None, {}

    entity_refs = set()
    fact_refs = set()
    for path in sorted(facts_dir.glob("*.json")):
        for fact in json.loads(path.read_text())["facts"]:
            entity_refs.add(fact["entityRef"])
            fact_refs.add(fact["factRef"])
    if len(entity_refs) > 1:
        raise ValueError(f"Expected one entityRef in {facts_dir}, found {sorted(entity_refs)}")

    checks_by_fact_ref = {}
    scorecard = yaml.safe_load(scorecard_path.read_text())
    for phase, phase_config in scorecard["phases"].items():
        for check_id, check in phase_config["checks"].items():
            fact_ref = check.get("fact_ref")
            if not fact_ref:
                continue
            if fact_ref in checks_by_fact_ref:
                raise ValueError(f"Duplicate fact_ref {fact_ref} in {scorecard_path}")
            checks_by_fact_ref[fact_ref] = (phase, check_id)

    unknown = fact_refs - checks_by_fact_ref.keys()
    if unknown:
        raise ValueError(f"Fact refs missing from {scorecard_path}: {sorted(unknown)}")

    entity_ref = next(iter(entity_refs), None)
    return entity_ref, {checks_by_fact_ref[ref]: ref for ref in fact_refs}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--report-dir", type=Path, required=True)
    parser.add_argument("--facts-dir", type=Path, required=True)
    parser.add_argument("--scorecard-config", type=Path, required=True)
    parser.add_argument("--component-name", required=True)
    parser.add_argument("--git-url", required=True)
    parser.add_argument("--commit-sha", required=True)
    parser.add_argument("--pipeline-run-id", required=True)
    parser.add_argument("--started-at", type=datetime.fromisoformat, required=True)
    args = parser.parse_args()

    summaries = []
    for phase in PHASES:
        path = args.report_dir / f"{phase}-summary.json"
        if not path.is_file():
            continue
        summary = json.loads(path.read_text())
        if summary["phase"] != phase:
            raise ValueError(f"Expected phase {phase} in {path}")
        summaries.append(summary)

    if not summaries:
        raise FileNotFoundError(f"No MCP phase summaries found in {args.report_dir}")

    phases_found = {summary["phase"] for summary in summaries}
    if any(not summary["passed"] for summary in summaries):
        overall_status = "fail"
    elif not {"static-eval", "conformance-eval"} <= phases_found:
        overall_status = "incomplete"
    else:
        overall_status = "pass"

    entity_ref, fact_refs = load_compass_identifiers(args.facts_dir, args.scorecard_config)
    stored_checks = {
        (summary["phase"], entry["check"]) for summary in summaries for entry in summary["checks"]
    }
    unmatched = fact_refs.keys() - stored_checks
    if unmatched:
        raise ValueError(f"Generated facts have no matching check summary: {sorted(unmatched)}")

    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        parser.error("DATABASE_URL is required")

    with create_engine(database_url).begin() as db:
        db.execute(
            text("""
                INSERT INTO public.mcp_components (id, name, git_url)
                VALUES (:id, :name, :git_url)
                ON CONFLICT (name, git_url) DO NOTHING
            """),
            {"id": uuid4(), "name": args.component_name, "git_url": args.git_url},
        )
        component_id = db.execute(
            text("""
                SELECT id FROM public.mcp_components
                WHERE name = :name AND git_url = :git_url
            """),
            {"name": args.component_name, "git_url": args.git_url},
        ).scalar_one()

        evaluation_id = db.execute(
            text("""
                INSERT INTO public.mcp_evaluations
                    (id, component_id, run_id, commit_sha, status, entity_ref, started_at)
                VALUES (:id, :component_id, :run_id, :commit_sha, :status, :entity_ref, :started_at)
                ON CONFLICT (run_id) DO NOTHING
                RETURNING id
            """),
            {
                "id": uuid4(),
                "component_id": component_id,
                "run_id": args.pipeline_run_id,
                "commit_sha": args.commit_sha,
                "status": overall_status,
                "entity_ref": entity_ref,
                "started_at": args.started_at,
            },
        ).scalar_one_or_none()
        if evaluation_id is None:
            print(f"PipelineRun {args.pipeline_run_id} is already stored")
            return

        for summary in summaries:
            phase_id = uuid4()
            db.execute(
                text("""
                    INSERT INTO public.mcp_phase_results
                        (id, evaluation_id, phase, passed, summary_json)
                    VALUES
                        (:id, :evaluation_id, :phase, :passed,
                         CAST(:summary_json AS jsonb))
                """),
                {
                    "id": phase_id,
                    "evaluation_id": evaluation_id,
                    "phase": summary["phase"],
                    "passed": summary["passed"],
                    "summary_json": json.dumps(summary),
                },
            )

            for entry in summary["checks"]:
                status = entry.get("status")
                if status not in ("pass", "fail", "not_evaluated"):
                    status = "pass" if entry["passed"] else "fail"

                db.execute(
                    text("""
                        INSERT INTO public.mcp_check_results
                            (id, phase_result_id, check_id, status, passed,
                             score, source, message, findings_count, fact_ref)
                        VALUES
                            (:id, :phase_result_id, :check_id, :status, :passed,
                             :score, :source, :message, :findings_count, :fact_ref)
                    """),
                    {
                        "id": uuid4(),
                        "phase_result_id": phase_id,
                        "check_id": entry["check"],
                        "status": status,
                        "passed": None if status == "not_evaluated" else status == "pass",
                        "score": None if status == "not_evaluated" else entry.get("score"),
                        "source": entry.get("source") or SOURCES[summary["phase"]],
                        "message": entry.get("message") or "",
                        "findings_count": entry.get("findings"),
                        "fact_ref": fact_refs.get((summary["phase"], entry["check"])),
                    },
                )

    print(f"Stored PipelineRun {args.pipeline_run_id}")


if __name__ == "__main__":
    main()

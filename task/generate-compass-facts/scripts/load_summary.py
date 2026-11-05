"""Load and parse MCP evaluation phase summary files."""

from __future__ import annotations

from pathlib import Path

from .models import McpCheckResult, McpPhaseResult
from .scorecard import DEFAULT_SOURCE, VALID_CHECK_STATUSES
from .validation import validate_phase_summary


def load_phase_summary(
    path: Path,
    phase_map: dict[str, dict],
) -> McpPhaseResult:
    """Load and validate a phase summary JSON file into a domain model."""
    data = validate_phase_summary(path)

    phase_name = data["phase"]

    if phase_name not in phase_map:
        raise ValueError(
            f"Unknown phase {phase_name!r} in {path}. "
            f"Valid phases: {', '.join(phase_map.keys())}"
        )

    checks: list[McpCheckResult] = []

    for check in data.get("checks", []):
        check_id = check["check"]

        if check_id not in phase_map[phase_name]["checks"]:
            raise ValueError(
                f"Unknown check {check_id!r} in phase {phase_name!r} in {path}. "
                f"Valid checks for {phase_name}: {', '.join(phase_map[phase_name]['checks'].keys())}"
            )

        check_name = phase_map[phase_name]["checks"][check_id]["name"]

        status = check.get("status")
        if status is None:
            status = "pass" if check["passed"] else "fail"
        if status not in VALID_CHECK_STATUSES:
            raise ValueError(f"Invalid status {status!r} for check {check_id!r} in phase {phase_name!r}")

        passed = True if status == "pass" else False if status == "fail" else None
        default_score = 1.0 if status == "pass" else 0.0

        source = (
            check.get("source")
            or phase_map[phase_name]["checks"][check_id].get("source")
            or phase_map[phase_name].get("source", DEFAULT_SOURCE)
        )

        checks.append(
            McpCheckResult(
                check_id=check_id,
                name=check_name,
                passed=passed,
                score=None if status == "not_evaluated" else check.get("score", default_score),
                status=status,
                message=check.get("message", ""),
                source=source,
            )
        )

    return McpPhaseResult(phase=phase_name, checks=checks)

"""Load and parse MCP evaluation phase summary files."""

from __future__ import annotations

import json
from collections.abc import Iterable
from pathlib import Path

import jsonschema

from scripts.phase_map import DEFAULT_SOURCE, PHASES, VALID_CHECK_STATUSES
from scripts.models.check import McpCheckResult
from scripts.models.evaluation import McpEvalResult
from scripts.models.phase import McpPhaseResult
from scripts.validation.schema import get_summary_schema


def load_phase_summary(path: Path, *, validate: bool = True) -> McpPhaseResult:
    """Load a standardized phase summary JSON file into a domain model.

    When *validate* is True (default), the file is validated against the
    phase summary JSON Schema before loading.  The parsed dict is reused
    — the file is read only once.
    """
    data = json.loads(path.read_text())
    if validate:
        jsonschema.validate(data, get_summary_schema())

    phase_name = data["phase"]

    # Validate phase exists in phase map
    if phase_name not in PHASES:
        raise ValueError(
            f"Unknown phase {phase_name!r} in {path}. "
            f"Valid phases: {', '.join(PHASES.keys())}"
        )

    checks: list[McpCheckResult] = []

    for check in data.get("checks", []):
        # Get check ID from JSON
        check_id = check["check"]

        # Validate check exists in this phase and get its metadata
        if check_id not in PHASES[phase_name]["checks"]:
            raise ValueError(
                f"Unknown check {check_id!r} in phase {phase_name!r} in {path}. "
                f"Valid checks for {phase_name}: {', '.join(PHASES[phase_name]['checks'].keys())}"
            )

        # Get check name from phase map
        check_name = PHASES[phase_name]["checks"][check_id]["name"]

        # Validate status
        status = check.get("status")
        if status is None:
            status = "pass" if check["passed"] else "fail"
        if status not in VALID_CHECK_STATUSES:
            raise ValueError(f"Invalid status {status!r} for check {check_id!r} in phase {phase_name!r}")

        passed = True if status == "pass" else False if status == "fail" else None
        default_score = 1.0 if status == "pass" else 0.0

        # Source hierarchy: JSON > check override > phase default > global default
        source = (
            check.get("source")
            or PHASES[phase_name]["checks"][check_id].get("source")
            or PHASES[phase_name].get("source", DEFAULT_SOURCE)
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

    return McpPhaseResult(phase=phase_name, passed=data["passed"], checks=checks)


def build_mcp_eval_result(phases: Iterable[McpPhaseResult]) -> McpEvalResult:
    """Assemble any nonempty set of unique phase results."""
    phase_map: dict[str, McpPhaseResult] = {}
    for phase in phases:
        if phase.phase in phase_map:
            raise ValueError(f"Duplicate phase result: {phase.phase!r}")
        phase_map[phase.phase] = phase
    return McpEvalResult(phases=phase_map)

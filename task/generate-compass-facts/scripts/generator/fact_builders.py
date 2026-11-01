"""Build fact data structures for Compass SoundCheck."""

from datetime import datetime
from typing import Any

from scripts.models.check import McpCheckResult
from scripts.models.evaluation import McpEvalResult
from scripts.models.phase import McpPhaseResult


def build_check_fact_data(
    check: McpCheckResult,
    fact_ref: str,
    evaluated_at: datetime,
) -> dict[str, Any]:
    """Build fact data for a single check result."""
    return {
        "facts": [
            {
                "factRef": fact_ref,
                "entityRef": "",
                "data": {
                    "passed": check.passed,
                    "score": check.score,
                    "status": check.status,
                    "message": check.message,
                    "source": check.source,
                    "evaluated_at": evaluated_at.isoformat(),
                },
            }
        ]
    }


def build_phase_fact_data(
    phase_result: McpPhaseResult,
    fact_ref: str,
    evaluated_at: datetime,
) -> dict[str, Any]:
    """Build fact data for a phase result."""
    checks_data = [
        {
            "check_id": c.check_id,
            "name": c.name,
            "passed": c.passed,
            "score": c.score,
            "status": c.status,
            "source": c.source,
        }
        for c in phase_result.checks
    ]
    return {
        "facts": [
            {
                "factRef": fact_ref,
                "entityRef": "",
                "data": {
                    "phase": phase_result.phase,
                    "passed": phase_result.passed,
                    "checks_passed": phase_result.checks_passed,
                    "checks_evaluated": phase_result.checks_evaluated,
                    "checks_total": phase_result.checks_total,
                    "overall_score": phase_result.overall_score,
                    "checks": checks_data,
                    "evaluated_at": evaluated_at.isoformat(),
                },
            }
        ]
    }


def build_eval_fact_data(
    eval_result: McpEvalResult,
    fact_ref: str,
    evaluated_at: datetime,
) -> dict[str, Any]:
    """Build fact data for the overall evaluation result."""
    return {
        "facts": [
            {
                "factRef": fact_ref,
                "entityRef": "",
                "data": {
                    "phases": {
                        phase_name: {
                            "passed": phase.passed,
                            "score": phase.overall_score,
                            "checks_evaluated": phase.checks_evaluated,
                            "checks_total": phase.checks_total,
                        }
                        for phase_name, phase in eval_result.phases.items()
                    },
                    "evaluated_at": evaluated_at.isoformat(),
                },
            }
        ]
    }

"""Generate fact data files from phase results."""

from __future__ import annotations

import json
import logging
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .models import McpCheckResult, McpPhaseResult

logger = logging.getLogger(__name__)


def build_check_fact_data(
    check: McpCheckResult,
    fact_ref: str,
    entity_ref: str,
    evaluated_at: datetime,
) -> dict[str, Any]:
    """Build a Soundcheck-compliant fact payload for a single check result."""
    return {
        "facts": [
            {
                "factRef": fact_ref,
                "entityRef": entity_ref,
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


def _sanitize_fact_ref(fact_ref: str) -> str:
    """Turn a factRef into a safe filename stem."""
    return re.sub(r"[^A-Za-z0-9_-]", "_", fact_ref)


def _write_fact_file(fact_data: dict[str, Any], fact_ref: str, output_dir: Path) -> Path:
    """Write a fact data file and return its path."""
    path = output_dir / f"{_sanitize_fact_ref(fact_ref)}.json"
    path.write_text(json.dumps(fact_data, indent=2))
    return path


def generate_mcp_eval_fact_files(
    phase_results: list[McpPhaseResult],
    output_dir: Path,
    entity_ref: str,
    phase_map: dict[str, dict],
) -> None:
    """Generate check-level fact data files without publishing.

    Each file contains ``{"facts": [{"factRef": "...", "entityRef": "...", "data": {...}}]}``
    — one fact per check result.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    evaluated_at = datetime.now(UTC)
    written: list[Path] = []

    for phase_result in phase_results:
        phase_checks = phase_map[phase_result.phase]["checks"]

        for check in phase_result.checks:
            if check.status == "not_evaluated":
                logger.info("Skipping not-evaluated check %s", check.check_id)
                continue
            if phase_checks[check.check_id].get("consumed", False):
                logger.debug("Skipping consumed check %s", check.check_id)
                continue

            fact_ref = phase_checks[check.check_id]["fact_ref"]
            fact_data = build_check_fact_data(check, fact_ref, entity_ref, evaluated_at)
            written.append(_write_fact_file(fact_data, fact_ref, output_dir))

    logger.info("Generated %d check fact file(s) in %s", len(written), output_dir)

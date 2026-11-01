"""Write fact data files to disk."""

from __future__ import annotations

import json
import logging
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from scripts.phase_map import (
    MCP_EVAL_FACT,
    PHASE_CONSUMED_CHECKS,
    PHASE_FACT_MAPS,
    PHASE_FACTS,
)
from scripts.generator.fact_builders import (
    build_check_fact_data,
    build_eval_fact_data,
    build_phase_fact_data,
)
from scripts.models.evaluation import McpEvalResult

logger = logging.getLogger(__name__)


def _sanitize_fact_ref(fact_ref: str) -> str:
    """Turn a factRef into a safe filename stem."""
    return re.sub(r"[^A-Za-z0-9_-]", "_", fact_ref)


def _write_fact_file(fact_data: dict[str, Any], fact_ref: str, output_dir: Path) -> Path:
    """Write a fact data file and return its path."""
    path = output_dir / f"{_sanitize_fact_ref(fact_ref)}.json"
    path.write_text(json.dumps(fact_data, indent=2))
    return path


def generate_mcp_eval_fact_files(
    eval_result: McpEvalResult,
    output_dir: Path,
) -> list[Path]:
    """Generate fact data files without publishing.

    Each file contains ``{"facts": [{"factRef": "...", "entityRef": "", "data": {...}}]}``
    — the evaluation data keyed by fact reference.  The ``entityRef`` is
    initialized as an empty string; the publishing step populates it from
    the Compass secret before POSTing.

    Returns the list of written file paths.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    evaluated_at = datetime.now(UTC)
    written: list[Path] = []

    for phase_name, phase_result in eval_result.phases.items():
        # Generate per-check facts
        fact_map = PHASE_FACT_MAPS[phase_name]
        consumed_checks = PHASE_CONSUMED_CHECKS.get(phase_name, set())
        for check in phase_result.checks:
            if check.status == "not_evaluated":
                logger.info("Skipping not-evaluated check %s", check.check_id)
                continue
            if check.check_id in consumed_checks:
                logger.debug("Skipping consumed check %s", check.check_id)
                continue
            check_fact_ref = fact_map[check.check_id]
            check_fact_data = build_check_fact_data(check, check_fact_ref, evaluated_at)
            written.append(_write_fact_file(check_fact_data, check_fact_ref, output_dir))

        # Generate phase summary fact
        phase_fact_ref = PHASE_FACTS[phase_name]
        phase_fact_data = build_phase_fact_data(phase_result, phase_fact_ref, evaluated_at)
        written.append(_write_fact_file(phase_fact_data, phase_fact_ref, output_dir))

    eval_fact_data = build_eval_fact_data(eval_result, MCP_EVAL_FACT, evaluated_at)
    written.append(_write_fact_file(eval_fact_data, MCP_EVAL_FACT, output_dir))

    logger.info("Generated %d fact file(s) in %s", len(written), output_dir)
    return written

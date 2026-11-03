#!/usr/bin/env python3
"""Generate Compass SoundCheck check-level fact data files from phase summaries.

Reads all JSON files from a summary directory, validates each against the phase
summary schema, and writes check-level fact data files (factRef + data, no
entityRef) to an output directory. Only individual check facts are generated
(no phase or evaluation summaries). No Compass interaction — this is a pure
transformation step. The publishing task injects entityRef from the Compass
secret before POSTing.

Usage:
    python -m scripts.run_generate_compass_facts \
        --summary-dir reports \
        --output-dir facts
"""

import argparse
import logging
import sys
from pathlib import Path

from .generator import generate_mcp_eval_fact_files
from .load_summary import load_phase_summary

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate Compass fact payloads from phase summaries")
    parser.add_argument(
        "--summary-dir",
        type=Path,
        required=True,
        help="Directory containing phase summary JSON files",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        required=True,
        help="Directory to write fact payload JSON files",
    )
    args = parser.parse_args()

    if not args.summary_dir.is_dir():
        logger.error("Not a directory: %s", args.summary_dir)
        return 1

    json_files = sorted(args.summary_dir.glob("*.json"))
    if not json_files:
        logger.error("No JSON files found in %s", args.summary_dir)
        return 1

    phases = []
    seen: set[str] = set()
    for path in json_files:
        try:
            phase_result = load_phase_summary(path)
        except Exception as exc:
            logger.error("Failed to load %s: %s", path.name, exc)
            return 1

        if phase_result.phase in seen:
            logger.error("Duplicate phase %r in %s", phase_result.phase, path.name)
            return 1

        if phase_result.checks_total == 0:
            logger.warning("Skipping %s: phase %r has no checks", path.name, phase_result.phase)
            continue

        seen.add(phase_result.phase)
        phases.append(phase_result)
        logger.info("Loaded phase %r from %s (%d checks)", phase_result.phase, path.name, phase_result.checks_total)

    if not phases:
        logger.error("No valid phase summaries found")
        return 1

    generate_mcp_eval_fact_files(phases, args.output_dir)
    return 0


if __name__ == "__main__":
    sys.exit(main())

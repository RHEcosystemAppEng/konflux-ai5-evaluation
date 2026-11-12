#!/usr/bin/env python3
"""Run the MCP static evaluation gates over the normalized scan reports.

Reads the three scan JSON files produced by the static evaluation scanners, evaluates
each gate, and writes results:

- ``<gate>-result.json`` per gate (the full GateResult) → results directory
- ``static-eval-summary.json`` (overall pass/fail + per-gate summary) → reports directory

All checks always run and results (pass/fail) are logged. Summary is always created.
The task itself does not fail based on check results.

Usage:
    python -m scripts.runners.static_eval_gate --results-dir <dir> --reports-dir <dir>
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

from abevalflow.mcp.gates import run_static_eval
from abevalflow.schemas import GatePolicy

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

SUMMARY_FILENAME = "static-eval-summary.json"


def main() -> int:
    parser = argparse.ArgumentParser(description="Run MCP static evaluation gates")
    parser.add_argument(
        "--results-dir",
        type=Path,
        required=True,
        help="Directory holding the static evaluation scan JSON files (input)",
    )
    parser.add_argument(
        "--reports-dir",
        type=Path,
        required=True,
        help="Directory for writing the summary JSON file (output)",
    )
    args = parser.parse_args()

    if not args.results_dir.is_dir():
        logger.error("Not a directory: %s", args.results_dir)
        return 1

    args.reports_dir.mkdir(parents=True, exist_ok=True)

    # Run all checks with default policy
    policy = GatePolicy()
    results = run_static_eval(args.results_dir, policy)

    summary: list[dict] = []
    for result in results:
        gate_key = result.get_policy_key()
        (args.results_dir / f"{gate_key}-result.json").write_text(result.model_dump_json(indent=2))
        summary.append(
            {
                "check": gate_key,
                "passed": result.passed,
                "score": result.score,
                "findings": len(result.findings),
                "message": result.message,
            }
        )
        logger.info(
            "%s: passed=%s score=%.2f findings=%d",
            gate_key,
            result.passed,
            result.score,
            len(result.findings),
        )

    overall_passed = all(r.passed for r in results)

    (args.reports_dir / SUMMARY_FILENAME).write_text(
        json.dumps(
            {"phase": "static-eval", "passed": overall_passed, "checks": summary},
            indent=2,
        )
    )

    logger.info("Static evaluation overall: %s", "PASS" if overall_passed else "FAIL")

    # Always return 0 - the task succeeds and creates the summary.
    # Downstream tasks check the results.
    return 0


if __name__ == "__main__":
    sys.exit(main())

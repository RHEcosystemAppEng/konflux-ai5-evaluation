#!/usr/bin/env bash
# Shared gate wrapper for static/conformance evaluation, baked into the MCP eval image.
#
# Runs the evaluation's gate module and extracts the passed flag from the summary JSON.
# The task always completes and creates a summary - it does not fail based on check results.
#
# Usage:
#   gate_wrapper.sh <gate-module> <results-dir> <reports-dir> <summary-json> <passed-result-path>
set -uo pipefail

GATE_MODULE="$1"        # e.g. scripts.runners.static_eval_gate
RESULTS_DIR="$2"        # absolute results dir for this submission/evaluation (input scans)
REPORTS_DIR="$3"        # absolute reports dir for this submission/evaluation (output summaries)
SUMMARY="$4"            # *-eval-summary.json written by the gate module
PASSED_RESULT_PATH="$5" # Tekton result path for the passed flag

# Run the gate module. Always creates summary, logs all results.
# The task succeeds even if checks fail - downstream tasks handle the results.
python -m "$GATE_MODULE" --results-dir "$RESULTS_DIR" --reports-dir "$REPORTS_DIR" || {
  echo "WARNING: Gate module failed, but continuing to emit results" >&2
}

# Extract the passed flag from the summary. A missing summary or one without a
# 'passed' key is itself a failure: fail loudly rather than writing an empty
# result that a downstream `when` would read as neither true nor false.
if ! python3 -c "import json,sys;print(str(json.load(open(sys.argv[1]))['passed']).lower(),end='')" \
    "$SUMMARY" > "$PASSED_RESULT_PATH"; then
  echo "run_gate: gate summary $SUMMARY is missing or has no 'passed' key" >&2
  exit 1
fi

# Always exit 0 - the task succeeds and downstream tasks check the results
exit 0

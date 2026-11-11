#!/usr/bin/env bash
# Mount the production Task script and regression fixtures into the test Pipeline.
set -euo pipefail

TASK_COPY="$1"
TEST_NS="$2"
TESTS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPT_FILE=$(mktemp)
trap 'rm -f "$SCRIPT_FILE"' EXIT
yq -r '.spec.steps[0].script' "$TASK_COPY" > "$SCRIPT_FILE"
kubectl create configmap check-pr-label-regression \
  --from-file=check-pr-label.py="$SCRIPT_FILE" \
  --from-file=test_check_pr_label.py="$TESTS_DIR/test_check_pr_label.py" \
  -n "$TEST_NS" --dry-run=client -o yaml | kubectl apply -f -

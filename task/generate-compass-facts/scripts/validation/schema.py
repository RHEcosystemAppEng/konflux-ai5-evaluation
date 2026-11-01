"""JSON Schema validation for phase summaries."""

import json
from pathlib import Path

_SCHEMAS_DIR = Path(__file__).resolve().parent.parent.parent / "schemas"

_SUMMARY_SCHEMA: dict | None = None


def get_summary_schema() -> dict:
    """Load and cache the phase summary JSON Schema."""
    global _SUMMARY_SCHEMA
    if _SUMMARY_SCHEMA is None:
        _SUMMARY_SCHEMA = json.loads((_SCHEMAS_DIR / "mcp_eval_report_schema.json").read_text())
    return _SUMMARY_SCHEMA

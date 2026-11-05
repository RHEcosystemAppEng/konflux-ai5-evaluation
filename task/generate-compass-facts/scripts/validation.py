"""JSON Schema validation for phase summaries."""

import json
from pathlib import Path

import jsonschema

_SCHEMAS_DIR = Path(__file__).resolve().parent.parent / "schemas"

_SUMMARY_SCHEMA: dict | None = None


def get_summary_schema() -> dict:
    """Load and cache the phase summary JSON Schema."""
    global _SUMMARY_SCHEMA
    if _SUMMARY_SCHEMA is None:
        _SUMMARY_SCHEMA = json.loads((_SCHEMAS_DIR / "mcp_eval_report_schema.json").read_text())
    return _SUMMARY_SCHEMA


def validate_phase_summary(path: Path, data: dict | None = None) -> dict:
    """Return parsed phase summary data after validating against the schema.

    Args:
        path: Path to the summary file (used for reading if data is None).
        data: Pre-loaded summary data to validate. If None, reads from path.

    Returns:
        The validated summary data.
    """
    if data is None:
        data = json.loads(path.read_text())
    jsonschema.validate(data, get_summary_schema())
    return data

"""Validate generated fact files before publishing them to Compass."""

from __future__ import annotations

import json
from pathlib import Path

import jsonschema

_SCHEMA_PATH = Path(__file__).resolve().parent.parent / "schemas" / "compass_fact_schema.json"
_FACT_SCHEMA: dict | None = None


def _get_fact_schema() -> dict:
    """Load and cache the Compass fact schema."""
    global _FACT_SCHEMA
    if _FACT_SCHEMA is None:
        _FACT_SCHEMA = json.loads(_SCHEMA_PATH.read_text())
    return _FACT_SCHEMA


def validate_compass_fact_file(path: Path) -> dict:
    """Return a parsed fact document after validating it against the schema."""
    data = json.loads(path.read_text())
    jsonschema.validate(data, _get_fact_schema())
    return data

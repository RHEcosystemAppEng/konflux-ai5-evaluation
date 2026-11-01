"""Validation functions for phase names and statuses."""

import re

PHASE_NAME_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]*\Z")


def validate_phase_name(phase_name: str) -> str:
    """Validate phase-name syntax without restricting names to configured phases."""
    if not PHASE_NAME_PATTERN.fullmatch(phase_name):
        raise ValueError("phase name must contain only letters, digits, underscores, and hyphens")
    return phase_name

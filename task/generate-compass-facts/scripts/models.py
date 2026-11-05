"""Domain models for MCP evaluation results."""

import re

from pydantic import BaseModel, Field, computed_field, field_validator

from .scorecard import DEFAULT_SOURCE

PHASE_NAME_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]*\Z")


def validate_phase_name(phase_name: str) -> str:
    """Validate phase-name syntax without restricting names to configured phases."""
    if not PHASE_NAME_PATTERN.fullmatch(phase_name):
        raise ValueError("phase name must contain only letters, digits, underscores, and hyphens")
    return phase_name


class McpCheckResult(BaseModel):
    """Result of a single check within a phase."""

    check_id: str = Field(description="Gate or check name (e.g. mcp-secrets, http-support)")
    name: str = Field(description="Human-readable check name")
    passed: bool | None = Field(description="True / false, or None when the check was not evaluated")
    score: float | None = Field(default=None, ge=0.0, le=1.0)
    status: str = Field(description="Three-state: pass / fail / not_evaluated")
    message: str = ""
    source: str = Field(default=DEFAULT_SOURCE, description="pipeline / compass / probe")


class McpPhaseResult(BaseModel):
    """Aggregate result of one evaluation phase."""

    phase: str
    checks: list[McpCheckResult]

    @field_validator("phase")
    @classmethod
    def phase_name_has_valid_format(cls, phase_name: str) -> str:
        return validate_phase_name(phase_name)

    @computed_field
    @property
    def checks_total(self) -> int:
        """Total number of checks in this phase (used for logging)."""
        return len(self.checks)

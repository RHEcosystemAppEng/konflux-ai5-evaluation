"""Evaluation result model."""

from pydantic import BaseModel, model_validator

from scripts.models.phase import McpPhaseResult


class McpEvalResult(BaseModel):
    """Complete MCP evaluation result across any supplied phases."""

    phases: dict[str, McpPhaseResult]

    @model_validator(mode="after")
    def phases_are_nonempty(self) -> "McpEvalResult":
        if not self.phases:
            raise ValueError("at least one phase result is required")
        return self

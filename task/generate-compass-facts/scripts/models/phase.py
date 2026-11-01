"""Phase result model."""

from pydantic import BaseModel, computed_field, field_validator

from scripts.models.check import McpCheckResult
from scripts.validation.validators import validate_phase_name


class McpPhaseResult(BaseModel):
    """Aggregate result of one evaluation phase."""

    phase: str
    passed: bool
    checks: list[McpCheckResult]

    @field_validator("phase")
    @classmethod
    def phase_name_has_valid_format(cls, phase_name: str) -> str:
        return validate_phase_name(phase_name)

    @computed_field
    @property
    def checks_passed(self) -> int:
        return sum(1 for c in self.checks if c.status == "pass")

    @computed_field
    @property
    def checks_total(self) -> int:
        return len(self.checks)

    @computed_field
    @property
    def checks_evaluated(self) -> int:
        return sum(1 for c in self.checks if c.status in {"pass", "fail"})

    @computed_field
    @property
    def overall_score(self) -> float:
        evaluated = [c for c in self.checks if c.status in {"pass", "fail"}]
        if not evaluated:
            return 0.0

        def score_or_default(check: McpCheckResult) -> float:
            if check.score is not None:
                return check.score
            return 1.0 if check.status == "pass" else 0.0

        return sum(score_or_default(c) for c in evaluated) / len(evaluated)

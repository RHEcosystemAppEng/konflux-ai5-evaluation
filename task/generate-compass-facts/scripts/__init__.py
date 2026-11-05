"""Generate and validate Compass SoundCheck fact data files from MCP
evaluation phase summaries.

Top-to-bottom flow:
  1. Scorecard config — loaded from a YAML file (phases, checks, sources, fact-refs)
  2. Domain models — McpCheckResult, McpPhaseResult
  3. Summary loader — load_phase_summary
  4. Schema validation — validate against JSON Schema files in schemas/
  5. Fact builders + file generator — transform models into check-level fact data files

No Compass interaction — this is a pure transformation and validation
module.
"""

from .generator import generate_mcp_eval_fact_files
from .load_summary import load_phase_summary
from .models import McpCheckResult, McpPhaseResult
from .scorecard import build_entity_ref, load_scorecard

__all__ = [
    "McpCheckResult",
    "McpPhaseResult",
    "load_phase_summary",
    "generate_mcp_eval_fact_files",
    "load_scorecard",
    "build_entity_ref",
]

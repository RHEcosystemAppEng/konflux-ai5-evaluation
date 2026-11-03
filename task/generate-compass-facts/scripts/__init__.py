"""Generate and validate Compass SoundCheck fact data files from MCP
evaluation phase summaries.

Top-to-bottom flow:
  1. Phase map — PHASES dict (single source of truth for phases, checks, sources, fact-refs)
  2. Domain models — McpCheckResult, McpPhaseResult
  3. Summary loader — load_phase_summary
  4. Schema validation — validate against JSON Schema files in schemas/
  5. Fact builders + file generator — transform models into check-level fact data files

No Compass interaction — this is a pure transformation and validation
module. The publishing Job injects entityRef from the Compass secret
before POSTing.
"""

from .generator import generate_mcp_eval_fact_files
from .load_summary import load_phase_summary
from .models import McpCheckResult, McpPhaseResult
from .phase_map import PHASE_CONSUMED_CHECKS, PHASE_FACT_MAPS, PHASES

__all__ = [
    # Models
    "McpCheckResult",
    "McpPhaseResult",
    # Summary loading
    "load_phase_summary",
    # Fact generation
    "generate_mcp_eval_fact_files",
    # Phase map
    "PHASES",
    "PHASE_FACT_MAPS",
    "PHASE_CONSUMED_CHECKS",
]

"""Single source of truth for phases, checks, and their metadata.

All phase and check configuration lives here. Other modules import the
derived lookup tables computed from PHASES.
"""

from __future__ import annotations

# ============================================================================
# Core Configuration - Single Source of Truth
# ============================================================================

PHASES: dict[str, dict] = {
    "static-eval": {
        "fact_ref": "abevalflow:default/mcp_static_eval",
        "source": "pipeline",
        "checks": {
            "mcp-secrets": {
                "name": "Secrets Management",
                "fact_ref": "abevalflow:default/mcp_secrets",
            },
            "mcp-no-user-code": {
                "name": "No User-Code Execution",
                "fact_ref": "abevalflow:default/mcp_no_user_code",
            },
            "mcp-license": {
                "name": "License Compliance",
                "fact_ref": "abevalflow:default/mcp_license",
            },
        },
    },
    "conformance-eval": {
        "fact_ref": "abevalflow:default/mcp_conformance_eval",
        "source": "probe",
        "checks": {
            "http-support": {
                "name": "HTTP Support",
                "fact_ref": "abevalflow:default/mcp_http_support",
            },
            "protocol-compliance": {
                "name": "Protocol Compliance",
                "fact_ref": "abevalflow:default/mcp_protocol_compliance",
            },
            "schema-conformance": {
                "name": "Schema Conformance",
                "fact_ref": "abevalflow:default/mcp_schema_conformance",
            },
            "tool-annotations": {
                "name": "Tool Annotations",
                "fact_ref": "abevalflow:default/mcp_tool_annotations",
            },
            "rate-limiting": {
                "name": "Rate Limiting",
                "fact_ref": "abevalflow:default/mcp_rate_limiting",
            },
            "response-size-limit": {
                "name": "Response Size Limit",
                "fact_ref": "abevalflow:default/mcp_response_size_limit",
            },
            "mandatory-timeouts": {
                "name": "Mandatory Timeouts",
                "fact_ref": "abevalflow:default/mcp_mandatory_timeouts",
            },
            "openapi-conformance": {
                "name": "OpenAPI Conformance",
                "fact_ref": "abevalflow:default/mcp_openapi_conformance",
            },
            "tool-name-rules": {
                "name": "Tool-Name Rules",
                "fact_ref": "abevalflow:default/mcp_tool_name_rules",
                "source": "compass",
                "consumed": True,
            },
            "oauth-catalog-match": {
                "name": "OAuth Matches Catalog",
                "fact_ref": "abevalflow:default/mcp_oauth_catalog_match",
                "source": "compass",
                "consumed": True,
            },
        },
    },
    "behavioral-eval": {
        "fact_ref": "abevalflow:default/mcp_behavioral_eval",
        "source": "pipeline",
        "checks": {
            "tool-correctness": {
                "name": "Tool Correctness",
                "fact_ref": "abevalflow:default/mcp_tool_correctness",
            },
            "edge-case-handling": {
                "name": "Edge Case Handling",
                "fact_ref": "abevalflow:default/mcp_edge_case_handling",
            },
            "sensitive-data-redaction": {
                "name": "Sensitive Data Redaction",
                "fact_ref": "abevalflow:default/mcp_sensitive_data_redaction",
            },
        },
    },
}

# Top-level fact for overall MCP evaluation
MCP_EVAL_FACT = "abevalflow:default/mcp_eval"

# Source validation and defaults
DEFAULT_SOURCE = "pipeline"
VALID_CHECK_STATUSES = frozenset({"pass", "fail", "not_evaluated"})

# ============================================================================
# Derived Lookups - Computed from PHASES
# ============================================================================

# Check names by phase
PHASE_CHECK_NAMES: dict[str, dict[str, str]] = {
    phase: {check_id: check_data["name"] for check_id, check_data in phase_data["checks"].items()}
    for phase, phase_data in PHASES.items()
}

# Fact mappings by phase
PHASE_FACT_MAPS: dict[str, dict[str, str]] = {
    phase: {check_id: check_data["fact_ref"] for check_id, check_data in phase_data["checks"].items()}
    for phase, phase_data in PHASES.items()
}

# Phase fact refs
PHASE_FACTS: dict[str, str] = {
    phase: phase_data["fact_ref"] for phase, phase_data in PHASES.items()
}

# Consumed checks by phase (checks marked as consumed=True)
PHASE_CONSUMED_CHECKS: dict[str, set[str]] = {
    phase: {
        check_id for check_id, check_data in phase_data["checks"].items() if check_data.get("consumed", False)
    }
    for phase, phase_data in PHASES.items()
    if any(check_data.get("consumed", False) for check_data in phase_data["checks"].values())
}

# Source defaults by phase
PHASE_SOURCE_DEFAULTS: dict[str, str] = {
    phase: phase_data["source"] for phase, phase_data in PHASES.items()
}

# Per-check source overrides by phase
PHASE_CHECK_SOURCE_DEFAULTS: dict[str, dict[str, str]] = {
    phase: {
        check_id: check_data["source"]
        for check_id, check_data in phase_data["checks"].items()
        if "source" in check_data
    }
    for phase, phase_data in PHASES.items()
    if any("source" in check_data for check_data in phase_data["checks"].values())
}

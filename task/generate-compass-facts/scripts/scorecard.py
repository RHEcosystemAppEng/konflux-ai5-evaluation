"""Load scorecard configuration from a YAML file."""

from __future__ import annotations

from pathlib import Path

import yaml

DEFAULT_SOURCE = "pipeline"
VALID_CHECK_STATUSES = frozenset({"pass", "fail", "not_evaluated"})


def load_scorecard(config_path: Path) -> dict:
    """Load scorecard config from a YAML file and return it as-is."""
    with open(config_path) as f:
        return yaml.safe_load(f)


def build_entity_ref(component_name: str, namespace: str) -> str:
    """Build the entity ref from a component name and namespace."""
    return f"{namespace}/{component_name}"

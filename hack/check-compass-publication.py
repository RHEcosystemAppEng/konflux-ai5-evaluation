#!/usr/bin/env python3
"""Check the Compass PipelineRun and its Konflux bundle-build inputs."""

import json
import os
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory

import yaml


ROOT = Path(__file__).resolve().parents[1]
NAME = "compass-publication"
DEFINITION = f"pipelines/{NAME}/{NAME}.yaml"
run = yaml.safe_load((ROOT / DEFINITION).read_text())
assert run["kind"] == "PipelineRun" and run["metadata"]["name"] == NAME
assert any(
    workspace["name"] == "data" and "volumeClaimTemplate" in workspace
    for workspace in run["spec"]["workspaces"]
)
tasks = {task["name"]: task for task in run["spec"]["pipelineSpec"]["tasks"]}
assert "verify-enterprise-contract" in tasks["publish-compass"]["runAfter"]
selector = tasks["select-component"]["taskSpec"]["steps"][0]
component = {"name": "rh-sre", "containerImage": "fixture"}

with TemporaryDirectory() as work:
    target = Path(work) / "selected"
    script = selector["args"][0].replace("$(results.selected.path)", str(target))
    for trigger, marked, expected in (
        ("rh-sre", "true", True),
        ("rh-sre", "", False),
        ("another-plugin", "true", False),
    ):
        subprocess.run(
            [sys.executable, "-c", script],
            check=True,
            env={
                **os.environ,
                "SNAPSHOT": json.dumps(
                    {"components": [component, {"name": "another-plugin"}]}
                ),
                "COMPONENT": "rh-sre",
                "TRIGGER_COMPONENT": trigger,
                "PUBLISH": marked,
            },
        )
        output = target.read_text()
        assert (json.loads(output) if expected else output) == (
            {"components": [component]} if expected else "skip"
        )

for event in ("pull-request", "push"):
    invocation = yaml.safe_load(
        (ROOT / f".tekton/pipeline-{NAME}-{event}.yaml").read_text()
    )
    assert invocation["metadata"]["labels"]["appstudio.openshift.io/component"] == (
        f"pipeline-{NAME}"
    )
    spec = invocation["spec"]
    params = {item["name"]: item["value"] for item in spec["params"]}
    assert params["path-context"] == DEFINITION
    assert params["output-image"].startswith(
        f"quay.io/redhat-user-workloads/ai5-marketplace-tenant/pipeline-{NAME}:"
    )
    builder = next(
        task for task in spec["pipelineSpec"]["tasks"] if task["name"] == "build-container"
    )
    assert any(
        param["name"] == "name" and param["value"] == "tkn-bundle-oci-ta"
        for param in builder["taskRef"]["params"]
    )

print("Compass PipelineRun selector, workspace and bundle-build wiring passed")

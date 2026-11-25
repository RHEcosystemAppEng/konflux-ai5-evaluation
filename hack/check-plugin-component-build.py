#!/usr/bin/env python3
"""Check the reusable build Pipeline's interface and Task wiring."""

import re
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
NAME = "plugin-component-build"
pipeline = yaml.safe_load((ROOT / f"pipelines/{NAME}/{NAME}.yaml").read_text())
assert pipeline["kind"] == "Pipeline" and pipeline["metadata"]["name"] == NAME

spec = pipeline["spec"]
params = {item["name"]: item for item in spec["params"]}
assert len(params) == len(spec["params"]), "Duplicate Pipeline parameter"
references = set(re.findall(r"\$\(params\.([\w-]+)\)", yaml.safe_dump(spec)))
assert references <= params.keys(), f"Undeclared Pipeline parameters: {references - params.keys()}"

tasks = {task["name"]: task for task in spec["tasks"]}
bundles = {
    "select-evaluation-tiers": ("check-pr-label", "label-task-bundle"),
    "evaluate-skill": ("aeh-skill-eval", "evaluation-task-bundle"),
    "verify-plugin-evidence": ("verify-plugin-evidence", "verify-task-bundle"),
    "collect-plugin-context": ("collect-plugin-context", "compass-task-bundle"),
}
for task_name, (name, bundle_param) in bundles.items():
    task = tasks[task_name]
    ref = task["taskRef"]
    assert ref["resolver"] == "bundles"
    assert {item["name"]: item["value"] for item in ref["params"]} == {
        "name": name,
        "kind": "task",
        "bundle": f"$(params.{bundle_param})",
    }, task_name

    definition = yaml.safe_load((ROOT / f"task/{name}/{name}.yaml").read_text())["spec"]
    declared = {item["name"] for item in definition["params"]}
    required = {item["name"] for item in definition["params"] if "default" not in item}
    supplied = {item["name"] for item in task["params"]}
    assert supplied <= declared, f"{task_name} unknown inputs: {supplied - declared}"
    assert required <= supplied, f"{task_name} missing inputs: {required - supplied}"

assert params["mirror-source"]["default"] == ""
label_lookup = {item["name"]: item["value"] for item in tasks["select-evaluation-tiers"]["params"]}
assert label_lookup["source-url"] == "$(params.git-url)"
assert label_lookup["mirror-source"] == "$(params.mirror-source)"

evaluation = {item["name"]: item["value"] for item in tasks["evaluate-skill"]["params"]}
assert {"compass-secret", "compass-token-key"}.isdisjoint(evaluation)
assert "compass-token-key" not in params
assert params["persist"]["default"] == "postgres"
collector = {item["name"]: item["value"] for item in tasks["collect-plugin-context"]["params"]}
assert collector["compass-secret"] == "$(params.compass-secret)"
assert evaluation["tiers"] == "$(tasks.select-evaluation-tiers.results.tiers)"
assert [
    task["name"]
    for task in spec["tasks"]
    if any(item["value"] == "$(params.insecure-ssl)" for item in task.get("params", []))
] == ["evaluate-skill"]

print("plugin-component-build interface and Task wiring passed")

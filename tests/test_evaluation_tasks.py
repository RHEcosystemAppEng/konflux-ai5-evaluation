"""Local task contracts and optional executable CLI smoke tests (no cluster required)."""

import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

import yaml

ROOT = Path(__file__).resolve().parents[1]
TASK = yaml.safe_load((ROOT / "task/aeh-skill-eval/aeh-skill-eval.yaml").read_text())["spec"]
STEPS = {s["name"]: s for s in TASK["steps"]}


class TaskContracts(unittest.TestCase):
    def test_compass_credential_key_is_selected_by_the_consumer(self):
        params = {p["name"]: p for p in TASK["params"]}
        env = {e["name"]: e for e in STEPS["evaluate"]["env"]}
        self.assertEqual(params["compass-token-key"]["default"], "token")
        reference = env["ABEVAL_COMPASS_TOKEN"]["valueFrom"]["secretKeyRef"]
        self.assertEqual(reference["name"], "$(params.compass-secret)")
        self.assertEqual(reference["key"], "$(params.compass-token-key)")

    def test_array_is_passed_as_arguments_without_shell_interpolation(self):
        for name in ("evaluate", "emit-results"):
            step = STEPS[name]
            self.assertEqual(step["args"][-2:], ["bash", "$(params.changed-skills[*])"])
            self.assertIn('"$@"', step["args"][0])
            self.assertNotIn("$(params.changed-skills", step["args"][0])
        self.assertEqual(STEPS["evaluate"]["onError"], "continue")
        self.assertNotIn("onError", STEPS["emit-results"])

    def test_registry_credentials_and_attachment_stay_in_konflux(self):
        script = STEPS["attach-oci-reports"]["script"]
        for expected in ("select-oci-auth", "retry oras attach", "oci-attachment.json"):
            self.assertIn(expected, script)
        package = STEPS["package-oci-reports"]
        self.assertEqual(package["command"], ["bash", "-c"])
        self.assertIn('abeval batch-package --batch-dir "$ABEVAL_OUTPUT"', package["args"][0])

    def test_tls_mode_is_an_explicit_cli_setting(self):
        params = {p["name"]: p for p in TASK["params"]}
        self.assertEqual(params["insecure-ssl"]["default"], "false")
        env = {e["name"]: e for e in STEPS["evaluate"]["env"]}
        self.assertEqual(env["ABEVAL_INSECURE_SSL"]["value"], "$(params.insecure-ssl)")

    def test_trial_case_concurrency_is_configurable(self):
        params = {p["name"]: p for p in TASK["params"]}
        env = {e["name"]: e for e in STEPS["evaluate"]["env"]}
        self.assertEqual(params["n-concurrent"]["default"], "1")
        self.assertEqual(env["ABEVAL_N_CONCURRENT"]["value"], "$(params.n-concurrent)")


@unittest.skipUnless(os.environ.get("ABEVAL_TEST_CLI"), "Set ABEVAL_TEST_CLI to an installed abeval executable")
class ExecutableTaskSmoke(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.batch = self.root / "batch"
        self.exitfile = self.root / "source.exit"
        self.exitfile.write_text("0")
        self.env = {
            **os.environ,
            "PATH": str(Path(os.environ["ABEVAL_TEST_CLI"]).parent) + os.pathsep + os.environ["PATH"],
            "ABEVAL_SOURCE": str(self.root / "missing-source"),
            "ABEVAL_OUTPUT": str(self.batch),
            "ABEVAL_RUN_ID": "task-smoke",
            "ABEVAL_REVISION": "deadbeef",
            "EVALUATION_TIERS": "1",
            "ABEVAL_PERSIST": "",
            "IMAGE_URL": "",
            "IMAGE_DIGEST": "",
            "BATCH_MANIFEST_PATH": str(self.root / "manifest-result"),
            "BATCH_MANIFEST": "runs/task-smoke/summary.json",
            "FAIL_ON_NON_SUCCESS": "true",
        }

    def execute(self, step, skills):
        script = STEPS[step]["args"][0]
        script = script.replace("$(steps.step-use-trusted-artifact.exitCode.path)", str(self.exitfile))
        script = script.replace("/tekton/results", str(self.root / "results"))
        return subprocess.run(["bash", "-c", script, "bash", *skills], env=self.env,
                              capture_output=True, text=True, timeout=30)

    def test_empty_list_finishes_without_source(self):
        self.exitfile.write_text("1")
        result = self.execute("evaluate", [])
        self.assertEqual(result.returncode, 0, result.stderr)
        emitted = self.execute("emit-results", [])
        self.assertEqual(emitted.returncode, 0, emitted.stderr)
        self.assertEqual(json.loads((self.batch / "summary.json").read_text())["items"], [])

    def test_packaged_archive_is_accessible_to_the_attachment_image_uid(self):
        import stat

        self.assertEqual(self.execute("evaluate", []).returncode, 0)
        packaged = self.execute("package-oci-reports", [])
        self.assertEqual(packaged.returncode, 0, packaged.stderr)
        self.assertEqual(stat.S_IMODE((self.batch / "reports.tar.gz").stat().st_mode), 0o644)
        self.assertEqual(stat.S_IMODE(self.batch.stat().st_mode), 0o733)
        self.assertEqual(stat.S_IMODE(self.batch.parent.stat().st_mode), 0o711)

    def test_missing_skill_emits_error_and_gates_after_evaluation(self):
        self.assertEqual(self.execute("evaluate", ["pack/missing"]).returncode, 3)
        emitted = self.execute("emit-results", ["pack/missing"])
        self.assertEqual(emitted.returncode, 1, emitted.stderr)
        result = json.loads((self.root / "results/TEST_OUTPUT_TIER_A").read_text())
        self.assertEqual(result["result"], "ERROR")
        self.assertTrue((self.batch / "summary.json").is_file())

    def test_source_failure_still_emits_fail_closed_results(self):
        self.exitfile.write_text("1")
        self.assertEqual(self.execute("evaluate", ["pack/skill"]).returncode, 3)
        self.assertEqual(self.execute("emit-results", ["pack/skill"]).returncode, 1)
        self.assertEqual(json.loads((self.root / "results/TEST_OUTPUT_PUBLICATION").read_text())["result"], "ERROR")


if __name__ == "__main__":
    unittest.main()

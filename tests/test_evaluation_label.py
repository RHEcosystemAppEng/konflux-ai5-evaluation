"""Execute the bundled label selector against GitLab response fixtures."""

import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import urllib.error

import yaml

SCRIPT = yaml.safe_load(
    (
        Path(__file__).resolve().parents[1] / "task/check-pr-label/check-pr-label.yaml"
    ).read_text()
)["spec"]["steps"][0]["script"]
SHA = "a" * 40


def merged(**overrides):
    return {
        "iid": 95,
        "state": "merged",
        "target_branch": "pilot",
        "merge_commit_sha": SHA,
        "labels": ["evaluate"],
        **overrides,
    }


class EvaluationLabel(unittest.TestCase):
    def select(self, rows, mode="auto", error=None):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            script = SCRIPT.replace("$(results.tiers.path)", str(root / "tiers"))
            script = script.replace(
                "$(results.should-evaluate.path)", str(root / "enabled")
            )
            env = {
                "TIERS": mode,
                "CURRENT_SHA": SHA,
                "TARGET_BRANCH": "pilot",
                "LABEL_NAME": "evaluate",
                "GITLAB_SERVER_URL": "https://gitlab.example.com",
                "GITLAB_PROJECT_PATH": "group%2Frepo",
                "GIT_TOKEN": "fixture-token",
            }
            response = io.BytesIO(json.dumps(rows).encode())
            response.headers = {}
            with (
                patch.dict(os.environ, env),
                patch("time.sleep"),
                patch("builtins.print"),
                patch(
                    "urllib.request.urlopen", side_effect=error, return_value=response
                ) as request,
            ):
                # Each retry requires its own stream.
                if error is None:

                    def respond(*args, **kwargs):
                        stream = io.BytesIO(json.dumps(rows).encode())
                        stream.headers = {}
                        return stream

                    request.side_effect = respond
                exec(compile(script, "bundled-check-pr-label", "exec"), {})
                return (
                    (root / "tiers").read_text(),
                    (root / "enabled").read_text(),
                    request.call_count,
                )

    def test_matching_merged_label_requests_both_tiers(self):
        self.assertEqual(self.select([merged()])[:2], ("1,2", "true"))

    def test_unlabeled_merge_runs_only_tier_one(self):
        self.assertEqual(self.select([merged(labels=[])])[:2], ("1", "false"))

    def test_other_commits_branches_and_open_mrs_cannot_select_tier_two(self):
        for rows in (
            [merged(merge_commit_sha="b" * 40)],
            [merged(target_branch="main")],
            [merged(state="opened")],
            [],
        ):
            with self.subTest(rows=rows):
                self.assertEqual(self.select(rows)[:2], ("1", "false"))

    def test_squash_and_fast_forward_merge_identities(self):
        for row in (
            merged(merge_commit_sha="b" * 40, squash_commit_sha=SHA),
            merged(merge_commit_sha=None, sha=SHA, diff_refs=None),
        ):
            with self.subTest(row=row):
                self.assertEqual(self.select([row])[:2], ("1,2", "true"))

    def test_explicit_override_does_not_query_gitlab(self):
        for mode in ("1", "1,2"):
            with self.subTest(mode=mode):
                self.assertEqual(
                    self.select([], mode),
                    (mode, "true" if mode == "1,2" else "false", 0),
                )

    def test_api_or_tls_errors_do_not_silently_skip_a_requested_evaluation(self):
        with self.assertRaisesRegex(SystemExit, "Cannot resolve evaluation label"):
            self.select([], error=urllib.error.URLError("unavailable"))

    def test_ambiguous_merge_is_rejected(self):
        with self.assertRaisesRegex(SystemExit, "Ambiguous"):
            self.select([merged(), merged(iid=96)])

    def test_invalid_tiers_are_rejected(self):
        with self.assertRaisesRegex(SystemExit, "tiers must"):
            self.select([], mode="2")

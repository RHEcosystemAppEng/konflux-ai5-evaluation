"""Execute the bundled label selector against GitLab and GitHub response fixtures."""

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
GITHUB_REPOSITORY = "example/plugins"


def merged(**overrides):
    return {
        "iid": 95,
        "state": "merged",
        "target_branch": "pilot",
        "merge_commit_sha": SHA,
        "labels": ["evaluate"],
        **overrides,
    }


def github_pull(**overrides):
    return {
        "number": 19,
        "state": "closed",
        "merged_at": "2026-11-24T00:00:00Z",
        "base": {"ref": "pilot", "repo": {"full_name": GITHUB_REPOSITORY}},
        "merge_commit_sha": SHA,
        "labels": [{"name": "evaluate"}],
        **overrides,
    }


def github_error(code, message):
    return urllib.error.HTTPError(
        "https://api.github.com/", code, message, {},
        io.BytesIO(json.dumps({"message": message}).encode()),
    )


class EvaluationLabel(unittest.TestCase):
    def select(
        self, rows, mode="auto", error=None, *, repository="", github_token="", github_pages=()
    ):
        self.github_requests = []
        pages = iter(github_pages)

        def respond(request, **_):
            if request.full_url.startswith("https://api.github.com/"):
                self.github_requests.append(request)
                page = next(pages)
                if isinstance(page, Exception):
                    raise page
                body, headers = page
            else:
                if error is not None:
                    raise error
                body, headers = rows, {}
            stream = io.BytesIO(json.dumps(body).encode())
            stream.headers = headers
            return stream

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
                "GITHUB_UPSTREAM_REPOSITORY": repository,
                "GITHUB_PR_TOKEN": github_token,
            }
            with (
                patch.dict(os.environ, env),
                patch("time.sleep"),
                patch("builtins.print"),
                patch("urllib.request.urlopen", side_effect=respond) as request,
            ):
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

    def test_explicit_override_does_not_query_either_provider(self):
        for mode in ("1", "1,2"):
            with self.subTest(mode=mode):
                self.assertEqual(
                    self.select([], mode, repository=GITHUB_REPOSITORY),
                    (mode, "true" if mode == "1,2" else "false", 0),
                )

    def test_api_or_tls_errors_do_not_silently_skip_a_requested_evaluation(self):
        with self.assertRaisesRegex(SystemExit, "Cannot resolve evaluation label"):
            self.select([], error=urllib.error.URLError("unavailable"), repository=GITHUB_REPOSITORY)
        self.assertEqual(self.github_requests, [])

    def test_ambiguous_merge_is_rejected(self):
        with self.assertRaisesRegex(SystemExit, "Ambiguous"):
            self.select([merged(), merged(iid=96)])

    def test_invalid_tiers_are_rejected(self):
        with self.assertRaisesRegex(SystemExit, "tiers must"):
            self.select([], mode="2")

    def test_unlabeled_gitlab_match_still_takes_precedence(self):
        self.assertEqual(self.select([merged(labels=[])], repository=GITHUB_REPOSITORY), ("1", "false", 1))
        self.assertEqual(self.github_requests, [])

    def test_github_fallback_looks_up_the_exact_sha_without_credentials(self):
        result = self.select([], repository=GITHUB_REPOSITORY, github_pages=[([github_pull()], {})])
        self.assertEqual(result[:2], ("1,2", "true"))
        (request,) = self.github_requests
        self.assertEqual(
            request.full_url,
            f"https://api.github.com/repos/{GITHUB_REPOSITORY}/commits/{SHA}/pulls?per_page=100&page=1",
        )
        self.assertIsNone(request.get_header("Authorization"))
        self.assertIsNone(request.get_header("Private-token"))

    def test_unlabeled_or_unrelated_github_pulls_stay_in_tier_one(self):
        for rows in (
            [],
            [github_pull(labels=[])],
            [github_pull(state="open", merged_at=None)],
            [github_pull(merged_at=None)],
            [github_pull(merge_commit_sha="b" * 40)],
            [github_pull(base={"ref": "other", "repo": {"full_name": GITHUB_REPOSITORY}})],
            [github_pull(base={"ref": "pilot", "repo": {"full_name": "another/plugins"}})],
        ):
            with self.subTest(rows=rows):
                result = self.select([], repository=GITHUB_REPOSITORY, github_pages=[(rows, {})])
                self.assertEqual(result[:2], ("1", "false"))

    def test_github_next_page_uses_github_token_only(self):
        next_page = {"Link": '<https://api.github.com/repositories/123/commits/example/pulls?page=2>; rel="next"'}
        result = self.select(
            [], repository=GITHUB_REPOSITORY, github_token="fixture-github-token",
            github_pages=[([], next_page), ([github_pull()], {})],
        )
        self.assertEqual(result[:2], ("1,2", "true"))
        first, second = self.github_requests
        self.assertEqual(first.get_header("Authorization"), "Bearer fixture-github-token")
        self.assertEqual(second.get_header("Authorization"), "Bearer fixture-github-token")
        self.assertTrue(second.full_url.endswith("/pulls?per_page=100&page=2"))

    def test_gitlab_only_commit_absent_from_github_stays_in_tier_one(self):
        absent = github_error(422, f"No commit found for SHA: {SHA}")
        result = self.select([], repository=GITHUB_REPOSITORY, github_pages=[absent])
        self.assertEqual(result[:2], ("1", "false"))

    def test_github_errors_do_not_silently_skip_evaluation(self):
        for code, message in ((403, "Rate limit exceeded"), (404, "Not Found"), (422, "Validation Failed")):
            with self.subTest(code=code), self.assertRaisesRegex(SystemExit, f"GitHub: HTTP {code}"):
                self.select([], repository=GITHUB_REPOSITORY, github_pages=[github_error(code, message)])

    def test_github_repository_requires_owner_and_repository_name(self):
        with self.assertRaisesRegex(SystemExit, "github-repository must be a GitHub.com owner/repo"):
            self.select([], repository="https://github.com/example/plugins")
        self.assertEqual(self.github_requests, [])

    def test_invalid_or_ambiguous_github_results_are_rejected(self):
        for rows, message in (
            ([github_pull(), github_pull(number=20)], "Ambiguous merged GitHub PR"),
            ([github_pull(labels=["evaluate"])], "Invalid GitHub PR labels"),
            ({"error": "unexpected"}, "Invalid GitHub PR response"),
        ):
            with self.subTest(rows=rows), self.assertRaisesRegex(SystemExit, message):
                self.select([], repository=GITHUB_REPOSITORY, github_pages=[(rows, {})])

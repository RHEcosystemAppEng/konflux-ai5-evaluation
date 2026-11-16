import contextlib
import io
import json
import os
from pathlib import Path
import runpy
import tempfile
import unittest
from unittest.mock import patch
import urllib.error


SCRIPT = Path(os.environ["CHECK_PR_LABEL_SCRIPT"])


class LabelCheckTests(unittest.TestCase):
    def run_case(self, fixture, *, host="gitlab.example.com", status="merged",
                 label="evaluate", token="fixture-token", error=None,
                 pr_number="", context_pr_number=None, pages=None,
                 expect_failure=False, warning=None):
        if isinstance(error, urllib.error.HTTPError):
            self.addCleanup(error.close)

        class Response:
            def __init__(self, fixture, link=""):
                self.fixture = fixture
                self.headers = {"Link": link}

            def __enter__(self):
                return self
            def __exit__(self, *args):
                return False
            def read(self):
                return (self.fixture if isinstance(self.fixture, str) else json.dumps(self.fixture)).encode()

        with tempfile.TemporaryDirectory() as temp:
            result = Path(temp) / "result"
            env = {"GIT_URL": f"https://{host}/group/sub/repo.git", "REVISION": "deadbeef",
                   "TARGET_LABEL": label, "PR_STATUS": status, "GIT_TOKEN": token,
                   "PR_NUMBER": pr_number, "RESULT_PATH": str(result)}
            with patch.dict(os.environ, env), patch("urllib.request.urlopen") as lookup:
                if context_pr_number is None:
                    os.environ.pop("CONTEXT_PR_NUMBER", None)
                else:
                    os.environ["CONTEXT_PR_NUMBER"] = context_pr_number
                lookup.return_value = Response(fixture)
                lookup.side_effect = ([page if isinstance(page, Exception) else Response(*page)
                                       for page in pages] if pages is not None else error)
                stderr = io.StringIO()
                with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(stderr):
                    if expect_failure:
                        with self.assertRaises(SystemExit) as failure:
                            runpy.run_path(str(SCRIPT), run_name="__main__")
                        self.assertTrue(failure.exception.code)
                        self.assertFalse(result.exists(), "A failed check must not write has-label")
                    else:
                        runpy.run_path(str(SCRIPT), run_name="__main__")
                if warning is not None:
                    self.assertIn(warning, stderr.getvalue())
                return result.read_text() if result.exists() else None, lookup

    def test_gitlab_legacy_gate(self):
        cases = [
            ("merged matching", [{"state": "merged", "labels": ["evaluate"]}], "true"),
            ("later merged matching", [{"iid": 16, "created_at": "2026-11-14T10:00:00Z", "state": "opened", "labels": ["other"]},
                                       {"iid": 17, "created_at": "2026-11-15T10:00:00Z", "state": "merged", "labels": ["evaluate"]}], "true"),
            ("open matching", [{"state": "opened", "labels": ["evaluate"]}], "false"),
            ("closed matching", [{"state": "closed", "labels": ["evaluate"]}], "false"),
            ("merged wrong label", [{"state": "merged", "labels": ["other"]}], "false"),
            ("separate matching fields", [{"iid": 16, "created_at": "2026-11-14T10:00:00Z", "state": "opened", "labels": ["evaluate"]},
                                          {"iid": 17, "created_at": "2026-11-15T10:00:00Z", "state": "merged", "labels": []}], "false"),
        ]
        for name, fixture, expected in cases:
            with self.subTest(name=name):
                result, lookup = self.run_case(fixture)
                self.assertEqual(result, expected)
                self.assertEqual(lookup.call_args.args[0].full_url,
                                 "https://gitlab.example.com/api/v4/projects/group%2Fsub%2Frepo/repository/commits/deadbeef/merge_requests")
                self.assertEqual(lookup.call_args.args[0].get_header("Private-token"), "fixture-token")

    def test_gitlab_optional_status_and_label(self):
        for status in ("", "open"):
            with self.subTest(status=status):
                result, _ = self.run_case([{"state": "opened", "labels": ["mcpchecker"]}], status=status, label="mcpchecker")
                self.assertEqual(result, "true")
        result, _ = self.run_case([{"state": "closed", "labels": ["evaluate"]}], status="closed")
        self.assertEqual(result, "true")

    def test_github_and_enterprise(self):
        cases = [
            ("github.com", "merged", "closed", "2026-11-09", "true"),
            ("github.com", "open", "open", None, "true"),
            ("github.com", "merged", "open", None, "false"),
            ("github.com", "closed", "closed", "2026-11-09", "false"),
            ("github.com", "closed", "closed", None, "true"),
            ("github.example.com", "merged", "closed", "2026-11-09", "true"),
        ]
        for host, status, state, merged, expected in cases:
            with self.subTest(host=host, status=status, state=state, merged=merged):
                result, lookup = self.run_case([{"state": state, "merged_at": merged,
                                                "labels": [{"name": "evaluate"}]}], host=host, status=status)
                self.assertEqual(result, expected)
                api = "https://api.github.com" if host == "github.com" else "https://github.example.com/api/v3"
                self.assertEqual(lookup.call_args.args[0].full_url,
                                 api + "/repos/group/sub/repo/commits/deadbeef/pulls")
                self.assertEqual(lookup.call_args.args[0].get_header("Authorization"), "token fixture-token")

    def test_missing_token_fails_without_api(self):
        for host in ("github.com", "gitlab.example.com"):
            with self.subTest(host=host):
                _, lookup = self.run_case([], host=host, token="", expect_failure=True)
                lookup.assert_not_called()

    def test_lookup_failures_fail_without_result(self):
        errors = [urllib.error.URLError("fixture connection refused"),
                  TimeoutError("fixture timeout")]
        errors += [urllib.error.HTTPError("https://example.com", code, "fixture error", {}, None)
                   for code in (401, 403, 404, 500, 503)]
        for host in ("github.com", "gitlab.example.com"):
            for error in errors:
                with self.subTest(host=host, error=type(error).__name__):
                    self.run_case([], host=host, error=error, expect_failure=True)
            self.run_case("not-json", host=host, expect_failure=True)

    def test_invalid_configuration_fails(self):
        for options in ({"status": "invalid"}, {"host": "unsupported.example.com"}):
            with self.subTest(options=options):
                self.run_case([], expect_failure=True, **options)

    def test_direct_github_pr_lookup(self):
        for host in ("github.com", "github.example.com"):
            with self.subTest(host=host):
                result, lookup = self.run_case(
                    {"state": "closed", "merged_at": "2026-11-09", "labels": [{"name": "evaluate"}]},
                    host=host, pr_number="17")
                self.assertEqual(result, "true")
                lookup.assert_called_once()
                api = "https://api.github.com" if host == "github.com" else "https://github.example.com/api/v3"
                self.assertEqual(lookup.call_args.args[0].full_url, api + "/repos/group/sub/repo/pulls/17")

    def test_direct_gitlab_mr_lookup(self):
        result, lookup = self.run_case(
            {"iid": 17, "id": 987654, "state": "merged", "labels": ["evaluate"]}, pr_number="17")
        self.assertEqual(result, "true")
        lookup.assert_called_once()
        self.assertEqual(lookup.call_args.args[0].full_url,
                         "https://gitlab.example.com/api/v4/projects/group%2Fsub%2Frepo/merge_requests/17")

    def test_explicit_pr_overrides_context(self):
        for host, path in [("github.com", "/pulls/17"), ("gitlab.example.com", "/merge_requests/17")]:
            with self.subTest(host=host):
                fixture = {"state": "merged", "labels": ["evaluate"]} if "gitlab" in host else {
                    "state": "closed", "merged_at": "2026-11-09", "labels": [{"name": "evaluate"}]}
                _, lookup = self.run_case(fixture, host=host, pr_number="17", context_pr_number="99")
                lookup.assert_called_once()
                self.assertTrue(lookup.call_args.args[0].full_url.endswith(path))

    def test_context_pr_number_used(self):
        for host, path in [("github.com", "/pulls/99"), ("gitlab.example.com", "/merge_requests/99")]:
            with self.subTest(host=host):
                fixture = {"state": "merged", "labels": ["evaluate"]} if "gitlab" in host else {
                    "state": "closed", "merged_at": "2026-11-09", "labels": [{"name": "evaluate"}]}
                _, lookup = self.run_case(fixture, host=host, context_pr_number="99")
                lookup.assert_called_once()
                self.assertTrue(lookup.call_args.args[0].full_url.endswith(path))

    def test_no_pr_number_uses_commit_lookup(self):
        for host, path in [("github.com", "/commits/deadbeef/pulls"),
                           ("gitlab.example.com", "/repository/commits/deadbeef/merge_requests")]:
            for context in (None, ""):
                with self.subTest(host=host, context=context):
                    fixture = {"state": "merged", "labels": []} if "gitlab" in host else {
                        "state": "closed", "merged_at": "2026-11-09", "labels": []}
                    result, lookup = self.run_case([fixture], host=host, context_pr_number=context)
                    self.assertEqual(result, "false")
                    lookup.assert_called_once()
                    self.assertTrue(lookup.call_args.args[0].full_url.endswith(path))

    def test_direct_label_and_status_filtering(self):
        cases = [
            ("open", "", ["evaluate"], "true"),
            ("open", "open", ["evaluate"], "true"),
            ("open", "merged", ["evaluate"], "false"),
            ("merged", "merged", ["evaluate"], "true"),
            ("merged", "closed", ["evaluate"], "false"),
            ("closed", "closed", ["evaluate"], "true"),
            ("merged", "merged", ["other"], "false"),
            ("merged", "merged", [], "false"),
        ]
        for host in ("github.com", "gitlab.example.com"):
            for state, status, labels, expected in cases:
                with self.subTest(host=host, state=state, status=status, labels=labels):
                    if "github" in host:
                        fixture = {"state": "closed" if state == "merged" else state,
                                   "merged_at": "2026-11-09" if state == "merged" else None,
                                   "labels": [{"name": label} for label in labels]}
                    else:
                        fixture = {"state": "opened" if state == "open" else state, "labels": labels}
                    result, _ = self.run_case(fixture, host=host, status=status, pr_number="17")
                    self.assertEqual(result, expected)

    def test_direct_failure_does_not_fall_back(self):
        errors = [urllib.error.URLError("fixture connection refused"),
                  urllib.error.HTTPError("https://example.com", 404, "fixture not found", {}, None),
                  TimeoutError("fixture timeout")]
        failures = [(None, error) for error in errors] + [("not-json", None), ("", None)]
        for host, path in [("github.com", "/pulls/17"), ("gitlab.example.com", "/merge_requests/17")]:
            for source in ("explicit", "context"):
                for fixture, error in failures:
                    with self.subTest(host=host, source=source, error=error, fixture=fixture):
                        options = {"pr_number": "17"} if source == "explicit" else {"context_pr_number": "17"}
                        _, lookup = self.run_case(fixture, host=host, error=error, expect_failure=True, **options)
                        lookup.assert_called_once()
                        self.assertTrue(lookup.call_args.args[0].full_url.endswith(path))

    def test_no_associated_pr_fails(self):
        for host in ("github.com", "gitlab.example.com"):
            with self.subTest(host=host):
                _, lookup = self.run_case([], host=host, expect_failure=True)
                lookup.assert_called_once()

    def test_invalid_response_fails(self):
        for host in ("github.com", "gitlab.example.com"):
            invalid_items = [{}, {"state": "merged"}, {"state": "merged", "labels": None},
                             {"state": "merged", "labels": "evaluate"}, {"labels": []},
                             {"state": "invalid", "labels": []},
                             {"state": "closed", "merged_at": None, "labels": [None]}]
            if "github" in host:
                invalid_items += [{"state": "invalid", "merged_at": "2026-11-09", "labels": []},
                                  {"state": "closed", "merged_at": False, "labels": [{"name": "evaluate"}]},
                                  {"state": "closed", "merged_at": "", "labels": []}]
            for item in invalid_items:
                for number, fixture in (("17", item), ("", [item])):
                    with self.subTest(host=host, fixture=fixture, pr_number=number):
                        self.run_case(fixture, host=host, pr_number=number, expect_failure=True)
            for number, fixture in (("17", []), ("17", None), ("", {}), ("", [None])):
                with self.subTest(host=host, fixture=fixture, pr_number=number):
                    self.run_case(fixture, host=host, pr_number=number, expect_failure=True)

    def test_latest_pr_selected_before_label_and_status(self):
        for host in ("github.com", "gitlab.example.com"):
            for status, newest_matches_label, newest_is_merged, expected in (
                    ("", False, True, "false"), ("merged", False, True, "false"),
                    ("merged", True, False, "false"), ("", True, False, "true"),
                    ("merged", True, True, "true")):
                older = {"created_at": "2026-11-14T10:00:00Z", "updated_at": "2026-11-16T10:00:00Z"}
                newer = {"created_at": "2026-11-15T10:00:00Z", "updated_at": "2026-11-15T10:00:00Z"}
                if "github" in host:
                    older.update(number=16, state="closed", merged_at="2026-11-14", labels=[{"name": "evaluate"}])
                    newer.update(number=17, state="closed" if newest_is_merged else "open",
                                 merged_at="2026-11-15" if newest_is_merged else None,
                                 labels=[{"name": "evaluate"}] if newest_matches_label else [])
                else:
                    older.update(iid=16, state="merged", labels=["evaluate"])
                    newer.update(iid=17, state="merged" if newest_is_merged else "opened",
                                 labels=["evaluate"] if newest_matches_label else [])
                for fixtures in ([older, newer], [newer, older]):
                    with self.subTest(host=host, status=status, fixtures=fixtures):
                        value, lookup = self.run_case(fixtures, host=host, status=status,
                            warning="Found 2 PRs/MRs without a PR number; checking only the latest PR/MR 17")
                        self.assertEqual(value, expected)
                        lookup.assert_called_once()

    def test_invalid_creation_date_fails_when_selection_is_ambiguous(self):
        for host in ("github.com", "gitlab.example.com"):
            for bad in ({}, {"created_at": "not-a-date"}):
                with self.subTest(host=host, bad=bad):
                    self.run_case([{"created_at": "2026-11-14T10:00:00Z"}, bad],
                                  host=host, expect_failure=True)

    def test_pagination_selects_latest_pr(self):
        for host in ("github.com", "gitlab.example.com"):
            if "github" in host:
                url = "https://api.github.com/repos/group/sub/repo/commits/deadbeef/pulls"
                older = {"number": 16, "state": "closed", "merged_at": "2026-11-14", "labels": [{"name": "evaluate"}]}
                newer = {"number": 17, "state": "closed", "merged_at": "2026-11-15", "labels": []}
            else:
                url = "https://gitlab.example.com/api/v4/projects/group%2Fsub%2Frepo/repository/commits/deadbeef/merge_requests"
                older = {"iid": 16, "state": "merged", "labels": ["evaluate"]}
                newer = {"iid": 17, "state": "merged", "labels": []}
            older["created_at"] = "2026-11-14T10:00:00Z"
            newer["created_at"] = "2026-11-15T10:00:00Z"
            with self.subTest(host=host):
                value, lookup = self.run_case(None, host=host,
                    pages=[([older], f'<{url}?page=2>; rel="next"'), ([newer], "")],
                    warning="Found 2 PRs/MRs without a PR number; checking only the latest PR/MR 17")
                self.assertEqual(value, "false")
                self.assertEqual(lookup.call_count, 2)
                self.assertEqual(lookup.call_args.args[0].full_url, url + "?page=2")
                self.run_case(None, host=host,
                    pages=[([older], f'<{url}?page=2>; rel="next"'), TimeoutError("fixture timeout")],
                    expect_failure=True)

    def test_pagination_rejects_another_host(self):
        _, lookup = self.run_case(None, pages=[([], '<https://other.example.com/page2>; rel="next"')],
                                  expect_failure=True)
        lookup.assert_called_once()


if __name__ == "__main__":
    unittest.main()

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


SCRIPT = Path(os.environ["CHECK_LABEL_SCRIPT"])


class LabelCheckTests(unittest.TestCase):
    def run_case(self, fixture, *, host="gitlab.example.com", status="merged",
                 label="evaluate", token="fixture-token", error=None):
        class Response:
            def __enter__(self):
                return self
            def __exit__(self, *args):
                return False
            def read(self):
                return (fixture if isinstance(fixture, str) else json.dumps(fixture)).encode()

        with tempfile.TemporaryDirectory() as temp:
            result = Path(temp) / "result"
            env = {"GIT_URL": f"https://{host}/group/sub/repo.git", "REVISION": "deadbeef",
                   "TARGET_LABEL": label, "PR_STATUS": status, "GIT_TOKEN": token,
                   "RESULT_PATH": str(result)}
            with patch.dict(os.environ, env), patch("urllib.request.urlopen") as lookup:
                lookup.return_value = Response()
                lookup.side_effect = error
                with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                    runpy.run_path(str(SCRIPT), run_name="__main__")
                return result.read_text(), lookup

    def test_gitlab_legacy_gate(self):
        cases = [
            ("merged matching", [{"state": "merged", "labels": ["evaluate"]}], "true"),
            ("open matching", [{"state": "opened", "labels": ["evaluate"]}], "false"),
            ("closed matching", [{"state": "closed", "labels": ["evaluate"]}], "false"),
            ("merged wrong label", [{"state": "merged", "labels": ["other"]}], "false"),
            ("no merge requests", [], "false"),
            ("missing labels", [{"state": "merged"}], "false"),
            ("null labels", [{"state": "merged", "labels": None}], "false"),
            ("separate matching fields", [{"state": "opened", "labels": ["evaluate"]},
                                          {"state": "merged", "labels": []}], "false"),
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

    def test_missing_token_skips_api(self):
        for host in ("github.com", "gitlab.example.com"):
            with self.subTest(host=host):
                result, lookup = self.run_case([], host=host, token="")
                self.assertEqual(result, "false")
                lookup.assert_not_called()

    def test_lookup_failures_return_false(self):
        errors = [urllib.error.URLError("fixture connection refused"),
                  urllib.error.HTTPError("https://gitlab.example.com", 503, "fixture unavailable", {}, None),
                  TimeoutError("fixture timeout")]
        for host in ("github.com", "gitlab.example.com"):
            for error in errors:
                with self.subTest(host=host, error=type(error).__name__):
                    result, _ = self.run_case([], host=host, error=error)
                    self.assertEqual(result, "false")
            result, _ = self.run_case("not-json", host=host)
            self.assertEqual(result, "false")

    def test_invalid_configuration_fails(self):
        for options in ({"status": "invalid"}, {"host": "unsupported.example.com"}):
            with self.subTest(options=options), self.assertRaises(SystemExit):
                self.run_case([], **options)


if __name__ == "__main__":
    unittest.main()

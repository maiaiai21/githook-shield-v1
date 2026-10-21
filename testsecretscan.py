"""Tests for the GitHook Shield scanner.

Fake secrets are assembled from fragments at runtime so this file never
contains a complete token-shaped string. That keeps the repo's own pre-commit
hook from blocking commits to this project.
"""
import os
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scanner"))

import secretscan  # noqa: E402


def rules(text, name="sample.py"):
    return [f.rule for f in secretscan.scan_text(text, name)]


class SecretDetectionTests(unittest.TestCase):
    def test_aws_access_key_detected(self):
        key = "AKIA" + "Z7Q3XR2M5PLZ8WYN"
        self.assertIn("aws-access-key-id", rules(f'KEY = "{key}"'))

    def test_github_token_detected(self):
        token = "ghp_" + "a1B2c3D4e5F6g7H8i9J0k1L2m3N4o5P6q7R8"
        self.assertIn("github-token", rules(f'TOKEN = "{token}"'))

    def test_private_key_header_detected(self):
        header = "-----BEGIN RSA " + "PRIVATE KEY-----"
        self.assertIn("private-key", rules(header))

    def test_db_password_detected(self):
        # Regression: Gitleaks missed this in our evaluation.
        self.assertIn("credential-assignment", rules('DB_PASSWORD = "Sup3rS3cretP4ssw0rd!"'))

    def test_prefixed_api_key_detected(self):
        self.assertIn("credential-assignment",
                      rules('payment_api_key = "8f3kQ9xLp2Zr7WmT4vNc1BhD6sYe0JgU"'))

    def test_json_style_password_detected(self):
        self.assertIn("credential-assignment",
                      rules('{"password": "Tr0ub4dor&3xK9pQ"}', "config.json"))


class FalsePositiveTests(unittest.TestCase):
    def test_aws_documented_example_ignored(self):
        self.assertEqual(rules('AWS_ACCESS_KEY_ID = "AKIAIOSFODNN7EXAMPLE"'), [])

    def test_placeholders_ignored(self):
        self.assertEqual(rules('api_key = "your_api_key_here"'), [])
        self.assertEqual(rules('password = "changeme"'), [])
        self.assertEqual(rules('SECRET_KEY = "replace-me-in-production"'), [])

    def test_low_entropy_value_ignored(self):
        self.assertEqual(rules('password = "aaaaaaaaaaaa"'), [])

    def test_hash_without_credential_name_ignored(self):
        self.assertEqual(rules('SHA256 = "' + "ab" * 32 + '"'), [])

    def test_clean_code_ignored(self):
        code = "import os\nPORT = int(os.getenv('PORT', '5000'))\n"
        self.assertEqual(rules(code), [])

    def test_line_numbers_reported(self):
        text = "x = 1\n\napi_key = \"8f3kQ9xLp2Zr7WmT4vNc1BhD6sYe0JgU\"\n"
        findings = secretscan.scan_text(text, "a.py")
        self.assertEqual(findings[0].line, 3)

    def test_secret_is_redacted_in_output(self):
        value = "8f3kQ9xLp2Zr7WmT4vNc1BhD6sYe0JgU"
        findings = secretscan.scan_text(f'api_key = "{value}"', "a.py")
        self.assertNotIn(value, findings[0].redacted)


class SyntaxTests(unittest.TestCase):
    def test_broken_python_blocked(self):
        findings = secretscan.check_syntax("bad.py", "def f(:\n    pass\n")
        self.assertEqual([f.rule for f in findings], ["syntax-error"])

    def test_valid_python_passes(self):
        self.assertEqual(secretscan.check_syntax("ok.py", "x = 1\n"), [])

    def test_broken_json_blocked(self):
        findings = secretscan.check_syntax("bad.json", '{"a": 1,}')
        self.assertEqual([f.rule for f in findings], ["syntax-error"])

    def test_broken_shell_blocked(self):
        findings = secretscan.check_syntax("bad.sh", "if true; then\necho hi\n")
        self.assertEqual([f.rule for f in findings], ["syntax-error"])

    def test_unchecked_extension_skipped(self):
        self.assertEqual(secretscan.check_syntax("notes.md", "((( not code"), [])


class StagedModeTests(unittest.TestCase):
    """End-to-end: a real git repo, a staged secret, and the scanner's exit code."""

    def _run_in_repo(self, filename, content):
        with tempfile.TemporaryDirectory() as repo:
            subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
            subprocess.run(["git", "config", "user.email", "t@t"], cwd=repo, check=True)
            subprocess.run(["git", "config", "user.name", "t"], cwd=repo, check=True)
            with open(os.path.join(repo, filename), "w") as fh:
                fh.write(content)
            subprocess.run(["git", "add", filename], cwd=repo, check=True)
            log = os.path.join(repo, "scan-log.json")
            proc = subprocess.run(
                [sys.executable, os.path.join(ROOT, "scanner", "secretscan.py"),
                 "--staged", "--log", log],
                cwd=repo, capture_output=True, text=True,
            )
            log_text = ""
            if os.path.exists(log):
                with open(log) as fh:
                    log_text = fh.read()
            return proc.returncode, proc.stdout, log_text

    def test_clean_staged_file_passes(self):
        code, out, log = self._run_in_repo("app.py", "x = 1\n")
        self.assertEqual(code, 0)
        self.assertIn('"result": "pass"', log)

    def test_staged_secret_blocked_and_logged(self):
        content = 'api_key = "8f3kQ9xLp2Zr7WmT4vNc1BhD6sYe0JgU"\n'
        code, out, log = self._run_in_repo("config.py", content)
        self.assertEqual(code, 1)
        self.assertIn("Commit blocked", out)
        self.assertIn('"result": "block"', log)
        self.assertIn('"line": "1"', log)


if __name__ == "__main__":
    unittest.main()

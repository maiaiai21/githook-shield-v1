#!/usr/bin/env python3
"""GitHook Shield scanner.

Two checks run on each file:
  1. Secret detection: fixed-format regex rules for known token types, plus a
     name-based rule that flags high-entropy quoted values assigned to
     credential-like names (api_key, password, DB_PASSWORD, ...).
  2. Syntax checks for .py, .json and .sh files.

Usage:
  secretscan.py --staged [--log scan-log.json]   check staged changes (pre-commit)
  secretscan.py FILE [FILE ...]                  check files directly

Exit status: 0 when nothing is found, 1 when a secret or syntax error is found.
"""
import argparse
import ast
import datetime
import json
import math
import os
import re
import subprocess
import sys
import tempfile
from dataclasses import dataclass


@dataclass
class Finding:
    file: str
    line: int
    rule: str
    redacted: str


# Fixed-format rules: each matches one known token shape.
PATTERNS = [
    ("aws-access-key-id", re.compile(r"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b")),
    ("aws-secret-access-key", re.compile(
        r"(?i)aws_secret_access_key\s*[:=]\s*[\"']?[A-Za-z0-9/+=]{40}\b")),
    ("github-token", re.compile(r"\bgh[pousr]_[A-Za-z0-9]{36}\b")),
    ("slack-token", re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{10,}\b")),
    ("stripe-live-key", re.compile(r"\bsk_live_[0-9A-Za-z]{24,}\b")),
    ("google-api-key", re.compile(r"\bAIza[0-9A-Za-z_-]{35}\b")),
    ("private-key", re.compile(r"-----BEGIN (?:RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----")),
]

# Name-based rule. No leading word boundary, so DB_PASSWORD and payment_api_key
# also match. The value must be quoted.
ASSIGNMENT = re.compile(
    r"(?i)(?:api[_-]?key|secret[_-]?key|secret|access[_-]?token|auth[_-]?token|password|passwd)"
    r"[\"']?\s*[:=]\s*[\"']([^\"'\s]{8,})[\"']"
)

# Values that are documentation or template placeholders, not secrets.
PLACEHOLDER = re.compile(r"(?i)(example|your[_-]|changeme|replace|placeholder|dummy|xxxx|<|\$\{)")

ENTROPY_THRESHOLD = 3.0
SYNTAX_CHECKED = {".py", ".json", ".sh"}


def entropy(value: str) -> float:
    """Shannon entropy in bits per character."""
    if not value:
        return 0.0
    counts = {}
    for ch in value:
        counts[ch] = counts.get(ch, 0) + 1
    n = len(value)
    return -sum((c / n) * math.log2(c / n) for c in counts.values())


def redact(value: str) -> str:
    return value[:4] + "****" if len(value) > 4 else "****"


def scan_text(text: str, filename: str) -> list[Finding]:
    findings = []
    for lineno, line in enumerate(text.splitlines(), 1):
        hit = None
        for rule, pattern in PATTERNS:
            match = pattern.search(line)
            if match and not PLACEHOLDER.search(match.group(0)):
                hit = (rule, match.group(0))
                break
        if hit is None:
            for match in ASSIGNMENT.finditer(line):
                value = match.group(1)
                if PLACEHOLDER.search(value) or entropy(value) < ENTROPY_THRESHOLD:
                    continue
                hit = ("credential-assignment", value)
                break
        if hit:
            findings.append(Finding(filename, lineno, hit[0], redact(hit[1])))
    return findings


def check_syntax(filename: str, text: str) -> list[Finding]:
    ext = os.path.splitext(filename)[1]
    if ext not in SYNTAX_CHECKED:
        return []
    try:
        if ext == ".py":
            ast.parse(text, filename)
        elif ext == ".json":
            json.loads(text)
        elif ext == ".sh":
            with tempfile.NamedTemporaryFile("w", suffix=".sh", delete=False) as tmp:
                tmp.write(text)
                tmp_name = tmp.name
            try:
                proc = subprocess.run(["bash", "-n", tmp_name], capture_output=True, text=True)
            finally:
                os.unlink(tmp_name)
            if proc.returncode != 0:
                raise SyntaxError(proc.stderr.strip() or "shell syntax error")
    except SyntaxError as err:
        line = err.lineno or 1
        return [Finding(filename, line, "syntax-error", str(err.msg if hasattr(err, "msg") else err)[:80])]
    except ValueError as err:  # json.JSONDecodeError is a ValueError
        return [Finding(filename, getattr(err, "lineno", 1) or 1, "syntax-error", str(err)[:80])]
    return []


def staged_files() -> list[str]:
    out = subprocess.run(
        ["git", "diff", "--cached", "--name-only", "--diff-filter=ACM", "-z"],
        capture_output=True, text=True, check=True,
    ).stdout
    return [name for name in out.split("\0") if name]


def staged_content(path: str) -> bytes:
    return subprocess.run(["git", "show", f":{path}"], capture_output=True, check=True).stdout


def write_log(path: str, rows: list[dict]) -> None:
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    with open(path, "a") as log:
        for row in rows:
            log.write(json.dumps({"time": now, "commit": "-", **row}) + "\n")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="GitHook Shield scanner")
    parser.add_argument("paths", nargs="*", help="files to scan")
    parser.add_argument("--staged", action="store_true", help="scan staged git changes")
    parser.add_argument("--log", help="append JSON result lines to this file")
    args = parser.parse_args(argv)

    files = []  # (name, text) pairs
    if args.staged:
        print("GitHook Shield: scanning staged changes...")
        for name in staged_files():
            data = staged_content(name)
            if b"\0" in data:  # skip binary files
                continue
            files.append((name, data.decode("utf-8", errors="replace")))
    for path in args.paths:
        with open(path, "rb") as fh:
            data = fh.read()
        if b"\0" not in data:
            files.append((path, data.decode("utf-8", errors="replace")))

    all_findings = []
    log_rows = []
    for name, text in files:
        findings = check_syntax(name, text) + scan_text(text, name)
        all_findings.extend(findings)
        if findings:
            for f in findings:
                log_rows.append({"file": f.file, "line": str(f.line), "result": "block", "rule": f.rule})
                print(f"{f.file}:{f.line}  [{f.rule}]  {f.redacted}")
        else:
            log_rows.append({"file": name, "line": "-", "result": "pass", "rule": "-"})

    if args.log and args.staged:
        write_log(args.log, log_rows)

    if all_findings:
        n_files = len({f.file for f in all_findings})
        print(f"\n{len(all_findings)} finding(s) in {n_files} file(s).")
        if args.staged:
            print("Commit blocked: possible secret detected.")
        return 1
    if args.staged:
        print("No secrets found.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Generate a labeled dataset for evaluating secret scanners.

dataset/positives/ : 30 files, each containing exactly one SYNTHETIC secret.
dataset/negatives/ : 30 files with look-alike strings and no real secrets.

All secret values come from a fixed random seed, so re-running this script
reproduces the same files. The dataset directory is gitignored: the files
contain fake secrets, and the repo's own CI scan would flag them.
"""
import random
import string
from pathlib import Path

SEED = 20261021
ROOT = Path(__file__).resolve().parent
DATA = ROOT / "dataset"
POS = DATA / "positives"
NEG = DATA / "negatives"

rng = random.Random(SEED)
ALNUM = string.ascii_letters + string.digits
UPPER_NUM = string.ascii_uppercase + string.digits
HEX = "0123456789abcdef"


def rand(charset, n):
    return "".join(rng.choice(charset) for _ in range(n))


# (category, line template, value factory)
POSITIVE_TEMPLATES = [
    ("aws-access-key-id", 'AWS_ACCESS_KEY_ID = "AKIA{s}"', lambda: rand(UPPER_NUM, 16)),
    ("aws-secret-key", 'aws_secret_access_key = "{s}"', lambda: rand(ALNUM + "/+", 40)),
    ("generic-api-key", 'api_key = "{s}"', lambda: rand(ALNUM, 32)),
    ("github-pat", 'GITHUB_TOKEN = "ghp_{s}"', lambda: rand(ALNUM, 36)),
    ("slack-token", 'SLACK_TOKEN = "xoxb-{s}"',
     lambda: "-".join(rand(string.digits, 11) for _ in range(2)) + "-" + rand(ALNUM, 24)),
    ("stripe-live-key", 'STRIPE_KEY = "sk_live_{s}"', lambda: rand(ALNUM, 24)),
    ("google-api-key", 'GOOGLE_API_KEY = "AIza{s}"', lambda: rand(ALNUM + "-_", 35)),
    ("jwt-token", 'AUTH_TOKEN = "eyJ{s}"',
     lambda: rand(ALNUM, 20) + ".eyJ" + rand(ALNUM, 24) + "." + rand(ALNUM, 27)),
    ("generic-password", 'password = "{s}"', lambda: rand(ALNUM + "!@#$", 16)),
    ("db-password-var", 'DB_PASSWORD = "{s}"', lambda: rand(ALNUM + "!@#$", 16)),
    ("hex-secret-key", 'SECRET_KEY = "{s}"', lambda: rand(HEX, 64)),
    ("npm-token", 'NPM_TOKEN = "npm_{s}"', lambda: rand(ALNUM, 36)),
    ("mailgun-key", 'MAILGUN_API_KEY = "key-{s}"', lambda: rand(HEX, 32)),
    ("twilio-sid", 'TWILIO_ACCOUNT_SID = "AC{s}"', lambda: rand(HEX, 32)),
    # Header built at runtime so this source file never holds a full PEM marker.
    ("private-key-header", 'PRIVATE_KEY = "{s}"',
     lambda: "-----BEGIN RSA " + "PRIVATE KEY-----" + rand(ALNUM + "+/", 64)),
]

ORDER = ["py", "env", "yaml", "sh"]


def render(layout, line):
    if layout == "env":
        return "APP_ENV=production\n" + line.replace(" = ", "=").replace('"', "") + "\nLOG_LEVEL=info\n"
    if layout == "yaml":
        return "service:\n  name: demo\n  port: 5000\n  " + line.replace(" = ", ": ") + "\n"
    if layout == "sh":
        return "#!/bin/sh\nset -e\necho starting\n" + line + "\necho done\n"
    return "import os\n\nAPP_NAME = 'demo'\n" + line + "\nDEBUG = False\n"


def write_positives():
    POS.mkdir(parents=True, exist_ok=True)
    n = 0
    for idx, (category, template, factory) in enumerate(POSITIVE_TEMPLATES):
        for layout in (ORDER[idx % 4], ORDER[(idx + 1) % 4]):
            n += 1
            line = template.format(s=factory())
            (POS / f"pos_{n:02d}_{category}.{layout}").write_text(render(layout, line))


NEGATIVE_LINES = [
    'SHA256 = "{h}"',
    'COMMIT_SHA = "{h40}"',
    'REQUEST_ID = "{u}"',
    'api_key = "your_api_key_here"',
    'password = "<changeme>"',
    'SECRET_KEY = "replace-me-in-production"',
    'AWS_ACCESS_KEY_ID = "AKIAIOSFODNN7EXAMPLE"',
    'AWS_SECRET_ACCESS_KEY = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"',
    'VERSION = "1.12.1-distroless"',
    'IMAGE = "ghcr.io/example/app:1.0.0"',
    'MD5 = "{m}"',
    'TRACE_ID = "{h32}"',
]


def write_negatives():
    NEG.mkdir(parents=True, exist_ok=True)
    for i in range(1, 31):
        template = NEGATIVE_LINES[(i - 1) % len(NEGATIVE_LINES)]
        line = template.format(
            h=rand(HEX, 64),
            h40=rand(HEX, 40),
            h32=rand(HEX, 32),
            m=rand(HEX, 32),
            u="-".join([rand(HEX, 8), rand(HEX, 4), rand(HEX, 4), rand(HEX, 4), rand(HEX, 12)]),
        )
        layout = ORDER[i % 4]
        (NEG / f"neg_{i:02d}.{layout}").write_text(render(layout, line))


if __name__ == "__main__":
    write_positives()
    write_negatives()
    print(f"positives: {len(list(POS.iterdir()))}  negatives: {len(list(NEG.iterdir()))}")
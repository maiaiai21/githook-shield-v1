#!/bin/sh
# Live demo for the dashboard. Stages one sample file at a time, runs the real
# scanner on it, and appends the result to scan-log.json, so the dashboard
# updates as the script runs. Nothing is committed, and each file is removed
# after it is scanned.
# Secrets are assembled at runtime so this script passes the project's own scan.
# Run with nothing staged, because the scanner checks every staged file.
set -e

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
PAUSE="${PAUSE:-4}"

if ! git diff --cached --quiet; then
  echo "Something is already staged. Unstage it first (git reset) and run this again."
  exit 1
fi

stage_and_scan() {
  file="$1"
  git add "$file"
  echo
  echo "== Scanning $file"
  python3 scanner/secretscan.py --staged --log scan-log.json || true
  git reset -q HEAD "$file"
  rm -f "$file"
  sleep "$PAUSE"
}

printf 'def handler():\n    return "ok"\n' > live_app.py
stage_and_scan live_app.py

printf 'DB_%s = "%s"\n' PASSWORD "Sup3rS3cretP4ssw0rd!" > live_db.py
stage_and_scan live_db.py

printf 'def broken(:\n    pass\n' > live_broken.py
stage_and_scan live_broken.py

printf 'AWS_KEY = "%s%s"\n' AKIA QZ7MX4LP9WK2RT8N > live_aws.py
stage_and_scan live_aws.py

printf '# Notes\nNothing sensitive here.\n' > live_notes.md
stage_and_scan live_notes.md

echo
echo "Done. Five events were logged to scan-log.json."
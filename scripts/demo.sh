#!/bin/sh
# Demo of the local protection layer. Runs offline in a throwaway repo, so it
# never touches your working tree. Secrets are assembled at runtime so this
# script itself passes the project's own CI scan.
set -e

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DEMO="$(mktemp -d)"
trap 'rm -rf "$DEMO"' EXIT

mkdir -p "$DEMO/scanner" "$DEMO/hooks" "$DEMO/scripts"
cp "$ROOT/scanner/secretscan.py" "$DEMO/scanner/"
cp "$ROOT/hooks/pre-commit" "$DEMO/hooks/"
cp "$ROOT/scripts/install-hooks.sh" "$DEMO/scripts/"

cd "$DEMO"
git init -q
git config user.email demo@githook-shield.local
git config user.name "GitHook Shield Demo"
sh scripts/install-hooks.sh >/dev/null

echo
echo "== 1. Clean change"
printf 'print("hello from the app")\n' > app.py
git add app.py
git commit -qm "add app" && echo "Committed."

echo
echo "== 2. Hardcoded database password"
printf 'DB_%s = "%s"\n' PASSWORD "Sup3rS3cretP4ssw0rd!" > db.py
git add db.py
if git commit -qm "add db config"; then
  echo "Unexpected: commit went through."
else
  echo "Blocked as expected."
fi
git reset -q HEAD db.py && rm -f db.py

echo
echo "== 3. Broken Python syntax"
printf 'def broken(:\n    pass\n' > broken.py
git add broken.py
if git commit -qm "add broken module"; then
  echo "Unexpected: commit went through."
else
  echo "Blocked as expected."
fi
git reset -q HEAD broken.py && rm -f broken.py

echo
echo "== 4. Bypass with --no-verify"
printf 'DB_%s = "%s"\n' PASSWORD "Sup3rS3cretP4ssw0rd!" > db.py
git add db.py
git commit -q --no-verify -m "bypass the hook" && echo "Committed. The hook was skipped and nothing was logged."

echo
echo "== Scan log (scan-log.json)"
cat scan-log.json

if [ -f "$ROOT/evaluation/results.md" ]; then
  echo
  echo "== Evaluation summary (evaluation/results.md)"
  sed -n '1,12p' "$ROOT/evaluation/results.md"
fi
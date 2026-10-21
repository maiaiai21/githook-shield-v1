#!/bin/sh
# Installs the GitHook Shield pre-commit hook into this clone.
set -e
ROOT="$(git rev-parse --show-toplevel)"
HOOK_DIR="$(git rev-parse --git-path hooks)"
mkdir -p "$HOOK_DIR"
cp "$ROOT/hooks/pre-commit" "$HOOK_DIR/pre-commit"
chmod +x "$HOOK_DIR/pre-commit" "$ROOT/hooks/pre-commit"
echo "GitHook Shield installed into $HOOK_DIR/pre-commit"

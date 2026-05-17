#!/usr/bin/env bash
# Authenticate gh + git from $GITHUB_TOKEN. Idempotent — safe to run on every startup.
set -euo pipefail

if [[ -z "${GITHUB_TOKEN:-}" ]]; then
  echo "gh-login: GITHUB_TOKEN is not set" >&2
  exit 1
fi

if ! command -v gh >/dev/null 2>&1; then
  echo "gh-login: 'gh' CLI is not installed (try: sudo apt install gh)" >&2
  exit 1
fi

if gh auth status --hostname github.com >/dev/null 2>&1; then
  echo "gh-login: already authenticated as $(gh api user -q .login)"
else
  printf '%s' "$GITHUB_TOKEN" | gh auth login \
    --hostname github.com \
    --git-protocol https \
    --with-token
  echo "gh-login: logged in as $(gh api user -q .login)"
fi

gh auth setup-git
echo "gh-login: git credential helper configured"

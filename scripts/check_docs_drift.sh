#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

if ! command -v uv >/dev/null 2>&1; then
  echo "Error: 'uv' is required to run this check."
  echo "Install: https://docs.astral.sh/uv/"
  exit 1
fi

tmp_file="$(mktemp -t api_reference.XXXXXX)"
cleanup() { rm -f "$tmp_file"; }
trap cleanup EXIT

(cd backend && uv run python scripts/generate_api_reference.py --output "$tmp_file")

if ! cmp -s docs/backend/API_REFERENCE.md "$tmp_file"; then
  echo "Docs drift detected: \`docs/backend/API_REFERENCE.md\` is out of date."
  echo "Regenerate with:"
  echo "  cd backend && uv run python scripts/generate_api_reference.py --output ../docs/backend/API_REFERENCE.md"
  echo ""
  diff -u docs/backend/API_REFERENCE.md "$tmp_file" || true
  exit 1
fi

echo "OK: docs are in sync."


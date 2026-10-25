#!/usr/bin/env bash
# Run ansible-test for this collection from a path ending in ansible_collections/egors/homeassistant.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BASE="${ANSIBLE_COLLECTIONS_BASE:-${TMPDIR:-/tmp}/ansible-test-egors}"
DEST="$BASE/ansible_collections/egors/homeassistant"
mkdir -p "$DEST"
rsync -a --delete \
  --exclude '/.venv' --exclude '/tests/output' --exclude '__pycache__' --exclude '*.pyc' \
  "$ROOT/" "$DEST/"
export PATH="$ROOT/.venv/bin:$PATH"
cd "$DEST"
exec ansible-test "$@"

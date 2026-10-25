#!/usr/bin/env bash
# Run the integration tests against the Home Assistant container from docker-compose.yml.
# By default HA is recreated from scratch; set HA_KEEP=1 to reuse a running instance.
# Arguments are passed to ansible-test integration (e.g. target names).
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BASE="${ANSIBLE_COLLECTIONS_BASE:-${TMPDIR:-/tmp}/ansible-test-egors}"
TOKEN_PATH="${HA_TOKEN_PATH:-$BASE/ha.token}"
mkdir -p "$(dirname "$TOKEN_PATH")"

cd "$ROOT"
if [[ "${HA_KEEP:-0}" != "1" ]]; then
  docker compose down -v
  rm -f "$TOKEN_PATH"
fi
docker compose up -d --wait

cat > "$ROOT/tests/integration/integration_config.yml" <<CONFIG
---
ha_url: http://127.0.0.1:8123
ha_token_path: $TOKEN_PATH
ha_owner_username: admin
ha_owner_password: ansible-test-password
ha_owner_name: Ansible Test
CONFIG

run() {
  "$ROOT/scripts/ansible-test.sh" integration --venv --python 3.12 "$@"
}

if [[ $# -eq 0 ]]; then
  # The onboarding target must see a fresh, un-onboarded HA, so it runs first on its own.
  run onboarding
  run
else
  run "$@"
fi

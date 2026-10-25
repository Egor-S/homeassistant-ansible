# Ansible Collection: egors.homeassistant

> **Status: MVP / work in progress.** Interfaces may change.

Ansible modules to provision and configure [Home Assistant](https://www.home-assistant.io/)
over its REST and WebSocket APIs. Modules run on the controller, compare the
current state with the desired one and apply changes only when needed (check
mode and `--diff` supported).

## Requirements

- ansible-core >= 2.20 (tested with 2.20 and 2.21)
- Python package `websocket-client` on the controller
- A recent Home Assistant release (only the newest release is supported)

## Installation

```shell
pip install websocket-client
ansible-galaxy collection install git+https://github.com/Egor-S/homeassistant-ansible.git
```

## Modules

| Module | Purpose |
|---|---|
| `egors.homeassistant.onboarding` | Complete first-run onboarding (creates the owner user) |
| `egors.homeassistant.login` | Log in with username and password; returns a token valid for 1 day |
| `egors.homeassistant.core_config` | Core configuration: name, location, units, time zone, URLs, ... (partial state) |
| `egors.homeassistant.http_config` | HTTP server: port, SSL, reverse proxy, IP bans, CORS (partial state; restarts HA) |
| `egors.homeassistant.area` | Manage a single area (match by `area_id` or case-insensitive `name`) |
| `egors.homeassistant.area_info` | List areas |
| `egors.homeassistant.floor` | Manage a single floor (`level` may be 0 or negative) |
| `egors.homeassistant.floor_info` | List floors |

All modules except `onboarding` and `login` belong to the action group
`egors.homeassistant.all`, so the connection is configured once with `module_defaults`.
`onboarding` and `login` take no token and are therefore not in the group.

## Authentication

No token is ever written to disk. Keep secrets in [Ansible Vault](https://docs.ansible.com/ansible/latest/vault_guide/index.html)
and pick one of:

- **Username and password** (recommended): `login` creates a fresh token on every run
  and returns it in memory. It is named `Ansible login <time> <random>` in the user
  profile, expires after `token_lifespan` days (default 1) and is deleted by a later
  run once expired. The login session itself is revoked right away. `login` never
  reports a change.
- **Long-lived access token**: create one in the Home Assistant user profile, put it
  in Vault and pass it as `token` (or the `HASS_TOKEN` environment variable):

  ```yaml
  module_defaults:
    group/egors.homeassistant.all:
      url: "{{ hass_url }}"
      token: "{{ vault_hass_token }}"
  ```

Multi-factor authentication is not supported by `login`; use a long-lived token instead.

## Example

See [examples/site.yml](examples/site.yml) for a playbook that goes from a fresh
container to a configured instance:

```yaml
- name: Onboard
  egors.homeassistant.onboarding:
    url: "{{ hass_url }}"
    name: Admin
    username: admin
    password: "{{ vault_hass_password }}"

- name: Log in
  egors.homeassistant.login:
    url: "{{ hass_url }}"
    username: admin
    password: "{{ vault_hass_password }}"
  register: hass_login
  no_log: true  # the result contains the token

- name: Configure
  module_defaults:
    group/egors.homeassistant.all:
      url: "{{ hass_url }}"
      token: "{{ hass_login.token }}"
  block:
    - egors.homeassistant.core_config:
        location_name: Cottage
        time_zone: Europe/Helsinki
    - egors.homeassistant.area:
        name: Office
        aliases: [Study]
```

Note: `--check` against a never-onboarded instance stops at `login`, since the
owner user does not exist yet. On an onboarded instance `login` logs in during
`--check` too, so the other modules can report their planned changes.

## Development

```shell
uv venv --python 3.12 .venv && uv pip install --python .venv -r requirements-dev.txt
scripts/ansible-test.sh sanity --venv --python 3.12
scripts/ansible-test.sh units --venv --python 3.12
scripts/integration.sh              # fresh HA from docker-compose.yml, all targets
HA_KEEP=1 scripts/integration.sh area   # reuse the running HA, one target
```

`scripts/ansible-test.sh` copies the repo into a path ending in
`ansible_collections/egors/homeassistant` (required by ansible-test) and runs it there.
The HA image is pinned in `docker-compose.yml` and bumped by Dependabot.

See [docs/design.md](docs/design.md) for design decisions and
[docs/api-notes.md](docs/api-notes.md) for verified API behaviour.

## License

GPL-3.0-or-later

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
| `egors.homeassistant.onboarding` | Complete first-run onboarding and create a long-lived token (persisted with `token_path`) |
| `egors.homeassistant.core_config` | Core configuration: name, location, units, time zone, URLs, ... (partial state) |
| `egors.homeassistant.area` | Manage a single area (match by `area_id` or case-insensitive `name`) |
| `egors.homeassistant.area_info` | List areas |
| `egors.homeassistant.floor` | Manage a single floor (`level` may be 0 or negative) |
| `egors.homeassistant.floor_info` | List floors |

All modules except `onboarding` belong to the action group `egors.homeassistant.all`,
so the connection is configured once with `module_defaults`. `onboarding` takes no
token and is therefore not in the group.

## Example

See [examples/site.yml](examples/site.yml) for a playbook that goes from a fresh
container to a configured instance:

```yaml
- name: Onboard (or read back the token of an onboarded instance)
  egors.homeassistant.onboarding:
    url: "{{ hass_url }}"
    name: Admin
    username: admin
    password: "{{ hass_password }}"
    token_path: "{{ playbook_dir }}/.hass.token"
  register: hass_onboarding
  no_log: true  # the result contains the token

- name: Configure
  module_defaults:
    group/egors.homeassistant.all:
      url: "{{ hass_url }}"
      token: "{{ hass_onboarding.token }}"
  block:
    - egors.homeassistant.core_config:
        location_name: Cottage
        time_zone: Europe/Helsinki
    - egors.homeassistant.area:
        name: Office
        aliases: [Study]
```

Notes:

- The long-lived token can only be read when it is created. Keep `token_path`
  (or store the returned `token` yourself); otherwise a re-run of an onboarded
  instance has no token to return.
- `--check` against a never-onboarded instance stops after `onboarding`, since no
  token exists yet to query the rest.

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

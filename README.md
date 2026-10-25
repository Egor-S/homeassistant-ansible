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
| `egors.homeassistant.label` | Manage a single label (icon, color, description) |
| `egors.homeassistant.label_info` | List labels |
| `egors.homeassistant.zone` | Manage a single zone (location, radius, passive, icon) |
| `egors.homeassistant.zone_info` | List zones |
| `egors.homeassistant.input_boolean`, `input_button`, `input_datetime`, `input_number`, `input_select`, `input_text`, `counter`, `timer`, `schedule` | Manage a single helper of that type |
| `egors.homeassistant.helper_info` | List helpers of one type |
| `egors.homeassistant.person` | Manage a single person (linked user, device trackers, picture) |
| `egors.homeassistant.person_info` | List people |
| `egors.homeassistant.tag` | Manage a single NFC tag or QR code, by its ID |
| `egors.homeassistant.tag_info` | List tags |
| `egors.homeassistant.entity` | Settings of an existing entity: name, icon, area, aliases, labels, entity ID, enabled, hidden |
| `egors.homeassistant.entity_info` | List entities of the entity registry |

All modules except `onboarding` and `login` belong to the action group
`egors.homeassistant.all`, so the connection is configured once with `module_defaults`.
`onboarding` and `login` take no token and are therefore not in the group.

## Coverage

What Home Assistant lets you configure, and what this collection covers. Checked
against the source of HA **2026.10.4** (the pinned image). Only ✅ rows are tested
against a live instance. 🟡 rows only say an API exists; they don't promise a module.

- ✅ supported by a module
- 🟡 API exists, no module yet
- ❌ YAML-only or no API, so out of scope for now (see [docs/design.md](docs/design.md))

### Bootstrap and core

| Setting | Status | API / notes |
|---|---|---|
| Onboarding (owner user, first-run steps) | ✅ `onboarding` | REST `/api/onboarding/*`. Restoring a backup or logging in to Cloud during onboarding is not supported. |
| Access token for a run | ✅ `login` | `/auth/login_flow`, WS `auth/long_lived_access_token`. No MFA. |
| Name, location, elevation, radius, units, time zone, currency, country, language, internal/external URL | ✅ `core_config` | WS `config/core/update`. `country` and `currency` can't be cleared. |
| HTTP server: port, bind address, SSL, reverse proxy, IP bans, CORS | ✅ `http_config` | WS `http/config*` (trial, then promote) |
| `customize`, `packages`, `allowlist_external_dirs`/`_urls`, `media_dirs`, `auth_providers`, `auth_mfa_modules`, `debug`, `webrtc` | ❌ | `homeassistant:` block in `configuration.yaml` |
| Network adapters | 🟡 | WS `network/configure` |
| Analytics preferences | 🟡 | WS `analytics/preferences`. `onboarding` leaves analytics off. |
| Labs (preview features) | 🟡 | WS `labs/update` |

### Registries

| Setting | Status | API / notes |
|---|---|---|
| Areas | ✅ `area`, `area_info` | WS `config/area_registry/*` |
| Floors | ✅ `floor`, `floor_info` | WS `config/floor_registry/*` |
| Area / floor ordering | 🟡 | WS `config/{area,floor}_registry/reorder` |
| Labels | ✅ `label`, `label_info` | WS `config/label_registry/*` |
| Categories | 🟡 | WS `config/category_registry/*` (CRUD) |
| Devices: area, name, labels, disable | 🟡 | WS `config/device_registry/update`. Devices come from integrations; no create. |
| Entities: name, icon, area, aliases, labels, device class, disable/hide, entity ID | ✅ `entity`, `entity_info` | WS `config/entity_registry/get`, `update`. Created by integrations, so update only. |
| Entities exposed to voice assistants | 🟡 | WS `homeassistant/expose_entity`, `expose_new_entities/set` |

### Users and people

| Setting | Status | API / notes |
|---|---|---|
| Users (create, groups such as admin, local-only, active, delete) | 🟡 | WS `config/auth/*`, `config/auth_provider/homeassistant/*` (credentials, passwords) |
| People | ✅ `person`, `person_info` | WS `person/*`. The user is linked by `user_id` for now. |
| Zones | ✅ `zone`, `zone_info` | WS `zone/*`. The home zone comes from `core_config`. |
| Tags | ✅ `tag`, `tag_info` | WS `tag/*` |
| MFA for a user | ❌ | Interactive (`auth/setup_mfa`) |

### Helpers

| Setting | Status | API / notes |
|---|---|---|
| `input_boolean`, `input_button`, `input_datetime`, `input_number`, `input_select`, `input_text`, `counter`, `timer`, `schedule` | ✅ one module each, `helper_info` | WS `<domain>/*` (storage collections) |
| Template, group, threshold, and other config-flow helpers | 🟡 | Config entry flows, see Integrations |

### Integrations

| Setting | Status | API / notes |
|---|---|---|
| Add an integration (config entry) | 🟡 | REST `/api/config/config_entries/flow`. Flows are multi-step and differ per integration, so they're harder to make declarative. |
| Integration options | 🟡 | REST `/api/config/config_entries/options/flow` |
| Enable/disable, rename, delete entries | 🟡 | WS `config_entries/update`, `config_entries/disable`, REST `DELETE .../entry/{id}` |
| Application credentials (OAuth client IDs) | 🟡 | WS `application_credentials/*` |
| Integrations set up only in YAML (`template:`, `mqtt:` entities, `command_line`, ...) | ❌ | `configuration.yaml` |

### Automations, dashboards and the rest

| Setting | Status | API / notes |
|---|---|---|
| Automations, scripts, scenes | 🟡 | REST `/api/config/{automation,script,scene}/config/{id}`. Writes `automations.yaml`, `scripts.yaml` and `scenes.yaml` on the HA host. |
| Blueprints | 🟡 | WS `blueprint/{import,save,delete}` |
| Dashboards | 🟡 | WS `lovelace/dashboards/{list,create,update,delete}`, `lovelace/config/save` (content) |
| Dashboard resources (custom cards) | 🟡 | WS `lovelace/resources/*` (in storage mode) |
| Voice assistant pipelines | 🟡 | WS `assist_pipeline/pipeline/*` |
| Backup schedule and retention | 🟡 | WS `backup/config/update` |
| Energy dashboard | 🟡 | WS `energy/save_prefs` |
| Log level per integration | 🟡 | WS `logger/integration_log_level` (`persistence: permanent`) |
| Default log level, log filters | ❌ | `logger:` in YAML |
| Recorder: database URL, retention, excludes | ❌ | `recorder:` in YAML. Only `recorder/info` is readable. |

Runtime commands that aren't configuration (state, services, events, history, logbook,
traces, statistics, cameras, media, previews, templates) are out of scope.

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

See [docs/design.md](docs/design.md) for design decisions, [docs/roadmap.md](docs/roadmap.md) for what comes next, and
[docs/api-notes.md](docs/api-notes.md) for verified API behaviour.

## License

GPL-3.0-or-later

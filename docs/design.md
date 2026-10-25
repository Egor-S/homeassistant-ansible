# egors.homeassistant — design decisions

Ansible collection for provisioning and configuring Home Assistant (HA) over its
API. Modules receive a target state, query the current state, and apply changes
only when needed.

Status: MVP. Only the newest HA release is supported; we are not going back in
time. Support for older versions may be added later.

## Scope

- **API-only** (REST + WebSocket) for the MVP. YAML-only settings (`recorder`,
  `logger`, packages) are out of scope; a YAML/file-managing component may be
  added later. `http` is already API-managed in the pinned 2026.10.4 (store plus
  `http/config*` WS commands; YAML is imported once, then ignored, breaking in
  2027.2.0), so `http_config` covers it.
- Start small; add features once the MVP proves the approach.

## Architecture

- **Logic lives in modules** (Python): query → diff → apply, with check mode
  and `--diff` support from day one. Roles, if any, are thin wrappers later.
- **Modules run on the controller** (`delegate_to: localhost` /
  `ansible_connection: local`). Works identically for HAOS, Docker and Core
  installs; nothing is required on the HA host.
- **Own synchronous WebSocket client** in `module_utils`, built on
  `websocket-client` (guarded import, sanity-test friendly). Existing HA client
  libraries are async/heavy and lag behind the config commands.
- **Common connection options** via a doc fragment: `url`, `token`,
  `validate_certs`, `timeout`, with `HASS_URL` / `HASS_TOKEN` env fallbacks.
  Action group `egors.homeassistant.all` so `module_defaults` can set them once.
  `onboarding` and `login` are **not** in the group: they take no `token`, and
  `module_defaults` for a group fails modules that do not accept every default.
- **No secrets on disk**: the collection never writes a token anywhere. Credentials
  live in Ansible Vault; `login` turns them into a token held in memory for one run.
  Users who prefer it pass their own long-lived token (from Vault) as `token`.
- **Version check**: modules read the HA version (WS auth response) and
  **warn** — never fail — when it is older than the `MIN_HA_VERSION` constant.

## MVP modules

| Module | Kind | Notes |
|---|---|---|
| `onboarding` | bootstrap | Completes all onboarding steps (`user`, `core_config`, `analytics`, `integration`) with minimal defaults (analytics off). No core-config inputs — `core_config` owns those. Polls until HA is up (`wait_timeout`, default 300s). Creates no token; its login session is revoked at the end. |
| `login` | auth | Username/password → long-lived token with a short lifespan (default 1 day), named `<token_client_name> <UTC time> <random hex>` (HA allows one LLAT per name). Deletes tokens matching that pattern older than the lifespan, keeps younger ones (parallel runs). Revokes its login session. Always `changed: false`; runs in check mode. |
| `core_config` | singleton | **Partial** state: only keys provided are compared/updated (`config/core/update`). |
| `area` | collection item | `state: present/absent`. Match by `area_id` if given, else case-insensitive `name`; rename = `area_id` + new `name`. Fields: `name`, `aliases` (set semantics), `icon`, `picture`; `floor_id`, `labels`, `temperature_entity_id`, `humidity_entity_id` passed through as raw IDs. |
| `area_info` | info | Lists areas. |
| `floor` | collection item | Same shape as `area`: match by `floor_id`, else case-insensitive `name`. Fields: `name`, `aliases` (set semantics), `icon`, `level` (int). |
| `floor_info` | info | Lists floors. |
| `label` / `label_info` | collection item / info | Same shape as `floor` (match by `label_id`, else name). Fields: `name`, `icon`, `color` (hex or theme color), `description`. |
| `zone` / `zone_info` | collection item / info | Storage collection on the same `registry.py` (`entry_key="id"`; commands take `zone_id`). Names may repeat, so a name matching several zones fails. `latitude`/`longitude` required to create; `icon` can't be removed. |
| `input_boolean`, `input_button`, `input_datetime`, `input_number`, `input_select`, `input_text`, `counter`, `timer`, `schedule` | collection item | One typed module per helper type (argspec validation and docs per type), field specs shared in `module_utils/helpers.py`. HA **replaces the whole item** on update, so `registry.py` sends the current entry with the changes applied (`replace=True`); a cleared field is left out and falls back to HA's default. `input_select.options` is ordered. Values HA rewrites (`timer.duration` to `H:MM:SS`, `schedule` ranges to sorted `HH:MM:SS`) are converted to the stored form before comparing (`convert` in `registry.py`). |
| `helper_info` | info | One info module for all helper types (`type` option, `helper_id` filter) instead of one per type. |
| `person` / `person_info` | collection item / info | Like `zone`; `person/list` returns `{storage, config}`, only `storage` is managed (`list_key`). `user_id` is a raw ID until a `user` module exists. |
| `tag` / `tag_info` | collection item / info | The ID is the scanned tag ID, chosen by the user: `tag_id` is required, a missing tag is created with it (`create_with_id`), never matched by name. |
| `entity` / `entity_info` | existing item / info | Update only (`config/entity_registry/get` + `update`), matched by `entity_id`; `new_entity_id` renames, and a missing `entity_id` whose `new_entity_id` exists counts as renamed. `disabled`/`hidden` booleans map to `disabled_by`/`hidden_by` (`user` or null). The `null` alias (the entity's own name) is kept and not reported. Own code in `module_utils/entity.py`, not `registry.py`. |
| `http_config` | singleton | **Partial** state like `core_config`, but `http/config/configure` replaces the whole config, so stable plus changes is sent. A change restarts HA into a 5-minute trial; the module waits for the WS connection to drop, reconnects (`reconnect_url`, for port/TLS changes) until `RUNNING`, checks HA runs on the new config, then promotes it. An unreachable result reverts itself. |

Deferred: a set-level module (`areas` with `purge`, default `false`) once the
per-item module is proven. Purging areas is destructive (strips device/entity
assignments), hence opt-in.

## Testing

- `ansible-test` sanity + units + integration.
- **Unit tests** cover pure logic only (diffing, matching, argspec); the WS
  client is mocked. All API behaviour is tested against a **real HA container**.
- HA image is **pinned to an exact version**; Renovate/Dependabot bumps it via
  PRs so a breakage points at a specific release.
- One container per CI job. The `onboarding` integration target onboards it
  (and re-runs to prove idempotency); a `setup_ha` target provides the token to
  the other targets; targets clean up after themselves.
- Local runs use the same `docker compose` file as CI.
- CI: GitHub Actions; matrix over the **last two ansible-core releases**
  (2.20, 2.21). HA is started by `scripts/integration.sh` from the same
  `docker-compose.yml` as local runs (instead of a job service container) for
  exact local/CI parity. The image pin is bumped by **Dependabot**
  (`docker-compose` ecosystem; no app install needed, unlike Renovate).

## Project

- Namespace/name: `egors.homeassistant`. Installed from git during the MVP;
  Galaxy publish workflow later.
- semver from `0.1.0`; `antsibull-changelog` fragments from the first commit.
- License: GPL-3.0-or-later.

## MVP viability criteria

1. Fresh container → onboarded HA with core config and areas, in one playbook.
2. Second run → `changed=0`.
3. `--check --diff` reports accurate planned changes without applying them.
4. CI green on the pinned HA × both ansible-core versions.
5. Adding another registry resource (e.g. floors) is mostly copying the area
   module (~100 lines). If not, revisit the module structure before adding
   features.

## Implementation notes (deviations found while building)

- Onboarding steps after `user` use the short-lived access token (the
  `integration` step rejects long-lived tokens).
- A run interrupted after the `user` step recovers by logging in as the owner via
  `/auth/login_flow`.
- Persisting the token (`token_path`) was dropped before the first release: a 10-year
  admin token in plaintext next to the playbook, outside Vault, saved nothing over a
  login with the password the playbook already has.
- `--check` on a never-onboarded instance cannot get past `login` (no owner yet).
- Generic registry logic (find/diff/create/update/delete, check mode, diff) lives
  in `module_utils/registry.py`; `area.py`/`floor.py` are ~20 lines of code plus docs.
  Field kinds: `strings` and `ints` (`""` clears), `lists` (set semantics) and `values` (typed by
  the argument spec, e.g. floats and bools). Storage collections (zones, later helpers) use the same
  class with `entry_key`, `unclearable` and `required`.
- An onboarded HA answers `/api/onboarding` with 404 after a restart (the views are
  only registered while onboarding is unfinished); `onboarding` treats that as done,
  and the compose healthcheck uses `/manifest.json`. Found by `http_config` restarts.

## MVP status (2026-10-25, HA 2026.10.4)

1. ✅ Fresh container → configured, one playbook (`examples/site.yml`).
2. ✅ Second run `changed=0`.
3. ✅ `--check --diff` shows pending changes without applying (on an onboarded
   instance).
4. ✅ CI green on GitHub Actions: sanity, units and integration on ansible-core
   2.20 and 2.21 against the pinned HA.
5. ✅ Proven by adding `floor`/`floor_info`: 19 lines of module code (area: 18).
   `registry.py` needed one generic extension (an `ints` field kind for `level`)
   and the second resource exposed a latent bug (create dropped `0` values).

## Open

- When to add YAML-managed settings (`recorder`, `logger`, packages).
- Whether a "whole config" role is worth having.
- Galaxy publishing (viability is now shown).

## Assumptions to verify

None open. Verified against the pinned HA (see `api-notes.md`): WS `config/core/update`,
`config/area_registry/*`, the onboarding REST flow, and the HA version in the WS
auth response, and the `http/config*` commands. `websocket-client` on the controller is a documented requirement
(README).

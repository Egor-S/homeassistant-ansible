# Roadmap

Priorities for the 🟡 rows of the README coverage table (API exists, no module yet), agreed
2026-10-25 against HA 2026.10.4. Each item ships as its own PR with unit and integration tests
against the pinned container, and is merged when CI is green. The order trades the value for a
declarative home setup against effort and risk.

## Tier 1: new resources with plain CRUD

These look like the area and floor registries: `list`, `create`, `update` and `delete` over WS.
They let a playbook describe a home from scratch.

| # | Module(s) | API | Notes |
|---|---|---|---|
| 1 | `label`, `label_info` | `config/label_registry/*` | Same shape as floors; reuses `module_utils/registry.py` as is. Fields `icon`, `color`, `description`. |
| 2 | `zone`, `zone_info` | `zone/*` | Storage collection: id field `zone_id` on update/delete, `id` in entries. Needs a generic collection helper next to `registry.py`. Zones from YAML are not listed and can't be changed. |
| 3a | Helpers: `input_boolean`, `input_button`, `input_number`, `input_select`, `input_text`, `counter`, `helper_info` | `<domain>/*` | One typed module per type on the zone helper, with full-replace updates. |
| 3b | Helpers: `input_datetime`, `timer`, `schedule` | `<domain>/*` | Need normalizers: HA rewrites durations and times (see api-notes). |
| 4 | `person`, `tag` | `person/*`, `tag/*` | Collections. `person.user_id` links to a user (see #8). |

## Tier 2: settings on existing objects

The objects come from integrations or users; modules update them but don't create them.

| # | Module(s) | API | Notes |
|---|---|---|---|
| 5 | `entity` | `config/entity_registry/update` | Name, icon, area, labels, aliases, disabled/hidden, renaming the entity ID. Only entities with a unique ID are in the registry. |
| 6 | `device` | `config/device_registry/update` | Area, user-given name, labels, disabled. |
| 7 | `category` | `config/category_registry/*` | CRUD, but each category is scoped (`automation`, `script`, ...). |
| 8 | `user` | `config/auth/*`, `config/auth_provider/homeassistant/*` | Users plus their username/password credentials. A password can't be read back, so it is only set on create or when asked to (`update_password`). |

## Tier 3: larger documents and singletons

| # | Module(s) | API | Notes |
|---|---|---|---|
| 9 | `automation`, `script`, `scene` | REST `/api/config/{automation,script,scene}/config/{id}` | Whole-document compare. Writes `automations.yaml` etc. on the HA host and reloads. |
| 10 | `dashboard`, `dashboard_resource` | `lovelace/dashboards/*`, `lovelace/config/save`, `lovelace/resources/*` | Dashboard metadata plus content (whole-document compare). |
| 11 | Small singletons | `backup/config/update`, `analytics/preferences`, `logger/integration_log_level`, `network/configure`, `energy/save_prefs`, `homeassistant/expose_entity`, `config/{area,floor}_registry/reorder` | Each is a small partial-state module like `core_config`; the order within this item follows demand. |

## Tier 4: needs a design spike first

| # | Module(s) | API | Notes |
|---|---|---|---|
| 12 | `integration` (config entries), options | REST `/api/config/config_entries/flow`, `.../options/flow` | Flows are multi-step and differ per integration; some need OAuth or discovery. Spike: which integrations can be driven by a list of step inputs, and how to make that idempotent (match on domain + title/unique ID). |

## Not planned

Blueprints, labs, assist pipelines, application credentials (only useful with #12), and MFA
setup (interactive). Revisit on request.

## Progress

| # | Status | PR |
|---|---|---|
| 1 | done | #3 |
| 2 | done | #4 |
| 3a | done | #5 |
| 3b | done | #6 |
| 4 | done | #7 |

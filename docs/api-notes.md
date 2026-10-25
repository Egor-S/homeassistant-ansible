# HA API spike notes

Verified against `ghcr.io/home-assistant/home-assistant:2026.10.4` (fresh container
from `docker-compose.yml`, `docker compose down -v` resets it). Base URL
`http://127.0.0.1:8123`.

## Headline

- **Full onboarding is possible over REST, no UI-only steps.** Core config and
  areas are fully reachable over WS. `ha_version` is in the WS auth messages.
- **Contradictions / surprises vs docs/design.md**
  1. `integration` step REQUIRES `client_id` and `redirect_uri` (400 otherwise) and
     returns an `auth_code` that we simply discard. Not a no-body call.
  2. `area` `aliases` have **set semantics server-side**: deduped and returned in
     arbitrary (not input, not sorted) order. Matches the design ("set semantics"):
     compare as sets, never as lists.
  3. HA does **not validate** `floor_id` / `labels` on area create/update (unknown
     `floor_id` is stored as is; unknown `labels` silently produce `[]`).
     "Passed through as raw IDs" is OK, but there is no server-side error to rely on.
  4. Unknown `area_id` on `area_registry/update` gives a generic
     `unknown_error` / "Unknown error" (not `not_found`). `delete` gives `invalid_info`.
  5. HA ships **3 default areas** (Living Room, Kitchen, Bedroom) created at the `user`
     step. Tests must account for them (and the area module must match `Kitchen` etc.
     case-insensitively).
  6. `get_config.unit_system` is a **dict of units**, not the `metric`/`us_customary`
     name; infer from `unit_system.length` (`km` -> metric, `mi` -> us_customary).
  7. `config/core/update` returns `result: null` (no new config); re-read with `get_config`.
  8. `auth/long_lived_access_token` requires `lifespan` (days); no default.

## Startup behaviour (item i)

`docker compose up -d`, polling `GET /api/onboarding` every 1s: for ~6s the port
accepts nothing useful (curl http code `000`, no HTTP response; no 502 since no proxy),
then `200` with the onboarding list straight away. Docker healthcheck went healthy at
~20s. Poll for a 200 JSON from `/api/onboarding`; treat connection errors/timeouts as
"not up yet". WS and `/auth/token` also work as soon as that returns 200.

## Onboarding REST (unauthenticated GET, steps as noted)

### GET /api/onboarding (no auth)
Fresh: `200`
```json
[{"step":"user","done":false},{"step":"core_config","done":false},{"step":"analytics","done":false},{"step":"integration","done":false}]
```
After `user` step: `user.done=true`, others false. After all: all four `done:true`,
still `200` with the list - but only until the next restart. `onboarding.async_setup` skips
registering its views when every step is done at startup, so an onboarded HA answers **404**
after any restart. HTTP only starts listening once `frontend` (which depends on `onboarding`) is
set up, so a 404 from a responding HA (`/auth/providers` is 200) means fully onboarded.

### POST /api/onboarding/users (no auth)
Body (all required; voluptuous): `client_id`, `name`, `username`, `password`, `language`.
```json
{"client_id":"http://127.0.0.1:8123/","name":"Admin","username":"admin","password":"pw-12345","language":"en"}
```
-> `200 {"auth_code":"d7cf4d45fc4e45a9adec74bd6b36d17d"}`
- Missing field: `400 {"message":"Message format incorrect: required key not provided at 'language'"}`
- Repeat after done: `403 {"message":"User step already done"}`
- `client_id` is NOT validated here (`"foo"` accepted), but is bound to the code; see below.
- Creates owner + default areas (Living Room/Kitchen/Bedroom).

### POST /auth/token (form-encoded, no auth)
`grant_type=authorization_code&code=<auth_code>&client_id=<same client_id>`
-> `200`
```json
{"access_token":"eyJ...","token_type":"Bearer","refresh_token":"9657f6...","expires_in":1800,"ha_auth_provider":"homeassistant"}
```
- `client_id` must be a URL (http/https with host): `foo` -> `400 {"error":"invalid_request","error_description":"Invalid client id"}`.
  `http://127.0.0.1:8123` and `http://127.0.0.1:8123/` both fine; any URL works as long
  as the same one is used at both calls.
- Different client_id than the user step: `400 ... "Invalid code"`. Code is **single use**
  (second exchange -> `Invalid code`). The failed attempt with a wrong client_id did not
  consume the code.
- Access token lifetime 1800s; `grant_type=refresh_token` (+ `refresh_token`, `client_id`)
  gives a new access token. Not needed if we mint an LLAT immediately.
- Form-encoded, not JSON.

### POST /api/onboarding/core_config, /analytics
Need `Authorization: Bearer <access_token>` (`401 "401: Unauthorized"` without; also 401
before the user step exists). Body optional (none or `{}`), both -> `200 {}`.
Repeat: `403 {"message":"Core config step already done"}` / `"Analytics config step already done"`.
Analytics stays "off" by default (no body sent).

### POST /api/onboarding/integration
Bearer required. Body REQUIRED: `client_id` and `redirect_uri`.
`{}` -> `400 ... required key not provided at 'client_id'`; with only client_id ->
`... at 'redirect_uri'`. Valid:
```json
{"client_id":"http://127.0.0.1:8123/","redirect_uri":"http://127.0.0.1:8123/?auth_callback=1"}
```
-> `200 {"auth_code":"..."}` (discard). Repeat: `403 {"message":"Integration step already done"}`.
Steps can be done in any order after `user`; I ran core_config, analytics, integration.

Idempotency: every repeat is `403 "<X> step already done"`; so check `GET /api/onboarding`
first and only run missing steps. Once the `user` step is done a token needs the
owner's credentials (`/auth/login_flow`, see below).

## WebSocket `ws://127.0.0.1:8123/api/websocket`

1. server: `{"type":"auth_required","ha_version":"2026.10.4"}` (**version available before auth**)
2. client: `{"type":"auth","access_token":"<token>"}`
3. server: `{"type":"auth_ok","ha_version":"2026.10.4"}`; bad token:
   `{"type":"auth_invalid","message":"Invalid access token or password"}` then close.
Commands: `{"id":N,"type":"...", ...}` (ids increasing); replies
`{"id":N,"type":"result","success":true,"result":...}`.

### Long-lived token
`{"id":4,"type":"auth/long_lived_access_token","client_name":"ansible","lifespan":3650}`
-> `result` is the token string (JWT, ~exp +10y). `lifespan` (days) is required, else
`invalid_format "required key not provided at 'lifespan'. Got None"`. Works for
`GET /api/` (`200 {"message":"API running."}`) and WS auth/commands.
- **One LLAT per `client_name`** per user: a second create with the same name fails with
  `unknown_error "Unknown error"` (HA log: `ValueError: <name> already exists`).
- List: `{"type":"auth/refresh_tokens"}` -> entries `id`, `client_name`, `client_id`,
  `type` (`normal` / `long_lived_access_token`), `created_at` (ISO string), `expire_at`,
  `last_used_at`, `is_current`, ... (`created_at` e.g. `2026-10-25T15:14:05.279676+00:00`). The token value and the LLAT lifespan cannot be read back.
- Delete: `{"type":"auth/delete_refresh_token","refresh_token_id":"..."}` -> `result: {}`
  (verified). Unknown id -> `invalid_token_id` (from source). Deleting the refresh token of the open
  connection makes HA drop the connection (verified), so revoke the own session over REST instead.
Bad token on REST: `401`.

### Expiry (from `homeassistant/auth/const.py`)
| Token | Lifetime |
|---|---|
| Access token | 30 min |
| Normal refresh token (login session) | 90 days, sliding: renewed on every use |
| Long-lived token | its `lifespan`; `expire_at` is `null`, so the 90-day cleanup never removes it |

### Login flow (owner credentials)
1. `POST /auth/login_flow` `{"client_id","handler":["homeassistant",null],"redirect_uri"}` -> `flow_id`
2. `POST /auth/login_flow/<flow_id>` `{"client_id","username","password"}` ->
   `type: create_entry` with `result` = auth code; wrong password -> `type: form`,
   `errors: {"base":"invalid_auth"}` (verified); MFA enabled -> `type: form`, `step_id: mfa`
   (from source, not tested).
3. Exchange the code at `/auth/token` as above.

### POST /auth/revoke (form, no auth)
`token=<refresh_token>` -> `200`, removes the session and its access tokens (verified:
after `onboarding` and `login` the owner has no `normal` tokens left). Unknown tokens also
give `200`. `/auth/token` with `action=revoke` is deprecated.

### Errors
```json
{"id":7,"type":"result","success":false,"error":{"code":"invalid_format","message":"invalid ISO 3166 formatted country at 'country'. Got 'ZZ'"}}
```
Codes seen: `invalid_format` (schema; multiple problems joined with `\n`), `invalid_info`
(semantic: duplicate name, bad time zone, missing id on delete), `unknown_error`
(`"Unknown error"`), `unknown_command` (`"Unknown command."`).

## Core config

Read: `{"type":"get_config"}` -> object. Relevant fields (plus `components` (huge list, ignore),
`version`, `state`, `config_dir`, `config_source` (`default` -> `storage` after first update),
allowlist_* etc.):
```json
{"latitude":0,"longitude":0,"elevation":0,"radius":100,"location_name":"Home","time_zone":"UTC",
 "language":"en","country":null,"currency":"EUR","external_url":null,"internal_url":null,
 "unit_system":{"length":"km","accumulated_precipitation":"mm","area":"m²","mass":"g","pressure":"Pa","temperature":"°C","volume":"L","wind_speed":"m/s"},
 "version":"2026.10.4","state":"RUNNING"}
```
Defaults after onboarding with no body: lat/lon 0, elevation 0, UTC, Home, en, country null, currency EUR.
(`config_source` would be useful to know but is not needed.)

Write: `config/core/update`; every key optional (empty command is fine):
`latitude, longitude, elevation, unit_system, location_name, time_zone, external_url, internal_url, currency, country, language, radius`. All accepted. Success reply:
`{"id":2,"type":"result","success":true,"result":null}` (no config returned).
- Update with unchanged / partial / no values: success, no complaint.
- `unit_system`: `"metric"` or `"us_customary"`; legacy `"imperial"` also accepted (maps to us_customary).
  `"bogus"` -> `invalid_format "expected 'metric' or 'us_customary' at 'unit_system'. Got 'bogus'"`.
- `latitude: "abc"` / `999` -> `invalid_format "invalid latitude at 'latitude'. Got 999"` (same for longitude presumably).
- `elevation`: coerced to **int** (`1.5` -> 1, `"12"` -> 12). Compare with int. lat/lon keep float precision.
- `radius`: int >= 0 (`-5` -> `value must be at least 0`).
- `time_zone: "Mars/Olympus"` -> `invalid_info "Received invalid time zone Mars/Olympus"`; `null` -> `invalid_format`.
- `currency` ISO 4217, `country` ISO 3166, `language` RFC 5646 validated (`invalid_format`). **`country`/`currency` cannot be set to null** (error) - cannot be cleared via API.
- `external_url`/`internal_url`: must be a valid URL (`"not a url"`, `""` -> `invalid_format "invalid url"`), **`null` clears**. Stored/returned verbatim (no trailing slash normalisation: sent without slash, read back without).
- `location_name: ""` accepted.
- Unknown key `foo` -> `invalid_format "not a valid option at 'foo'. Got 'bar'"`.
- Changes apply immediately and are visible in `get_config`.

## Area registry (`config/area_registry/*`)

Entry shape (all `list`/`create`/`update` results):
```json
{"area_id":"living_room","name":"Living Room","aliases":[],"icon":"mdi:sofa","picture":null,
 "floor_id":null,"labels":[],"temperature_entity_id":null,"humidity_entity_id":null,
 "created_at":1792937191.807653,"modified_at":1792937191.807655}
```
(`created_at`/`modified_at` are float epoch seconds.)

- **list**: `{"type":"config/area_registry/list"}` -> array. Order: creation order.
- **create**: `name` required; optional `aliases` (list), `icon`, `picture`, `floor_id`, `labels` (list),
  `temperature_entity_id`, `humidity_entity_id`. Returns the new entry. On create, `null` for
  `aliases`/`floor_id`/`icon` is rejected (`expected str at 'icon'. Got None`), `picture: null` ok - just omit.
- **area_id** = slugified name, with unique suffix on clash: `"Master Bedroom & Bath!"` -> `master_bedroom_bath`,
  `"Ünïcode Zone"` -> `unicode_zone`, `"  Pad  "` -> `pad`. Name is stored verbatim (whitespace kept).
  Empty name `""` is accepted (area_id `""`) - guard in module.
- **Duplicate name**: normalized (casefold + strip, compared on the slug-like normalized name):
  `garage` / `" GARAGE "` vs `Garage` -> `invalid_info "The name garage (garage) is already in use"`;
  same on update to a clashing name. Name differing only in case/whitespace is a duplicate,
  consistent with design's case-insensitive match (also strip whitespace).
- **update**: `area_id` required; every other field optional (partial). Returns the full updated entry.
  Update with unchanged values or only `area_id`: success, `modified_at` unchanged (HA no-ops).
  Renaming keeps `area_id` (`Garage` -> `Carport` still `garage`).
  Clearing: `icon: null`, `picture: null`, `floor_id: null`, `temperature_entity_id: null`,
  `humidity_entity_id: null` accepted; `aliases: []`, `labels: []` for lists (`labels: null` and `name: null` rejected `invalid_format`).
  Unknown key -> `invalid_format "not a valid option at 'bogus'"`.
- **aliases**: JSON list in/out but stored as a set: input `["Zeta","alpha","Zeta","beta"]` -> `["Zeta","beta","alpha"]`;
  `["b","a"]` -> `["a","b"]`. Case-sensitive, deduped, order not reliable -> compare as sets.
- **delete**: `{"type":"config/area_registry/delete","area_id":"garage"}` -> `result: "success"`.
- **Errors**: unknown `area_id` on update -> `{"code":"unknown_error","message":"Unknown error"}`;
  on delete -> `{"code":"invalid_info","message":"Area ID doesn't exist"}`.
  `temperature_entity_id`/`humidity_entity_id` pointing to a nonexistent entity ->
  `invalid_info "Entity sensor.nope does not exist"` (validated!). `floor_id: "nofloor"` is **accepted and stored**
  (not validated); `labels: ["nolabel"]` is silently dropped to `[]`. `aliases: "str"` -> `invalid_format "expected list"`.
  `icon: "notmdi"` accepted (no format check).
- Floors: see the Floor registry section.

### Default areas (item j)
Created at the `user` onboarding step (before `core_config`): **Living Room** (`living_room`, `mdi:sofa`),
**Kitchen** (`kitchen`, `mdi:stove`), **Bedroom** (`bedroom`, `mdi:bed`); no aliases/floor/labels.
Integration tests that create e.g. "Kitchen" will see "already exists"; use unique names
(and don't assert an empty list).

## Floor registry (`config/floor_registry/*`)

Entry: `{"floor_id","name","aliases":[],"icon":null,"level":null,"created_at","modified_at"}`
(`level` is an int or null; timestamps are float epoch seconds). Empty by default (no default floors).
Same shape of commands as areas: `list`, `create` (`name` required; optional `aliases`, `icon`, `level`),
`update` (`floor_id` required, rest optional), `delete` (`floor_id`).

- `floor_id` = slugified name (`ansible_probe`); renaming keeps it.
- `level`: `0` and negative values accepted and stored; `level: null` is accepted on **create and update** and
  **clears** it; `level: "x"` -> `invalid_format "expected int or None at 'level'. Got 'x'"`.
  So `0` must never be treated as "unset" (falsy) in the module.
- `aliases`: set semantics as for areas (`["b","a","b"]` -> `["b","a"]`, order arbitrary).
- `icon: null` clears on update; `name: null` -> `invalid_format`.
- Duplicate name (casefold + strip, slug compare), also on update:
  `invalid_info "The name   ANSIBLE_PROBE  (ansible_probe) is already in use"`.
- Unknown `floor_id`: update -> `unknown_error "Unknown error"`; delete -> `invalid_info "Floor ID doesn't exist"`.
- Unchanged update is a no-op (`modified_at` unchanged).

## Label registry (`config/label_registry/*`)

Entry: `{"label_id","name","icon","color","description","created_at","modified_at"}`. Empty by default.
Same commands as floors (`list`, `create`, `update`, `delete` by `label_id`); no aliases.

- `color`: `#RRGGBB` or a theme color (`primary`, `accent`, `disabled`, `red`, `light-blue`, `blue-grey`, ...);
  anything else -> `invalid_format "Color should be in the format #RRGGBB"`. Stored verbatim.
- `null` clears `icon`, `color` and `description`; `description: ""` is stored as `""`.
- Duplicate name (casefold + strip) -> `invalid_info "... is already in use"`; unknown `label_id`: update
  -> `unknown_error`, delete -> `invalid_info "Label ID doesn't exist"`. Delete returns `null`.
- Deleting a label removes it from the areas that had it.

## Zones (`zone/*`, storage collection)

Entry: `{"id","name","latitude","longitude","radius","passive"}` plus `icon` only when set. Empty by default;
the home zone and YAML zones are not in `zone/list`.

- `create`: `name`, `latitude`, `longitude` required; `radius` defaults to `100.0`, `passive` to `false`.
  Returned values are floats (`radius: 250` -> `250.0`).
- `update` and `delete` take `zone_id` (the entry's `id`); `update` merges the given fields into the entry.
- **Names are not unique**: a second `Probe` gets `id` `probe_2`.
- `icon: null` -> `invalid_format "Icons should be specified in the form \"prefix:name\""`: an icon can't be
  removed once set (no field can be).
- Unknown `zone_id`: update and delete -> `not_found "Unable to find zone_id <id>"`. Delete returns `null`.
- Invalid latitude -> `invalid_format "invalid latitude at 'latitude'"`.

## HTTP config (`http/config*`, admin only)

Verified in the 2026.10.4 source (`components/http/{config,websocket_api}.py`) and live.
The `http:` YAML block is imported into storage once (`yaml_migration_done`), ignored afterwards,
with repair issues `deprecated_yaml` / `yaml_still_present_after_migration`
(`breaks_in_ha_version="2027.2.0"`). UI: Settings > System > Network.

- **get** `{"type":"http/config"}` -> `{"stable","pending","revert_at","active_config_type","default"}`.
  Default stable on a fresh container:
  `{"server_port":8123,"cors_allowed_origins":["https://cast.home-assistant.io"],"login_attempts_threshold":-1,
  "ip_ban_enabled":true,"ssl_profile":"modern","use_x_frame_options":true,"created_at":...,"error":null,"error_message":null}`.
  Keys without a default (`server_host`, `ssl_certificate`, `ssl_key`, `ssl_peer_certificate`,
  `use_x_forwarded_for`, `trusted_proxies`) are **absent** when unset.
  `active_config_type`: `stable` / `pending` / `default` / `default_legacy_port`.
- **configure** `{"type":"http/config/configure","config":{...}|null}` -> `{"restart": bool}`.
  The config is a **full replacement**: omitted keys fall back to schema defaults, so send stable
  (minus `created_at`/`error`/`error_message`) plus changes. `null` clears pending.
  - Stored as **pending**; HA restarts itself whenever the pending slot changes (`restart: true`,
    the WS connection drops). Same config as stable or as an error-free pending -> `restart: false`.
  - `trusted_proxies` normalised via `ip_network` (`172.16.0.1` -> `172.16.0.1/32`; `10.0.0.1/8` is
    invalid). `use_x_forwarded_for: true` without proxies -> `invalid_format`.
  - A new `server_port` is bind-checked first (`bind_failed`); SSL paths must exist on the HA host.
  - Only while `RUNNING`, else `not_running`.
- After the restart HA runs on pending (`active_config_type: pending`) and schedules an auto-revert
  5 minutes later (`revert_at`). Back up in ~5 s on the test container.
- **promote** `{"type":"http/config/promote"}` -> pending becomes stable, revert cancelled.
  Nothing pending -> `not_allowed "No pending HTTP config to promote"`.
- A trial that is not promoted gets `error: not_promoted` and HA restarts on stable; one that fails
  to bind gets `error: apply_failed` + `error_message` and HA continues on stable. A pending config
  with an error is kept for inspection but never applied again.
- Recovery mode always uses stable.

## Misc
- `refresh_token` grant with wrong `client_id` -> `400 {"error":"invalid_request"}`.
- Unauthenticated `POST /auth/token` before onboarding works the same; just returns 400 for bad code.

## Findings while implementing `onboarding`

- The `integration` onboarding step **rejects a long-lived token** (`403 Credentials
  for user not available`); use the short-lived access token from the `/auth/token`
  code exchange for the remaining steps.
- If a run is interrupted after the `user` step, the remaining steps are completed by
  logging in as the owner via `/auth/login_flow` (username/password).
- `GET /api/config` with the session's access token yields the HA version.

#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2026, Egor Sklyarov
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

DOCUMENTATION = r"""
module: login
short_description: Log in to Home Assistant and get a short-lived token for the other modules
version_added: 0.1.0
author: Egor Sklyarov (@Egor-S)
description:
  - Logs in with a username and password and returns a long-lived access token with a short
    lifespan (O(token_lifespan)), to pass as O(egors.homeassistant.core_config#module:token) to the other modules.
  - The token is only returned, never written anywhere. Keep the credentials in Ansible Vault and log in on every run.
  - Home Assistant allows one long-lived token per client name, so every token gets a unique name made of
    O(token_client_name), the creation time and a random suffix, for example C(Ansible login 2026-10-25T15:12:31Z 3f9a1c).
  - Tokens named like that which are older than O(token_lifespan) are deleted, so repeated runs do not
    accumulate tokens. Younger ones are kept, so parallel runs do not break each other.
  - The login session itself is revoked before the module returns.
  - The token is a temporary credential, not managed configuration, so the module never reports a change.
  - This module is not part of the action group C(egors.homeassistant.all) because it does not take a O(ignore:token).
extends_documentation_fragment:
  - egors.homeassistant.connection.endpoint
options:
  username:
    description:
      - Username of a Home Assistant user, usually the owner created by M(egors.homeassistant.onboarding).
      - Only the C(homeassistant) auth provider without multi-factor authentication is supported.
    type: str
    required: true
  password:
    description:
      - Password of the user.
    type: str
    required: true
  client_id:
    description:
      - OAuth client ID used for the login. Must be an C(http) or C(https) URL.
      - Defaults to O(url) with a trailing slash.
    type: str
  token_client_name:
    description:
      - Prefix of the client name of the created token, as shown in the Home Assistant user profile.
      - Only tokens whose name is this prefix followed by a creation time and a random suffix are ever deleted.
    type: str
    default: Ansible login
  token_lifespan:
    description:
      - Lifespan of the created token in days. Must be at least V(1).
    type: int
    default: 1
requirements:
  - websocket-client
attributes:
  check_mode:
    support: full
    description: Logs in and creates the token in check mode too, so the following modules can check their changes.
  diff_mode:
    support: none
    description: Nothing is managed, so there is nothing to diff.
  platform:
    platforms: all
    support: full
    description: The module talks to Home Assistant over the network from the controller.
notes:
  - The returned token is sensitive. Set C(no_log) on the task.
  - Fails on an instance that is not onboarded yet; run M(egors.homeassistant.onboarding) first.
seealso:
  - module: egors.homeassistant.onboarding
"""

EXAMPLES = r"""
- name: Log in
  egors.homeassistant.login:
    url: http://homeassistant.local:8123
    username: admin
    password: "{{ vault_ha_admin_password }}"
  delegate_to: localhost
  register: ha_login
  no_log: true  # the result contains the token

- name: Use the token with the other modules
  module_defaults:
    group/egors.homeassistant.all:
      url: http://homeassistant.local:8123
      token: "{{ ha_login.token }}"
  delegate_to: localhost
  block:
    - name: Core configuration
      egors.homeassistant.core_config:
        location_name: Home
"""

RETURN = r"""
token:
  description:
    - Access token valid for O(token_lifespan) days. This value is sensitive.
  returned: success
  type: str
ha_version:
  description: Home Assistant version.
  returned: success
  type: str
  sample: 2026.10.4
token_name:
  description: Client name of the created token.
  returned: success
  type: str
  sample: Ansible login 2026-10-25T15:12:31Z 3f9a1c
deleted_tokens:
  description: Number of expired tokens created by earlier runs that were deleted.
  returned: success
  type: int
  sample: 1
"""

import re
import secrets
from datetime import datetime, timedelta, timezone

from ansible.module_utils.basic import AnsibleModule, missing_required_lib
from ansible.module_utils.common.text.converters import to_native

from ansible_collections.egors.homeassistant.plugins.module_utils.api import (
    HAS_WEBSOCKET,
    MIN_HA_VERSION,
    WEBSOCKET_IMPORT_ERROR,
    HomeAssistantError,
    WebSocketClient,
    derive_client_id,
    endpoint_argument_spec,
    exchange_code,
    is_valid_client_id,
    is_version_supported,
    login_flow,
    rest_request,
    revoke_token,
)

LONG_LIVED = "long_lived_access_token"
NAME_TIME_FORMAT = "%Y-%m-%dT%H:%M:%SZ"
NAME_SUFFIX = r" \d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ [0-9a-f]{6}"


def parse_timestamp(value):
    """Parse a ``created_at`` value (ISO string or epoch seconds) into an aware datetime; ``None`` if unknown."""
    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(value, timezone.utc)
    try:
        parsed = datetime.fromisoformat(str(value))
    except ValueError:
        return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def token_name(prefix, now, suffix=None):
    """Unique client name: HA allows one long-lived token per client name."""
    return "%s %s %s" % (prefix, now.strftime(NAME_TIME_FORMAT), suffix or secrets.token_hex(3))


def stale_token_ids(tokens, prefix, lifespan, now):
    """IDs of long-lived tokens named by ``token_name(prefix, ...)`` created more than ``lifespan`` days ago."""
    pattern = re.compile(re.escape(prefix) + NAME_SUFFIX + r"\Z")
    cutoff = now - timedelta(days=lifespan)
    stale = []
    for token in tokens:
        if token.get("type") != LONG_LIVED or not pattern.match(token.get("client_name") or ""):
            continue
        created_at = parse_timestamp(token.get("created_at"))
        if created_at is not None and created_at <= cutoff:
            stale.append(token["id"])
    return stale


class Login:
    def __init__(self, module):
        self.module = module
        self.params = module.params
        self.url = self.params["url"]
        self.client_id = self.params["client_id"] or derive_client_id(self.url)
        self.connection = dict(timeout=self.params["timeout"], validate_certs=self.params["validate_certs"])

    def check_onboarded(self):
        try:
            status, payload = rest_request(self.url, "/api/onboarding", **self.connection)
        except HomeAssistantError as exc:
            self.module.fail_json(msg=to_native(exc))
        if status == 200 and isinstance(payload, list):
            if any(item.get("step") == "user" and not item.get("done") for item in payload if isinstance(item, dict)):
                self.module.fail_json(msg="Home Assistant at %s is not onboarded yet; run "
                                          "egors.homeassistant.onboarding first." % self.url)

    def create_token(self, access_token):
        """Create the new token and delete the expired ones; return the result fields."""
        now = datetime.now(timezone.utc)
        name = token_name(self.params["token_client_name"], now)
        client = WebSocketClient(self.url, access_token, **self.connection)
        with client:
            # The id of the new token is not returned, so pick the stale ones before creating it.
            stale = stale_token_ids(client.call("auth/refresh_tokens"), self.params["token_client_name"],
                                    self.params["token_lifespan"], now)
            token = client.call("auth/long_lived_access_token", client_name=name,
                                lifespan=self.params["token_lifespan"])
            for token_id in stale:
                client.call("auth/delete_refresh_token", refresh_token_id=token_id)
            return dict(token=token, token_name=name, deleted_tokens=len(stale), ha_version=client.ha_version)

    def run(self):
        self.check_onboarded()
        try:
            code = login_flow(self.url, self.params["username"], self.params["password"], self.client_id,
                              **self.connection)
            session = exchange_code(self.url, code, self.client_id, **self.connection)
        except HomeAssistantError as exc:
            self.module.fail_json(msg=to_native(exc))
        try:
            result = self.create_token(session["access_token"])
        except HomeAssistantError as exc:
            self.module.fail_json(msg="Creating the token failed: %s" % to_native(exc))
        finally:
            # Revoked over REST after the WebSocket is closed: deleting the token of an open
            # connection makes HA drop it.
            try:
                revoke_token(self.url, session["refresh_token"], **self.connection)
            except HomeAssistantError as exc:
                self.module.warn(to_native(exc))

        ha_version = result["ha_version"]
        if ha_version and not is_version_supported(ha_version):
            self.module.warn("Home Assistant %s is older than the oldest supported release %s; "
                             "the module may not work as expected." % (ha_version, MIN_HA_VERSION))
        self.module.exit_json(changed=False, **result)


def main():
    argument_spec = endpoint_argument_spec()
    argument_spec.update(
        username=dict(type="str", required=True),
        password=dict(type="str", required=True, no_log=True),
        client_id=dict(type="str"),
        token_client_name=dict(type="str", default="Ansible login", no_log=False),
        token_lifespan=dict(type="int", default=1, no_log=False),
    )
    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=True)
    if not HAS_WEBSOCKET:
        module.fail_json(msg=missing_required_lib("websocket-client"), exception=WEBSOCKET_IMPORT_ERROR)
    client_id = module.params["client_id"] or derive_client_id(module.params["url"])
    if not is_valid_client_id(client_id):
        module.fail_json(msg="client_id must be an http(s) URL, got %r" % client_id)
    if module.params["token_lifespan"] < 1:
        module.fail_json(msg="token_lifespan must be at least 1 day, got %s" % module.params["token_lifespan"])
    Login(module).run()


if __name__ == "__main__":
    main()

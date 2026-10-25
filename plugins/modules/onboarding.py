#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2026, Egor Sklyarov
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

DOCUMENTATION = r"""
module: onboarding
short_description: Onboard a fresh Home Assistant instance and create a long-lived access token
version_added: 0.1.0
author: Egor Sklyarov (@Egor-S)
description:
  - Waits until Home Assistant answers, then completes all pending onboarding steps
    (V(user), V(core_config), V(analytics), V(integration)) with minimal defaults.
  - The V(user) step creates the owner account. A long-lived access token is then created for it.
  - Analytics stay disabled and core configuration keeps the Home Assistant defaults;
    use M(egors.homeassistant.core_config) to manage the core configuration.
  - Steps that are already done are skipped, so the module is idempotent.
  - This module is not part of the action group C(egors.homeassistant.all) because it does not take a O(ignore:token).
extends_documentation_fragment:
  - egors.homeassistant.connection.endpoint
options:
  name:
    description:
      - Display name of the owner user.
    type: str
    required: true
  username:
    description:
      - Username of the owner user.
    type: str
    required: true
  password:
    description:
      - Password of the owner user.
    type: str
    required: true
  language:
    description:
      - Language of the owner user.
    type: str
    default: en
  client_id:
    description:
      - OAuth client ID used for the onboarding token exchange. Must be an C(http) or C(https) URL.
      - Defaults to O(url) with a trailing slash.
    type: str
  token_path:
    description:
      - Path on the controller where the long-lived access token is stored.
      - When the token is created it is written to this file with mode C(0600). The parent directory must exist.
      - When the owner user already exists, the token is read back from this file, checked against
        Home Assistant, and returned. An invalid token in this file makes the module fail.
    type: path
  token_client_name:
    description:
      - Client name of the created long-lived access token, as shown in the Home Assistant user profile.
    type: str
    default: Ansible
  token_lifespan:
    description:
      - Lifespan of the created long-lived access token in days.
    type: int
    default: 3650
  wait_timeout:
    description:
      - How long to wait, in seconds, for Home Assistant to start answering requests.
    type: int
    default: 300
requirements:
  - websocket-client
attributes:
  check_mode:
    support: full
    description: Reports pending steps as changes without performing them.
  diff_mode:
    support: full
    description: Shows the onboarding step status before and after the run.
  platform:
    platforms: all
    support: full
    description: The module talks to Home Assistant over the network from the controller.
notes:
  - If the owner user already exists but other steps are pending (for example after an interrupted run),
    the module logs in with O(username) and O(password) to finish them.
  - The token value can not be read from Home Assistant. It is only returned when it is created
    by this run or when it can be read from O(token_path).
seealso:
  - module: egors.homeassistant.core_config
"""

EXAMPLES = r"""
- name: Onboard Home Assistant and keep the token on the controller
  egors.homeassistant.onboarding:
    url: http://homeassistant.local:8123
    name: Admin
    username: admin
    password: "{{ vault_ha_admin_password }}"
    token_path: "{{ playbook_dir }}/.ha.token"
  delegate_to: localhost
  register: ha_onboarding

- name: Use the token with the other modules
  egors.homeassistant.core_config:
    url: http://homeassistant.local:8123
    token: "{{ ha_onboarding.token }}"
    location_name: Home
  delegate_to: localhost
"""

RETURN = r"""
token:
  description:
    - Long-lived access token of the owner user. This value is sensitive.
    - Only returned when the token was created by this run or read from O(token_path).
  returned: when available
  type: str
steps:
  description: Onboarding steps and whether they are done after the run (or would be, in check mode).
  returned: always
  type: dict
  sample: {"user": true, "core_config": true, "analytics": true, "integration": true}
ha_version:
  description: Home Assistant version.
  returned: when a token was available
  type: str
  sample: 2026.10.4
"""

import os
import tempfile
import time

from ansible.module_utils.basic import AnsibleModule, missing_required_lib
from ansible.module_utils.common.text.converters import to_native
from ansible.module_utils.six.moves.urllib.parse import urlparse

from ansible_collections.egors.homeassistant.plugins.module_utils.api import (
    HAS_WEBSOCKET,
    MIN_HA_VERSION,
    WEBSOCKET_IMPORT_ERROR,
    HomeAssistantError,
    WebSocketClient,
    endpoint_argument_spec,
    is_version_supported,
    rest_request,
)

STEPS = ("user", "core_config", "analytics", "integration")
POLL_INTERVAL = 2


def derive_client_id(url):
    """Default OAuth client ID: the base URL with exactly one trailing slash."""
    return url.rstrip("/") + "/"


def is_valid_client_id(client_id):
    parsed = urlparse(client_id)
    return parsed.scheme in ("http", "https") and bool(parsed.netloc)


def redirect_uri(client_id):
    return client_id.rstrip("/") + "/?auth_callback=1"


def parse_steps(payload):
    """Convert the ``GET /api/onboarding`` list into ``{step: done}``; ``None`` if malformed."""
    if not isinstance(payload, list):
        return None
    steps = {}
    for item in payload:
        if not isinstance(item, dict) or "step" not in item:
            return None
        steps[item["step"]] = bool(item.get("done"))
    return steps


def pending_steps(steps):
    """Steps not done yet, in the order they must run (known steps first, then unknown ones)."""
    ordered = [step for step in STEPS if step in steps] + sorted(step for step in steps if step not in STEPS)
    return [step for step in ordered if not steps[step]]


class Onboarding:
    def __init__(self, module):
        self.module = module
        self.params = module.params
        self.url = self.params["url"]
        self.client_id = self.params["client_id"] or derive_client_id(self.url)
        self.ha_version = None

    def request(self, path, **kwargs):
        kwargs.setdefault("timeout", self.params["timeout"])
        kwargs.setdefault("validate_certs", self.params["validate_certs"])
        try:
            return rest_request(self.url, path, **kwargs)
        except HomeAssistantError as exc:
            self.module.fail_json(msg=to_native(exc))

    def fetch_steps(self, wait_timeout):
        """Poll ``GET /api/onboarding`` until HA answers with the step list."""
        deadline = time.time() + wait_timeout
        last_error = None
        while True:
            try:
                status, payload = rest_request(self.url, "/api/onboarding", timeout=self.params["timeout"],
                                               validate_certs=self.params["validate_certs"])
            except HomeAssistantError as exc:
                last_error = to_native(exc)
            else:
                steps = parse_steps(payload) if status == 200 else None
                if steps is not None:
                    return steps
                last_error = "GET /api/onboarding returned HTTP %s: %r" % (status, payload)
                if status < 500 and status != 200:
                    # A 4xx will not go away by waiting (e.g. wrong URL or onboarding disabled).
                    self.module.fail_json(msg=last_error)
            if time.time() >= deadline:
                self.module.fail_json(msg="Home Assistant at %s did not become ready within %s seconds: %s"
                                      % (self.url, wait_timeout, last_error))
            time.sleep(POLL_INTERVAL)

    def check_ok(self, status, payload, what):
        if status != 200:
            message = payload.get("message", payload) if isinstance(payload, dict) else payload
            self.module.fail_json(msg="%s failed with HTTP %s: %s" % (what, status, message))
        return payload

    def create_user(self):
        data = dict(client_id=self.client_id, name=self.params["name"], username=self.params["username"],
                    password=self.params["password"], language=self.params["language"])
        status, payload = self.request("/api/onboarding/users", method="POST", data=data)
        payload = self.check_ok(status, payload, "Onboarding step user")
        return self.exchange_code(payload["auth_code"])

    def exchange_code(self, code):
        status, payload = self.request("/auth/token", method="POST", form=True, data=dict(
            grant_type="authorization_code", code=code, client_id=self.client_id))
        payload = self.check_ok(status, payload, "Token exchange")
        return payload["access_token"]

    def login(self):
        """Log the owner in with username and password; return a short-lived access token."""
        status, payload = self.request("/auth/login_flow", method="POST", data=dict(
            client_id=self.client_id, handler=["homeassistant", None], redirect_uri=redirect_uri(self.client_id)))
        payload = self.check_ok(status, payload, "Starting the login flow")
        status, payload = self.request("/auth/login_flow/%s" % payload["flow_id"], method="POST", data=dict(
            client_id=self.client_id, username=self.params["username"], password=self.params["password"]))
        payload = self.check_ok(status, payload, "Login")
        if payload.get("type") != "create_entry":
            self.module.fail_json(msg="Login as %s failed: %s" % (self.params["username"], payload.get("errors") or payload))
        return self.exchange_code(payload["result"])

    def create_long_lived_token(self, access_token):
        client = WebSocketClient(self.url, access_token, timeout=self.params["timeout"],
                                 validate_certs=self.params["validate_certs"])
        try:
            with client:
                self.ha_version = client.ha_version
                return client.call("auth/long_lived_access_token", client_name=self.params["token_client_name"],
                                   lifespan=self.params["token_lifespan"])
        except HomeAssistantError as exc:
            self.module.fail_json(msg="Creating the long-lived access token failed: %s" % to_native(exc))

    def run_step(self, step, token):
        data = {}
        if step == "integration":
            data = dict(client_id=self.client_id, redirect_uri=redirect_uri(self.client_id))
        status, payload = self.request("/api/onboarding/%s" % step, method="POST", data=data, token=token)
        self.check_ok(status, payload, "Onboarding step %s" % step)

    def read_token(self):
        """Read and validate the token from token_path; ``None`` if there is no file."""
        path = self.params["token_path"]
        if not path or not os.path.exists(path):
            return None
        try:
            with open(path) as handle:
                token = handle.read().strip()
        except (IOError, OSError) as exc:
            self.module.fail_json(msg="Cannot read token_path %s: %s" % (path, to_native(exc)))
        status, payload = self.request("/api/config", token=token)
        if status == 401:
            self.module.fail_json(msg="The token in token_path %s is not accepted by Home Assistant (HTTP 401). "
                                      "Remove the file or replace it with a valid token." % path)
        payload = self.check_ok(status, payload, "Validating the token from token_path")
        if isinstance(payload, dict):
            self.ha_version = payload.get("version")
        return token

    def write_token(self, token):
        path = self.params["token_path"]
        directory = os.path.dirname(os.path.abspath(path))
        if not os.path.isdir(directory):
            self.module.fail_json(msg="Parent directory of token_path %s does not exist" % path)
        fd, tmp_path = tempfile.mkstemp(dir=directory, prefix=".%s." % os.path.basename(path))
        try:
            os.fchmod(fd, 0o600)
            with os.fdopen(fd, "w") as handle:
                handle.write(token + "\n")
            os.replace(tmp_path, path)
        except (IOError, OSError) as exc:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
            self.module.fail_json(msg="Cannot write token_path %s: %s" % (path, to_native(exc)))

    def run(self):
        before = self.fetch_steps(self.params["wait_timeout"])
        pending = pending_steps(before)
        after = dict((step, True) for step in before)
        result = dict(changed=bool(pending), steps=after)
        if self.module._diff:
            result["diff"] = dict(before=dict(steps=before), after=dict(steps=after))

        token = None
        if before.get("user"):
            token = self.read_token()

        if pending and not self.module.check_mode:
            # The remaining steps need a regular access token: the integration step is rejected
            # for a long-lived access token ("Credentials for user not available").
            if "user" in pending:
                access_token = self.create_user()
                token = self.create_long_lived_token(access_token)
                if self.params["token_path"]:
                    self.write_token(token)
            else:
                # Resuming an interrupted run: the owner exists, log in with its credentials.
                access_token = self.login()
            for step in pending:
                if step != "user":
                    self.run_step(step, access_token)

        if token is not None:
            result["token"] = token
        if self.ha_version:
            result["ha_version"] = self.ha_version
            if not is_version_supported(self.ha_version):
                self.module.warn("Home Assistant %s is older than the oldest supported release %s; "
                                 "the module may not work as expected." % (self.ha_version, MIN_HA_VERSION))
        self.module.exit_json(**result)


def main():
    argument_spec = endpoint_argument_spec()
    argument_spec.update(
        name=dict(type="str", required=True),
        username=dict(type="str", required=True),
        password=dict(type="str", required=True, no_log=True),
        language=dict(type="str", default="en"),
        client_id=dict(type="str"),
        token_path=dict(type="path", no_log=False),
        token_client_name=dict(type="str", default="Ansible", no_log=False),
        token_lifespan=dict(type="int", default=3650, no_log=False),
        wait_timeout=dict(type="int", default=300),
    )
    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=True)
    if not HAS_WEBSOCKET:
        module.fail_json(msg=missing_required_lib("websocket-client"), exception=WEBSOCKET_IMPORT_ERROR)
    client_id = module.params["client_id"] or derive_client_id(module.params["url"])
    if not is_valid_client_id(client_id):
        module.fail_json(msg="client_id must be an http(s) URL, got %r" % client_id)
    Onboarding(module).run()


if __name__ == "__main__":
    main()

#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2026, Egor Sklyarov
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

DOCUMENTATION = r"""
module: onboarding
short_description: Onboard a fresh Home Assistant instance
version_added: 0.1.0
author: Egor Sklyarov (@Egor-S)
description:
  - Waits until Home Assistant answers, then completes all pending onboarding steps
    (V(user), V(core_config), V(analytics), V(integration)) with minimal defaults.
  - The V(user) step creates the owner account. Use M(egors.homeassistant.login) to get a token for it.
  - Analytics stay disabled and core configuration keeps the Home Assistant defaults;
    use M(egors.homeassistant.core_config) to manage the core configuration.
  - Steps that are already done are skipped, so the module is idempotent.
  - The module does not create or return any token. The login session it uses is revoked at the end of the run.
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
  wait_timeout:
    description:
      - How long to wait, in seconds, for Home Assistant to start answering requests.
    type: int
    default: 300
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
seealso:
  - module: egors.homeassistant.login
  - module: egors.homeassistant.core_config
"""

EXAMPLES = r"""
- name: Onboard Home Assistant
  egors.homeassistant.onboarding:
    url: http://homeassistant.local:8123
    name: Admin
    username: admin
    password: "{{ vault_ha_admin_password }}"
  delegate_to: localhost

- name: Log in to get a token for the other modules
  egors.homeassistant.login:
    url: http://homeassistant.local:8123
    username: admin
    password: "{{ vault_ha_admin_password }}"
  delegate_to: localhost
  register: ha_login
  no_log: true
"""

RETURN = r"""
steps:
  description: Onboarding steps and whether they are done after the run (or would be, in check mode).
  returned: always
  type: dict
  sample: {"user": true, "core_config": true, "analytics": true, "integration": true}
ha_version:
  description: Home Assistant version.
  returned: when onboarding steps were run
  type: str
  sample: 2026.10.4
"""

import time

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.common.text.converters import to_native

from ansible_collections.egors.homeassistant.plugins.module_utils.api import (
    MIN_HA_VERSION,
    HomeAssistantError,
    derive_client_id,
    endpoint_argument_spec,
    exchange_code,
    is_valid_client_id,
    is_version_supported,
    login_flow,
    redirect_uri,
    rest_request,
    revoke_token,
)

STEPS = ("user", "core_config", "analytics", "integration")
POLL_INTERVAL = 2


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
        self.connection = dict(timeout=self.params["timeout"], validate_certs=self.params["validate_certs"])
        self.ha_version = None

    def request(self, path, **kwargs):
        kwargs.update(self.connection)
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
                status, payload = rest_request(self.url, "/api/onboarding", **self.connection)
            except HomeAssistantError as exc:
                last_error = to_native(exc)
            else:
                steps = parse_steps(payload) if status == 200 else None
                if steps is not None:
                    return steps
                if status == 404 and self.is_home_assistant():
                    # HA only registers the onboarding views while onboarding is unfinished at startup, and only
                    # serves HTTP once onboarding is set up: after a restart, 404 means fully onboarded.
                    return dict((step, True) for step in STEPS)
                last_error = "GET /api/onboarding returned HTTP %s: %r" % (status, payload)
                if status < 500 and status != 200:
                    # A 4xx will not go away by waiting (e.g. wrong URL or onboarding disabled).
                    self.module.fail_json(msg=last_error)
            if time.time() >= deadline:
                self.module.fail_json(msg="Home Assistant at %s did not become ready within %s seconds: %s"
                                      % (self.url, wait_timeout, last_error))
            time.sleep(POLL_INTERVAL)

    def is_home_assistant(self):
        """Whether ``url`` is a Home Assistant (auth providers answer), to tell onboarded from a wrong URL."""
        try:
            status, payload = rest_request(self.url, "/auth/providers", **self.connection)
        except HomeAssistantError:
            return False
        return status == 200 and isinstance(payload, (dict, list))

    def check_ok(self, status, payload, what):
        if status != 200:
            message = payload.get("message", payload) if isinstance(payload, dict) else payload
            self.module.fail_json(msg="%s failed with HTTP %s: %s" % (what, status, message))
        return payload

    def start_session(self, create_user):
        """Create the owner (or log in as it); return the ``/auth/token`` payload."""
        try:
            if create_user:
                data = dict(client_id=self.client_id, name=self.params["name"], username=self.params["username"],
                            password=self.params["password"], language=self.params["language"])
                status, payload = self.request("/api/onboarding/users", method="POST", data=data)
                code = self.check_ok(status, payload, "Onboarding step user")["auth_code"]
            else:
                code = login_flow(self.url, self.params["username"], self.params["password"], self.client_id,
                                  **self.connection)
            return exchange_code(self.url, code, self.client_id, **self.connection)
        except HomeAssistantError as exc:
            self.module.fail_json(msg=to_native(exc))

    def run_step(self, step, token):
        data = {}
        if step == "integration":
            data = dict(client_id=self.client_id, redirect_uri=redirect_uri(self.client_id))
        status, payload = self.request("/api/onboarding/%s" % step, method="POST", data=data, token=token)
        self.check_ok(status, payload, "Onboarding step %s" % step)

    def run_steps(self, pending):
        # The steps need a regular access token: the integration step is rejected for a
        # long-lived access token ("Credentials for user not available").
        session = self.start_session("user" in pending)
        try:
            for step in pending:
                if step != "user":
                    self.run_step(step, session["access_token"])
            status, payload = self.request("/api/config", token=session["access_token"])
            if status == 200 and isinstance(payload, dict):
                self.ha_version = payload.get("version")
        finally:
            # Revoke even when a step failed (fail_json raises SystemExit) so no session is left behind.
            try:
                revoke_token(self.url, session["refresh_token"], **self.connection)
            except HomeAssistantError as exc:
                self.module.warn(to_native(exc))

    def run(self):
        before = self.fetch_steps(self.params["wait_timeout"])
        pending = pending_steps(before)
        after = dict((step, True) for step in before)
        result = dict(changed=bool(pending), steps=after)
        if self.module._diff:
            result["diff"] = dict(before=dict(steps=before), after=dict(steps=after))

        if pending and not self.module.check_mode:
            self.run_steps(pending)

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
        wait_timeout=dict(type="int", default=300),
    )
    module = AnsibleModule(argument_spec=argument_spec, supports_check_mode=True)
    client_id = module.params["client_id"] or derive_client_id(module.params["url"])
    if not is_valid_client_id(client_id):
        module.fail_json(msg="client_id must be an http(s) URL, got %r" % client_id)
    Onboarding(module).run()


if __name__ == "__main__":
    main()

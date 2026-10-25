#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2026, Egor Sklyarov
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

DOCUMENTATION = r"""
module: http_config
short_description: Manage the Home Assistant HTTP server configuration
version_added: 0.1.0
author: Egor Sklyarov (@Egor-S)
description:
  - Reads and updates the configuration of the HTTP server of Home Assistant (port, SSL, reverse proxy, IP bans, CORS),
    the settings formerly in the C(http:) block of C(configuration.yaml).
  - Only the options that are provided are compared and updated, all other settings are left untouched.
    Run the module without options to just read the current configuration.
  - Applying a change restarts Home Assistant. The new configuration starts as a trial; the module waits until
    Home Assistant is running again and then confirms (promotes) it. Home Assistant reverts a trial configuration
    that is not confirmed within 5 minutes, so a change that makes it unreachable undoes itself.
extends_documentation_fragment:
  - egors.homeassistant.connection
options:
  server_host:
    description:
      - Addresses the server binds to. An empty list binds to all interfaces (the default).
    type: list
    elements: str
  server_port:
    description:
      - Port the server listens on.
      - Set O(reconnect_url) when the new port makes O(url) unreachable.
    type: int
  ssl_certificate:
    description:
      - Path to the TLS certificate file on the Home Assistant host. An empty string disables TLS.
    type: str
  ssl_key:
    description:
      - Path to the TLS private key file on the Home Assistant host. An empty string unsets it.
    type: str
  ssl_peer_certificate:
    description:
      - Path to a client CA certificate file on the Home Assistant host; clients must present a certificate signed
        by it. An empty string unsets it.
    type: str
  ssl_profile:
    description:
      - Mozilla TLS profile.
    type: str
    choices: [intermediate, modern]
  cors_allowed_origins:
    description:
      - Origins allowed to make cross-origin requests, compared as a set.
    type: list
    elements: str
  use_x_forwarded_for:
    description:
      - Trust the C(X-Forwarded-For) header from O(trusted_proxies), needed behind a reverse proxy.
      - Requires at least one trusted proxy.
    type: bool
  trusted_proxies:
    description:
      - IP addresses or networks of the reverse proxies, for example V(172.30.33.0/24), compared as a set.
        A plain address is stored as a single-host network (V(10.0.0.1/32)).
      - An empty list removes all proxies.
    type: list
    elements: str
  login_attempts_threshold:
    description:
      - Failed login attempts after which the client IP is banned. V(-1) disables banning.
    type: int
  ip_ban_enabled:
    description:
      - Whether IP banning is enabled.
    type: bool
  use_x_frame_options:
    description:
      - Whether the C(X-Frame-Options) header is sent, which stops other sites from embedding the frontend.
    type: bool
  reconnect_url:
    description:
      - Base URL of Home Assistant after the restart, if O(url) stops working with the new configuration
        (for example a new O(server_port) or TLS). Defaults to O(url).
    type: str
  wait_timeout:
    description:
      - Seconds to wait for Home Assistant to restart and be running again.
      - Keep it below 5 minutes, after which Home Assistant reverts an unconfirmed configuration on its own.
    type: int
    default: 180
requirements:
  - websocket-client
attributes:
  check_mode:
    support: full
    description: Reports the changes without applying them or restarting Home Assistant.
  diff_mode:
    support: full
    description: Shows the HTTP configuration before and after the run.
  platform:
    platforms: all
    support: full
    description: The module talks to Home Assistant over the network from the controller.
notes:
  - Requires a Home Assistant release with the HTTP configuration in its storage (configurable under
    B(Settings > System > Network)). A C(http:) block in C(configuration.yaml) is imported once and ignored afterwards.
  - Home Assistant checks that a new O(server_port) can be bound and that the SSL files exist before restarting.
seealso:
  - module: egors.homeassistant.core_config
"""

EXAMPLES = r"""
- name: Trust the reverse proxy
  egors.homeassistant.http_config:
    url: http://homeassistant.local:8123
    token: "{{ ha_token }}"
    use_x_forwarded_for: true
    trusted_proxies:
      - 172.30.33.0/24
  delegate_to: localhost

- name: Move to another port
  egors.homeassistant.http_config:
    url: http://homeassistant.local:8123
    token: "{{ ha_token }}"
    server_port: 8443
    reconnect_url: http://homeassistant.local:8443
  delegate_to: localhost

- name: Read the current configuration
  egors.homeassistant.http_config:
    url: http://homeassistant.local:8123
    token: "{{ ha_token }}"
  delegate_to: localhost
  register: http
"""

RETURN = r"""
config:
  description:
    - HTTP configuration after the run (or as it would be after the run, in check mode).
    - Unset values are V(null), unset lists are empty, lists are sorted.
  returned: always
  type: dict
  sample:
    server_host: []
    server_port: 8123
    ssl_certificate: null
    ssl_key: null
    ssl_peer_certificate: null
    ssl_profile: modern
    cors_allowed_origins: [https://cast.home-assistant.io]
    use_x_forwarded_for: true
    trusted_proxies: [172.30.33.0/24]
    login_attempts_threshold: -1
    ip_ban_enabled: true
    use_x_frame_options: true
restarted:
  description: Whether Home Assistant was restarted to apply the change.
  returned: always
  type: bool
  sample: true
ha_version:
  description: Home Assistant version.
  returned: when known
  type: str
  sample: 2026.10.4
"""

import time
from ipaddress import ip_network

from ansible_collections.egors.homeassistant.plugins.module_utils.api import (
    HomeAssistantAPIError,
    HomeAssistantError,
    HomeAssistantModule,
    WebSocketClient,
)

KEYS = (
    "server_host", "server_port", "ssl_certificate", "ssl_key", "ssl_peer_certificate", "ssl_profile",
    "cors_allowed_origins", "use_x_forwarded_for", "trusted_proxies", "login_attempts_threshold",
    "ip_ban_enabled", "use_x_frame_options",
)
# Keys whose empty value means "remove the key" (HA has no default for them).
CLEARABLE_STRINGS = ("ssl_certificate", "ssl_key", "ssl_peer_certificate")
CLEARABLE_LISTS = ("server_host", "trusted_proxies")
SET_KEYS = ("server_host", "cors_allowed_origins", "trusted_proxies")
# Bookkeeping HA keeps next to each stored config; not part of the configure schema.
META_KEYS = ("created_at", "error", "error_message")
REVERT_NOTE = "Home Assistant reverts an unconfirmed HTTP configuration 5 minutes after the restart."


def strip_meta(config):
    return {key: value for key, value in config.items() if key not in META_KEYS}


def normalize_proxies(values):
    """Proxies as HA stores them (``10.0.0.1`` -> ``10.0.0.1/32``); raise ValueError on bad entries."""
    return [str(ip_network(value.strip())) for value in values]


def normalize_config(config):
    """All supported keys with comparable values: unset is ``None``/``[]``/``False``, sets are sorted lists."""
    normalized = {}
    for key in KEYS:
        value = config.get(key)
        if key == "trusted_proxies" and value:
            value = normalize_proxies(value)
        if key in SET_KEYS:
            value = sorted(set(value or []))
        elif key == "use_x_forwarded_for":
            value = bool(value)
        normalized[key] = value
    return normalized


def desired_config(stable, params):
    """The full config to send: ``stable`` without metadata plus the provided options.

    ``configure`` replaces the whole config (omitted keys fall back to defaults), so nothing may be dropped.
    """
    desired = strip_meta(stable)
    for key in KEYS:
        value = params.get(key)
        if value is None:
            continue
        if (key in CLEARABLE_STRINGS and value == "") or (key in CLEARABLE_LISTS and value == []):
            desired.pop(key, None)
            continue
        if key == "trusted_proxies":
            value = normalize_proxies(value)
        desired[key] = value
    return desired


def plan(state, desired):
    """Return the action that brings HA to ``desired``: None, ``configure``, ``clear`` or ``promote``.

    A pending config with an error already failed its trial and is never applied again, so it is ignored.
    """
    target = normalize_config(desired)
    pending = state.get("pending")
    trial = pending if pending and pending.get("error") is None else None
    if target == normalize_config(state["stable"]):
        # An untested pending config would replace the desired one on the next restart.
        return "clear" if trial else None
    if trial and normalize_config(trial) == target and state.get("active_config_type") == "pending":
        # Running on exactly this config already (an earlier run was interrupted before confirming it).
        return "promote"
    return "configure"


class HTTPConfigModule(HomeAssistantModule):

    def wait_for_restart(self, url, deadline):
        """Wait for the current connection to drop, then reconnect to ``url`` once HA is running again."""
        if not self.ws.wait_closed(max(deadline - time.time(), 0)):
            self.fail_json(msg="Home Assistant did not restart within %ss." % self.params["wait_timeout"])
        self._ws = None
        last_error = None
        while time.time() < deadline:
            client = WebSocketClient(url, self.params["token"], timeout=self.params["timeout"],
                                     validate_certs=self.params["validate_certs"])
            try:
                client.connect()
                state = client.call("get_config").get("state")
            except HomeAssistantError as exc:
                last_error = exc
                client.close()
            else:
                if state == "RUNNING":
                    self._ws = client
                    return
                last_error = "Home Assistant is %s" % state
                client.close()
            time.sleep(2)
        self.fail_json(msg="Home Assistant did not come back at %s within %ss (last error: %s). %s"
                       % (url, self.params["wait_timeout"], last_error, REVERT_NOTE))

    def promote(self):
        try:
            self.ws.call("http/config/promote")
        except HomeAssistantAPIError as exc:
            self.fail_json(msg="Home Assistant rejected confirming the HTTP configuration: %s" % exc.message,
                           error_code=exc.code)
        except HomeAssistantError as exc:
            self.fail_json(msg="%s %s" % (exc, REVERT_NOTE))


def main():
    argument_spec = dict(
        server_host=dict(type="list", elements="str"),
        server_port=dict(type="int"),
        ssl_certificate=dict(type="str"),
        ssl_key=dict(type="str", no_log=False),
        ssl_peer_certificate=dict(type="str"),
        ssl_profile=dict(type="str", choices=["intermediate", "modern"]),
        cors_allowed_origins=dict(type="list", elements="str"),
        use_x_forwarded_for=dict(type="bool"),
        trusted_proxies=dict(type="list", elements="str"),
        login_attempts_threshold=dict(type="int"),
        ip_ban_enabled=dict(type="bool"),
        use_x_frame_options=dict(type="bool"),
        reconnect_url=dict(type="str"),
        wait_timeout=dict(type="int", default=180),
    )
    module = HTTPConfigModule(argument_spec, supports_check_mode=True)

    state = module.call("http/config")
    try:
        desired = desired_config(state["stable"], module.params)
    except ValueError as exc:
        module.fail_json(msg="Invalid trusted proxy: %s" % exc)
    before = normalize_config(state["stable"])
    after = normalize_config(desired)
    if after["use_x_forwarded_for"] and not after["trusted_proxies"]:
        module.fail_json(msg="use_x_forwarded_for requires at least one trusted proxy.")

    action = plan(state, desired)
    restarted = False
    if action and not module.check_mode:
        deadline = time.time() + module.params["wait_timeout"]
        if action in ("configure", "clear"):
            reply = module.call("http/config/configure", config=desired if action == "configure" else None)
            if reply.get("restart"):
                module.wait_for_restart(module.params["reconnect_url"] or module.params["url"], deadline)
                restarted = True
        if action != "clear":
            current = module.call("http/config")
            pending = current.get("pending")
            if not pending or normalize_config(pending) != after:
                module.fail_json(msg="Home Assistant did not keep the new HTTP configuration as pending.")
            if pending.get("error"):
                module.fail_json(msg="Home Assistant could not apply the new HTTP configuration and kept the "
                                 "previous one: %s" % (pending.get("error_message") or pending["error"]))
            if current.get("active_config_type") != "pending":
                # Never confirm a config the server is not actually running with.
                module.fail_json(msg="Home Assistant is not running with the new HTTP configuration (active: %s)."
                                 % current.get("active_config_type"))
            module.promote()
        after = normalize_config(module.call("http/config")["stable"])

    result = dict(changed=bool(action), config=after, restarted=restarted)
    version = getattr(module.ws, "ha_version", None)
    if version:
        result["ha_version"] = version
    if module._diff:
        result["diff"] = dict(before=before, after=after)
    module.exit_json(**result)


if __name__ == "__main__":
    main()

#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2026, Egor Sklyarov
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

DOCUMENTATION = r"""
module: dashboard
short_description: Manage Home Assistant dashboards and their content
version_added: 0.1.0
author: Egor Sklyarov (@Egor-S)
description:
  - Creates, updates and deletes dashboards created in the UI, and sets their content.
  - The dashboard is found by O(url_path). Only the options that are set are managed.
  - O(url_path=lovelace) is the default dashboard (Overview); only its O(config) can be set.
  - Dashboards defined in C(configuration.yaml) (YAML mode) are not managed.
extends_documentation_fragment:
  - egors.homeassistant.connection
options:
  url_path:
    description:
      - Path of the dashboard, the part after the host in its URL, for example V(home-energy).
        Home Assistant requires a hyphen in it.
      - V(lovelace) selects the default dashboard.
    type: str
    required: true
  state:
    description:
      - V(present) creates or updates the dashboard, V(absent) deletes it with its content.
      - With O(url_path=lovelace), V(absent) deletes the content, so the default dashboard is generated automatically again.
    type: str
    choices: [present, absent]
    default: present
  title:
    description:
      - Title in the sidebar. Required to create a dashboard.
    type: str
  icon:
    description:
      - Icon in the sidebar, for example V(mdi:lightning-bolt). An empty string removes it.
    type: str
  show_in_sidebar:
    description:
      - Whether the dashboard is listed in the sidebar. Home Assistant uses V(true) when a dashboard is created without it.
    type: bool
  require_admin:
    description:
      - Whether only administrators can open it. Home Assistant uses V(false) when a dashboard is created without it.
    type: bool
  config:
    description:
      - Content of the dashboard, as shown by "Raw configuration editor" in the UI, for example with C(views).
      - It replaces the stored content and is compared with it as a whole. Leaving it out keeps the content.
    type: dict
attributes:
  check_mode:
    support: full
    description: Reports the changes and the predicted dashboard without writing.
  diff_mode:
    support: full
    description: Shows the dashboard and its content before and after the run.
  platform:
    platforms: all
    support: full
    description: The module talks to Home Assistant over the network from the controller.
seealso:
  - module: egors.homeassistant.dashboard_resource
"""

EXAMPLES = r"""
- name: An energy dashboard
  egors.homeassistant.dashboard:
    url_path: home-energy
    title: Energy
    icon: mdi:lightning-bolt
    config:
      views:
        - title: Today
          cards:
            - type: energy-usage-graph

- name: Set the content of the default dashboard
  egors.homeassistant.dashboard:
    url_path: lovelace
    config: "{{ lookup('ansible.builtin.file', 'overview.yaml') | from_yaml }}"
"""

RETURN = r"""
dashboard:
  description: The dashboard after the run (predicted in check mode), or an empty dictionary if it is absent.
  returned: always
  type: dict
  contains:
    url_path:
      description: Path of the dashboard.
      type: str
      sample: home-energy
    dashboard_id:
      description: ID of the dashboard. Null for the default dashboard and for one that would be created in check mode.
      type: str
      sample: home_energy
    title:
      description: Title.
      type: str
    icon:
      description: Icon, or null.
      type: str
    show_in_sidebar:
      description: Whether it is listed in the sidebar.
      type: bool
    require_admin:
      description: Whether only administrators can open it.
      type: bool
config:
  description: Content after the run when O(config) is given or the dashboard is deleted, else not returned.
  returned: when O(config) is given or O(state=absent)
  type: dict
"""

from ansible_collections.egors.homeassistant.plugins.module_utils.api import HomeAssistantModule
from ansible_collections.egors.homeassistant.plugins.module_utils.lovelace import (
    DEFAULT_URL_PATH,
    dashboard_changes,
    get_config,
    normalize_dashboard,
)


def main():
    argument_spec = dict(
        url_path=dict(type="str", required=True),
        state=dict(type="str", choices=["present", "absent"], default="present"),
        title=dict(type="str"),
        icon=dict(type="str"),
        show_in_sidebar=dict(type="bool"),
        require_admin=dict(type="bool"),
        config=dict(type="dict"),
    )
    module = HomeAssistantModule(argument_spec, supports_check_mode=True)
    params = module.params
    url_path = params["url_path"]
    is_default = url_path == DEFAULT_URL_PATH
    present = params["state"] == "present"

    if is_default:
        if any(params[f] is not None for f in ("title", "icon", "show_in_sidebar", "require_admin")):
            module.fail_json(msg="only config can be set for the default dashboard")
        entry = before = after = {"url_path": url_path, "dashboard_id": None}
        changed = False
    else:
        entry = next((d for d in module.call("lovelace/dashboards/list") if d.get("url_path") == url_path), None)
        before = normalize_dashboard(entry) if entry else {}
        if not present:
            after, changed = {}, entry is not None
            if changed and not module.check_mode:
                module.call("lovelace/dashboards/delete", dashboard_id=entry["id"])
        elif entry is None:
            if params["title"] is None:
                module.fail_json(msg="title is required to create a dashboard")
            payload = dict(url_path=url_path, title=params["title"])
            for field in ("show_in_sidebar", "require_admin"):
                if params[field] is not None:
                    payload[field] = params[field]
            if params["icon"]:
                payload["icon"] = params["icon"]
            changed = True
            after = dict(normalize_dashboard(dict(dict(show_in_sidebar=True, require_admin=False), **payload)),
                         dashboard_id=None)
            if not module.check_mode:
                after = normalize_dashboard(module.call("lovelace/dashboards/create", **payload))
        else:
            changes = dashboard_changes(params, before)
            changed = bool(changes)
            after = dict(before, **changes)
            if changed and not module.check_mode:
                after = normalize_dashboard(module.call("lovelace/dashboards/update", dashboard_id=entry["id"],
                                                        **changes))

    result = {"dashboard": after}
    diff_before, diff_after = dict(before), dict(after)
    # The content of a dashboard that does not exist (yet) can not be read.
    if (params["config"] is not None and present) or (is_default and not present):
        config_before = get_config(module, None if is_default else url_path) if entry else None
        config_after = params["config"] if present else None
        if config_before != config_after:
            changed = True
            if not module.check_mode:
                if present:
                    module.call("lovelace/config/save", url_path=None if is_default else url_path, config=config_after)
                else:
                    module.call("lovelace/config/delete", url_path=None)
        result["config"] = config_after or {}
        if before:
            diff_before["config"] = config_before or {}
        if after:
            diff_after["config"] = config_after or {}
    elif not present:
        result["config"] = {}
    result["changed"] = changed
    if module._diff:
        result["diff"] = dict(before=diff_before, after=diff_after)
    module.exit_json(**result)


if __name__ == "__main__":
    main()

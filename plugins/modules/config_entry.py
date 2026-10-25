#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2026, Egor Sklyarov
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

DOCUMENTATION = r"""
module: config_entry
short_description: Add and remove Home Assistant integrations (config entries)
version_added: 0.1.0
author: Egor Sklyarov (@Egor-S)
description:
  - Adds an integration or a UI helper (a config entry) by running its config flow with the given O(steps),
    and removes config entries.
  - The entry is found by O(domain) and O(title), ignoring case and surrounding or repeated whitespace. After creating
    an entry the module sets its title to O(title), so that later runs find it.
  - The settings an entry was created with can't be read back. An existing entry is left as it is, even if O(steps)
    changed; remove and add it again to apply new settings.
  - Flows that need a browser (OAuth), wait for a device, or use discovery can't be run.
extends_documentation_fragment:
  - egors.homeassistant.connection
options:
  domain:
    description:
      - Domain of the integration, for example V(local_calendar) or V(template).
    type: str
    required: true
  title:
    description:
      - Title of the entry, shown on the integration page. It identifies the entry.
    type: str
    required: true
  steps:
    description:
      - Input for each step of the config flow, in order, each a dictionary. A form step takes its fields
        (for example C(calendar_name) for V(local_calendar)); a menu step takes C(next_step_id) with one of its options.
      - The steps are only used when the entry is created. They are not logged, as they often hold passwords or API keys.
      - When the flow asks for more steps than given, or rejects the input, the module fails, names the step and its
        fields, and cancels the flow.
    type: list
    elements: dict
    default: []
  state:
    description:
      - V(present) adds the entry if it does not exist, V(absent) removes it.
    type: str
    choices: [present, absent]
    default: present
attributes:
  check_mode:
    support: full
    description: Reports whether the entry would be added or removed, without starting a flow.
  diff_mode:
    support: none
    description: The settings of an entry can not be read.
  platform:
    platforms: all
    support: full
    description: The module talks to Home Assistant over the network from the controller.
seealso:
  - module: egors.homeassistant.config_entry_info
"""

EXAMPLES = r"""
- name: A local calendar
  egors.homeassistant.config_entry:
    domain: local_calendar
    title: Family
    steps:
      - calendar_name: Family

- name: A template sensor helper (the first step is a menu)
  egors.homeassistant.config_entry:
    domain: template
    title: Outdoor temperature (rounded)
    steps:
      - next_step_id: sensor
      - name: Outdoor temperature (rounded)
        # !unsafe keeps Ansible from rendering the Home Assistant template itself.
        state: !unsafe "{{ states('sensor.outdoor_temperature') | float | round(0) }}"
        unit_of_measurement: °C

- name: Remove it
  egors.homeassistant.config_entry:
    domain: template
    title: Outdoor temperature (rounded)
    state: absent
"""

RETURN = r"""
entry:
  description: The entry after the run, or an empty dictionary if it is absent or would be created in check mode.
  returned: always
  type: dict
  contains:
    entry_id:
      description: ID of the entry.
      type: str
    domain:
      description: Domain of the integration.
      type: str
    title:
      description: Title.
      type: str
    state:
      description: V(loaded), V(setup_error), V(setup_retry), V(not_loaded), ...
      type: str
    source:
      description: How the entry was created, for example V(user).
      type: str
    disabled_by:
      description: Who disabled the entry, or null.
      type: str
    supports_options:
      description: Whether the entry has options.
      type: bool
require_restart:
  description: Whether Home Assistant must be restarted to finish removing the entry.
  returned: when an entry was removed
  type: bool
"""

from ansible_collections.egors.homeassistant.plugins.module_utils.api import HomeAssistantModule
from ansible_collections.egors.homeassistant.plugins.module_utils.config_entry import (
    ALREADY,
    FlowError,
    find_entries,
    normalize_entry,
    run_flow,
)

FLOW_PATH = "/api/config/config_entries/flow"


def main():
    argument_spec = dict(
        domain=dict(type="str", required=True),
        title=dict(type="str", required=True),
        steps=dict(type="list", elements="dict", default=[], no_log=True),
        state=dict(type="str", choices=["present", "absent"], default="present"),
    )
    module = HomeAssistantModule(argument_spec, supports_check_mode=True)
    domain, title = module.params["domain"], module.params["title"]
    entries = module.call("config_entries/get", domain=domain)
    matches = find_entries(entries, domain, title)
    if len(matches) > 1:
        module.fail_json(msg="%d %s entries are titled %r" % (len(matches), domain, title),
                         matches=[normalize_entry(e) for e in matches])
    entry = matches[0] if matches else None
    result = dict(changed=False, entry=normalize_entry(entry) if entry else {})

    if module.params["state"] == "absent":
        if entry:
            result.update(changed=True, entry={})
            if not module.check_mode:
                status, payload = module.rest("/api/config/config_entries/entry/%s" % entry["entry_id"], method="DELETE")
                if status != 200:
                    module.fail_json(msg="removing the entry failed with HTTP %s: %s" % (status, payload))
                result["require_restart"] = bool(payload.get("require_restart"))
        module.exit_json(**result)

    if entry or module.check_mode:
        result["changed"] = entry is None
        module.exit_json(**result)

    def rest(path, method, data):
        return module.rest(path, method=method, data=data)

    try:
        step = run_flow(rest, FLOW_PATH, dict(handler=domain, show_advanced_options=True), module.params["steps"])
    except FlowError as e:
        module.fail_json(msg="%s flow: %s" % (domain, e))
    if step["type"] == "abort":
        if step.get("reason") in ALREADY:
            module.warn("%s is already set up (%s); existing entries: %s" % (
                domain, step["reason"], ", ".join(repr(e.get("title")) for e in entries) or "none visible"))
            module.exit_json(**result)
        module.fail_json(msg="%s flow aborted: %s" % (domain, step.get("reason")))

    created = step["result"]
    if created.get("title") != title:
        module.call("config_entries/update", entry_id=created["entry_id"], title=title)
        created = dict(created, title=title)
    if created.get("state") != "loaded":
        module.warn("the new %s entry is in state %s, not loaded" % (domain, created.get("state")))
    result.update(changed=True, entry=normalize_entry(created))
    module.exit_json(**result)


if __name__ == "__main__":
    main()

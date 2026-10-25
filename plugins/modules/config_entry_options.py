#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2026, Egor Sklyarov
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

DOCUMENTATION = r"""
module: config_entry_options
short_description: Set the options of a Home Assistant config entry
version_added: 0.1.0
author: Egor Sklyarov (@Egor-S)
description:
  - Sets the options of an integration or UI helper (its "Configure" dialog) by running its options flow with the given O(steps).
  - Each form shows the current options. The module compares the given fields with them and keeps the fields it was not given,
    so only the given fields change. If none differ the flow is cancelled and nothing is written.
  - The options may hold secrets, so only the names of changed fields are returned, never values.
extends_documentation_fragment:
  - egors.homeassistant.connection
options:
  domain:
    description:
      - Domain of the integration, for example V(template).
    type: str
    required: true
  title:
    description:
      - Title of the entry, ignoring case and surrounding or repeated whitespace.
    type: str
    required: true
  steps:
    description:
      - Input for each step of the options flow, in order, each a dictionary of fields of that step's form.
        A menu step takes C(next_step_id) with one of its options.
      - A field that is not in the form fails, to catch typos.
    type: list
    elements: dict
    required: true
attributes:
  check_mode:
    support: full
    description: Walks the options flow to compare, then cancels it.
  diff_mode:
    support: none
    description: Values are not shown, as they may be secret. RV(changed_fields) names the changed fields.
  platform:
    platforms: all
    support: full
    description: The module talks to Home Assistant over the network from the controller.
seealso:
  - module: egors.homeassistant.config_entry
"""

EXAMPLES = r"""
- name: Change the unit of a template sensor helper
  egors.homeassistant.config_entry_options:
    domain: template
    title: Outdoor temperature (rounded)
    steps:
      - unit_of_measurement: °F
"""

RETURN = r"""
changed_fields:
  description: Changed fields (or that would change in check mode), as C(<step_id>.<field>).
  returned: always
  type: list
  elements: str
  sample: [init.unit_of_measurement]
entry_id:
  description: ID of the entry.
  returned: always
  type: str
"""

from ansible_collections.egors.homeassistant.plugins.module_utils.api import HomeAssistantModule
from ansible_collections.egors.homeassistant.plugins.module_utils.config_entry import (
    FlowError,
    find_entries,
    run_options_flow,
)


def main():
    argument_spec = dict(
        domain=dict(type="str", required=True),
        title=dict(type="str", required=True),
        steps=dict(type="list", elements="dict", required=True, no_log=True),
    )
    module = HomeAssistantModule(argument_spec, supports_check_mode=True)
    domain, title = module.params["domain"], module.params["title"]
    matches = find_entries(module.call("config_entries/get", domain=domain), domain, title)
    if len(matches) != 1:
        module.fail_json(msg="%d %s entries are titled %r" % (len(matches), domain, title))
    entry = matches[0]
    if not entry.get("supports_options"):
        module.fail_json(msg="the %s entry %r has no options" % (domain, title))

    def rest(path, method, data):
        return module.rest(path, method=method, data=data)

    try:
        changed = run_options_flow(rest, "/api/config/config_entries/options/flow", entry["entry_id"],
                                   module.params["steps"], module.check_mode)
    except FlowError as e:
        module.fail_json(msg="%s options flow: %s" % (domain, e))
    module.exit_json(changed=bool(changed), changed_fields=changed, entry_id=entry["entry_id"])


if __name__ == "__main__":
    main()

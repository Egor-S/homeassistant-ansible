#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2026, Egor Sklyarov
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

DOCUMENTATION = r"""
module: dashboard_resource
short_description: Manage Home Assistant dashboard resources
version_added: 0.1.0
author: Egor Sklyarov (@Egor-S)
description:
  - Adds, updates and removes dashboard resources, the JavaScript modules and stylesheets that custom cards need
    (Settings > Dashboards > Resources).
  - The resource is found by O(resource_url).
  - Resources can only be managed while dashboards are in storage mode, the default.
extends_documentation_fragment:
  - egors.homeassistant.connection
options:
  resource_url:
    description:
      - URL of the resource, for example V(/local/my-card.js) or V(/hacsfiles/button-card/button-card.js).
    type: str
    required: true
  type:
    description:
      - V(module) for a JavaScript module (most custom cards), V(js) for a plain script, V(css) for a stylesheet.
      - Required to add a resource.
    type: str
    choices: [css, js, module]
  state:
    description:
      - V(present) adds or updates the resource, V(absent) removes it.
    type: str
    choices: [present, absent]
    default: present
attributes:
  check_mode:
    support: full
    description: Reports the changes and the predicted resource without writing.
  diff_mode:
    support: full
    description: Shows the resource before and after the run.
  platform:
    platforms: all
    support: full
    description: The module talks to Home Assistant over the network from the controller.
seealso:
  - module: egors.homeassistant.dashboard
"""

EXAMPLES = r"""
- name: Load a custom card
  egors.homeassistant.dashboard_resource:
    resource_url: /local/my-card.js
    type: module
"""

RETURN = r"""
resource:
  description: The resource after the run (predicted in check mode), or an empty dictionary if it is absent.
  returned: always
  type: dict
  contains:
    resource_id:
      description: ID of the resource. Null for a resource that would be added in check mode.
      type: str
    url:
      description: URL.
      type: str
      sample: /local/my-card.js
    type:
      description: V(module), V(js) or V(css).
      type: str
      sample: module
"""

from ansible_collections.egors.homeassistant.plugins.module_utils.api import HomeAssistantModule
from ansible_collections.egors.homeassistant.plugins.module_utils.lovelace import normalize_resource


def main():
    argument_spec = dict(
        resource_url=dict(type="str", required=True),
        type=dict(type="str", choices=["css", "js", "module"]),
        state=dict(type="str", choices=["present", "absent"], default="present"),
    )
    module = HomeAssistantModule(argument_spec, supports_check_mode=True)
    params = module.params
    matches = [r for r in module.call("lovelace/resources/list") if r.get("url") == params["resource_url"]]
    entry = matches[0] if matches else None
    before = normalize_resource(entry) if entry else {}

    if params["state"] == "absent":
        after, changed = {}, bool(matches)
        if changed and not module.check_mode:
            for match in matches:
                module.call("lovelace/resources/delete", resource_id=match["id"])
    elif entry is None:
        if params["type"] is None:
            module.fail_json(msg="type is required to add a resource")
        changed = True
        after = dict(resource_id=None, url=params["resource_url"], type=params["type"])
        if not module.check_mode:
            after = normalize_resource(module.call("lovelace/resources/create", url=params["resource_url"],
                                                   res_type=params["type"]))
    else:
        changed = params["type"] is not None and params["type"] != before["type"]
        after = dict(before, type=params["type"]) if changed else before
        if changed and not module.check_mode:
            after = normalize_resource(module.call("lovelace/resources/update", resource_id=entry["id"],
                                                   res_type=params["type"]))

    result = dict(changed=changed, resource=after)
    if module._diff:
        result["diff"] = dict(before=before, after=after)
    module.exit_json(**result)


if __name__ == "__main__":
    main()

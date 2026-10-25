#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2026, Egor Sklyarov
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

DOCUMENTATION = r"""
module: entity_info
short_description: List entities of the Home Assistant entity registry
version_added: 0.1.0
author: Egor Sklyarov (@Egor-S)
description:
  - Returns entity registry entries, optionally filtered. All filters that are set must match.
  - Entities without a unique ID are not in the registry and not returned.
extends_documentation_fragment:
  - egors.homeassistant.connection
options:
  entity_id:
    description:
      - Only return these entities. Entity IDs that are not in the registry are left out.
    type: list
    elements: str
  area_id:
    description:
      - Only return entities with this area of their own. Entities that follow the area of their device are not matched.
    type: str
  device_id:
    description:
      - Only return entities of this device.
    type: str
  platform:
    description:
      - Only return entities of this integration, for example V(sun).
    type: str
  label:
    description:
      - Only return entities with this label ID.
    type: str
attributes:
  check_mode:
    support: full
    description: The module only reads.
  diff_mode:
    support: none
    description: The module does not change anything.
  platform:
    platforms: all
    support: full
    description: The module talks to Home Assistant over the network from the controller.
seealso:
  - module: egors.homeassistant.entity
"""

EXAMPLES = r"""
- name: Entities of the sun integration
  egors.homeassistant.entity_info:
    platform: sun
  register: sun

- name: One entity
  egors.homeassistant.entity_info:
    entity_id: [sensor.sun_next_dawn]
  register: dawn
"""

RETURN = r"""
entities:
  description: Matching entities in registry order, in the same format as the RV(egors.homeassistant.entity#module:entity) return value.
  returned: always
  type: list
  elements: dict
  sample:
    - entity_id: sensor.sun_next_dawn
      name: null
      icon: null
      area_id: null
      device_class: null
      aliases: []
      labels: []
      disabled_by: null
      hidden_by: null
      original_name: Next dawn
      original_icon: null
      original_device_class: timestamp
      device_id: 107dca174fa5db043adc152803b6bace
      platform: sun
      unique_id: 01M5SWJ7XMM46Y2Q8XH1JSH8FS-next_dawn
"""

from ansible_collections.egors.homeassistant.plugins.module_utils.api import HomeAssistantModule
from ansible_collections.egors.homeassistant.plugins.module_utils.entity import normalize

FILTERS = ("area_id", "device_id", "platform")


def main():
    argument_spec = dict(
        entity_id=dict(type="list", elements="str"),
        area_id=dict(type="str"),
        device_id=dict(type="str"),
        platform=dict(type="str"),
        label=dict(type="str"),
    )
    module = HomeAssistantModule(argument_spec, supports_check_mode=True)
    params = module.params
    entries = module.call("config/entity_registry/list")
    if params["entity_id"] is not None:
        wanted = set(params["entity_id"])
        entries = [e for e in entries if e.get("entity_id") in wanted]
    for field in FILTERS:
        if params[field] is not None:
            entries = [e for e in entries if e.get(field) == params[field]]
    if params["label"] is not None:
        entries = [e for e in entries if params["label"] in (e.get("labels") or [])]
    ids = [e["entity_id"] for e in entries]
    # The list leaves out aliases and device classes; get_entries has the full entries.
    full = module.call("config/entity_registry/get_entries", entity_ids=ids) if ids else {}
    module.exit_json(changed=False, entities=[normalize(full[i]) for i in ids if full.get(i)])


if __name__ == "__main__":
    main()

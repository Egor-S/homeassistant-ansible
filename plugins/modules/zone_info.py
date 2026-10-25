#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2026, Egor Sklyarov
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

DOCUMENTATION = r"""
module: zone_info
short_description: List Home Assistant zones
version_added: 0.1.0
author: Egor Sklyarov (@Egor-S)
description:
  - Returns the zones created in the UI or over the API, optionally filtered by name or ID.
  - The home zone and zones defined in C(configuration.yaml) are not included.
extends_documentation_fragment:
  - egors.homeassistant.connection
options:
  name:
    description:
      - Only return the zones with this name, ignoring case and surrounding or repeated whitespace.
    type: str
  zone_id:
    description:
      - Only return the zone with this ID.
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
  - module: egors.homeassistant.zone
"""

EXAMPLES = r"""
- name: List all zones
  egors.homeassistant.zone_info:
  register: result

- name: Get zones by name
  egors.homeassistant.zone_info:
    name: Office
  register: office
"""

RETURN = r"""
zones:
  description: Matching zones in creation order, in the same format as the RV(egors.homeassistant.zone#module:zone) return value.
  returned: always
  type: list
  elements: dict
  sample:
    - zone_id: office
      name: Office
      latitude: 60.1699
      longitude: 24.9384
      radius: 150.0
      passive: false
      icon: mdi:briefcase
"""

from ansible_collections.egors.homeassistant.plugins.module_utils.api import HomeAssistantModule
from ansible_collections.egors.homeassistant.plugins.module_utils.registry import Registry


STRINGS = ("icon",)
VALUES = ("latitude", "longitude", "radius", "passive")


def main():
    module = HomeAssistantModule(dict(name=dict(type="str"), zone_id=dict(type="str")), supports_check_mode=True)
    Registry(module, "zone", "zone_id", STRINGS, values=VALUES, entry_key="id").info("zones")


if __name__ == "__main__":
    main()

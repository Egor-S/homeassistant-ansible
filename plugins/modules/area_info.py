#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2026, Egor Sklyarov
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

DOCUMENTATION = r"""
module: area_info
short_description: List areas of the Home Assistant area registry
version_added: 0.1.0
author: Egor Sklyarov (@Egor-S)
description:
  - Returns the areas of the area registry, optionally filtered by name or ID.
extends_documentation_fragment:
  - egors.homeassistant.connection
options:
  name:
    description:
      - Only return the area with this name, ignoring case and surrounding or repeated whitespace.
    type: str
  area_id:
    description:
      - Only return the area with this ID.
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
  - module: egors.homeassistant.area
"""

EXAMPLES = r"""
- name: List all areas
  egors.homeassistant.area_info:
  register: result

- name: Get one area
  egors.homeassistant.area_info:
    name: Living Room
  register: living_room
"""

RETURN = r"""
areas:
  description: Matching areas in creation order, in the same format as the RV(egors.homeassistant.area#module:area) return value.
  returned: always
  type: list
  elements: dict
  sample:
    - area_id: living_room
      name: Living Room
      aliases: []
      icon: mdi:sofa
      picture: null
      floor_id: null
      temperature_entity_id: null
      humidity_entity_id: null
      labels: []
"""

from ansible_collections.egors.homeassistant.plugins.module_utils.api import HomeAssistantModule
from ansible_collections.egors.homeassistant.plugins.module_utils.registry import Registry


STRINGS = ("icon", "picture", "floor_id", "temperature_entity_id", "humidity_entity_id")
LISTS = ("aliases", "labels")


def main():
    module = HomeAssistantModule(dict(name=dict(type="str"), area_id=dict(type="str")), supports_check_mode=True)
    Registry(module, "config/area_registry", "area_id", STRINGS, LISTS).info("areas")


if __name__ == "__main__":
    main()

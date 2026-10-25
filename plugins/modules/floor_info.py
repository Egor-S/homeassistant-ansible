#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2026, Egor Sklyarov
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

DOCUMENTATION = r"""
module: floor_info
short_description: List floors of the Home Assistant floor registry
version_added: 0.1.0
author: Egor Sklyarov (@Egor-S)
description:
  - Returns the floors of the floor registry, optionally filtered by name or ID.
extends_documentation_fragment:
  - egors.homeassistant.connection
options:
  name:
    description:
      - Only return the floor with this name, ignoring case and surrounding or repeated whitespace.
    type: str
  floor_id:
    description:
      - Only return the floor with this ID.
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
  - module: egors.homeassistant.floor
"""

EXAMPLES = r"""
- name: List all floors
  egors.homeassistant.floor_info:
  register: result

- name: Get one floor
  egors.homeassistant.floor_info:
    name: Ground floor
  register: ground
"""

RETURN = r"""
floors:
  description: Matching floors in creation order, in the same format as the RV(egors.homeassistant.floor#module:floor) return value.
  returned: always
  type: list
  elements: dict
  sample:
    - floor_id: ground_floor
      name: Ground floor
      aliases: []
      icon: mdi:home-floor-0
      level: 0
"""

from ansible_collections.egors.homeassistant.plugins.module_utils.api import HomeAssistantModule
from ansible_collections.egors.homeassistant.plugins.module_utils.registry import Registry


STRINGS = ("icon",)
LISTS = ("aliases",)
INTS = ("level",)


def main():
    module = HomeAssistantModule(dict(name=dict(type="str"), floor_id=dict(type="str")), supports_check_mode=True)
    Registry(module, "config/floor_registry", "floor_id", STRINGS, LISTS, INTS).info("floors")


if __name__ == "__main__":
    main()

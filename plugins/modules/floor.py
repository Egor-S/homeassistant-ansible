#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2026, Egor Sklyarov
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

DOCUMENTATION = r"""
module: floor
short_description: Manage floors in the Home Assistant floor registry
version_added: 0.1.0
author: Egor Sklyarov (@Egor-S)
description:
  - Creates, updates and deletes floors.
  - Only the options that are set are managed; other properties of an existing floor are left unchanged.
  - The floor is found by O(floor_id) if given, otherwise by O(name), ignoring case and surrounding or repeated whitespace.
extends_documentation_fragment:
  - egors.homeassistant.connection
options:
  name:
    description:
      - Name of the floor. Required to create a floor.
      - If O(floor_id) is also given, an existing floor is renamed to this name.
      - At least one of O(name) and O(floor_id) is required.
    type: str
  floor_id:
    description:
      - ID of the floor, for example V(ground_floor).
      - Home Assistant generates the ID from the name on creation, so it can not be chosen.
      - With O(state=present) the floor must already exist.
    type: str
  state:
    description:
      - V(present) creates or updates the floor, V(absent) deletes it.
    type: str
    choices: [present, absent]
    default: present
  aliases:
    description:
      - Alternative names of the floor, compared as a set (order and duplicates are ignored).
      - An empty list removes all aliases.
    type: list
    elements: str
  icon:
    description:
      - Icon, for example V(mdi:home-floor-1). An empty string removes the icon.
    type: str
  level:
    description:
      - Level of the floor, an integer used for ordering. V(0) is a level (usually the ground floor), negative values are allowed.
      - An empty string removes the level. Leaving the option out keeps the current level.
      - It is declared as V(raw) so that both an integer and an empty string are accepted; other values fail.
    type: raw
attributes:
  check_mode:
    support: full
    description: Reports the changes and the predicted floor without writing.
  diff_mode:
    support: full
    description: Shows the floor before and after the run.
  platform:
    platforms: all
    support: full
    description: The module talks to Home Assistant over the network from the controller.
seealso:
  - module: egors.homeassistant.floor_info
"""

EXAMPLES = r"""
- name: Create a floor
  egors.homeassistant.floor:
    name: Ground floor
    level: 0
    icon: mdi:home-floor-0

- name: Rename a floor
  egors.homeassistant.floor:
    floor_id: ground_floor
    name: Main floor

- name: Remove the level
  egors.homeassistant.floor:
    name: Main floor
    level: ""

- name: Delete a floor
  egors.homeassistant.floor:
    name: Main floor
    state: absent
"""

RETURN = r"""
floor:
  description: The floor after the run (predicted in check mode), or an empty dictionary if it is absent.
  returned: always
  type: dict
  contains:
    floor_id:
      description: ID of the floor. Null for a floor that would be created in check mode.
      type: str
      sample: ground_floor
    name:
      description: Name of the floor.
      type: str
      sample: Ground floor
    aliases:
      description: Sorted aliases.
      type: list
      elements: str
    icon:
      description: Icon, or null.
      type: str
    level:
      description: Level, or null.
      type: int
"""

from ansible_collections.egors.homeassistant.plugins.module_utils.api import HomeAssistantModule
from ansible_collections.egors.homeassistant.plugins.module_utils.registry import Registry

STRINGS = ("icon",)
LISTS = ("aliases",)
INTS = ("level",)


def main():
    argument_spec = dict(
        name=dict(type="str"),
        floor_id=dict(type="str"),
        state=dict(type="str", choices=["present", "absent"], default="present"),
        aliases=dict(type="list", elements="str"),
        icon=dict(type="str"),
        level=dict(type="raw"),
    )
    module = HomeAssistantModule(argument_spec, required_one_of=[("name", "floor_id")], supports_check_mode=True)
    Registry(module, "config/floor_registry", "floor_id", STRINGS, LISTS, INTS).ensure("floor")


if __name__ == "__main__":
    main()

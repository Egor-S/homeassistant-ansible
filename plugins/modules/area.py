#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2026, Egor Sklyarov
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

DOCUMENTATION = r"""
module: area
short_description: Manage areas in the Home Assistant area registry
version_added: 0.1.0
author: Egor Sklyarov (@Egor-S)
description:
  - Creates, updates and deletes areas.
  - Only the options that are set are managed; other properties of an existing area are left unchanged.
  - The area is found by O(area_id) if given, otherwise by O(name), ignoring case and surrounding or repeated whitespace.
extends_documentation_fragment:
  - egors.homeassistant.connection
options:
  name:
    description:
      - Name of the area. Required to create an area.
      - If O(area_id) is also given, an existing area is renamed to this name.
      - At least one of O(name) and O(area_id) is required.
    type: str
  area_id:
    description:
      - ID of the area, for example V(living_room).
      - Home Assistant generates the ID from the name on creation, so it can not be chosen.
      - With O(state=present) the area must already exist.
    type: str
  state:
    description:
      - V(present) creates or updates the area, V(absent) deletes it.
    type: str
    choices: [present, absent]
    default: present
  aliases:
    description:
      - Alternative names of the area, compared as a set (order and duplicates are ignored).
      - An empty list removes all aliases.
    type: list
    elements: str
  icon:
    description:
      - Icon, for example V(mdi:sofa). An empty string removes the icon.
    type: str
  picture:
    description:
      - Picture URL of the area. An empty string removes the picture.
    type: str
  floor_id:
    description:
      - ID of the floor of the area. Home Assistant does not check that the floor exists.
      - An empty string removes the area from its floor.
    type: str
  temperature_entity_id:
    description:
      - Entity ID of the temperature sensor of the area. An empty string unsets it.
    type: str
  humidity_entity_id:
    description:
      - Entity ID of the humidity sensor of the area. An empty string unsets it.
    type: str
  labels:
    description:
      - Label IDs of the area, compared as a set. An empty list removes all labels.
      - Home Assistant silently drops unknown labels; the module warns when that happens.
    type: list
    elements: str
attributes:
  check_mode:
    support: full
    description: Reports the changes and the predicted area without writing.
  diff_mode:
    support: full
    description: Shows the area before and after the run.
  platform:
    platforms: all
    support: full
    description: The module talks to Home Assistant over the network from the controller.
seealso:
  - module: egors.homeassistant.area_info
"""

EXAMPLES = r"""
- name: Create an area
  egors.homeassistant.area:
    name: Garage
    icon: mdi:garage
    aliases: [Carport]

- name: Rename an area
  egors.homeassistant.area:
    area_id: garage
    name: Workshop

- name: Remove the icon
  egors.homeassistant.area:
    name: Workshop
    icon: ""

- name: Delete an area
  egors.homeassistant.area:
    name: Workshop
    state: absent
"""

RETURN = r"""
area:
  description: The area after the run (predicted in check mode), or an empty dictionary if it is absent.
  returned: always
  type: dict
  contains:
    area_id:
      description: ID of the area. Null for an area that would be created in check mode.
      type: str
      sample: garage
    name:
      description: Name of the area.
      type: str
      sample: Garage
    aliases:
      description: Sorted aliases.
      type: list
      elements: str
    icon:
      description: Icon, or null.
      type: str
    picture:
      description: Picture, or null.
      type: str
    floor_id:
      description: Floor ID, or null.
      type: str
    temperature_entity_id:
      description: Temperature sensor entity ID, or null.
      type: str
    humidity_entity_id:
      description: Humidity sensor entity ID, or null.
      type: str
    labels:
      description: Sorted label IDs.
      type: list
      elements: str
"""

from ansible_collections.egors.homeassistant.plugins.module_utils.api import HomeAssistantModule
from ansible_collections.egors.homeassistant.plugins.module_utils.registry import Registry

STRINGS = ("icon", "picture", "floor_id", "temperature_entity_id", "humidity_entity_id")
LISTS = ("aliases", "labels")


def main():
    argument_spec = dict(
        name=dict(type="str"),
        area_id=dict(type="str"),
        state=dict(type="str", choices=["present", "absent"], default="present"),
        aliases=dict(type="list", elements="str"),
        labels=dict(type="list", elements="str"),
    )
    argument_spec.update((field, dict(type="str")) for field in STRINGS)
    module = HomeAssistantModule(argument_spec, required_one_of=[("name", "area_id")], supports_check_mode=True)
    Registry(module, "config/area_registry", "area_id", STRINGS, LISTS).ensure("area")


if __name__ == "__main__":
    main()

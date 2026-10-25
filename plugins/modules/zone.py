#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2026, Egor Sklyarov
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

DOCUMENTATION = r"""
module: zone
short_description: Manage Home Assistant zones
version_added: 0.1.0
author: Egor Sklyarov (@Egor-S)
description:
  - Creates, updates and deletes zones created in the UI or over the API.
  - Only the options that are set are managed; other properties of an existing zone are left unchanged.
  - The zone is found by O(zone_id) if given, otherwise by O(name), ignoring case and surrounding or repeated whitespace.
    Home Assistant allows several zones with the same name; the module fails if the name matches more than one, then use O(zone_id).
  - The home zone is not managed here; its location and radius are set with M(egors.homeassistant.core_config).
    Zones defined in C(configuration.yaml) are not visible to this module.
extends_documentation_fragment:
  - egors.homeassistant.connection
options:
  name:
    description:
      - Name of the zone. Required to create a zone.
      - If O(zone_id) is also given, an existing zone is renamed to this name.
      - At least one of O(name) and O(zone_id) is required.
    type: str
  zone_id:
    description:
      - ID of the zone, for example V(office). The entity is C(zone.<zone_id>).
      - Home Assistant generates the ID from the name on creation, so it can not be chosen.
      - With O(state=present) the zone must already exist.
    type: str
  state:
    description:
      - V(present) creates or updates the zone, V(absent) deletes it.
    type: str
    choices: [present, absent]
    default: present
  latitude:
    description:
      - Latitude of the center. Required to create a zone.
    type: float
  longitude:
    description:
      - Longitude of the center. Required to create a zone.
    type: float
  radius:
    description:
      - Radius in meters. Home Assistant uses V(100) when a zone is created without it.
    type: float
  passive:
    description:
      - A passive zone is only used for automations; its name is not used as the state of a person or tracker in it.
      - Home Assistant uses V(false) when a zone is created without it.
    type: bool
  icon:
    description:
      - Icon, for example V(mdi:briefcase).
      - Home Assistant does not allow removing the icon of a zone, only changing it.
    type: str
attributes:
  check_mode:
    support: full
    description: Reports the changes and the predicted zone without writing.
  diff_mode:
    support: full
    description: Shows the zone before and after the run.
  platform:
    platforms: all
    support: full
    description: The module talks to Home Assistant over the network from the controller.
seealso:
  - module: egors.homeassistant.zone_info
  - module: egors.homeassistant.core_config
"""

EXAMPLES = r"""
- name: Create a zone
  egors.homeassistant.zone:
    name: Office
    latitude: 60.1699
    longitude: 24.9384
    radius: 150
    icon: mdi:briefcase

- name: Make it passive
  egors.homeassistant.zone:
    name: Office
    passive: true

- name: Delete a zone
  egors.homeassistant.zone:
    name: Office
    state: absent
"""

RETURN = r"""
zone:
  description: The zone after the run (predicted in check mode), or an empty dictionary if it is absent.
  returned: always
  type: dict
  contains:
    zone_id:
      description: ID of the zone. Null for a zone that would be created in check mode.
      type: str
      sample: office
    name:
      description: Name of the zone.
      type: str
      sample: Office
    latitude:
      description: Latitude of the center.
      type: float
      sample: 60.1699
    longitude:
      description: Longitude of the center.
      type: float
      sample: 24.9384
    radius:
      description: Radius in meters. Null for a zone that would be created in check mode without it.
      type: float
      sample: 150.0
    passive:
      description: Whether the zone is passive. Null for a zone that would be created in check mode without it.
      type: bool
    icon:
      description: Icon, or null.
      type: str
"""

from ansible_collections.egors.homeassistant.plugins.module_utils.api import HomeAssistantModule
from ansible_collections.egors.homeassistant.plugins.module_utils.registry import Registry

STRINGS = ("icon",)
VALUES = ("latitude", "longitude", "radius", "passive")


def main():
    argument_spec = dict(
        name=dict(type="str"),
        zone_id=dict(type="str"),
        state=dict(type="str", choices=["present", "absent"], default="present"),
        latitude=dict(type="float"),
        longitude=dict(type="float"),
        radius=dict(type="float"),
        passive=dict(type="bool"),
        icon=dict(type="str"),
    )
    module = HomeAssistantModule(argument_spec, required_one_of=[("name", "zone_id")], supports_check_mode=True)
    Registry(module, "zone", "zone_id", STRINGS, values=VALUES, entry_key="id", unclearable=("icon",), required=("latitude", "longitude")).ensure("zone")


if __name__ == "__main__":
    main()

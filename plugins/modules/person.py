#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2026, Egor Sklyarov
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

DOCUMENTATION = r"""
module: person
short_description: Manage Home Assistant people
version_added: 0.1.0
author: Egor Sklyarov (@Egor-S)
description:
  - Creates, updates and deletes people created in the UI or over the API.
  - Only the options that are set are managed; other properties of an existing person are left unchanged.
  - The person is found by O(person_id) if given, otherwise by O(name), ignoring case and surrounding or repeated whitespace.
    Home Assistant allows several people with the same name; the module fails if the name matches more than one, then use O(person_id).
  - People defined in C(configuration.yaml) are not visible to this module.
extends_documentation_fragment:
  - egors.homeassistant.connection
options:
  name:
    description:
      - Name of the person. Required to create a person.
      - If O(person_id) is also given, an existing person is renamed to this name.
      - At least one of O(name) and O(person_id) is required.
    type: str
  person_id:
    description:
      - ID of the person, for example V(jane). The entity is C(person.<person_id>).
      - Home Assistant generates the ID from the name on creation, so it can not be chosen.
      - With O(state=present) the person must already exist.
    type: str
  state:
    description:
      - V(present) creates or updates the person, V(absent) deletes it.
    type: str
    choices: [present, absent]
    default: present
  user_id:
    description:
      - ID of the Home Assistant user who is this person, so that the person can log in. An empty string unlinks the user.
      - A user can be linked to one person only.
    type: str
  device_trackers:
    description:
      - Entity IDs of the device trackers that locate the person, for example V(device_tracker.phone).
        Compared as a set (order and duplicates are ignored). An empty list removes all trackers.
    type: list
    elements: str
  picture:
    description:
      - URL or path of the picture. An empty string removes it.
    type: str
attributes:
  check_mode:
    support: full
    description: Reports the changes and the predicted person without writing.
  diff_mode:
    support: full
    description: Shows the person before and after the run.
  platform:
    platforms: all
    support: full
    description: The module talks to Home Assistant over the network from the controller.
seealso:
  - module: egors.homeassistant.person_info
"""

EXAMPLES = r"""
- name: Create a person tracked by a phone
  egors.homeassistant.person:
    name: Jane
    device_trackers:
      - device_tracker.jane_phone

- name: Delete a person
  egors.homeassistant.person:
    name: Jane
    state: absent
"""

RETURN = r"""
person:
  description: The person after the run (predicted in check mode), or an empty dictionary if it is absent.
  returned: always
  type: dict
  contains:
    person_id:
      description: ID of the person. Null for a person that would be created in check mode.
      type: str
      sample: jane
    name:
      description: Name of the person.
      type: str
      sample: Jane
    user_id:
      description: ID of the linked user, or null.
      type: str
    device_trackers:
      description: Sorted entity IDs of the device trackers.
      type: list
      elements: str
    picture:
      description: Picture, or null.
      type: str
"""

from ansible_collections.egors.homeassistant.plugins.module_utils.api import HomeAssistantModule
from ansible_collections.egors.homeassistant.plugins.module_utils.registry import Registry

STRINGS = ("user_id", "picture")
LISTS = ("device_trackers",)


def main():
    argument_spec = dict(
        name=dict(type="str"),
        person_id=dict(type="str"),
        state=dict(type="str", choices=["present", "absent"], default="present"),
        user_id=dict(type="str"),
        device_trackers=dict(type="list", elements="str"),
        picture=dict(type="str"),
    )
    module = HomeAssistantModule(argument_spec, required_one_of=[("name", "person_id")], supports_check_mode=True)
    Registry(module, "person", "person_id", STRINGS, LISTS, entry_key="id", list_key="storage").ensure("person")


if __name__ == "__main__":
    main()

#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2026, Egor Sklyarov
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

DOCUMENTATION = r"""
module: person_info
short_description: List Home Assistant people
version_added: 0.1.0
author: Egor Sklyarov (@Egor-S)
description:
  - Returns the people created in the UI or over the API, optionally filtered by name or ID.
  - People defined in C(configuration.yaml) are not included.
extends_documentation_fragment:
  - egors.homeassistant.connection
options:
  name:
    description:
      - Only return the people with this name, ignoring case and surrounding or repeated whitespace.
    type: str
  person_id:
    description:
      - Only return the person with this ID.
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
  - module: egors.homeassistant.person
"""

EXAMPLES = r"""
- name: List all people
  egors.homeassistant.person_info:
  register: result
"""

RETURN = r"""
people:
  description: Matching people in creation order, in the same format as the RV(egors.homeassistant.person#module:person) return value.
  returned: always
  type: list
  elements: dict
  sample:
    - person_id: jane
      name: Jane
      user_id: null
      device_trackers: [device_tracker.jane_phone]
      picture: null
"""

from ansible_collections.egors.homeassistant.plugins.module_utils.api import HomeAssistantModule
from ansible_collections.egors.homeassistant.plugins.module_utils.registry import Registry


STRINGS = ("user_id", "picture")
LISTS = ("device_trackers",)


def main():
    module = HomeAssistantModule(dict(name=dict(type="str"), person_id=dict(type="str")), supports_check_mode=True)
    Registry(module, "person", "person_id", STRINGS, LISTS, entry_key="id", list_key="storage").info("people")


if __name__ == "__main__":
    main()

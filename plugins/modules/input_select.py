#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2026, Egor Sklyarov
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

DOCUMENTATION = r"""
module: input_select
short_description: Manage Home Assistant dropdown (input_select) helpers
version_added: 0.1.0
author: Egor Sklyarov (@Egor-S)
description:
  - Creates, updates and deletes dropdowns created in the UI or over the API (Settings > Devices & services > Helpers).
  - Only the options that are set are managed; other settings of an existing dropdown are left unchanged.
  - O(options) is required to create a dropdown.
  - The dropdown is found by O(input_select_id) if given, otherwise by O(name), ignoring case and surrounding or repeated whitespace.
    Home Assistant allows several dropdowns with the same name; the module fails if the name matches more than one, then use O(input_select_id).
  - Helpers defined in C(configuration.yaml) are not visible to this module.
extends_documentation_fragment:
  - egors.homeassistant.connection
options:
  name:
    description:
      - Name of the dropdown. Required to create a dropdown.
      - If O(input_select_id) is also given, an existing dropdown is renamed to this name.
      - At least one of O(name) and O(input_select_id) is required.
    type: str
  input_select_id:
    description:
      - ID of the dropdown. The entity is C(input_select.<input_select_id>).
      - Home Assistant generates the ID from the name on creation, so it can not be chosen.
      - With O(state=present) the dropdown must already exist.
    type: str
  state:
    description:
      - V(present) creates or updates the dropdown, V(absent) deletes it.
    type: str
    choices: [present, absent]
    default: present
  icon:
    description:
      - Icon, for example V(mdi:format-list-bulleted). An empty string removes the icon.
    type: str
  options:
    description:
      - Choices in the order they are shown. Required to create a dropdown; the order is compared too and duplicates fail.
    type: list
    elements: str
  initial:
    description:
      - Option selected at startup. Without it the selection from before the restart is restored. An empty string removes it.
    type: str
attributes:
  check_mode:
    support: full
    description: Reports the changes and the predicted dropdown without writing.
  diff_mode:
    support: full
    description: Shows the dropdown before and after the run.
  platform:
    platforms: all
    support: full
    description: The module talks to Home Assistant over the network from the controller.
seealso:
  - module: egors.homeassistant.helper_info
"""

EXAMPLES = r"""
- name: Create a dropdown
  egors.homeassistant.input_select:
    name: House mode
    options: [Home, Away, Night]

- name: Delete it
  egors.homeassistant.input_select:
    name: House mode
    state: absent
"""

RETURN = r"""
input_select:
  description: The dropdown after the run (predicted in check mode), or an empty dictionary if it is absent.
  returned: always
  type: dict
  contains:
    input_select_id:
      description: ID of the dropdown. Null for a dropdown that would be created in check mode.
      type: str
    name:
      description: Name of the dropdown.
      type: str
      sample: House mode
    icon:
      description: Icon, or null.
      type: str
    options:
      description: Choices in their order.
      type: list
      elements: str
    initial:
      description: Option selected at startup, or null.
      type: str
"""

from ansible_collections.egors.homeassistant.plugins.module_utils.api import HomeAssistantModule
from ansible_collections.egors.homeassistant.plugins.module_utils.helpers import helper_registry


def main():
    argument_spec = dict(
        name=dict(type="str"),
        input_select_id=dict(type="str"),
        state=dict(type="str", choices=["present", "absent"], default="present"),
        icon=dict(type="str"),
        options=dict(type="list", elements="str"),
        initial=dict(type="str"),
    )
    module = HomeAssistantModule(argument_spec, required_one_of=[("name", "input_select_id")], supports_check_mode=True)
    helper_registry(module, "input_select").ensure("input_select")


if __name__ == "__main__":
    main()

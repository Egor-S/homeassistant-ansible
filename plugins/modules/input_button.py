#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2026, Egor Sklyarov
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

DOCUMENTATION = r"""
module: input_button
short_description: Manage Home Assistant button (input_button) helpers
version_added: 0.1.0
author: Egor Sklyarov (@Egor-S)
description:
  - Creates, updates and deletes buttons created in the UI or over the API (Settings > Devices & services > Helpers).
  - Only the options that are set are managed; other settings of an existing button are left unchanged.
  - The button is found by O(input_button_id) if given, otherwise by O(name), ignoring case and surrounding or repeated whitespace.
    Home Assistant allows several buttons with the same name; the module fails if the name matches more than one, then use O(input_button_id).
  - Helpers defined in C(configuration.yaml) are not visible to this module.
extends_documentation_fragment:
  - egors.homeassistant.connection
options:
  name:
    description:
      - Name of the button. Required to create a button.
      - If O(input_button_id) is also given, an existing button is renamed to this name.
      - At least one of O(name) and O(input_button_id) is required.
    type: str
  input_button_id:
    description:
      - ID of the button. The entity is C(input_button.<input_button_id>).
      - Home Assistant generates the ID from the name on creation, so it can not be chosen.
      - With O(state=present) the button must already exist.
    type: str
  state:
    description:
      - V(present) creates or updates the button, V(absent) deletes it.
    type: str
    choices: [present, absent]
    default: present
  icon:
    description:
      - Icon, for example V(mdi:gesture-tap-button). An empty string removes the icon.
    type: str
attributes:
  check_mode:
    support: full
    description: Reports the changes and the predicted button without writing.
  diff_mode:
    support: full
    description: Shows the button before and after the run.
  platform:
    platforms: all
    support: full
    description: The module talks to Home Assistant over the network from the controller.
seealso:
  - module: egors.homeassistant.helper_info
"""

EXAMPLES = r"""
- name: Create a button
  egors.homeassistant.input_button:
    name: Ring bell
    icon: mdi:bell

- name: Delete it
  egors.homeassistant.input_button:
    name: Ring bell
    state: absent
"""

RETURN = r"""
input_button:
  description: The button after the run (predicted in check mode), or an empty dictionary if it is absent.
  returned: always
  type: dict
  contains:
    input_button_id:
      description: ID of the button. Null for a button that would be created in check mode.
      type: str
    name:
      description: Name of the button.
      type: str
      sample: Ring bell
    icon:
      description: Icon, or null.
      type: str
"""

from ansible_collections.egors.homeassistant.plugins.module_utils.api import HomeAssistantModule
from ansible_collections.egors.homeassistant.plugins.module_utils.helpers import helper_registry


def main():
    argument_spec = dict(
        name=dict(type="str"),
        input_button_id=dict(type="str"),
        state=dict(type="str", choices=["present", "absent"], default="present"),
        icon=dict(type="str"),
    )
    module = HomeAssistantModule(argument_spec, required_one_of=[("name", "input_button_id")], supports_check_mode=True)
    helper_registry(module, "input_button").ensure("input_button")


if __name__ == "__main__":
    main()

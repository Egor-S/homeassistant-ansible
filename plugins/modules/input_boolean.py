#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2026, Egor Sklyarov
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

DOCUMENTATION = r"""
module: input_boolean
short_description: Manage Home Assistant toggle (input_boolean) helpers
version_added: 0.1.0
author: Egor Sklyarov (@Egor-S)
description:
  - Creates, updates and deletes toggles created in the UI or over the API (Settings > Devices & services > Helpers).
  - Only the options that are set are managed; other settings of an existing toggle are left unchanged.
  - The toggle is found by O(input_boolean_id) if given, otherwise by O(name), ignoring case and surrounding or repeated whitespace.
    Home Assistant allows several toggles with the same name; the module fails if the name matches more than one, then use O(input_boolean_id).
  - Helpers defined in C(configuration.yaml) are not visible to this module.
extends_documentation_fragment:
  - egors.homeassistant.connection
options:
  name:
    description:
      - Name of the toggle. Required to create a toggle.
      - If O(input_boolean_id) is also given, an existing toggle is renamed to this name.
      - At least one of O(name) and O(input_boolean_id) is required.
    type: str
  input_boolean_id:
    description:
      - ID of the toggle. The entity is C(input_boolean.<input_boolean_id>).
      - Home Assistant generates the ID from the name on creation, so it can not be chosen.
      - With O(state=present) the toggle must already exist.
    type: str
  state:
    description:
      - V(present) creates or updates the toggle, V(absent) deletes it.
    type: str
    choices: [present, absent]
    default: present
  icon:
    description:
      - Icon, for example V(mdi:toggle-switch). An empty string removes the icon.
    type: str
  initial:
    description:
      - State at startup. Without it the state from before the restart is restored.
    type: bool
attributes:
  check_mode:
    support: full
    description: Reports the changes and the predicted toggle without writing.
  diff_mode:
    support: full
    description: Shows the toggle before and after the run.
  platform:
    platforms: all
    support: full
    description: The module talks to Home Assistant over the network from the controller.
seealso:
  - module: egors.homeassistant.helper_info
"""

EXAMPLES = r"""
- name: Create a toggle
  egors.homeassistant.input_boolean:
    name: Guest mode
    icon: mdi:account-multiple

- name: Delete it
  egors.homeassistant.input_boolean:
    name: Guest mode
    state: absent
"""

RETURN = r"""
input_boolean:
  description: The toggle after the run (predicted in check mode), or an empty dictionary if it is absent.
  returned: always
  type: dict
  contains:
    input_boolean_id:
      description: ID of the toggle. Null for a toggle that would be created in check mode.
      type: str
    name:
      description: Name of the toggle.
      type: str
      sample: Guest mode
    icon:
      description: Icon, or null.
      type: str
    initial:
      description: State at startup, or null.
      type: bool
"""

from ansible_collections.egors.homeassistant.plugins.module_utils.api import HomeAssistantModule
from ansible_collections.egors.homeassistant.plugins.module_utils.helpers import helper_registry


def main():
    argument_spec = dict(
        name=dict(type="str"),
        input_boolean_id=dict(type="str"),
        state=dict(type="str", choices=["present", "absent"], default="present"),
        icon=dict(type="str"),
        initial=dict(type="bool"),
    )
    module = HomeAssistantModule(argument_spec, required_one_of=[("name", "input_boolean_id")], supports_check_mode=True)
    helper_registry(module, "input_boolean").ensure("input_boolean")


if __name__ == "__main__":
    main()

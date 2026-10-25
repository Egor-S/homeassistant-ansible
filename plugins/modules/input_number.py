#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2026, Egor Sklyarov
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

DOCUMENTATION = r"""
module: input_number
short_description: Manage Home Assistant number (input_number) helpers
version_added: 0.1.0
author: Egor Sklyarov (@Egor-S)
description:
  - Creates, updates and deletes numbers created in the UI or over the API (Settings > Devices & services > Helpers).
  - Only the options that are set are managed; other settings of an existing number are left unchanged.
  - O(min) and O(max) are required to create a number.
  - The number is found by O(input_number_id) if given, otherwise by O(name), ignoring case and surrounding or repeated whitespace.
    Home Assistant allows several numbers with the same name; the module fails if the name matches more than one, then use O(input_number_id).
  - Helpers defined in C(configuration.yaml) are not visible to this module.
extends_documentation_fragment:
  - egors.homeassistant.connection
options:
  name:
    description:
      - Name of the number. Required to create a number.
      - If O(input_number_id) is also given, an existing number is renamed to this name.
      - At least one of O(name) and O(input_number_id) is required.
    type: str
  input_number_id:
    description:
      - ID of the number. The entity is C(input_number.<input_number_id>).
      - Home Assistant generates the ID from the name on creation, so it can not be chosen.
      - With O(state=present) the number must already exist.
    type: str
  state:
    description:
      - V(present) creates or updates the number, V(absent) deletes it.
    type: str
    choices: [present, absent]
    default: present
  icon:
    description:
      - Icon, for example V(mdi:thermometer). An empty string removes the icon.
    type: str
  min:
    description:
      - Minimum value. Required to create a number.
    type: float
  max:
    description:
      - Maximum value. Required to create a number.
    type: float
  step:
    description:
      - Step between values. Home Assistant uses V(1) when a number is created without it.
    type: float
  initial:
    description:
      - Value at startup. Without it the value from before the restart is restored.
      - Once set it can only be changed, not removed.
    type: float
  mode:
    description:
      - Shown as a V(slider) or an input V(box). Home Assistant uses V(slider) when a number is created without it.
    type: str
    choices: [box, slider]
  unit_of_measurement:
    description:
      - Unit, for example V(°C). An empty string removes it.
    type: str
attributes:
  check_mode:
    support: full
    description: Reports the changes and the predicted number without writing.
  diff_mode:
    support: full
    description: Shows the number before and after the run.
  platform:
    platforms: all
    support: full
    description: The module talks to Home Assistant over the network from the controller.
seealso:
  - module: egors.homeassistant.helper_info
"""

EXAMPLES = r"""
- name: Create a number
  egors.homeassistant.input_number:
    name: Target temperature
    min: 15
    max: 25
    step: 0.5
    unit_of_measurement: °C

- name: Delete it
  egors.homeassistant.input_number:
    name: Target temperature
    state: absent
"""

RETURN = r"""
input_number:
  description: The number after the run (predicted in check mode), or an empty dictionary if it is absent.
  returned: always
  type: dict
  contains:
    input_number_id:
      description: ID of the number. Null for a number that would be created in check mode.
      type: str
    name:
      description: Name of the number.
      type: str
      sample: Target temperature
    icon:
      description: Icon, or null.
      type: str
    min:
      description: Minimum value.
      type: float
    max:
      description: Maximum value.
      type: float
    step:
      description: Step between values.
      type: float
    initial:
      description: Value at startup, or null.
      type: float
    mode:
      description: V(box) or V(slider).
      type: str
    unit_of_measurement:
      description: Unit, or null.
      type: str
"""

from ansible_collections.egors.homeassistant.plugins.module_utils.api import HomeAssistantModule
from ansible_collections.egors.homeassistant.plugins.module_utils.helpers import helper_registry


def main():
    argument_spec = dict(
        name=dict(type="str"),
        input_number_id=dict(type="str"),
        state=dict(type="str", choices=["present", "absent"], default="present"),
        icon=dict(type="str"),
        min=dict(type="float"),
        max=dict(type="float"),
        step=dict(type="float"),
        initial=dict(type="float"),
        mode=dict(type="str", choices=["box", "slider"]),
        unit_of_measurement=dict(type="str"),
    )
    module = HomeAssistantModule(argument_spec, required_one_of=[("name", "input_number_id")], supports_check_mode=True)
    helper_registry(module, "input_number").ensure("input_number")


if __name__ == "__main__":
    main()

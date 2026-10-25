#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2026, Egor Sklyarov
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

DOCUMENTATION = r"""
module: helper_info
short_description: List Home Assistant helpers of one type
version_added: 0.1.0
author: Egor Sklyarov (@Egor-S)
description:
  - Returns the helpers of one type created in the UI or over the API, optionally filtered by name or ID.
  - Helpers defined in C(configuration.yaml) are not included.
extends_documentation_fragment:
  - egors.homeassistant.connection
options:
  type:
    description:
      - Type of the helpers, the name of the module that manages them.
    type: str
    required: true
    choices: [counter, input_boolean, input_button, input_datetime, input_number, input_select, input_text, schedule, timer]
  name:
    description:
      - Only return the helpers with this name, ignoring case and surrounding or repeated whitespace.
    type: str
  helper_id:
    description:
      - Only return the helper with this ID, for example V(guest_mode) for C(input_boolean.guest_mode).
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
  - module: egors.homeassistant.counter
  - module: egors.homeassistant.input_boolean
  - module: egors.homeassistant.input_button
  - module: egors.homeassistant.input_datetime
  - module: egors.homeassistant.input_number
  - module: egors.homeassistant.input_select
  - module: egors.homeassistant.input_text
  - module: egors.homeassistant.schedule
  - module: egors.homeassistant.timer
"""

EXAMPLES = r"""
- name: List all toggles
  egors.homeassistant.helper_info:
    type: input_boolean
  register: result

- name: Get a counter by name
  egors.homeassistant.helper_info:
    type: counter
    name: Coffees
  register: coffees
"""

RETURN = r"""
helpers:
  description:
    - Matching helpers in creation order, in the same format as the return value of the module of that type,
      for example RV(egors.homeassistant.counter#module:counter).
    - The ID is returned as C(<type>_id), for example C(counter_id).
  returned: always
  type: list
  elements: dict
  sample:
    - counter_id: coffees
      name: Coffees
      icon: null
      initial: 0
      step: 1
      minimum: 0
      maximum: null
      restore: true
"""

from ansible_collections.egors.homeassistant.plugins.module_utils.api import HomeAssistantModule
from ansible_collections.egors.homeassistant.plugins.module_utils.helpers import HELPERS, helper_registry


def main():
    argument_spec = dict(
        type=dict(type="str", required=True, choices=sorted(HELPERS)),
        name=dict(type="str"),
        helper_id=dict(type="str"),
    )
    module = HomeAssistantModule(argument_spec, supports_check_mode=True)
    helper_registry(module, module.params["type"]).info("helpers", id_param="helper_id")


if __name__ == "__main__":
    main()

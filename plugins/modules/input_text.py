#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2026, Egor Sklyarov
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

DOCUMENTATION = r"""
module: input_text
short_description: Manage Home Assistant text (input_text) helpers
version_added: 0.1.0
author: Egor Sklyarov (@Egor-S)
description:
  - Creates, updates and deletes texts created in the UI or over the API (Settings > Devices & services > Helpers).
  - Only the options that are set are managed; other settings of an existing text are left unchanged.
  - The text is found by O(input_text_id) if given, otherwise by O(name), ignoring case and surrounding or repeated whitespace.
    Home Assistant allows several texts with the same name; the module fails if the name matches more than one, then use O(input_text_id).
  - Helpers defined in C(configuration.yaml) are not visible to this module.
extends_documentation_fragment:
  - egors.homeassistant.connection
options:
  name:
    description:
      - Name of the text. Required to create a text.
      - If O(input_text_id) is also given, an existing text is renamed to this name.
      - At least one of O(name) and O(input_text_id) is required.
    type: str
  input_text_id:
    description:
      - ID of the text. The entity is C(input_text.<input_text_id>).
      - Home Assistant generates the ID from the name on creation, so it can not be chosen.
      - With O(state=present) the text must already exist.
    type: str
  state:
    description:
      - V(present) creates or updates the text, V(absent) deletes it.
    type: str
    choices: [present, absent]
    default: present
  icon:
    description:
      - Icon, for example V(mdi:form-textbox). An empty string removes the icon.
    type: str
  min:
    description:
      - Minimum length. Home Assistant uses V(0) when a text is created without it.
    type: int
  max:
    description:
      - Maximum length, at most V(255). Home Assistant uses V(100) when a text is created without it.
    type: int
  mode:
    description:
      - Shown as plain V(text) or as a V(password) field. Home Assistant uses V(text) when a text is created without it.
    type: str
    choices: [text, password]
  pattern:
    description:
      - Regular expression the value must match in the frontend. An empty string removes it.
    type: str
  initial:
    description:
      - Value at startup. Without it the value from before the restart is restored. An empty string removes it.
    type: str
  unit_of_measurement:
    description:
      - Unit. An empty string removes it.
    type: str
attributes:
  check_mode:
    support: full
    description: Reports the changes and the predicted text without writing.
  diff_mode:
    support: full
    description: Shows the text before and after the run.
  platform:
    platforms: all
    support: full
    description: The module talks to Home Assistant over the network from the controller.
seealso:
  - module: egors.homeassistant.helper_info
"""

EXAMPLES = r"""
- name: Create a text
  egors.homeassistant.input_text:
    name: Greeting
    max: 50
    initial: Hello

- name: Delete it
  egors.homeassistant.input_text:
    name: Greeting
    state: absent
"""

RETURN = r"""
input_text:
  description: The text after the run (predicted in check mode), or an empty dictionary if it is absent.
  returned: always
  type: dict
  contains:
    input_text_id:
      description: ID of the text. Null for a text that would be created in check mode.
      type: str
    name:
      description: Name of the text.
      type: str
      sample: Greeting
    icon:
      description: Icon, or null.
      type: str
    min:
      description: Minimum length.
      type: int
    max:
      description: Maximum length.
      type: int
    mode:
      description: V(text) or V(password).
      type: str
    pattern:
      description: Regular expression, or null.
      type: str
    initial:
      description: Value at startup, or null.
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
        input_text_id=dict(type="str"),
        state=dict(type="str", choices=["present", "absent"], default="present"),
        icon=dict(type="str"),
        min=dict(type="int"),
        max=dict(type="int"),
        mode=dict(type="str", choices=["text", "password"]),
        pattern=dict(type="str"),
        initial=dict(type="str"),
        unit_of_measurement=dict(type="str"),
    )
    module = HomeAssistantModule(argument_spec, required_one_of=[("name", "input_text_id")], supports_check_mode=True)
    helper_registry(module, "input_text").ensure("input_text")


if __name__ == "__main__":
    main()

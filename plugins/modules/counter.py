#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2026, Egor Sklyarov
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

DOCUMENTATION = r"""
module: counter
short_description: Manage Home Assistant counter helpers
version_added: 0.1.0
author: Egor Sklyarov (@Egor-S)
description:
  - Creates, updates and deletes counters created in the UI or over the API (Settings > Devices & services > Helpers).
  - Only the options that are set are managed; other settings of an existing counter are left unchanged.
  - The counter is found by O(counter_id) if given, otherwise by O(name), ignoring case and surrounding or repeated whitespace.
    Home Assistant allows several counters with the same name; the module fails if the name matches more than one, then use O(counter_id).
  - Helpers defined in C(configuration.yaml) are not visible to this module.
extends_documentation_fragment:
  - egors.homeassistant.connection
options:
  name:
    description:
      - Name of the counter. Required to create a counter.
      - If O(counter_id) is also given, an existing counter is renamed to this name.
      - At least one of O(name) and O(counter_id) is required.
    type: str
  counter_id:
    description:
      - ID of the counter. The entity is C(counter.<counter_id>).
      - Home Assistant generates the ID from the name on creation, so it can not be chosen.
      - With O(state=present) the counter must already exist.
    type: str
  state:
    description:
      - V(present) creates or updates the counter, V(absent) deletes it.
    type: str
    choices: [present, absent]
    default: present
  icon:
    description:
      - Icon, for example V(mdi:counter). An empty string removes the icon.
    type: str
  initial:
    description:
      - Value at startup and after a reset. Home Assistant uses V(0) when a counter is created without it.
    type: int
  step:
    description:
      - Increment, a positive integer. Home Assistant uses V(1) when a counter is created without it.
    type: int
  minimum:
    description:
      - Lowest value. An empty string removes it. Leaving the option out keeps the current minimum.
      - It is declared as V(raw) so that both an integer and an empty string are accepted; other values fail.
    type: raw
  maximum:
    description:
      - Highest value. An empty string removes it. Leaving the option out keeps the current maximum.
      - It is declared as V(raw) so that both an integer and an empty string are accepted; other values fail.
    type: raw
  restore:
    description:
      - Restore the value from before a restart instead of starting at O(initial).
        Home Assistant uses V(true) when a counter is created without it.
    type: bool
attributes:
  check_mode:
    support: full
    description: Reports the changes and the predicted counter without writing.
  diff_mode:
    support: full
    description: Shows the counter before and after the run.
  platform:
    platforms: all
    support: full
    description: The module talks to Home Assistant over the network from the controller.
seealso:
  - module: egors.homeassistant.helper_info
"""

EXAMPLES = r"""
- name: Create a counter
  egors.homeassistant.counter:
    name: Coffees
    step: 1
    minimum: 0

- name: Delete it
  egors.homeassistant.counter:
    name: Coffees
    state: absent
"""

RETURN = r"""
counter:
  description: The counter after the run (predicted in check mode), or an empty dictionary if it is absent.
  returned: always
  type: dict
  contains:
    counter_id:
      description: ID of the counter. Null for a counter that would be created in check mode.
      type: str
    name:
      description: Name of the counter.
      type: str
      sample: Coffees
    icon:
      description: Icon, or null.
      type: str
    initial:
      description: Value at startup and after a reset.
      type: int
    step:
      description: Increment.
      type: int
    minimum:
      description: Lowest value, or null.
      type: int
    maximum:
      description: Highest value, or null.
      type: int
    restore:
      description: Whether the value is restored after a restart.
      type: bool
"""

from ansible_collections.egors.homeassistant.plugins.module_utils.api import HomeAssistantModule
from ansible_collections.egors.homeassistant.plugins.module_utils.helpers import helper_registry


def main():
    argument_spec = dict(
        name=dict(type="str"),
        counter_id=dict(type="str"),
        state=dict(type="str", choices=["present", "absent"], default="present"),
        icon=dict(type="str"),
        initial=dict(type="int"),
        step=dict(type="int"),
        minimum=dict(type="raw"),
        maximum=dict(type="raw"),
        restore=dict(type="bool"),
    )
    module = HomeAssistantModule(argument_spec, required_one_of=[("name", "counter_id")], supports_check_mode=True)
    helper_registry(module, "counter").ensure("counter")


if __name__ == "__main__":
    main()

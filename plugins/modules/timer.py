#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2026, Egor Sklyarov
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

DOCUMENTATION = r"""
module: timer
short_description: Manage Home Assistant timer helpers
version_added: 0.1.0
author: Egor Sklyarov (@Egor-S)
description:
  - Creates, updates and deletes timers created in the UI or over the API (Settings > Devices & services > Helpers).
  - Only the options that are set are managed; other settings of an existing timer are left unchanged.
  - The timer is found by O(timer_id) if given, otherwise by O(name), ignoring case and surrounding or repeated whitespace.
    Home Assistant allows several timers with the same name; the module fails if the name matches more than one, then use O(timer_id).
  - Helpers defined in C(configuration.yaml) are not visible to this module.
extends_documentation_fragment:
  - egors.homeassistant.connection
options:
  name:
    description:
      - Name of the timer. Required to create a timer.
      - If O(timer_id) is also given, an existing timer is renamed to this name.
      - At least one of O(name) and O(timer_id) is required.
    type: str
  timer_id:
    description:
      - ID of the timer. The entity is C(timer.<timer_id>).
      - Home Assistant generates the ID from the name on creation, so it can not be chosen.
      - With O(state=present) the timer must already exist.
    type: str
  state:
    description:
      - V(present) creates or updates the timer, V(absent) deletes it.
    type: str
    choices: [present, absent]
    default: present
  icon:
    description:
      - Icon, for example V(mdi:timer). An empty string removes the icon.
    type: str
  duration:
    description:
      - Default duration, as seconds (V(90)) or V(H:MM) / V(H:MM:SS) (V(0:01:30)).
        Home Assistant uses V(0:00:00) when a timer is created without it.
      - It is compared in the form Home Assistant stores, V(H:MM:SS), so V(90), V(0:01:30) and V(00:01:30) are the same.
    type: str
  restore:
    description:
      - Restore a running timer after a restart. Home Assistant uses V(false) when a timer is created without it.
    type: bool
attributes:
  check_mode:
    support: full
    description: Reports the changes and the predicted timer without writing.
  diff_mode:
    support: full
    description: Shows the timer before and after the run.
  platform:
    platforms: all
    support: full
    description: The module talks to Home Assistant over the network from the controller.
seealso:
  - module: egors.homeassistant.helper_info
"""

EXAMPLES = r"""
- name: Create a timer
  egors.homeassistant.timer:
    name: Tea
    duration: "0:04:00"

- name: Delete it
  egors.homeassistant.timer:
    name: Tea
    state: absent
"""

RETURN = r"""
timer:
  description: The timer after the run (predicted in check mode), or an empty dictionary if it is absent.
  returned: always
  type: dict
  contains:
    timer_id:
      description: ID of the timer. Null for a timer that would be created in check mode.
      type: str
    name:
      description: Name of the timer.
      type: str
    icon:
      description: Icon, or null.
      type: str
    duration:
      description: Default duration as V(H:MM:SS).
      type: str
      sample: "0:04:00"
    restore:
      description: Whether a running timer is restored after a restart.
      type: bool
"""

from ansible_collections.egors.homeassistant.plugins.module_utils.api import HomeAssistantModule
from ansible_collections.egors.homeassistant.plugins.module_utils.helpers import helper_registry


def main():
    argument_spec = dict(
        name=dict(type="str"),
        timer_id=dict(type="str"),
        state=dict(type="str", choices=["present", "absent"], default="present"),
        icon=dict(type="str"),
        duration=dict(type="str"),
        restore=dict(type="bool"),
    )
    module = HomeAssistantModule(argument_spec, required_one_of=[("name", "timer_id")], supports_check_mode=True)
    helper_registry(module, "timer").ensure("timer")


if __name__ == "__main__":
    main()

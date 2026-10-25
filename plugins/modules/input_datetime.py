#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2026, Egor Sklyarov
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

DOCUMENTATION = r"""
module: input_datetime
short_description: Manage Home Assistant date and/or time (input_datetime) helpers
version_added: 0.1.0
author: Egor Sklyarov (@Egor-S)
description:
  - Creates, updates and deletes dates and times created in the UI or over the API (Settings > Devices & services > Helpers).
  - Only the options that are set are managed; other settings of an existing date/time are left unchanged.
  - At least one of O(has_date) and O(has_time) must be V(true) to create a date/time.
  - The date/time is found by O(input_datetime_id) if given, otherwise by O(name), ignoring case and surrounding or repeated whitespace.
    Home Assistant allows several dates and times with the same name; the module fails if the name matches more than one, then use O(input_datetime_id).
  - Helpers defined in C(configuration.yaml) are not visible to this module.
extends_documentation_fragment:
  - egors.homeassistant.connection
options:
  name:
    description:
      - Name of the date/time. Required to create a date/time.
      - If O(input_datetime_id) is also given, an existing date/time is renamed to this name.
      - At least one of O(name) and O(input_datetime_id) is required.
    type: str
  input_datetime_id:
    description:
      - ID of the date/time. The entity is C(input_datetime.<input_datetime_id>).
      - Home Assistant generates the ID from the name on creation, so it can not be chosen.
      - With O(state=present) the date/time must already exist.
    type: str
  state:
    description:
      - V(present) creates or updates the date/time, V(absent) deletes it.
    type: str
    choices: [present, absent]
    default: present
  icon:
    description:
      - Icon, for example V(mdi:calendar-clock). An empty string removes the icon.
    type: str
  has_date:
    description:
      - Whether it holds a date. Home Assistant uses V(false) when it is created without it.
    type: bool
  has_time:
    description:
      - Whether it holds a time. Home Assistant uses V(false) when it is created without it.
    type: bool
  initial:
    description:
      - Value at startup, for example V(07:30), V(2026-12-24) or V(2026-12-24 07:30) depending on O(has_date) and O(has_time).
        Without it the value from before the restart is restored. An empty string removes it.
      - Home Assistant stores the text as given, so it is compared as given.
    type: str
attributes:
  check_mode:
    support: full
    description: Reports the changes and the predicted date/time without writing.
  diff_mode:
    support: full
    description: Shows the date/time before and after the run.
  platform:
    platforms: all
    support: full
    description: The module talks to Home Assistant over the network from the controller.
seealso:
  - module: egors.homeassistant.helper_info
"""

EXAMPLES = r"""
- name: Create a time
  egors.homeassistant.input_datetime:
    name: Wake up
    has_time: true
    initial: "07:00"

- name: Delete it
  egors.homeassistant.input_datetime:
    name: Wake up
    state: absent
"""

RETURN = r"""
input_datetime:
  description: The date/time after the run (predicted in check mode), or an empty dictionary if it is absent.
  returned: always
  type: dict
  contains:
    input_datetime_id:
      description: ID of the date/time. Null for a date/time that would be created in check mode.
      type: str
    name:
      description: Name of the date/time.
      type: str
    icon:
      description: Icon, or null.
      type: str
    has_date:
      description: Whether it holds a date.
      type: bool
    has_time:
      description: Whether it holds a time.
      type: bool
    initial:
      description: Value at startup, or null.
      type: str
"""

from ansible_collections.egors.homeassistant.plugins.module_utils.api import HomeAssistantModule
from ansible_collections.egors.homeassistant.plugins.module_utils.helpers import helper_registry


def main():
    argument_spec = dict(
        name=dict(type="str"),
        input_datetime_id=dict(type="str"),
        state=dict(type="str", choices=["present", "absent"], default="present"),
        icon=dict(type="str"),
        has_date=dict(type="bool"),
        has_time=dict(type="bool"),
        initial=dict(type="str"),
    )
    module = HomeAssistantModule(argument_spec, required_one_of=[("name", "input_datetime_id")], supports_check_mode=True)
    helper_registry(module, "input_datetime").ensure("input_datetime")


if __name__ == "__main__":
    main()

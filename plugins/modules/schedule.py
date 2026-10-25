#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2026, Egor Sklyarov
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

DOCUMENTATION = r"""
module: schedule
short_description: Manage Home Assistant weekly schedule helpers
version_added: 0.1.0
author: Egor Sklyarov (@Egor-S)
description:
  - Creates, updates and deletes schedules created in the UI or over the API (Settings > Devices & services > Helpers).
  - Only the options that are set are managed; other settings of an existing schedule are left unchanged.
  - The schedule is found by O(schedule_id) if given, otherwise by O(name), ignoring case and surrounding or repeated whitespace.
    Home Assistant allows several schedules with the same name; the module fails if the name matches more than one, then use O(schedule_id).
  - Helpers defined in C(configuration.yaml) are not visible to this module.
extends_documentation_fragment:
  - egors.homeassistant.connection
options:
  name:
    description:
      - Name of the schedule. Required to create a schedule.
      - If O(schedule_id) is also given, an existing schedule is renamed to this name.
      - At least one of O(name) and O(schedule_id) is required.
    type: str
  schedule_id:
    description:
      - ID of the schedule. The entity is C(schedule.<schedule_id>).
      - Home Assistant generates the ID from the name on creation, so it can not be chosen.
      - With O(state=present) the schedule must already exist.
    type: str
  state:
    description:
      - V(present) creates or updates the schedule, V(absent) deletes it.
    type: str
    choices: [present, absent]
    default: present
  icon:
    description:
      - Icon, for example V(mdi:calendar). An empty string removes the icon.
    type: str
  monday:
    description:
      - Time ranges on Monday during which the schedule is on. An empty list removes all ranges of the day.
      - A day that is left out keeps its ranges. The ranges are compared in the form Home Assistant stores
        (times as V(HH:MM:SS), sorted by start), so their order and the spelling of the times don't matter.
    type: list
    elements: dict
    suboptions: &time_range
      from:
        description: Start time, V(H:MM) or V(H:MM:SS).
        type: str
        required: true
      to:
        description: End time, V(H:MM) or V(H:MM:SS); V(24:00) is the end of the day.
        type: str
        required: true
      data:
        description: Extra attributes of the schedule entity while this range is active.
        type: dict
  tuesday:
    description:
      - Time ranges on Tuesday, see O(monday). An empty list removes all ranges of the day.
    type: list
    elements: dict
    suboptions: *time_range
  wednesday:
    description:
      - Time ranges on Wednesday, see O(monday). An empty list removes all ranges of the day.
    type: list
    elements: dict
    suboptions: *time_range
  thursday:
    description:
      - Time ranges on Thursday, see O(monday). An empty list removes all ranges of the day.
    type: list
    elements: dict
    suboptions: *time_range
  friday:
    description:
      - Time ranges on Friday, see O(monday). An empty list removes all ranges of the day.
    type: list
    elements: dict
    suboptions: *time_range
  saturday:
    description:
      - Time ranges on Saturday, see O(monday). An empty list removes all ranges of the day.
    type: list
    elements: dict
    suboptions: *time_range
  sunday:
    description:
      - Time ranges on Sunday, see O(monday). An empty list removes all ranges of the day.
    type: list
    elements: dict
    suboptions: *time_range
attributes:
  check_mode:
    support: full
    description: Reports the changes and the predicted schedule without writing.
  diff_mode:
    support: full
    description: Shows the schedule before and after the run.
  platform:
    platforms: all
    support: full
    description: The module talks to Home Assistant over the network from the controller.
seealso:
  - module: egors.homeassistant.helper_info
"""

EXAMPLES = r"""
- name: Working hours
  egors.homeassistant.schedule:
    name: Working hours
    monday: &workday
      - from: "9:00"
        to: "12:00"
      - from: "13:00"
        to: "17:30"
        data:
          location: office
    tuesday: *workday
    wednesday: *workday
    thursday: *workday
    friday: *workday

- name: Delete it
  egors.homeassistant.schedule:
    name: Working hours
    state: absent
"""

RETURN = r"""
schedule:
  description: The schedule after the run (predicted in check mode), or an empty dictionary if it is absent.
  returned: always
  type: dict
  contains:
    schedule_id:
      description: ID of the schedule. Null for a schedule that would be created in check mode.
      type: str
    name:
      description: Name of the schedule.
      type: str
    icon:
      description: Icon, or null.
      type: str
    monday:
      description: Time ranges, sorted by start, with C(from) and C(to) as V(HH:MM:SS) and C(data) if set.
      type: list
      elements: dict
    tuesday:
      description: Time ranges, sorted by start, with C(from) and C(to) as V(HH:MM:SS) and C(data) if set.
      type: list
      elements: dict
    wednesday:
      description: Time ranges, sorted by start, with C(from) and C(to) as V(HH:MM:SS) and C(data) if set.
      type: list
      elements: dict
    thursday:
      description: Time ranges, sorted by start, with C(from) and C(to) as V(HH:MM:SS) and C(data) if set.
      type: list
      elements: dict
    friday:
      description: Time ranges, sorted by start, with C(from) and C(to) as V(HH:MM:SS) and C(data) if set.
      type: list
      elements: dict
    saturday:
      description: Time ranges, sorted by start, with C(from) and C(to) as V(HH:MM:SS) and C(data) if set.
      type: list
      elements: dict
    sunday:
      description: Time ranges, sorted by start, with C(from) and C(to) as V(HH:MM:SS) and C(data) if set.
      type: list
      elements: dict
"""

from ansible_collections.egors.homeassistant.plugins.module_utils.api import HomeAssistantModule
from ansible_collections.egors.homeassistant.plugins.module_utils.helpers import WEEKDAYS, helper_registry


def main():
    time_range = dict(type="list", elements="dict", options=dict(
        dict((key, dict(type="str", required=True)) for key in ("from", "to")), data=dict(type="dict")))
    argument_spec = dict(
        name=dict(type="str"),
        schedule_id=dict(type="str"),
        state=dict(type="str", choices=["present", "absent"], default="present"),
        icon=dict(type="str"),
        **dict((day, time_range) for day in WEEKDAYS)
    )
    module = HomeAssistantModule(argument_spec, required_one_of=[("name", "schedule_id")], supports_check_mode=True)
    helper_registry(module, "schedule").ensure("schedule")


if __name__ == "__main__":
    main()

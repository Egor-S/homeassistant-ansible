#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2026, Egor Sklyarov
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

DOCUMENTATION = r"""
module: label
short_description: Manage labels in the Home Assistant label registry
version_added: 0.1.0
author: Egor Sklyarov (@Egor-S)
description:
  - Creates, updates and deletes labels.
  - Only the options that are set are managed; other properties of an existing label are left unchanged.
  - The label is found by O(label_id) if given, otherwise by O(name), ignoring case and surrounding or repeated whitespace.
  - Labels are assigned to areas with the O(egors.homeassistant.area#module:area:labels) option of the area module.
extends_documentation_fragment:
  - egors.homeassistant.connection
options:
  name:
    description:
      - Name of the label. Required to create a label.
      - If O(label_id) is also given, an existing label is renamed to this name.
      - At least one of O(name) and O(label_id) is required.
    type: str
  label_id:
    description:
      - ID of the label, for example V(outdoor).
      - Home Assistant generates the ID from the name on creation, so it can not be chosen.
      - With O(state=present) the label must already exist.
    type: str
  state:
    description:
      - V(present) creates or updates the label, V(absent) deletes it.
    type: str
    choices: [present, absent]
    default: present
  icon:
    description:
      - Icon, for example V(mdi:tag). An empty string removes the icon.
    type: str
  color:
    description:
      - Color, either a hex value like V(#ff0000) or a theme color such as V(red), V(light-blue) or V(primary).
      - An empty string removes the color.
    type: str
  description:
    description:
      - Description of the label. An empty string removes it.
    type: str
attributes:
  check_mode:
    support: full
    description: Reports the changes and the predicted label without writing.
  diff_mode:
    support: full
    description: Shows the label before and after the run.
  platform:
    platforms: all
    support: full
    description: The module talks to Home Assistant over the network from the controller.
seealso:
  - module: egors.homeassistant.label_info
  - module: egors.homeassistant.area
"""

EXAMPLES = r"""
- name: Create a label
  egors.homeassistant.label:
    name: Outdoor
    icon: mdi:tree
    color: green
    description: Everything outside the house

- name: Rename a label
  egors.homeassistant.label:
    label_id: outdoor
    name: Garden

- name: Delete a label
  egors.homeassistant.label:
    name: Garden
    state: absent
"""

RETURN = r"""
label:
  description: The label after the run (predicted in check mode), or an empty dictionary if it is absent.
  returned: always
  type: dict
  contains:
    label_id:
      description: ID of the label. Null for a label that would be created in check mode.
      type: str
      sample: outdoor
    name:
      description: Name of the label.
      type: str
      sample: Outdoor
    icon:
      description: Icon, or null.
      type: str
    color:
      description: Color, or null.
      type: str
      sample: green
    description:
      description: Description, or null.
      type: str
"""

from ansible_collections.egors.homeassistant.plugins.module_utils.api import HomeAssistantModule
from ansible_collections.egors.homeassistant.plugins.module_utils.registry import Registry

STRINGS = ("icon", "color", "description")


def main():
    argument_spec = dict(
        name=dict(type="str"),
        label_id=dict(type="str"),
        state=dict(type="str", choices=["present", "absent"], default="present"),
        icon=dict(type="str"),
        color=dict(type="str"),
        description=dict(type="str"),
    )
    module = HomeAssistantModule(argument_spec, required_one_of=[("name", "label_id")], supports_check_mode=True)
    Registry(module, "config/label_registry", "label_id", STRINGS).ensure("label")


if __name__ == "__main__":
    main()

#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2026, Egor Sklyarov
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

DOCUMENTATION = r"""
module: category
short_description: Manage Home Assistant categories
version_added: 0.1.0
author: Egor Sklyarov (@Egor-S)
description:
  - Creates, updates and deletes categories. Categories group the items of one table in the UI, such as automations or
    scripts; each category belongs to one O(scope).
  - Only the options that are set are managed; other properties of an existing category are left unchanged.
  - The category is found by O(category_id) if given, otherwise by O(name) within the O(scope), ignoring case and
    surrounding or repeated whitespace. Home Assistant allows several categories with the same name; the module fails
    if the name matches more than one, then use O(category_id).
extends_documentation_fragment:
  - egors.homeassistant.connection
options:
  scope:
    description:
      - Table the category belongs to. The UI uses V(automation), V(script), V(scene) and V(helpers).
    type: str
    required: true
  name:
    description:
      - Name of the category. Required to create a category.
      - If O(category_id) is also given, an existing category is renamed to this name.
      - At least one of O(name) and O(category_id) is required.
    type: str
  category_id:
    description:
      - ID of the category. Home Assistant generates a random ID on creation, so it can not be chosen.
      - With O(state=present) the category must already exist.
    type: str
  state:
    description:
      - V(present) creates or updates the category, V(absent) deletes it.
    type: str
    choices: [present, absent]
    default: present
  icon:
    description:
      - Icon, for example V(mdi:lightbulb). An empty string removes the icon.
    type: str
attributes:
  check_mode:
    support: full
    description: Reports the changes and the predicted category without writing.
  diff_mode:
    support: full
    description: Shows the category before and after the run.
  platform:
    platforms: all
    support: full
    description: The module talks to Home Assistant over the network from the controller.
seealso:
  - module: egors.homeassistant.category_info
"""

EXAMPLES = r"""
- name: Create a category for automations
  egors.homeassistant.category:
    scope: automation
    name: Lighting
    icon: mdi:lightbulb

- name: Delete it
  egors.homeassistant.category:
    scope: automation
    name: Lighting
    state: absent
"""

RETURN = r"""
category:
  description: The category after the run (predicted in check mode), or an empty dictionary if it is absent.
  returned: always
  type: dict
  contains:
    category_id:
      description: ID of the category. Null for a category that would be created in check mode.
      type: str
      sample: 01M5T2G8G5SJB2Y4E2DAJGKVK0
    name:
      description: Name of the category.
      type: str
      sample: Lighting
    icon:
      description: Icon, or null.
      type: str
"""

from ansible_collections.egors.homeassistant.plugins.module_utils.api import HomeAssistantModule
from ansible_collections.egors.homeassistant.plugins.module_utils.registry import Registry

STRINGS = ("icon",)


def main():
    argument_spec = dict(
        scope=dict(type="str", required=True),
        name=dict(type="str"),
        category_id=dict(type="str"),
        state=dict(type="str", choices=["present", "absent"], default="present"),
        icon=dict(type="str"),
    )
    module = HomeAssistantModule(argument_spec, required_one_of=[("name", "category_id")], supports_check_mode=True)
    Registry(module, "config/category_registry", "category_id", STRINGS,
             common=dict(scope=module.params["scope"])).ensure("category")


if __name__ == "__main__":
    main()

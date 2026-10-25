#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2026, Egor Sklyarov
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

DOCUMENTATION = r"""
module: category_info
short_description: List Home Assistant categories of one scope
version_added: 0.1.0
author: Egor Sklyarov (@Egor-S)
description:
  - Returns the categories of one scope, optionally filtered by name or ID.
extends_documentation_fragment:
  - egors.homeassistant.connection
options:
  scope:
    description:
      - Table the categories belong to, for example V(automation), V(script), V(scene) or V(helpers).
    type: str
    required: true
  name:
    description:
      - Only return the categories with this name, ignoring case and surrounding or repeated whitespace.
    type: str
  category_id:
    description:
      - Only return the category with this ID.
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
  - module: egors.homeassistant.category
"""

EXAMPLES = r"""
- name: List the categories of automations
  egors.homeassistant.category_info:
    scope: automation
  register: result
"""

RETURN = r"""
categories:
  description: Matching categories in creation order, in the same format as the RV(egors.homeassistant.category#module:category) return value.
  returned: always
  type: list
  elements: dict
  sample:
    - category_id: 01M5T2G8G5SJB2Y4E2DAJGKVK0
      name: Lighting
      icon: mdi:lightbulb
"""

from ansible_collections.egors.homeassistant.plugins.module_utils.api import HomeAssistantModule
from ansible_collections.egors.homeassistant.plugins.module_utils.registry import Registry


STRINGS = ("icon",)


def main():
    argument_spec = dict(scope=dict(type="str", required=True), name=dict(type="str"), category_id=dict(type="str"))
    module = HomeAssistantModule(argument_spec, supports_check_mode=True)
    Registry(module, "config/category_registry", "category_id", STRINGS,
             common=dict(scope=module.params["scope"])).info("categories")


if __name__ == "__main__":
    main()

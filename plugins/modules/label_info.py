#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2026, Egor Sklyarov
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

DOCUMENTATION = r"""
module: label_info
short_description: List labels of the Home Assistant label registry
version_added: 0.1.0
author: Egor Sklyarov (@Egor-S)
description:
  - Returns the labels of the label registry, optionally filtered by name or ID.
extends_documentation_fragment:
  - egors.homeassistant.connection
options:
  name:
    description:
      - Only return the label with this name, ignoring case and surrounding or repeated whitespace.
    type: str
  label_id:
    description:
      - Only return the label with this ID.
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
  - module: egors.homeassistant.label
"""

EXAMPLES = r"""
- name: List all labels
  egors.homeassistant.label_info:
  register: result

- name: Get one label
  egors.homeassistant.label_info:
    name: Outdoor
  register: outdoor
"""

RETURN = r"""
labels:
  description: Matching labels in creation order, in the same format as the RV(egors.homeassistant.label#module:label) return value.
  returned: always
  type: list
  elements: dict
  sample:
    - label_id: outdoor
      name: Outdoor
      icon: mdi:tree
      color: green
      description: null
"""

from ansible_collections.egors.homeassistant.plugins.module_utils.api import HomeAssistantModule
from ansible_collections.egors.homeassistant.plugins.module_utils.registry import Registry


STRINGS = ("icon", "color", "description")


def main():
    module = HomeAssistantModule(dict(name=dict(type="str"), label_id=dict(type="str")), supports_check_mode=True)
    Registry(module, "config/label_registry", "label_id", STRINGS).info("labels")


if __name__ == "__main__":
    main()

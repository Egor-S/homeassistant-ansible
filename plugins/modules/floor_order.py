#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2026, Egor Sklyarov
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

DOCUMENTATION = r"""
module: floor_order
short_description: Set the order of Home Assistant floors
version_added: 0.1.0
author: Egor Sklyarov (@Egor-S)
description:
  - Sets the order in which floors are listed, as dragging them in the UI does.
  - The floors in O(order) come first, in that order; the others follow in their current order.
extends_documentation_fragment:
  - egors.homeassistant.connection
options:
  order:
    description:
      - IDs of the floors, for example V(ground_floor). Every ID must exist.
    type: list
    elements: str
    required: true
attributes:
  check_mode:
    support: full
    description: Reports the changes without writing.
  diff_mode:
    support: full
    description: Shows the order before and after the run.
  platform:
    platforms: all
    support: full
    description: The module talks to Home Assistant over the network from the controller.
seealso:
  - module: egors.homeassistant.floor
"""

EXAMPLES = r"""
- name: Put the most used floors first
  egors.homeassistant.floor_order:
    order: [ground_floor, first_floor]
"""

RETURN = r"""
order:
  description: IDs of all floors in their order after the run (predicted in check mode).
  returned: always
  type: list
  elements: str
"""

from ansible_collections.egors.homeassistant.plugins.module_utils.api import HomeAssistantModule
from ansible_collections.egors.homeassistant.plugins.module_utils.order import ensure_order


def main():
    module = HomeAssistantModule(dict(order=dict(type="list", elements="str", required=True)), supports_check_mode=True)
    ensure_order(module, "floor", "floor_id")


if __name__ == "__main__":
    main()

#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2026, Egor Sklyarov
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

DOCUMENTATION = r"""
module: tag_info
short_description: List Home Assistant tags
version_added: 0.1.0
author: Egor Sklyarov (@Egor-S)
description:
  - Returns the tags, optionally filtered by name or ID.
extends_documentation_fragment:
  - egors.homeassistant.connection
options:
  name:
    description:
      - Only return the tags with this name, ignoring case and surrounding or repeated whitespace.
    type: str
  tag_id:
    description:
      - Only return the tag with this ID.
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
  - module: egors.homeassistant.tag
"""

EXAMPLES = r"""
- name: List all tags
  egors.homeassistant.tag_info:
  register: result
"""

RETURN = r"""
tags:
  description: Matching tags, in the same format as the RV(egors.homeassistant.tag#module:tag) return value.
  returned: always
  type: list
  elements: dict
  sample:
    - tag_id: 04a2c3d2e15d80
      name: Front door
      description: Sticker inside the door frame
"""

from ansible_collections.egors.homeassistant.plugins.module_utils.api import HomeAssistantModule
from ansible_collections.egors.homeassistant.plugins.module_utils.registry import Registry


VALUES = ("description",)


def main():
    module = HomeAssistantModule(dict(name=dict(type="str"), tag_id=dict(type="str")), supports_check_mode=True)
    Registry(module, "tag", "tag_id", values=VALUES, entry_key="id").info("tags")


if __name__ == "__main__":
    main()

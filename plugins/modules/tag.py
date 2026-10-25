#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2026, Egor Sklyarov
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

DOCUMENTATION = r"""
module: tag
short_description: Manage Home Assistant tags (NFC tags and QR codes)
version_added: 0.1.0
author: Egor Sklyarov (@Egor-S)
description:
  - Creates, updates and deletes tags. A tag is identified by the ID written on the NFC tag or in the QR code,
    so it is always selected by O(tag_id), never by name.
  - Only the options that are set are managed; other properties of an existing tag are left unchanged.
extends_documentation_fragment:
  - egors.homeassistant.connection
options:
  tag_id:
    description:
      - ID of the tag, as scanned.
    type: str
    required: true
  state:
    description:
      - V(present) creates or updates the tag, V(absent) deletes it.
    type: str
    choices: [present, absent]
    default: present
  name:
    description:
      - Name of the tag. Without one, Home Assistant shows V(Tag <tag_id>). Once set it can only be changed, not removed.
    type: str
  description:
    description:
      - Description of the tag. An empty string empties it.
    type: str
attributes:
  check_mode:
    support: full
    description: Reports the changes and the predicted tag without writing.
  diff_mode:
    support: full
    description: Shows the tag before and after the run.
  platform:
    platforms: all
    support: full
    description: The module talks to Home Assistant over the network from the controller.
seealso:
  - module: egors.homeassistant.tag_info
"""

EXAMPLES = r"""
- name: Register the tag at the front door
  egors.homeassistant.tag:
    tag_id: 04a2c3d2e15d80
    name: Front door
    description: Sticker inside the door frame

- name: Delete a tag
  egors.homeassistant.tag:
    tag_id: 04a2c3d2e15d80
    state: absent
"""

RETURN = r"""
tag:
  description: The tag after the run (predicted in check mode), or an empty dictionary if it is absent.
  returned: always
  type: dict
  contains:
    tag_id:
      description: ID of the tag.
      type: str
      sample: 04a2c3d2e15d80
    name:
      description: Name of the tag (V(Tag <tag_id>) if it has none), or null for a tag that would be created in check mode without a name.
      type: str
      sample: Front door
    description:
      description: Description, or null.
      type: str
"""

from ansible_collections.egors.homeassistant.plugins.module_utils.api import HomeAssistantModule
from ansible_collections.egors.homeassistant.plugins.module_utils.registry import Registry

VALUES = ("description",)


def main():
    argument_spec = dict(
        tag_id=dict(type="str", required=True),
        state=dict(type="str", choices=["present", "absent"], default="present"),
        name=dict(type="str"),
        description=dict(type="str"),
    )
    module = HomeAssistantModule(argument_spec, supports_check_mode=True)
    Registry(module, "tag", "tag_id", values=VALUES, entry_key="id", create_with_id=True).ensure("tag")


if __name__ == "__main__":
    main()

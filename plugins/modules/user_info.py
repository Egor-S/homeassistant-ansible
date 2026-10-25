#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2026, Egor Sklyarov
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

DOCUMENTATION = r"""
module: user_info
short_description: List Home Assistant users
version_added: 0.1.0
author: Egor Sklyarov (@Egor-S)
description:
  - Returns the users who log in with a username and password, optionally filtered by username.
  - System users and users without a username are not included.
extends_documentation_fragment:
  - egors.homeassistant.connection
options:
  username:
    description:
      - Only return the user with this username.
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
  - module: egors.homeassistant.user
"""

EXAMPLES = r"""
- name: List all users
  egors.homeassistant.user_info:
  register: result
"""

RETURN = r"""
users:
  description: Matching users, in the same format as the RV(egors.homeassistant.user#module:user) return value.
  returned: always
  type: list
  elements: dict
  sample:
    - user_id: 7a77ae627f1d453c86ec7c977536c7fc
      username: admin
      name: Admin
      admin: true
      active: true
      local_only: false
      owner: true
"""

from ansible_collections.egors.homeassistant.plugins.module_utils.api import HomeAssistantModule
from ansible_collections.egors.homeassistant.plugins.module_utils.user import normalize


def main():
    module = HomeAssistantModule(dict(username=dict(type="str")), supports_check_mode=True)
    users = [u for u in module.call("config/auth/list") if u.get("username") and not u.get("system_generated")]
    if module.params["username"] is not None:
        users = [u for u in users if u["username"] == module.params["username"]]
    module.exit_json(changed=False, users=[normalize(u) for u in users])


if __name__ == "__main__":
    main()

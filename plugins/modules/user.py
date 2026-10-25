#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2026, Egor Sklyarov
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

DOCUMENTATION = r"""
module: user
short_description: Manage Home Assistant users
version_added: 0.1.0
author: Egor Sklyarov (@Egor-S)
description:
  - Creates, updates and deletes users who log in with a username and password.
  - The user is found by O(username). Users without a username (system users, users of other auth providers) are not managed.
  - Only the options that are set are managed; other settings of an existing user are left unchanged.
  - Creating a user does not create a person for them; use M(egors.homeassistant.person) with RV(user.user_id).
extends_documentation_fragment:
  - egors.homeassistant.connection
options:
  username:
    description:
      - Username to log in with. Home Assistant requires it in lowercase without surrounding whitespace.
      - Renaming a username is not supported.
    type: str
    required: true
  state:
    description:
      - V(present) creates or updates the user, V(absent) deletes it with its credentials.
      - The owner and the user of the O(token) can not be deleted.
    type: str
    choices: [present, absent]
    default: present
  name:
    description:
      - Display name. Home Assistant uses the username when a user is created without it.
    type: str
  password:
    description:
      - Password. Required to create a user.
      - Home Assistant can not tell whether a password matches, so an existing user's password is only set with O(update_password=always).
    type: str
  update_password:
    description:
      - V(on_create) sets O(password) only when the user is created.
      - V(always) also sets it on an existing user on every run and then always reports a change; use it to rotate a password.
    type: str
    choices: [always, on_create]
    default: on_create
  admin:
    description:
      - Whether the user is an administrator. Home Assistant creates users without it as non-administrators.
    type: bool
  active:
    description:
      - Whether the user can log in. Home Assistant creates users active.
    type: bool
  local_only:
    description:
      - Whether the user can only log in from the local network. Home Assistant creates users without this restriction.
    type: bool
attributes:
  check_mode:
    support: full
    description: Reports the changes and the predicted user without writing.
  diff_mode:
    support: full
    description: Shows the user before and after the run. The password is never shown.
  platform:
    platforms: all
    support: full
    description: The module talks to Home Assistant over the network from the controller.
seealso:
  - module: egors.homeassistant.user_info
  - module: egors.homeassistant.person
  - module: egors.homeassistant.login
"""

EXAMPLES = r"""
- name: Create a user
  egors.homeassistant.user:
    username: jane
    name: Jane
    password: "{{ vault_jane_password }}"
  register: jane

- name: Make Jane a person
  egors.homeassistant.person:
    name: Jane
    user_id: "{{ jane.user.user_id }}"

- name: Rotate a password
  egors.homeassistant.user:
    username: jane
    password: "{{ vault_jane_new_password }}"
    update_password: always

- name: Delete a user
  egors.homeassistant.user:
    username: jane
    state: absent
"""

RETURN = r"""
user:
  description: The user after the run (predicted in check mode), or an empty dictionary if it is absent.
  returned: always
  type: dict
  contains:
    user_id:
      description: ID of the user. Null for a user that would be created in check mode.
      type: str
      sample: 7a77ae627f1d453c86ec7c977536c7fc
    username:
      description: Username.
      type: str
      sample: jane
    name:
      description: Display name.
      type: str
      sample: Jane
    admin:
      description: Whether the user is an administrator.
      type: bool
    active:
      description: Whether the user can log in.
      type: bool
    local_only:
      description: Whether the user can only log in from the local network.
      type: bool
    owner:
      description: Whether the user is the owner, who can not be deleted.
      type: bool
"""

from ansible_collections.egors.homeassistant.plugins.module_utils.api import HomeAssistantError, HomeAssistantModule
from ansible_collections.egors.homeassistant.plugins.module_utils.user import (
    GROUP_ADMIN,
    GROUP_USER,
    compute_changes,
    find_user,
    is_normalized,
    normalize,
)


def main():
    argument_spec = dict(
        username=dict(type="str", required=True),
        state=dict(type="str", choices=["present", "absent"], default="present"),
        name=dict(type="str"),
        password=dict(type="str", no_log=True),
        update_password=dict(type="str", choices=["always", "on_create"], default="on_create", no_log=False),
        admin=dict(type="bool"),
        active=dict(type="bool"),
        local_only=dict(type="bool"),
    )
    module = HomeAssistantModule(argument_spec, supports_check_mode=True)
    params = module.params
    username = params["username"]
    if not is_normalized(username):
        module.fail_json(msg="username %r must be lowercase without surrounding whitespace, for example %r"
                         % (username, username.strip().casefold()))

    user = find_user(module.call("config/auth/list"), username)
    before = normalize(user) if user else {}

    if params["state"] == "absent":
        after, changed = {}, user is not None
        if changed and not module.check_mode:
            module.call("config/auth/delete", user_id=user["id"])
    elif user is None:
        if params["password"] is None:
            module.fail_json(msg="password is required to create a user")
        changed = True
        after = dict(user_id=None, username=username, name=params["name"] or username, admin=bool(params["admin"]),
                     active=params["active"] is not False, local_only=bool(params["local_only"]), owner=False)
        if not module.check_mode:
            created = module.call("config/auth/create", name=after["name"],
                                  group_ids=[GROUP_ADMIN if after["admin"] else GROUP_USER],
                                  local_only=after["local_only"])["user"]
            try:
                module.ws.call("config/auth_provider/homeassistant/create", user_id=created["id"], username=username,
                               password=params["password"])
            except HomeAssistantError as exc:
                # Without credentials the user has no username, so no later run could find and fix it.
                module.call("config/auth/delete", user_id=created["id"])
                module.fail_json(msg="Creating the credentials of %s failed, the user was removed again: %s"
                                 % (username, exc))
            if not after["active"]:
                created = module.call("config/auth/update", user_id=created["id"], is_active=False)["user"]
            after = dict(normalize(created), username=username)
    else:
        changes, after = compute_changes(params, before)
        set_password = params["password"] is not None and params["update_password"] == "always"
        changed = bool(changes) or set_password
        if not module.check_mode:
            if changes:
                after = normalize(module.call("config/auth/update", user_id=user["id"], **changes)["user"])
            if set_password:
                module.call("config/auth_provider/homeassistant/admin_change_password", user_id=user["id"],
                            password=params["password"])

    result = dict(changed=changed, user=after)
    if module._diff:
        result["diff"] = dict(before=before, after=after)
    module.exit_json(**result)


if __name__ == "__main__":
    main()

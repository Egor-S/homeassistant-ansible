#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2026, Egor Sklyarov
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

DOCUMENTATION = r"""
module: backup_config
short_description: Manage the automatic backup settings of Home Assistant
version_added: 0.1.0
author: Egor Sklyarov (@Egor-S)
description:
  - Reads and updates the settings of automatic backups (Settings > System > Backups > Backup settings).
  - Only the options that are set are compared and updated, all other settings are left untouched.
    Run the module without options to just read the settings.
extends_documentation_fragment:
  - egors.homeassistant.connection
options:
  agent_ids:
    description:
      - Locations to store backups in, for example V(backup.local) for the Home Assistant host. Compared as a set.
      - The available locations are listed by the C(backup/agents/info) WebSocket command.
    type: list
    elements: str
  include_database:
    description:
      - Whether backups include the history database.
    type: bool
  include_folders:
    description:
      - Extra folders to include (Home Assistant OS and Supervised installs). Compared as a set.
    type: list
    elements: str
    choices: [addons/local, media, share, ssl]
  name:
    description:
      - Name of automatic backups. An empty string restores the default name.
    type: str
  password:
    description:
      - Encryption key of automatic backups. An empty string removes it.
      - It is compared with the stored one but never returned.
    type: str
  retention_copies:
    description:
      - Keep this many automatic backups. V(0) removes the limit.
    type: int
  retention_days:
    description:
      - Keep automatic backups for this many days. V(0) removes the limit.
    type: int
  schedule_recurrence:
    description:
      - When to back up automatically. V(custom_days) uses O(schedule_days).
    type: str
    choices: [never, daily, custom_days]
  schedule_days:
    description:
      - Weekdays for O(schedule_recurrence=custom_days). Compared as a set.
    type: list
    elements: str
    choices: [mon, tue, wed, thu, fri, sat, sun]
  schedule_time:
    description:
      - Time of day for automatic backups, V(H:MM) or V(H:MM:SS). An empty string lets Home Assistant pick a time.
    type: str
  automatic_backups_configured:
    description:
      - Whether the backup settings count as reviewed. Until it is V(true) the UI asks to set up automatic backups.
    type: bool
attributes:
  check_mode:
    support: full
    description: Reports the changes and the predicted settings without writing.
  diff_mode:
    support: full
    description: Shows the settings before and after the run. The password is never shown.
  platform:
    platforms: all
    support: full
    description: The module talks to Home Assistant over the network from the controller.
"""

EXAMPLES = r"""
- name: Back up every night, keep a week
  egors.homeassistant.backup_config:
    agent_ids: [backup.local]
    password: "{{ vault_backup_key }}"
    schedule_recurrence: daily
    schedule_time: "04:45"
    retention_days: 7
    automatic_backups_configured: true
"""

RETURN = r"""
config:
  description: The settings after the run (predicted in check mode), with the same names as the options.
  returned: always
  type: dict
  contains:
    agent_ids:
      description: Sorted locations.
      type: list
      elements: str
    include_database:
      description: Whether the database is included.
      type: bool
    include_folders:
      description: Sorted extra folders, or null.
      type: list
      elements: str
    name:
      description: Name of automatic backups, or null.
      type: str
    password_set:
      description: Whether an encryption key is set. The key itself is not returned.
      type: bool
    retention_copies:
      description: Number of backups to keep, or null.
      type: int
    retention_days:
      description: Days to keep backups, or null.
      type: int
    schedule_recurrence:
      description: V(never), V(daily) or V(custom_days).
      type: str
    schedule_days:
      description: Sorted weekdays.
      type: list
      elements: str
    schedule_time:
      description: Time of day as V(HH:MM:SS), or null.
      type: str
    automatic_backups_configured:
      description: Whether the settings count as reviewed.
      type: bool
changed_options:
  description: Names of the options that were changed (or would be in check mode).
  returned: always
  type: list
  elements: str
"""

from ansible_collections.egors.homeassistant.plugins.module_utils.api import HomeAssistantModule
from ansible_collections.egors.homeassistant.plugins.module_utils.backup import compute_update, flatten, predict


def main():
    argument_spec = dict(
        agent_ids=dict(type="list", elements="str"),
        include_database=dict(type="bool"),
        include_folders=dict(type="list", elements="str", choices=["addons/local", "media", "share", "ssl"]),
        name=dict(type="str"),
        password=dict(type="str", no_log=True),
        retention_copies=dict(type="int"),
        retention_days=dict(type="int"),
        schedule_recurrence=dict(type="str", choices=["never", "daily", "custom_days"]),
        schedule_days=dict(type="list", elements="str", choices=["mon", "tue", "wed", "thu", "fri", "sat", "sun"]),
        schedule_time=dict(type="str"),
        automatic_backups_configured=dict(type="bool"),
    )
    module = HomeAssistantModule(argument_spec, supports_check_mode=True)
    current = module.call("backup/config/info")["config"]
    try:
        payload, changed_options = compute_update(module.params, current)
    except ValueError as e:
        module.fail_json(msg="invalid schedule_time: %s" % e)
    after = predict(current, payload)
    if payload and not module.check_mode:
        module.call("backup/config/update", **payload)
        after = module.call("backup/config/info")["config"]
    result = dict(changed=bool(payload), config=flatten(after), changed_options=changed_options)
    if module._diff:
        result["diff"] = dict(before=flatten(current), after=result["config"])
    module.exit_json(**result)


if __name__ == "__main__":
    main()

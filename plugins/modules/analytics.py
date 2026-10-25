#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2026, Egor Sklyarov
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

DOCUMENTATION = r"""
module: analytics
short_description: Manage what Home Assistant shares with its analytics
version_added: 0.1.0
author: Egor Sklyarov (@Egor-S)
description:
  - Reads and updates the analytics preferences (Settings > System > Analytics).
  - Only the options that are set are compared and updated. Run the module without options to just read them.
  - M(egors.homeassistant.onboarding) leaves all of them off.
extends_documentation_fragment:
  - egors.homeassistant.connection
options:
  base:
    description:
      - Share basic information (installation type, version). The other options except O(snapshots) need it.
    type: bool
  usage:
    description:
      - Share the names of the integrations in use.
    type: bool
  statistics:
    description:
      - Share counts of entities, automations and similar.
    type: bool
  diagnostics:
    description:
      - Share crash reports and diagnostics.
    type: bool
  snapshots:
    description:
      - Share device information to improve the device database.
    type: bool
attributes:
  check_mode:
    support: full
    description: Reports the changes and the predicted preferences without writing.
  diff_mode:
    support: full
    description: Shows the preferences before and after the run.
  platform:
    platforms: all
    support: full
    description: The module talks to Home Assistant over the network from the controller.
"""

EXAMPLES = r"""
- name: Share basic information and usage
  egors.homeassistant.analytics:
    base: true
    usage: true
"""

RETURN = r"""
preferences:
  description: The preferences after the run (predicted in check mode), with the same names as the options.
  returned: always
  type: dict
  sample:
    base: true
    usage: true
    statistics: false
    diagnostics: false
    snapshots: false
"""

from ansible_collections.egors.homeassistant.plugins.module_utils.api import HomeAssistantModule

PREFERENCES = ("base", "usage", "statistics", "diagnostics", "snapshots")


def main():
    module = HomeAssistantModule(dict((p, dict(type="bool")) for p in PREFERENCES), supports_check_mode=True)
    stored = module.call("analytics")["preferences"]
    current = dict((p, stored.get(p, False)) for p in PREFERENCES)
    changes = dict((p, module.params[p]) for p in PREFERENCES
                   if module.params[p] is not None and module.params[p] != current[p])
    after = dict(current, **changes)
    if changes and not module.check_mode:
        stored = module.call("analytics/preferences", preferences=changes)["preferences"]
        after = dict((p, stored.get(p, False)) for p in PREFERENCES)
    result = dict(changed=bool(changes), preferences=after)
    if module._diff:
        result["diff"] = dict(before=current, after=after)
    module.exit_json(**result)


if __name__ == "__main__":
    main()

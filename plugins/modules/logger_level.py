#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2026, Egor Sklyarov
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

DOCUMENTATION = r"""
module: logger_level
short_description: Set the log level of a Home Assistant integration
version_added: 0.1.0
author: Egor Sklyarov (@Egor-S)
description:
  - Sets the log level of an integration permanently, as the integration's "Enable debug logging" switch does
    but for any level. The level is kept across restarts.
  - The level is compared with the integration's current level. Home Assistant does not tell whether that level
    was set here or comes from the C(logger:) block of C(configuration.yaml); in the latter case nothing is stored.
  - The default level and log filters are only configurable in C(configuration.yaml).
extends_documentation_fragment:
  - egors.homeassistant.connection
options:
  integration:
    description:
      - Domain of the integration, for example V(zha) or V(mqtt). It must be loaded.
    type: str
    required: true
  level:
    description:
      - Log level.
    type: str
    required: true
    choices: [critical, error, warning, info, debug]
attributes:
  check_mode:
    support: full
    description: Reports whether the level would change without writing.
  diff_mode:
    support: full
    description: Shows the level before and after the run.
  platform:
    platforms: all
    support: full
    description: The module talks to Home Assistant over the network from the controller.
"""

EXAMPLES = r"""
- name: Debug logging for ZHA
  egors.homeassistant.logger_level:
    integration: zha
    level: debug
"""

RETURN = r"""
integration:
  description: Domain of the integration.
  returned: always
  type: str
  sample: zha
level:
  description: Level after the run (predicted in check mode).
  returned: always
  type: str
  sample: debug
"""

from ansible_collections.egors.homeassistant.plugins.module_utils.api import HomeAssistantModule

LEVELS = {"critical": 50, "error": 40, "warning": 30, "info": 20, "debug": 10}


def level_name(number):
    """Name of a level number; numbers between the named levels are reported as numbers."""
    return next((name for name, value in LEVELS.items() if value == number), str(number))


def main():
    argument_spec = dict(
        integration=dict(type="str", required=True),
        level=dict(type="str", required=True, choices=list(LEVELS)),
    )
    module = HomeAssistantModule(argument_spec, supports_check_mode=True)
    integration, level = module.params["integration"], module.params["level"]
    current = next((i["level"] for i in module.call("logger/log_info") if i.get("domain") == integration), None)
    if current is None:
        module.fail_json(msg="integration %s is not loaded" % integration)
    changed = current != LEVELS[level]
    if changed and not module.check_mode:
        module.call("logger/integration_log_level", integration=integration, level=level.upper(),
                    persistence="permanent")
    result = dict(changed=changed, integration=integration, level=level)
    if module._diff:
        result["diff"] = dict(before=dict(level=level_name(current)), after=dict(level=level))
    module.exit_json(**result)


if __name__ == "__main__":
    main()

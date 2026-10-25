#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2026, Egor Sklyarov
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

DOCUMENTATION = r"""
module: script
short_description: Manage Home Assistant scripts created in the UI
version_added: 0.1.0
author: Egor Sklyarov (@Egor-S)
description:
  - Creates, replaces and deletes scripts that the UI editor manages, the ones stored in C(scripts.yaml) on the Home Assistant host.
  - The O(config) is the whole script; it replaces the stored one and is compared with it as a whole.
    Home Assistant stores it as sent, so write it the way you want to read it back.
  - After a change Home Assistant reloads its scripts in the background; the script entity may appear a moment after the module returns.
  - Scripts defined elsewhere (other YAML files, packages, blueprints' own files) are not visible to this module.
extends_documentation_fragment:
  - egors.homeassistant.connection
options:
  script_id:
    description:
      - ID of the script, the key in C(scripts.yaml). The entity is C(script.<script_id>).
      - Home Assistant requires a slug, lowercase letters, digits and underscores.
    type: str
    required: true
  state:
    description:
      - V(present) creates or replaces the script, V(absent) deletes it.
    type: str
    choices: [present, absent]
    default: present
  config:
    description:
      - The script, as under its key in C(scripts.yaml), for example with C(alias), C(sequence), C(fields) and C(mode).
      - Required with O(state=present). Home Assistant validates it and rejects an invalid script without storing it.
    type: dict
attributes:
  check_mode:
    support: full
    description: Reports whether the script would change without writing.
  diff_mode:
    support: full
    description: Shows the stored and the new configuration.
  platform:
    platforms: all
    support: full
    description: The module talks to Home Assistant over the network from the controller.
"""

EXAMPLES = r"""
- name: A script that turns off all lights
  egors.homeassistant.script:
    script_id: all_lights_off
    config:
      alias: All lights off
      sequence:
        - action: light.turn_off
          target:
            entity_id: all
      mode: single
"""

RETURN = r"""
script_id:
  description: ID of the script.
  returned: always
  type: str
  sample: all_lights_off
config:
  description: The configuration after the run (predicted in check mode), or an empty dictionary if the script is absent.
  returned: always
  type: dict
"""

from ansible_collections.egors.homeassistant.plugins.module_utils.api import HomeAssistantModule
from ansible_collections.egors.homeassistant.plugins.module_utils.config_editor import ConfigEditor


def main():
    argument_spec = dict(
        script_id=dict(type="str", required=True),
        state=dict(type="str", choices=["present", "absent"], default="present"),
        config=dict(type="dict"),
    )
    module = HomeAssistantModule(argument_spec, required_if=[("state", "present", ["config"])], supports_check_mode=True)
    ConfigEditor(module, "script", "script_id", id_in_value=False).ensure()


if __name__ == "__main__":
    main()

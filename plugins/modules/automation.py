#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2026, Egor Sklyarov
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

DOCUMENTATION = r"""
module: automation
short_description: Manage Home Assistant automations created in the UI
version_added: 0.1.0
author: Egor Sklyarov (@Egor-S)
description:
  - Creates, replaces and deletes automations that the UI editor manages, the ones stored in C(automations.yaml) on the Home Assistant host.
  - The O(config) is the whole automation; it replaces the stored one and is compared with it as a whole.
    Home Assistant stores it as sent, so write it the way you want to read it back.
  - After a change Home Assistant reloads its automations in the background; the automation entity may appear a moment after the module returns.
  - Automations defined elsewhere (other YAML files, packages, blueprints' own files) are not visible to this module.
extends_documentation_fragment:
  - egors.homeassistant.connection
options:
  automation_id:
    description:
      - ID of the automation, the C(id) in C(automations.yaml). It is not the entity ID; Home Assistant derives the
        entity ID C(automation.<slug>) from the C(alias) when the automation is created.
      - The UI uses a number like V(1730000000000); any string works.
    type: str
    required: true
  state:
    description:
      - V(present) creates or replaces the automation, V(absent) deletes it.
    type: str
    choices: [present, absent]
    default: present
  config:
    description:
      - The automation, as in C(automations.yaml), for example with C(alias), C(description), C(triggers),
        C(conditions), C(actions) and C(mode). Without C(id); the module sets it from O(automation_id).
      - Required with O(state=present). Home Assistant validates it and rejects an invalid automation without storing it.
    type: dict
attributes:
  check_mode:
    support: full
    description: Reports whether the automation would change without writing.
  diff_mode:
    support: full
    description: Shows the stored and the new configuration.
  platform:
    platforms: all
    support: full
    description: The module talks to Home Assistant over the network from the controller.
"""

EXAMPLES = r"""
- name: Turn on the porch light at sunset
  egors.homeassistant.automation:
    automation_id: porch_light_at_sunset
    config:
      alias: Porch light at sunset
      triggers:
        - trigger: sun
          event: sunset
      actions:
        - action: light.turn_on
          target:
            entity_id: light.porch
      mode: single

- name: Delete it
  egors.homeassistant.automation:
    automation_id: porch_light_at_sunset
    state: absent
"""

RETURN = r"""
automation_id:
  description: ID of the automation.
  returned: always
  type: str
  sample: porch_light_at_sunset
config:
  description: The configuration after the run (predicted in check mode), or an empty dictionary if the automation is absent.
  returned: always
  type: dict
"""

from ansible_collections.egors.homeassistant.plugins.module_utils.api import HomeAssistantModule
from ansible_collections.egors.homeassistant.plugins.module_utils.config_editor import ConfigEditor


def main():
    argument_spec = dict(
        automation_id=dict(type="str", required=True),
        state=dict(type="str", choices=["present", "absent"], default="present"),
        config=dict(type="dict"),
    )
    module = HomeAssistantModule(argument_spec, required_if=[("state", "present", ["config"])], supports_check_mode=True)
    ConfigEditor(module, "automation", "automation_id", id_in_value=True).ensure()


if __name__ == "__main__":
    main()

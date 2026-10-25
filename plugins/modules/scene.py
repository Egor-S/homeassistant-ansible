#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2026, Egor Sklyarov
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

DOCUMENTATION = r"""
module: scene
short_description: Manage Home Assistant scenes created in the UI
version_added: 0.1.0
author: Egor Sklyarov (@Egor-S)
description:
  - Creates, replaces and deletes scenes that the UI editor manages, the ones stored in C(scenes.yaml) on the Home Assistant host.
  - The O(config) is the whole scene; it replaces the stored one and is compared with it as a whole.
    Home Assistant stores it as sent, so write it the way you want to read it back.
  - After a change Home Assistant reloads its scenes in the background; the scene entity may appear a moment after the module returns.
  - Scenes defined elsewhere (other YAML files, packages, blueprints' own files) are not visible to this module.
extends_documentation_fragment:
  - egors.homeassistant.connection
options:
  scene_id:
    description:
      - ID of the scene, the C(id) in C(scenes.yaml). It is not the entity ID; Home Assistant derives the entity ID
        C(scene.<slug>) from the C(name) when the scene is created.
    type: str
    required: true
  state:
    description:
      - V(present) creates or replaces the scene, V(absent) deletes it.
    type: str
    choices: [present, absent]
    default: present
  config:
    description:
      - The scene, as in C(scenes.yaml), with C(name) and C(entities) (entity ID to state and attributes), and optionally C(icon).
        Without C(id); the module sets it from O(scene_id).
      - Required with O(state=present). Home Assistant validates it and rejects an invalid scene without storing it.
    type: dict
attributes:
  check_mode:
    support: full
    description: Reports whether the scene would change without writing.
  diff_mode:
    support: full
    description: Shows the stored and the new configuration.
  platform:
    platforms: all
    support: full
    description: The module talks to Home Assistant over the network from the controller.
"""

EXAMPLES = r"""
- name: Movie scene
  egors.homeassistant.scene:
    scene_id: movie
    config:
      name: Movie
      entities:
        light.living_room:
          state: "on"
          brightness: 40
        media_player.tv: "on"
"""

RETURN = r"""
scene_id:
  description: ID of the scene.
  returned: always
  type: str
  sample: movie
config:
  description: The configuration after the run (predicted in check mode), or an empty dictionary if the scene is absent.
  returned: always
  type: dict
"""

from ansible_collections.egors.homeassistant.plugins.module_utils.api import HomeAssistantModule
from ansible_collections.egors.homeassistant.plugins.module_utils.config_editor import ConfigEditor


def main():
    argument_spec = dict(
        scene_id=dict(type="str", required=True),
        state=dict(type="str", choices=["present", "absent"], default="present"),
        config=dict(type="dict"),
    )
    module = HomeAssistantModule(argument_spec, required_if=[("state", "present", ["config"])], supports_check_mode=True)
    ConfigEditor(module, "scene", "scene_id", id_in_value=True).ensure()


if __name__ == "__main__":
    main()

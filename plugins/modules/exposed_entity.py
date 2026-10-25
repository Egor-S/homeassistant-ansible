#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2026, Egor Sklyarov
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

DOCUMENTATION = r"""
module: exposed_entity
short_description: Expose Home Assistant entities to voice assistants
version_added: 0.1.0
author: Egor Sklyarov (@Egor-S)
description:
  - Sets whether entities are exposed to Assist, Alexa and Google Assistant (Settings > Voice assistants > Expose).
  - Only the assistants that are set are managed.
  - Whether a new entity is exposed at first is decided by M(egors.homeassistant.expose_new_entities).
extends_documentation_fragment:
  - egors.homeassistant.connection
options:
  entity_id:
    description:
      - Entity IDs to set, for example V(light.kitchen).
    type: list
    elements: str
    required: true
  conversation:
    description:
      - Whether the entities are exposed to Assist, the built-in voice assistant.
    type: bool
  alexa:
    description:
      - Whether the entities are exposed to Amazon Alexa through Home Assistant Cloud.
    type: bool
  google_assistant:
    description:
      - Whether the entities are exposed to Google Assistant through Home Assistant Cloud.
    type: bool
attributes:
  check_mode:
    support: full
    description: Reports the changes without writing.
  diff_mode:
    support: full
    description: Shows the exposure before and after the run.
  platform:
    platforms: all
    support: full
    description: The module talks to Home Assistant over the network from the controller.
seealso:
  - module: egors.homeassistant.expose_new_entities
"""

EXAMPLES = r"""
- name: Expose the kitchen lights to Assist only
  egors.homeassistant.exposed_entity:
    entity_id: [light.kitchen, light.kitchen_counter]
    conversation: true
    alexa: false
    google_assistant: false
"""

RETURN = r"""
exposed:
  description: Exposure of each of the entities after the run (predicted in check mode), by assistant option.
  returned: always
  type: dict
  sample:
    light.kitchen:
      conversation: true
      alexa: false
      google_assistant: false
"""

from ansible_collections.egors.homeassistant.plugins.module_utils.api import HomeAssistantModule
from ansible_collections.egors.homeassistant.plugins.module_utils.assist import ASSISTANTS, argument_spec


def main():
    spec = argument_spec()
    spec["entity_id"] = dict(type="list", elements="str", required=True)
    module = HomeAssistantModule(spec, supports_check_mode=True)
    stored = module.call("homeassistant/expose_entity/list")["exposed_entities"]
    entity_ids = list(dict.fromkeys(module.params["entity_id"]))
    # The list only names the assistants an entity is exposed to.
    before = dict((e, dict((o, a in (stored.get(e) or {})) for o, a in ASSISTANTS.items())) for e in entity_ids)
    after = dict((e, dict(v)) for e, v in before.items())
    # One call per (assistant, value), for all entities that differ.
    calls = {}
    for option, assistant in ASSISTANTS.items():
        wanted = module.params[option]
        if wanted is None:
            continue
        for entity_id in entity_ids:
            if before[entity_id][option] != wanted:
                calls.setdefault((assistant, wanted), []).append(entity_id)
                after[entity_id][option] = wanted
    if calls and not module.check_mode:
        for (assistant, wanted), ids in calls.items():
            module.call("homeassistant/expose_entity", assistants=[assistant], entity_ids=ids, should_expose=wanted)
    result = dict(changed=bool(calls), exposed=after)
    if module._diff:
        result["diff"] = dict(before=before, after=after)
    module.exit_json(**result)


if __name__ == "__main__":
    main()

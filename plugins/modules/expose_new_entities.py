#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2026, Egor Sklyarov
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

DOCUMENTATION = r"""
module: expose_new_entities
short_description: Choose whether new entities are exposed to voice assistants
version_added: 0.1.0
author: Egor Sklyarov (@Egor-S)
description:
  - Sets, per voice assistant, whether entities are exposed by default ("Expose new entities").
    Only some kinds of entities (lights, switches, ...) are exposed by default even then.
  - Only the assistants that are set are managed. Run the module without options to just read the settings.
extends_documentation_fragment:
  - egors.homeassistant.connection
options:
  conversation:
    description:
      - Whether new entities are exposed to Assist, the built-in voice assistant.
    type: bool
  alexa:
    description:
      - Whether new entities are exposed to Amazon Alexa through Home Assistant Cloud.
    type: bool
  google_assistant:
    description:
      - Whether new entities are exposed to Google Assistant through Home Assistant Cloud.
    type: bool
attributes:
  check_mode:
    support: full
    description: Reports the changes without writing.
  diff_mode:
    support: full
    description: Shows the settings before and after the run.
  platform:
    platforms: all
    support: full
    description: The module talks to Home Assistant over the network from the controller.
seealso:
  - module: egors.homeassistant.exposed_entity
"""

EXAMPLES = r"""
- name: Expose nothing by default
  egors.homeassistant.expose_new_entities:
    conversation: false
    alexa: false
    google_assistant: false
"""

RETURN = r"""
expose_new:
  description: The settings after the run (predicted in check mode), by assistant option.
  returned: always
  type: dict
  sample:
    conversation: true
    alexa: false
    google_assistant: false
"""

from ansible_collections.egors.homeassistant.plugins.module_utils.api import HomeAssistantModule
from ansible_collections.egors.homeassistant.plugins.module_utils.assist import ASSISTANTS, argument_spec


def main():
    module = HomeAssistantModule(argument_spec(), supports_check_mode=True)
    before = dict((o, module.call("homeassistant/expose_new_entities/get", assistant=a)["expose_new"])
                  for o, a in ASSISTANTS.items())
    changes = dict((o, module.params[o]) for o in ASSISTANTS
                   if module.params[o] is not None and module.params[o] != before[o])
    if changes and not module.check_mode:
        for option, value in changes.items():
            module.call("homeassistant/expose_new_entities/set", assistant=ASSISTANTS[option], expose_new=value)
    after = dict(before, **changes)
    result = dict(changed=bool(changes), expose_new=after)
    if module._diff:
        result["diff"] = dict(before=before, after=after)
    module.exit_json(**result)


if __name__ == "__main__":
    main()

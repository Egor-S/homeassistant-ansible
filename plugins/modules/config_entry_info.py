#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2026, Egor Sklyarov
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

DOCUMENTATION = r"""
module: config_entry_info
short_description: List Home Assistant config entries
version_added: 0.1.0
author: Egor Sklyarov (@Egor-S)
description:
  - Returns the config entries (set up integrations and UI helpers), optionally filtered.
extends_documentation_fragment:
  - egors.homeassistant.connection
options:
  domain:
    description:
      - Only return entries of this integration.
    type: str
  title:
    description:
      - Only return entries with this title, ignoring case and surrounding or repeated whitespace.
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
  - module: egors.homeassistant.config_entry
"""

EXAMPLES = r"""
- name: All template helpers
  egors.homeassistant.config_entry_info:
    domain: template
  register: templates
"""

RETURN = r"""
entries:
  description: Matching entries, in the same format as the RV(egors.homeassistant.config_entry#module:entry) return value.
  returned: always
  type: list
  elements: dict
  sample:
    - entry_id: 01M5SWJ7XMM46Y2Q8XH1JSH8FS
      domain: sun
      title: Sun
      state: loaded
      source: import
      disabled_by: null
      supports_options: false
"""

from ansible_collections.egors.homeassistant.plugins.module_utils.api import HomeAssistantModule
from ansible_collections.egors.homeassistant.plugins.module_utils.registry import normalize_name
from ansible_collections.egors.homeassistant.plugins.module_utils.config_entry import normalize_entry


def main():
    module = HomeAssistantModule(dict(domain=dict(type="str"), title=dict(type="str")), supports_check_mode=True)
    params = module.params
    entries = module.call("config_entries/get", **(dict(domain=params["domain"]) if params["domain"] else {}))
    if params["title"] is not None:
        entries = [e for e in entries if normalize_name(e.get("title") or "") == normalize_name(params["title"])]
    module.exit_json(changed=False, entries=[normalize_entry(e) for e in entries])


if __name__ == "__main__":
    main()

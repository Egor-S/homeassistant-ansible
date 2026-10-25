#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2026, Egor Sklyarov
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

DOCUMENTATION = r"""
module: device_info
short_description: List devices of the Home Assistant device registry
version_added: 0.1.0
author: Egor Sklyarov (@Egor-S)
description:
  - Returns device registry entries, optionally filtered. All filters that are set must match.
extends_documentation_fragment:
  - egors.homeassistant.connection
options:
  device_id:
    description:
      - Only return the device with this ID.
    type: str
  name:
    description:
      - Only return devices with this name, given by the integration or by the user, ignoring case and surrounding or repeated whitespace.
    type: str
  area_id:
    description:
      - Only return devices in this area.
    type: str
  label:
    description:
      - Only return devices with this label ID.
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
  - module: egors.homeassistant.device
"""

EXAMPLES = r"""
- name: Devices in the kitchen
  egors.homeassistant.device_info:
    area_id: kitchen
  register: kitchen
"""

RETURN = r"""
devices:
  description: Matching devices in registry order, in the same format as the RV(egors.homeassistant.device#module:device) return value.
  returned: always
  type: list
  elements: dict
  sample:
    - device_id: 107dca174fa5db043adc152803b6bace
      name: Sun
      name_by_user: null
      area_id: null
      labels: []
      disabled_by: null
      manufacturer: null
      model: null
      entry_type: service
      via_device_id: null
      config_entries: [01M5SWJ7XMM46Y2Q8XH1JSH8FS]
      identifiers: [[sun, 01M5SWJ7XMM46Y2Q8XH1JSH8FS]]
"""

from ansible_collections.egors.homeassistant.plugins.module_utils.api import HomeAssistantModule
from ansible_collections.egors.homeassistant.plugins.module_utils.device import matches_name, normalize


def main():
    argument_spec = dict(
        device_id=dict(type="str"),
        name=dict(type="str"),
        area_id=dict(type="str"),
        label=dict(type="str"),
    )
    module = HomeAssistantModule(argument_spec, supports_check_mode=True)
    params = module.params
    devices = module.call("config/device_registry/list")
    if params["device_id"] is not None:
        devices = [d for d in devices if d.get("id") == params["device_id"]]
    if params["name"] is not None:
        devices = [d for d in devices if matches_name(d, params["name"])]
    if params["area_id"] is not None:
        devices = [d for d in devices if d.get("area_id") == params["area_id"]]
    if params["label"] is not None:
        devices = [d for d in devices if params["label"] in (d.get("labels") or [])]
    module.exit_json(changed=False, devices=[normalize(d) for d in devices])


if __name__ == "__main__":
    main()

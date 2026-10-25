#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2026, Egor Sklyarov
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

DOCUMENTATION = r"""
module: energy_prefs
short_description: Configure the Home Assistant energy dashboard
version_added: 0.1.0
author: Egor Sklyarov (@Egor-S)
description:
  - Sets the sources and devices of the energy dashboard (Settings > Dashboards > Energy).
  - Each option is one section of the settings; a section that is set replaces the stored one and is compared with it
    as a whole, sections that are left out are kept. Home Assistant validates the sections and stores them as sent.
  - Run the module without options to just read the settings.
extends_documentation_fragment:
  - egors.homeassistant.connection
options:
  energy_sources:
    description:
      - Grid, solar, battery, gas and water sources, each a dictionary with C(type) and the statistics of the source,
        as in C(.storage/energy) or the C(energy/get_prefs) WebSocket command.
    type: list
    elements: dict
  device_consumption:
    description:
      - Devices whose consumption is shown, each a dictionary with C(stat_consumption) and optionally C(name) and C(included_in_stat).
    type: list
    elements: dict
  device_consumption_water:
    description:
      - Devices whose water consumption is shown, like O(device_consumption).
    type: list
    elements: dict
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
"""

EXAMPLES = r"""
- name: Solar production and two devices
  egors.homeassistant.energy_prefs:
    energy_sources:
      - type: solar
        stat_energy_from: sensor.inverter_energy
    device_consumption:
      - stat_consumption: sensor.dishwasher_energy
      - stat_consumption: sensor.heat_pump_energy
        name: Heat pump
"""

RETURN = r"""
prefs:
  description: The settings after the run (predicted in check mode).
  returned: always
  type: dict
  sample:
    energy_sources:
      - type: solar
        stat_energy_from: sensor.inverter_energy
    device_consumption: []
    device_consumption_water: []
"""

from ansible_collections.egors.homeassistant.plugins.module_utils.api import HomeAssistantModule

SECTIONS = ("energy_sources", "device_consumption", "device_consumption_water")


def main():
    module = HomeAssistantModule(dict((s, dict(type="list", elements="dict")) for s in SECTIONS), supports_check_mode=True)
    # Before the first save Home Assistant has no preferences at all.
    stored = module.call_optional("energy/get_prefs") or {}
    before = dict((s, stored.get(s) or []) for s in SECTIONS)
    changes = dict((s, module.params[s]) for s in SECTIONS
                   if module.params[s] is not None and module.params[s] != before[s])
    after = dict(before, **changes)
    if changes and not module.check_mode:
        saved = module.call("energy/save_prefs", **changes)
        after = dict((s, saved.get(s) or []) for s in SECTIONS)
    result = dict(changed=bool(changes), prefs=after)
    if module._diff:
        result["diff"] = dict(before=before, after=after)
    module.exit_json(**result)


if __name__ == "__main__":
    main()

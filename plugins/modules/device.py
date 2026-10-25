#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2026, Egor Sklyarov
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

DOCUMENTATION = r"""
module: device
short_description: Manage the settings of a Home Assistant device
version_added: 0.1.0
author: Egor Sklyarov (@Egor-S)
description:
  - Updates the device registry entry of a device, which holds its user-given name, area, labels and whether it is enabled.
  - Devices are created by their integrations; this module never creates or deletes one.
  - The device is found by O(device_id) if given, otherwise by O(name), which matches both the name the integration
    gave the device and the name the user gave it, ignoring case and surrounding or repeated whitespace.
    The module fails if the name matches more than one device, then use O(device_id).
  - Only the options that are set are managed; other settings are left unchanged.
extends_documentation_fragment:
  - egors.homeassistant.connection
options:
  device_id:
    description:
      - ID of the device, see M(egors.homeassistant.device_info).
      - At least one of O(device_id) and O(name) is required.
    type: str
  name:
    description:
      - Name of the device, to find it. To rename the device use O(name_by_user).
    type: str
  name_by_user:
    description:
      - Name given by the user, shown instead of the integration's name. An empty string restores the integration's name.
    type: str
  area_id:
    description:
      - ID of the area of the device. Its entities follow it unless they have an area of their own. An empty string removes the area.
      - Home Assistant does not check that the area exists.
    type: str
  labels:
    description:
      - IDs of the labels of the device, compared as a set. An empty list removes all labels.
      - Home Assistant drops unknown labels; the module warns about it.
    type: list
    elements: str
  disabled:
    description:
      - V(true) disables the device and its entities, V(false) enables it.
      - V(false) also enables a device that its integration disabled.
    type: bool
attributes:
  check_mode:
    support: full
    description: Reports the changes and the predicted device without writing.
  diff_mode:
    support: full
    description: Shows the device before and after the run.
  platform:
    platforms: all
    support: full
    description: The module talks to Home Assistant over the network from the controller.
seealso:
  - module: egors.homeassistant.device_info
  - module: egors.homeassistant.entity
"""

EXAMPLES = r"""
- name: Put the thermostat in the living room
  egors.homeassistant.device:
    name: Thermostat 3F2A
    name_by_user: Living room thermostat
    area_id: living_room

- name: Disable a device
  egors.homeassistant.device:
    device_id: 107dca174fa5db043adc152803b6bace
    disabled: true
"""

RETURN = r"""
device:
  description: The registry entry after the run (predicted in check mode).
  returned: always
  type: dict
  contains:
    device_id:
      description: ID of the device.
      type: str
    name:
      description: Name given by the integration.
      type: str
      sample: Thermostat 3F2A
    name_by_user:
      description: Name given by the user, or null.
      type: str
      sample: Living room thermostat
    area_id:
      description: Area, or null.
      type: str
    labels:
      description: Sorted label IDs.
      type: list
      elements: str
    disabled_by:
      description: Who disabled the device (V(user), V(integration), V(config_entry)), or null if it is enabled.
      type: str
    manufacturer:
      description: Manufacturer, or null.
      type: str
    model:
      description: Model, or null.
      type: str
    entry_type:
      description: V(service) for a service rather than a physical device, else null.
      type: str
    via_device_id:
      description: ID of the device (such as a hub) through which this device is connected, or null.
      type: str
    config_entries:
      description: IDs of the config entries (integrations) that provide the device.
      type: list
      elements: str
    identifiers:
      description: Identifiers of the device within its integrations, as pairs of integration and ID.
      type: list
      elements: list
"""

from ansible_collections.egors.homeassistant.plugins.module_utils.api import HomeAssistantModule
from ansible_collections.egors.homeassistant.plugins.module_utils.device import compute_changes, matches_name, normalize


def main():
    argument_spec = dict(
        device_id=dict(type="str"),
        name=dict(type="str"),
        name_by_user=dict(type="str"),
        area_id=dict(type="str"),
        labels=dict(type="list", elements="str"),
        disabled=dict(type="bool"),
    )
    module = HomeAssistantModule(argument_spec, required_one_of=[("device_id", "name")], supports_check_mode=True)
    params = module.params
    devices = module.call("config/device_registry/list")
    if params["device_id"] is not None:
        found = [d for d in devices if d.get("id") == params["device_id"]]
    else:
        found = [d for d in devices if matches_name(d, params["name"])]
    if not found:
        module.fail_json(msg="no device %s" % (params["device_id"] or "named %r" % params["name"]))
    if len(found) > 1:
        module.fail_json(msg="%d devices are named %r; select one with device_id" % (len(found), params["name"]),
                         matches=[normalize(d) for d in found])

    before = normalize(found[0])
    changes, after = compute_changes(params, before)
    if changes and not module.check_mode:
        after = normalize(module.call("config/device_registry/update", device_id=before["device_id"], **changes))
        if "labels" in changes and after["labels"] != changes["labels"]:
            module.warn("Home Assistant stored labels=%r instead of the requested %r; unknown labels are dropped."
                        % (after["labels"], changes["labels"]))
    result = dict(changed=bool(changes), device=after)
    if module._diff:
        result["diff"] = dict(before=before, after=after)
    module.exit_json(**result)


if __name__ == "__main__":
    main()

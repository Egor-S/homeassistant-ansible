#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2026, Egor Sklyarov
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

DOCUMENTATION = r"""
module: entity
short_description: Manage the settings of a Home Assistant entity
version_added: 0.1.0
author: Egor Sklyarov (@Egor-S)
description:
  - Updates the entity registry entry of an entity, which holds the settings of the entity's settings dialog
    (name, icon, area, aliases, labels, entity ID, and whether it is enabled and visible).
  - Entities are created by their integrations; this module never creates or deletes one. Only entities with a
    unique ID are in the registry; for others Home Assistant shows "This entity does not have a unique ID".
  - Only the options that are set are managed; other settings are left unchanged.
extends_documentation_fragment:
  - egors.homeassistant.connection
options:
  entity_id:
    description:
      - Entity ID, for example V(sensor.outdoor_temperature).
      - If it does not exist but O(new_entity_id) does, the entity counts as already renamed.
    type: str
    required: true
  new_entity_id:
    description:
      - Rename the entity to this entity ID. The domain must stay the same.
    type: str
  name:
    description:
      - Name of the entity. An empty string restores the name given by the integration.
    type: str
  icon:
    description:
      - Icon, for example V(mdi:thermometer). An empty string restores the integration's icon.
    type: str
  area_id:
    description:
      - ID of the area of the entity, if it differs from the area of its device. An empty string makes it follow its device again.
      - Home Assistant rejects an area for an entity that has no name of its own (it is named after its device);
        set the area on the device then, or give the entity a O(name) in the same task.
    type: str
  device_class:
    description:
      - Device class shown in the UI, for example V(door) or V(window) for a binary sensor.
      - An empty string restores the integration's device class.
    type: str
  aliases:
    description:
      - Alternative names for voice assistants, compared as a set. An empty list removes them.
      - The entity's own name stays an alias where Home Assistant has it as one.
    type: list
    elements: str
  labels:
    description:
      - IDs of the labels of the entity, compared as a set. An empty list removes all labels.
      - Home Assistant drops unknown labels; the module warns about it.
    type: list
    elements: str
  disabled:
    description:
      - V(true) disables the entity, V(false) enables it.
      - V(false) also enables an entity that its integration or device disabled.
      - Home Assistant reloads the integration about 30 seconds after an entity is enabled.
    type: bool
  hidden:
    description:
      - V(true) hides the entity from automatically generated dashboards, V(false) shows it.
    type: bool
attributes:
  check_mode:
    support: full
    description: Reports the changes and the predicted entity without writing.
  diff_mode:
    support: full
    description: Shows the entity before and after the run.
  platform:
    platforms: all
    support: full
    description: The module talks to Home Assistant over the network from the controller.
seealso:
  - module: egors.homeassistant.entity_info
  - module: egors.homeassistant.area
  - module: egors.homeassistant.label
"""

EXAMPLES = r"""
- name: Name an entity and put it in the garden
  egors.homeassistant.entity:
    entity_id: sensor.aqara_temperature_3
    new_entity_id: sensor.garden_temperature
    name: Garden temperature
    area_id: garden
    labels: [outdoor]

- name: Hide and disable a diagnostic sensor
  egors.homeassistant.entity:
    entity_id: sensor.router_uptime
    hidden: true
    disabled: true
"""

RETURN = r"""
entity:
  description: The registry entry after the run (predicted in check mode).
  returned: always
  type: dict
  contains:
    entity_id:
      description: Entity ID.
      type: str
      sample: sensor.garden_temperature
    name:
      description: Name set by the user, or null if the integration's name is used.
      type: str
    icon:
      description: Icon set by the user, or null.
      type: str
    area_id:
      description: Area of the entity itself, or null if it follows its device.
      type: str
    device_class:
      description: Device class set by the user, or null.
      type: str
    aliases:
      description: Sorted aliases, without the entity's own name.
      type: list
      elements: str
    labels:
      description: Sorted label IDs.
      type: list
      elements: str
    disabled_by:
      description: Who disabled the entity (V(user), V(integration), V(device), ...), or null if it is enabled.
      type: str
    hidden_by:
      description: Who hid the entity, or null if it is visible.
      type: str
    original_name:
      description: Name given by the integration.
      type: str
    original_icon:
      description: Icon given by the integration.
      type: str
    original_device_class:
      description: Device class given by the integration.
      type: str
    device_id:
      description: ID of the device of the entity, or null.
      type: str
    platform:
      description: Integration that provides the entity.
      type: str
    unique_id:
      description: Unique ID within the integration.
      type: str
"""

from ansible_collections.egors.homeassistant.plugins.module_utils.api import HomeAssistantModule
from ansible_collections.egors.homeassistant.plugins.module_utils.entity import compute_changes, normalize, update_payload


def main():
    argument_spec = dict(
        entity_id=dict(type="str", required=True),
        new_entity_id=dict(type="str"),
        name=dict(type="str"),
        icon=dict(type="str"),
        area_id=dict(type="str"),
        device_class=dict(type="str"),
        aliases=dict(type="list", elements="str"),
        labels=dict(type="list", elements="str"),
        disabled=dict(type="bool"),
        hidden=dict(type="bool"),
    )
    module = HomeAssistantModule(argument_spec, supports_check_mode=True)
    params = module.params
    raw = module.call_optional("config/entity_registry/get", entity_id=params["entity_id"])
    if raw is None and params["new_entity_id"]:
        raw = module.call_optional("config/entity_registry/get", entity_id=params["new_entity_id"])
    if raw is None:
        module.fail_json(msg="entity %s is not in the entity registry" % params["entity_id"])

    before = normalize(raw)
    changes, after = compute_changes(params, before)
    if changes and not module.check_mode:
        payload = update_payload(changes, raw.get("aliases"))
        result = module.call("config/entity_registry/update", entity_id=before["entity_id"], **payload)
        after = normalize(result["entity_entry"])
        if "labels" in changes and after["labels"] != changes["labels"]:
            module.warn("Home Assistant stored labels=%r instead of the requested %r; unknown labels are dropped."
                        % (after["labels"], changes["labels"]))
    result = dict(changed=bool(changes), entity=after)
    if module._diff:
        result["diff"] = dict(before=before, after=after)
    module.exit_json(**result)


if __name__ == "__main__":
    main()

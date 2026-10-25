#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2026, Egor Sklyarov
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

DOCUMENTATION = r"""
module: core_config
short_description: Manage the Home Assistant core configuration
version_added: 0.1.0
author: Egor Sklyarov (@Egor-S)
description:
  - Reads and updates the core configuration of Home Assistant (location, units, time zone, URLs, and so on).
  - Only the options that are provided are compared and updated, all other settings are left untouched.
    Run the module without options to just read the current configuration.
extends_documentation_fragment:
  - egors.homeassistant.connection
options:
  location_name:
    description:
      - Name of the Home Assistant installation.
    type: str
  latitude:
    description:
      - Latitude of the home location.
    type: float
  longitude:
    description:
      - Longitude of the home location.
    type: float
  elevation:
    description:
      - Elevation of the home location in meters (or feet with the V(us_customary) unit system).
    type: int
  radius:
    description:
      - Radius of the home zone in meters.
    type: int
  unit_system:
    description:
      - Unit system.
    type: str
    choices: [metric, us_customary]
  time_zone:
    description:
      - IANA time zone name, for example V(Europe/Berlin).
    type: str
  currency:
    description:
      - ISO 4217 currency code, for example V(EUR).
      - It can not be cleared, Home Assistant rejects an empty value.
    type: str
  country:
    description:
      - ISO 3166 country code, for example V(DE).
      - It can not be cleared once set, Home Assistant rejects an empty value.
    type: str
  language:
    description:
      - Default language (RFC 5646), for example V(en).
    type: str
  external_url:
    description:
      - URL used to reach Home Assistant from the internet.
      - An empty string clears the setting.
    type: str
  internal_url:
    description:
      - URL used to reach Home Assistant from the local network.
      - An empty string clears the setting.
    type: str
requirements:
  - websocket-client
attributes:
  check_mode:
    support: full
    description: Reports the changes without applying them.
  diff_mode:
    support: full
    description: Shows the supported core configuration values before and after the run.
  platform:
    platforms: all
    support: full
    description: The module talks to Home Assistant over the network from the controller.
seealso:
  - module: egors.homeassistant.onboarding
"""

EXAMPLES = r"""
- name: Set location, units and time zone
  egors.homeassistant.core_config:
    url: http://homeassistant.local:8123
    token: "{{ ha_token }}"
    location_name: Home
    latitude: 52.52
    longitude: 13.405
    elevation: 34
    unit_system: metric
    time_zone: Europe/Berlin
    currency: EUR
    country: DE
  delegate_to: localhost

- name: Clear the external URL
  egors.homeassistant.core_config:
    url: http://homeassistant.local:8123
    token: "{{ ha_token }}"
    external_url: ""
  delegate_to: localhost

- name: Read the current configuration
  egors.homeassistant.core_config:
    url: http://homeassistant.local:8123
    token: "{{ ha_token }}"
  delegate_to: localhost
  register: core
"""

RETURN = r"""
config:
  description:
    - Supported core configuration values after the run (or as they would be after the run, in check mode).
    - V(unit_system) is V(metric) or V(us_customary). Unset URLs and country are V(null).
  returned: always
  type: dict
  sample:
    location_name: Home
    latitude: 52.52
    longitude: 13.405
    elevation: 34
    radius: 100
    unit_system: metric
    time_zone: Europe/Berlin
    currency: EUR
    country: DE
    language: en
    external_url: null
    internal_url: null
ha_version:
  description: Home Assistant version.
  returned: when known
  type: str
  sample: 2026.10.4
"""

from ansible_collections.egors.homeassistant.plugins.module_utils.api import HomeAssistantModule

KEYS = (
    "location_name", "latitude", "longitude", "elevation", "radius", "unit_system",
    "time_zone", "currency", "country", "language", "external_url", "internal_url",
)
URL_KEYS = ("external_url", "internal_url")
LENGTH_TO_SYSTEM = {"km": "metric", "mi": "us_customary"}


def normalize_config(raw):
    """Reduce a ``get_config`` reply to the supported keys with comparable types."""
    config = {}
    for key in KEYS:
        value = raw.get(key)
        if key == "unit_system":
            units = value if isinstance(value, dict) else {}
            if isinstance(value, str):
                value = {"imperial": "us_customary"}.get(value, value)
            else:
                value = LENGTH_TO_SYSTEM.get(units.get("length"))
        elif value is not None:
            if key in ("latitude", "longitude"):
                value = float(value)
            elif key in ("elevation", "radius"):
                value = int(value)
        config[key] = value
    return config


def desired_config(params):
    """Provided options only, with an empty URL string turned into ``None`` (clear)."""
    desired = {}
    for key in KEYS:
        value = params.get(key)
        if value is None:
            continue
        if key in URL_KEYS and value == "":
            value = None
        desired[key] = value
    return desired


def compute_changes(current, desired):
    """Subset of ``desired`` whose value differs from ``current``."""
    return {key: value for key, value in desired.items() if current.get(key) != value}


def main():
    argument_spec = dict(
        location_name=dict(type="str"),
        latitude=dict(type="float"),
        longitude=dict(type="float"),
        elevation=dict(type="int"),
        radius=dict(type="int"),
        unit_system=dict(type="str", choices=["metric", "us_customary"]),
        time_zone=dict(type="str"),
        currency=dict(type="str"),
        country=dict(type="str"),
        language=dict(type="str"),
        external_url=dict(type="str"),
        internal_url=dict(type="str"),
    )
    module = HomeAssistantModule(argument_spec, supports_check_mode=True)

    current = normalize_config(module.call("get_config"))
    changes = compute_changes(current, desired_config(module.params))
    after = dict(current)
    after.update(changes)

    if changes and not module.check_mode:
        module.call("config/core/update", **changes)
        after = normalize_config(module.call("get_config"))

    result = dict(changed=bool(changes), config=after)
    version = getattr(module.ws, "ha_version", None)
    if version:
        result["ha_version"] = version
    if module._diff:
        result["diff"] = dict(before=current, after=after)
    module.exit_json(**result)


if __name__ == "__main__":
    main()

#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) 2026, Egor Sklyarov
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

DOCUMENTATION = r"""
module: network
short_description: Choose the network adapters Home Assistant uses
version_added: 0.1.0
author: Egor Sklyarov (@Egor-S)
description:
  - Sets the network adapters that Home Assistant uses for discovery and other network features
    (Settings > System > Network > Network adapter).
  - Run the module without O(adapters) to just read the adapters.
extends_documentation_fragment:
  - egors.homeassistant.connection
options:
  adapters:
    description:
      - Names of the adapters to use, for example V(eth0). Compared as a set.
      - An empty list selects them automatically, the default.
      - Every name must be an adapter of the Home Assistant host.
    type: list
    elements: str
attributes:
  check_mode:
    support: full
    description: Reports whether the adapters would change without writing.
  diff_mode:
    support: full
    description: Shows the configured adapters before and after the run.
  platform:
    platforms: all
    support: full
    description: The module talks to Home Assistant over the network from the controller.
"""

EXAMPLES = r"""
- name: Use only the wired adapter
  egors.homeassistant.network:
    adapters: [eth0]
"""

RETURN = r"""
configured_adapters:
  description: Sorted names of the configured adapters after the run (predicted in check mode); empty when chosen automatically.
  returned: always
  type: list
  elements: str
  sample: [eth0]
adapters:
  description: Adapters of the host, as reported before the change.
  returned: always
  type: list
  elements: dict
  contains:
    name:
      description: Name of the adapter.
      type: str
    enabled:
      description: Whether Home Assistant uses it.
      type: bool
    default:
      description: Whether it holds the default route.
      type: bool
    ipv4:
      description: IPv4 addresses with C(address) and C(network_prefix).
      type: list
      elements: dict
    ipv6:
      description: IPv6 addresses.
      type: list
      elements: dict
"""

from ansible_collections.egors.homeassistant.plugins.module_utils.api import HomeAssistantModule


def main():
    module = HomeAssistantModule(dict(adapters=dict(type="list", elements="str")), supports_check_mode=True)
    network = module.call("network")
    names = [a["name"] for a in network["adapters"]]
    current = sorted(set(network.get("configured_adapters") or []))
    after = current
    if module.params["adapters"] is not None:
        after = sorted(set(module.params["adapters"]))
        unknown = [n for n in after if n not in names]
        if unknown:
            module.fail_json(msg="unknown adapters %s; the host has %s" % (", ".join(unknown), ", ".join(names)))
    changed = after != current
    if changed and not module.check_mode:
        after = sorted(module.call("network/configure", config=dict(configured_adapters=after))["configured_adapters"])
    adapters = [dict((k, a.get(k)) for k in ("name", "enabled", "default", "ipv4", "ipv6")) for a in network["adapters"]]
    result = dict(changed=changed, configured_adapters=after, adapters=adapters)
    if module._diff:
        result["diff"] = dict(before=dict(configured_adapters=current), after=dict(configured_adapters=after))
    module.exit_json(**result)


if __name__ == "__main__":
    main()

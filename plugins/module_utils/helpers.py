# -*- coding: utf-8 -*-
# Copyright (c) 2026, Egor Sklyarov
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

"""Field specs of the helper storage collections (``input_boolean``, ``counter``, ...), shared by their
modules and ``helper_info``. Helpers replace the whole item on update, see ``registry.py``."""

from __future__ import annotations

from ansible_collections.egors.homeassistant.plugins.module_utils.registry import Registry

HELPERS = {
    "input_boolean": dict(strings=("icon",), values=("initial",)),
    "input_button": dict(strings=("icon",)),
    "input_number": dict(strings=("icon", "unit_of_measurement"), values=("min", "max", "step", "initial", "mode"),
                         required=("min", "max")),
    "input_text": dict(strings=("icon", "pattern", "initial", "unit_of_measurement"), values=("min", "max", "mode")),
    "input_select": dict(strings=("icon", "initial"), values=("options",), required=("options",)),
    "counter": dict(strings=("icon",), ints=("minimum", "maximum"), values=("initial", "step", "restore")),
}


def helper_registry(module, domain):
    spec = HELPERS[domain]
    return Registry(module, domain, domain + "_id", spec.get("strings", ()), ints=spec.get("ints", ()),
                    values=spec.get("values", ()), required=spec.get("required", ()), entry_key="id", replace=True)

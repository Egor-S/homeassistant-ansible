# -*- coding: utf-8 -*-
# Copyright (c) 2026, Egor Sklyarov
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

from ansible_collections.egors.homeassistant.plugins.module_utils.registry import Registry
from ansible_collections.egors.homeassistant.plugins.modules import area_info

ENTRIES = [
    {"area_id": "kitchen", "name": "Kitchen", "aliases": ["x"], "created_at": 1},
    {"area_id": "bedroom", "name": "Bedroom"},
]


class FakeModule:
    def __init__(self, params):
        self.params = params
        self.result = None

    def call(self, command, **params):
        return ENTRIES

    def exit_json(self, **kwargs):
        self.result = kwargs


def info(**params):
    module = FakeModule(dict({"name": None, "area_id": None}, **params))
    Registry(module, "config/area_registry", "area_id", area_info.STRINGS, area_info.LISTS).info("areas")
    return module.result


def test_all_and_filters():
    assert [a["area_id"] for a in info()["areas"]] == ["kitchen", "bedroom"]
    assert [a["area_id"] for a in info(name=" BEDROOM")["areas"]] == ["bedroom"]
    assert [a["area_id"] for a in info(area_id="kitchen")["areas"]] == ["kitchen"]
    assert info(area_id="nope")["areas"] == []
    assert "created_at" not in info()["areas"][0]
    assert info()["areas"][0]["aliases"] == ["x"]

# -*- coding: utf-8 -*-
# Copyright (c) 2026, Egor Sklyarov
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

from ansible_collections.egors.homeassistant.plugins.modules import area, area_info
from ansible_collections.egors.homeassistant.plugins.module_utils.registry import Registry


def test_field_specs_match_between_modules():
    assert area.STRINGS == area_info.STRINGS
    assert area.LISTS == area_info.LISTS


class FakeModule:
    check_mode = False
    _diff = False

    def __init__(self, params):
        self.params = params
        self.calls = []
        self.warnings = []
        self.result = None

    def call(self, command, **params):
        self.calls.append((command, params))
        if command.endswith("/list"):
            return [{"area_id": "kitchen", "name": "Kitchen", "icon": "mdi:stove", "aliases": [], "labels": []}]
        return dict({"area_id": "new", "name": None, "aliases": []}, **dict(params, labels=[]))

    def warn(self, msg):
        self.warnings.append(msg)

    def exit_json(self, **kwargs):
        self.result = kwargs

    def fail_json(self, **kwargs):
        raise AssertionError(kwargs["msg"])


def run(params):
    base = dict(name=None, area_id=None, state="present", aliases=None, labels=None, icon=None, picture=None,
                floor_id=None, temperature_entity_id=None, humidity_entity_id=None)
    module = FakeModule(dict(base, **params))
    Registry(module, "config/area_registry", "area_id", area.STRINGS, area.LISTS).ensure("area")
    return module


def test_create_sends_only_provided_fields():
    module = run({"name": " Garage ", "icon": "mdi:garage", "floor_id": ""})
    assert module.calls[-1] == ("config/area_registry/create", {"name": "Garage", "icon": "mdi:garage"})
    assert module.result["changed"]


def test_noop_by_normalized_name():
    module = run({"name": "kitchen ", "icon": "mdi:stove"})
    assert not module.result["changed"]
    assert len(module.calls) == 1


def test_update_only_changed_fields():
    module = run({"name": "Kitchen", "icon": ""})
    assert module.calls[-1] == ("config/area_registry/update", {"area_id": "kitchen", "icon": None})


def test_rename_by_id():
    module = run({"area_id": "kitchen", "name": "Cookery"})
    assert module.calls[-1] == ("config/area_registry/update", {"area_id": "kitchen", "name": "Cookery"})


def test_dropped_label_warns():
    module = run({"name": "Kitchen", "labels": ["nolabel"]})
    assert module.warnings

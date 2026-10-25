# -*- coding: utf-8 -*-
# Copyright (c) 2026, Egor Sklyarov
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

import pytest

from ansible_collections.egors.homeassistant.plugins.modules import zone, zone_info
from ansible_collections.egors.homeassistant.plugins.module_utils.registry import Registry

ENTRIES = [
    {"id": "office", "name": "Office", "latitude": 60.1, "longitude": 24.9, "radius": 100.0, "passive": False},
    {"id": "gym", "name": "Gym", "latitude": 1.0, "longitude": 2.0, "radius": 50.0, "passive": True,
     "icon": "mdi:dumbbell"},
    {"id": "gym_2", "name": "gym", "latitude": 3.0, "longitude": 4.0, "radius": 50.0, "passive": False},
]


def test_field_specs_match_between_modules():
    assert zone.STRINGS == zone_info.STRINGS
    assert zone.VALUES == zone_info.VALUES


class Failed(Exception):
    pass


class FakeModule:
    check_mode = False
    _diff = False

    def __init__(self, params):
        self.params = params
        self.calls = []
        self.result = None

    def call(self, command, **params):
        self.calls.append((command, params))
        if command == "zone/list":
            return ENTRIES
        if command == "zone/create":
            return dict({"id": "new", "radius": 100.0, "passive": False}, **params)
        entry = next(e for e in ENTRIES if e["id"] == params["zone_id"])
        return dict(entry, **dict((k, v) for k, v in params.items() if k != "zone_id"))

    def warn(self, msg):
        raise AssertionError(msg)

    def exit_json(self, **kwargs):
        self.result = kwargs

    def fail_json(self, **kwargs):
        raise Failed(kwargs["msg"])


def run(params):
    base = dict(name=None, zone_id=None, state="present", latitude=None, longitude=None, radius=None, passive=None,
                icon=None)
    module = FakeModule(dict(base, **params))
    Registry(module, "zone", "zone_id", zone.STRINGS, values=zone.VALUES, entry_key="id", unclearable=("icon",),
             required=("latitude", "longitude")).ensure("zone")
    return module


def test_noop_with_int_radius():
    module = run({"name": "office", "radius": 100.0, "passive": False})
    assert not module.result["changed"]
    assert module.result["zone"]["zone_id"] == "office"


def test_update_passes_zone_id():
    module = run({"name": "Office", "radius": 250.0})
    assert module.calls[-1] == ("zone/update", {"zone_id": "office", "radius": 250.0})
    assert module.result["zone"]["radius"] == 250.0


def test_create_needs_coordinates():
    with pytest.raises(Failed, match="latitude and longitude are required"):
        run({"name": "Shop"})
    with pytest.raises(Failed, match="longitude is required"):
        run({"name": "Shop", "latitude": 1.0})


def test_create():
    module = run({"name": "Shop", "latitude": 1.0, "longitude": 2.0, "passive": False})
    assert module.calls[-1] == ("zone/create", {"name": "Shop", "latitude": 1.0, "longitude": 2.0, "passive": False})
    assert module.result["zone"]["zone_id"] == "new"


def test_ambiguous_name_fails_but_id_works():
    with pytest.raises(Failed, match="2 entries"):
        run({"name": "GYM", "radius": 10.0})
    module = run({"zone_id": "gym_2", "radius": 10.0})
    assert module.calls[-1] == ("zone/update", {"zone_id": "gym_2", "radius": 10.0})


def test_icon_can_not_be_removed():
    with pytest.raises(Failed, match="icon can not be removed"):
        run({"zone_id": "gym", "icon": ""})


def test_delete_by_id():
    module = run({"zone_id": "gym", "state": "absent"})
    assert module.calls[-1] == ("zone/delete", {"zone_id": "gym"})

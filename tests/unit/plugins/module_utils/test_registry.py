# -*- coding: utf-8 -*-
# Copyright (c) 2026, Egor Sklyarov
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

import pytest

from ansible_collections.egors.homeassistant.plugins.module_utils.registry import (
    compute_changes,
    desired_values,
    find_entries,
    find_entry,
    normalize_entry,
    normalize_name,
)

STRINGS = ("icon", "floor_id")
LISTS = ("aliases", "labels")
ENTRIES = [
    {"area_id": "kitchen", "name": "Kitchen", "icon": "mdi:stove", "aliases": ["b", "a"], "created_at": 1.0},
    {"area_id": "big_room", "name": "Big  Room", "aliases": None},
]


@pytest.mark.parametrize("name, expected", [
    ("Kitchen", "kitchen"), ("  KITCHEN ", "kitchen"), ("Big \t Room", "big room"), ("Straße", "strasse"),
])
def test_normalize_name(name, expected):
    assert normalize_name(name) == expected


def test_normalize_entry_drops_timestamps_and_sorts():
    entry = normalize_entry(ENTRIES[0], "area_id", STRINGS, LISTS)
    assert entry == {"area_id": "kitchen", "name": "Kitchen", "icon": "mdi:stove", "floor_id": None,
                     "aliases": ["a", "b"], "labels": []}


def test_find_entry():
    assert find_entry(ENTRIES, "area_id", entry_id="kitchen") is ENTRIES[0]
    assert find_entry(ENTRIES, "area_id", entry_id="nope") is None
    assert find_entry(ENTRIES, "area_id", name=" kitchen ") is ENTRIES[0]
    assert find_entry(ENTRIES, "area_id", name="big room") is ENTRIES[1]
    assert find_entry(ENTRIES, "area_id", name="nope") is None
    # id wins over name
    assert find_entry(ENTRIES, "area_id", entry_id="big_room", name="Kitchen") is ENTRIES[1]


def test_desired_values():
    params = {"icon": "", "floor_id": None, "aliases": ["b", "a", "b"], "labels": []}
    assert desired_values(params, STRINGS, LISTS) == {"icon": None, "aliases": ["a", "b"], "labels": []}


def test_compute_changes():
    current = normalize_entry(ENTRIES[0], "area_id", STRINGS, LISTS)
    assert compute_changes(current, {"icon": "mdi:stove", "aliases": ["a", "b"]}) == {}
    assert compute_changes(current, {"icon": None, "aliases": ["a"], "floor_id": None}) == {
        "icon": None, "aliases": ["a"]}


def test_ints_zero_is_a_value_and_empty_string_clears():
    assert desired_values({"level": 0}, (), (), ("level",)) == {"level": 0}
    assert desired_values({"level": "-2"}, (), (), ("level",)) == {"level": -2}
    assert desired_values({"level": ""}, (), (), ("level",)) == {"level": None}
    assert desired_values({"level": None}, (), (), ("level",)) == {}


@pytest.mark.parametrize("value", ["abc", True, 1.5, []])
def test_ints_rejects_non_integers(value):
    with pytest.raises(ValueError):
        desired_values({"level": value}, (), (), ("level",))


def test_normalize_entry_ints():
    entry = {"floor_id": "f", "name": "F", "level": 0}
    assert normalize_entry(entry, "floor_id", (), (), ("level",)) == {"floor_id": "f", "name": "F", "level": 0}
    assert normalize_entry({}, "floor_id", (), (), ("level",))["level"] is None
    assert compute_changes({"level": 0}, {"level": 0}) == {}
    assert compute_changes({"level": 0}, {"level": None}) == {"level": None}


def test_values_and_entry_key():
    entry = {"id": "office", "name": "Office", "radius": 100.0, "passive": False}
    assert normalize_entry(entry, "zone_id", (), (), values=("radius", "passive"), entry_key="id") == {
        "zone_id": "office", "name": "Office", "radius": 100.0, "passive": False}
    assert desired_values({"radius": 0.0, "passive": False, "x": None}, (), (), values=("radius", "passive", "x")) == {
        "radius": 0.0, "passive": False}


def test_find_entries_returns_all_name_matches():
    entries = [{"id": "a", "name": "Gym"}, {"id": "b", "name": " gym"}, {"id": "c", "name": "Pool"}]
    assert [e["id"] for e in find_entries(entries, "id", name="GYM")] == ["a", "b"]
    assert [e["id"] for e in find_entries(entries, "id", entry_id="c")] == ["c"]

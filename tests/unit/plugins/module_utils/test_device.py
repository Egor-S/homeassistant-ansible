# -*- coding: utf-8 -*-
# Copyright (c) 2026, Egor Sklyarov
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

from ansible_collections.egors.homeassistant.plugins.module_utils.device import compute_changes, matches_name, normalize

RAW = {"id": "d1", "name": "Sun", "name_by_user": "", "area_id": None, "labels": ["b", "a"],
       "disabled_by": "integration", "identifiers": [["sun", "x"]], "created_at": 1}
PARAMS = dict(name_by_user=None, area_id=None, labels=None, disabled=None)


def test_normalize():
    entry = normalize(RAW)
    assert entry["device_id"] == "d1"
    assert entry["name_by_user"] is None
    assert entry["labels"] == ["a", "b"]
    assert entry["identifiers"] == [["sun", "x"]]
    assert "created_at" not in entry


def test_matches_either_name():
    assert matches_name(RAW, " SUN ")
    assert matches_name(dict(RAW, name_by_user="Sky"), "sky")
    assert not matches_name(RAW, "Moon")


def test_changes():
    current = normalize(RAW)
    assert compute_changes(dict(PARAMS, name_by_user="", labels=["a", "b"], disabled=True), current)[0] == {}
    changes, predicted = compute_changes(dict(PARAMS, name_by_user="Sky", area_id="garden", disabled=False), current)
    assert changes == {"name_by_user": "Sky", "area_id": "garden", "disabled_by": None}
    assert predicted["name_by_user"] == "Sky"

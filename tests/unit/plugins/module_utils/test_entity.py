# -*- coding: utf-8 -*-
# Copyright (c) 2026, Egor Sklyarov
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

from ansible_collections.egors.homeassistant.plugins.module_utils.entity import compute_changes, normalize, update_payload

RAW = {"entity_id": "sensor.dawn", "name": None, "icon": None, "area_id": None, "device_class": None,
       "aliases": [None, "b", "a"], "labels": [], "disabled_by": "integration", "hidden_by": None,
       "original_name": "Next dawn", "platform": "sun", "created_at": 1}

PARAMS = dict(new_entity_id=None, name=None, icon=None, area_id=None, device_class=None, aliases=None, labels=None,
              disabled=None, hidden=None)


def changes(**params):
    return compute_changes(dict(PARAMS, **params), normalize(RAW))


def test_normalize_drops_the_computed_alias():
    entry = normalize(RAW)
    assert entry["aliases"] == ["a", "b"]
    assert "created_at" not in entry


def test_no_changes():
    assert changes(aliases=["b", "a", "a"], name="", disabled=True, hidden=False)[0] == {}


def test_changes_and_prediction():
    payload, predicted = changes(name="Dawn", icon="mdi:x", disabled=False, hidden=True,
                                 new_entity_id="sensor.ansible_dawn")
    assert payload == {"name": "Dawn", "icon": "mdi:x", "disabled_by": None, "hidden_by": "user",
                       "new_entity_id": "sensor.ansible_dawn"}
    assert predicted["entity_id"] == "sensor.ansible_dawn"
    assert predicted["disabled_by"] is None
    assert "new_entity_id" not in predicted


def test_rename_to_the_current_id_is_no_change():
    assert changes(new_entity_id="sensor.dawn")[0] == {}


def test_update_payload_keeps_the_computed_alias():
    assert update_payload({"aliases": ["c"]}, [None, "a"]) == {"aliases": [None, "c"]}
    assert update_payload({"aliases": ["c"]}, ["a"]) == {"aliases": ["c"]}
    assert update_payload({"name": "x"}, [None]) == {"name": "x"}

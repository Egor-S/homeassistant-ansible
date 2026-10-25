# -*- coding: utf-8 -*-
# Copyright (c) 2026, Egor Sklyarov
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

import pytest

from ansible_collections.egors.homeassistant.plugins.module_utils.backup import OPTIONS, compute_update, flatten, predict

CONFIG = {
    "agents": {}, "automatic_backups_configured": False,
    "create_backup": {"agent_ids": ["backup.local"], "include_database": True, "include_folders": None,
                      "name": None, "password": "secret"},
    "retention": {"copies": 3, "days": None},
    "schedule": {"days": [], "recurrence": "daily", "time": "04:45:00"},
    "next_automatic_backup": None,
}
PARAMS = dict((option, None) for option in OPTIONS)


def update(**params):
    return compute_update(dict(PARAMS, **params), CONFIG)


def test_flatten_hides_the_password():
    flat = flatten(CONFIG)
    assert "password" not in flat
    assert flat["password_set"] is True
    assert flat["retention_copies"] == 3 and flat["schedule_time"] == "04:45:00"


def test_no_changes_with_other_spellings():
    assert update(agent_ids=["backup.local", "backup.local"], schedule_time="4:45", password="secret",
                  retention_days=0, name="") == ({}, [])


def test_retention_is_sent_complete():
    payload, changed = update(retention_days=7)
    assert payload == {"retention": {"copies": 3, "days": 7}}
    assert changed == ["retention_days"]


def test_sections_and_top_level():
    payload = update(password="", schedule_recurrence="custom_days", schedule_days=["tue", "mon"],
                     automatic_backups_configured=True)[0]
    assert payload == {"create_backup": {"password": None},
                       "schedule": {"recurrence": "custom_days", "days": ["mon", "tue"]},
                       "automatic_backups_configured": True}
    predicted = predict(CONFIG, payload)
    assert predicted["schedule"]["time"] == "04:45:00"
    assert flatten(predicted)["password_set"] is False


def test_invalid_time():
    with pytest.raises(ValueError):
        update(schedule_time="late")

# -*- coding: utf-8 -*-
# Copyright (c) 2026, Egor Sklyarov
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

import pytest

from ansible_collections.egors.homeassistant.plugins.module_utils.user import (
    compute_changes,
    find_user,
    is_normalized,
    normalize,
)

USERS = [
    {"id": "s", "username": None, "name": "Home Assistant Content", "system_generated": True,
     "group_ids": ["system-read-only"]},
    {"id": "o", "username": "admin", "name": "Admin", "is_owner": True, "is_active": True, "local_only": False,
     "system_generated": False, "group_ids": ["system-admin"]},
]
PARAMS = dict(name=None, admin=None, active=None, local_only=None)


@pytest.mark.parametrize("username, ok", [("jane", True), ("Jane", False), (" jane", False), ("", False),
                                          ("jane.doe", True)])
def test_is_normalized(username, ok):
    assert is_normalized(username) is ok


def test_find_user_skips_system_users():
    assert find_user(USERS, "admin")["id"] == "o"
    assert find_user(USERS, None) is None


def test_normalize():
    assert normalize(USERS[1]) == {"user_id": "o", "username": "admin", "name": "Admin", "admin": True,
                                   "active": True, "local_only": False, "owner": True}


def test_compute_changes():
    current = normalize(USERS[1])
    assert compute_changes(dict(PARAMS, name="Admin", admin=True, active=True), current)[0] == {}
    changes, predicted = compute_changes(dict(PARAMS, admin=False, local_only=True), current)
    assert changes == {"group_ids": ["system-users"], "local_only": True}
    assert predicted["admin"] is False and predicted["local_only"] is True

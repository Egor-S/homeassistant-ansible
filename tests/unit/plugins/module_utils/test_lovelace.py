# -*- coding: utf-8 -*-
# Copyright (c) 2026, Egor Sklyarov
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

from ansible_collections.egors.homeassistant.plugins.module_utils.lovelace import (
    dashboard_changes,
    normalize_dashboard,
    normalize_resource,
)

ENTRY = {"id": "home_energy", "url_path": "home-energy", "title": "Energy", "icon": "mdi:x", "show_in_sidebar": True,
         "require_admin": False, "mode": "storage"}
PARAMS = dict(title=None, icon=None, show_in_sidebar=None, require_admin=None)


def test_normalize():
    assert normalize_dashboard(ENTRY) == {"url_path": "home-energy", "dashboard_id": "home_energy", "title": "Energy",
                                          "icon": "mdi:x", "show_in_sidebar": True, "require_admin": False}
    assert normalize_dashboard({"id": "d", "url_path": "a-b", "title": "T"})["icon"] is None
    assert normalize_resource({"id": "r", "url": "/x.js", "type": "module"}) == {
        "resource_id": "r", "url": "/x.js", "type": "module"}


def test_dashboard_changes():
    current = normalize_dashboard(ENTRY)
    assert dashboard_changes(dict(PARAMS, title="Energy", show_in_sidebar=True), current) == {}
    changes = dashboard_changes(dict(PARAMS, icon="", require_admin=True), current)
    assert changes == {"icon": None, "require_admin": True}

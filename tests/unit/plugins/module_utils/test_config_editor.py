# -*- coding: utf-8 -*-
# Copyright (c) 2026, Egor Sklyarov
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

import pytest

from ansible_collections.egors.homeassistant.plugins.module_utils.config_editor import ConfigEditor


class Failed(Exception):
    pass


class FakeModule:
    check_mode = False
    _diff = True

    def __init__(self, params, stored):
        self.params = params
        self.stored = stored
        self.requests = []
        self.result = None

    def rest(self, path, method="GET", data=None):
        self.requests.append((method, path, data))
        if method == "GET":
            return (200, self.stored) if self.stored is not None else (404, {"message": "Resource not found"})
        return 200, {"result": "ok"}

    def exit_json(self, **kwargs):
        self.result = kwargs

    def fail_json(self, **kwargs):
        raise Failed(kwargs["msg"])


def run(params, stored, domain="automation", id_in_value=True):
    module = FakeModule(dict(dict(automation_id="a 1", state="present", config=None), **params), stored)
    ConfigEditor(module, domain, "automation_id", id_in_value).ensure()
    return module


def test_unchanged_ignores_the_stored_id():
    module = run({"config": {"alias": "A", "actions": []}}, {"id": "a 1", "actions": [], "alias": "A"})
    assert not module.result["changed"]
    assert module.requests == [("GET", "/api/config/automation/config/a%201", None)]


def test_create_posts_without_id():
    module = run({"config": {"id": "a 1", "alias": "A"}}, None)
    assert module.result["changed"]
    assert module.requests[-1] == ("POST", "/api/config/automation/config/a%201", {"alias": "A"})
    assert module.result["diff"] == {"before": {}, "after": {"alias": "A"}}


def test_conflicting_id_fails():
    with pytest.raises(Failed, match="differs"):
        run({"config": {"id": "other"}}, None)


def test_delete():
    module = run({"state": "absent"}, {"id": "a 1", "alias": "A"})
    assert module.requests[-1][0] == "DELETE"
    assert module.result["config"] == {}
    assert not run({"state": "absent"}, None).result["changed"]

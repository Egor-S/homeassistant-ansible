# -*- coding: utf-8 -*-
# Copyright (c) 2026, Egor Sklyarov
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

import pytest

from ansible_collections.egors.homeassistant.plugins.module_utils.config_entry import (
    FlowError,
    describe_step,
    find_entries,
    run_flow,
)

MENU = {"type": "menu", "flow_id": "f", "step_id": "user", "menu_options": ["sensor", "switch"]}
FIELDS = [{"name": "name", "required": True},
          {"name": "unit", "required": False, "description": {"suggested_value": "secret"}}]
FORM = {"type": "form", "flow_id": "f", "step_id": "sensor", "errors": None, "data_schema": FIELDS}
DONE = {"type": "create_entry", "flow_id": "f", "result": {"entry_id": "e"}}


class FakeRest:
    def __init__(self, *responses):
        self.responses = list(responses)
        self.calls = []

    def __call__(self, path, method, data):
        self.calls.append((path, method, data))
        if method == "DELETE":
            return 200, {"message": "Flow aborted"}
        return self.responses.pop(0)


def test_menu_then_form():
    rest = FakeRest((200, MENU), (200, FORM), (200, DONE))
    assert run_flow(rest, "/flow", {"handler": "template"}, [{"next_step_id": "sensor"}, {"name": "x"}]) == DONE
    assert [c[2] for c in rest.calls] == [{"handler": "template"}, {"next_step_id": "sensor"}, {"name": "x"}]


def test_missing_step_aborts_the_flow_and_hides_values():
    rest = FakeRest((200, FORM))
    with pytest.raises(FlowError) as e:
        run_flow(rest, "/flow", {}, [])
    assert "form 'sensor' with fields name, unit?" in str(e.value)
    assert "secret" not in str(e.value)
    assert rest.calls[-1] == ("/flow/f", "DELETE", None)


def test_errors_and_external_steps_abort():
    with pytest.raises(FlowError, match="rejected"):
        run_flow(FakeRest((200, FORM), (200, dict(FORM, errors={"base": "x"}))), "/flow", {}, [{"name": "x"}])
    with pytest.raises(FlowError, match="not supported"):
        run_flow(FakeRest((200, {"type": "external", "flow_id": "f", "step_id": "auth"})), "/flow", {}, [])


def test_find_entries_and_describe():
    entries = [{"domain": "a", "title": "Family "}, {"domain": "b", "title": "Family"}]
    assert find_entries(entries, "a", "family") == [entries[0]]
    assert describe_step(MENU) == "menu 'user' with options sensor, switch"

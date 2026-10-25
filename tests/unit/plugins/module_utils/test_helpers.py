# -*- coding: utf-8 -*-
# Copyright (c) 2026, Egor Sklyarov
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

import importlib

import pytest

from ansible_collections.egors.homeassistant.plugins.module_utils.helpers import HELPERS, helper_registry


@pytest.mark.parametrize("domain", sorted(HELPERS))
def test_every_field_is_an_option_of_its_module(domain, monkeypatch):
    module = importlib.import_module("ansible_collections.egors.homeassistant.plugins.modules." + domain)
    captured = {}

    class Capture(Exception):
        pass

    def fake_module(argument_spec, **kwargs):
        captured.update(argument_spec)
        raise Capture()

    monkeypatch.setattr(module, "HomeAssistantModule", fake_module)
    with pytest.raises(Capture):
        module.main()
    spec = HELPERS[domain]
    fields = set(spec.get("strings", ())) | set(spec.get("ints", ())) | set(spec.get("values", ()))
    assert set(captured) == fields | {"name", domain + "_id", "state"}


class FakeModule:
    check_mode = False
    _diff = False

    def __init__(self, params, entries):
        self.params = params
        self.entries = entries
        self.calls = []
        self.result = None

    def call(self, command, **params):
        self.calls.append((command, params))
        if command.endswith("/list"):
            return self.entries
        return dict({"id": params.get(command.split("/")[0] + "_id", "new")}, **params)

    def warn(self, msg):
        raise AssertionError(msg)

    def exit_json(self, **kwargs):
        self.result = kwargs

    def fail_json(self, **kwargs):
        raise AssertionError(kwargs["msg"])


NUMBER = {"id": "target", "name": "Target", "min": 15.0, "max": 25.0, "step": 1.0, "mode": "slider", "icon": "mdi:x",
          "unit_of_measurement": "°C"}


def run(domain, params, entries):
    base = dict((k, None) for k in ("name", domain + "_id", "icon", "min", "max", "step", "initial", "mode",
                                    "unit_of_measurement", "minimum", "maximum", "restore", "options", "pattern"))
    module = FakeModule(dict(base, state="present", **params), entries)
    helper_registry(module, domain).ensure(domain)
    return module


def test_update_sends_the_whole_item():
    module = run("input_number", {"name": "target", "step": 0.5}, [NUMBER])
    assert module.calls[-1] == ("input_number/update", {
        "input_number_id": "target", "name": "Target", "min": 15.0, "max": 25.0, "step": 0.5, "mode": "slider",
        "icon": "mdi:x", "unit_of_measurement": "°C"})
    assert module.result["input_number"]["step"] == 0.5


def test_clearing_leaves_the_field_out():
    module = run("input_number", {"input_number_id": "target", "icon": "", "unit_of_measurement": ""}, [NUMBER])
    payload = module.calls[-1][1]
    assert "icon" not in payload and "unit_of_measurement" not in payload
    assert module.result["input_number"]["icon"] is None


def test_noop_with_integer_values():
    module = run("input_number", {"name": "Target", "min": 15, "max": 25}, [NUMBER])
    assert not module.result["changed"]


def test_options_are_ordered():
    entries = [{"id": "mode", "name": "Mode", "options": ["Home", "Away"]}]
    assert not run("input_select", {"name": "Mode", "options": ["Home", "Away"]}, entries).result["changed"]
    module = run("input_select", {"name": "Mode", "options": ["Away", "Home"]}, entries)
    assert module.calls[-1] == ("input_select/update", {"input_select_id": "mode", "name": "Mode",
                                                        "options": ["Away", "Home"]})


def test_counter_limits_clear():
    entries = [{"id": "c", "name": "C", "initial": 0, "step": 1, "minimum": 0, "maximum": 10, "restore": True}]
    module = run("counter", {"counter_id": "c", "maximum": ""}, entries)
    assert module.calls[-1] == ("counter/update", {"counter_id": "c", "name": "C", "initial": 0, "step": 1,
                                                   "minimum": 0, "restore": True})

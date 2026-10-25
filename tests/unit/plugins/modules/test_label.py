# -*- coding: utf-8 -*-
# Copyright (c) 2026, Egor Sklyarov
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

from ansible_collections.egors.homeassistant.plugins.modules import label, label_info
from ansible_collections.egors.homeassistant.plugins.module_utils.registry import Registry


def test_field_specs_match_between_modules():
    assert label.STRINGS == label_info.STRINGS


class FakeModule:
    check_mode = False
    _diff = False

    def __init__(self, params):
        self.params = params
        self.calls = []
        self.result = None

    def call(self, command, **params):
        self.calls.append((command, params))
        if command.endswith("/list"):
            return [{"label_id": "outdoor", "name": "Outdoor", "icon": None, "color": "green", "description": "",
                     "created_at": 1}]
        return dict({"label_id": "outdoor", "name": "Outdoor", "icon": None, "color": "green"}, **params)

    def warn(self, msg):
        raise AssertionError(msg)

    def exit_json(self, **kwargs):
        self.result = kwargs

    def fail_json(self, **kwargs):
        raise AssertionError(kwargs["msg"])


def run(params):
    base = dict(name=None, label_id=None, state="present", icon=None, color=None, description=None)
    module = FakeModule(dict(base, **params))
    Registry(module, "config/label_registry", "label_id", label.STRINGS).ensure("label")
    return module


def test_noop():
    module = run({"name": "outdoor", "color": "green"})
    assert not module.result["changed"]
    assert module.result["label"] == {"label_id": "outdoor", "name": "Outdoor", "icon": None, "color": "green",
                                      "description": ""}


def test_update_color_and_clear_description():
    module = run({"name": "Outdoor", "color": "#00ff00", "description": ""})
    assert module.calls[-1] == ("config/label_registry/update",
                                {"label_id": "outdoor", "color": "#00ff00", "description": None})

# -*- coding: utf-8 -*-
# Copyright (c) 2026, Egor Sklyarov
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

from ansible_collections.egors.homeassistant.plugins.modules import category, category_info
from ansible_collections.egors.homeassistant.plugins.module_utils.registry import Registry


def test_field_specs_match_between_modules():
    assert category.STRINGS == category_info.STRINGS


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
            return [{"category_id": "c1", "name": "Lighting", "icon": None}]
        return dict({"category_id": "c2"}, **params)

    def warn(self, msg):
        raise AssertionError(msg)

    def exit_json(self, **kwargs):
        self.result = kwargs


def test_scope_is_sent_with_every_command():
    module = FakeModule(dict(scope="automation", name="Lighting", category_id=None, state="absent", icon=None))
    Registry(module, "config/category_registry", "category_id", category.STRINGS,
             common=dict(scope="automation")).ensure("category")
    assert module.calls == [("config/category_registry/list", {"scope": "automation"}),
                            ("config/category_registry/delete", {"scope": "automation", "category_id": "c1"})]

# -*- coding: utf-8 -*-
# Copyright (c) 2026, Egor Sklyarov
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

import pytest

from ansible_collections.egors.homeassistant.plugins.modules import person, person_info, tag, tag_info
from ansible_collections.egors.homeassistant.plugins.module_utils.registry import Registry


def test_field_specs_match_between_modules():
    assert person.STRINGS == person_info.STRINGS
    assert person.LISTS == person_info.LISTS
    assert tag.VALUES == tag_info.VALUES


class Failed(Exception):
    pass


class FakeModule:
    check_mode = False
    _diff = False

    def __init__(self, params, listing):
        self.params = params
        self.listing = listing
        self.calls = []
        self.result = None

    def call(self, command, **params):
        self.calls.append((command, params))
        if command.endswith("/list"):
            return self.listing
        prefix = command.split("/")[0]
        return dict({"id": params.get(prefix + "_id", "new")},
                    **dict((k, v) for k, v in params.items() if k != prefix + "_id"))

    def warn(self, msg):
        raise AssertionError(msg)

    def exit_json(self, **kwargs):
        self.result = kwargs

    def fail_json(self, **kwargs):
        raise Failed(kwargs["msg"])


PEOPLE = {"storage": [{"id": "jane", "name": "Jane", "user_id": None, "device_trackers": ["device_tracker.b"]}],
          "config": [{"id": "yaml", "name": "Yaml"}]}


def run_person(params):
    base = dict(name=None, person_id=None, state="present", user_id=None, device_trackers=None, picture=None)
    module = FakeModule(dict(base, **params), PEOPLE)
    Registry(module, "person", "person_id", person.STRINGS, person.LISTS, entry_key="id",
             list_key="storage").ensure("person")
    return module


def test_person_reads_storage_entries_only():
    module = run_person({"name": "jane", "device_trackers": ["device_tracker.b", "device_tracker.b"]})
    assert not module.result["changed"]
    module = run_person({"name": "Yaml"})
    assert module.calls[-1] == ("person/create", {"name": "Yaml"})


def test_person_update():
    module = run_person({"person_id": "jane", "device_trackers": ["device_tracker.a"], "user_id": "u1"})
    assert module.calls[-1] == ("person/update", {"person_id": "jane", "device_trackers": ["device_tracker.a"],
                                                  "user_id": "u1"})


TAGS = [{"id": "abc", "name": "Card", "description": ""}]


def run_tag(params, check_mode=False):
    module = FakeModule(dict(dict(tag_id=None, name=None, state="present", description=None), **params), TAGS)
    module.check_mode = check_mode
    Registry(module, "tag", "tag_id", values=tag.VALUES, entry_key="id", create_with_id=True).ensure("tag")
    return module


def test_tag_created_with_its_id_and_without_name():
    module = run_tag({"tag_id": "new_tag"})
    assert module.calls[-1] == ("tag/create", {"tag_id": "new_tag"})
    assert module.result["tag"]["tag_id"] == "new_tag"


def test_tag_check_mode_predicts_the_id():
    module = run_tag({"tag_id": "new_tag", "name": "Door"}, check_mode=True)
    assert module.result["tag"] == {"tag_id": "new_tag", "name": "Door", "description": None}
    assert len(module.calls) == 1


def test_tag_empty_description_is_a_value():
    assert not run_tag({"tag_id": "abc", "description": ""}).result["changed"]
    module = run_tag({"tag_id": "abc", "description": "x", "name": "Card"})
    assert module.calls[-1] == ("tag/update", {"tag_id": "abc", "description": "x"})


def test_tag_empty_name_fails():
    with pytest.raises(Failed, match="empty"):
        run_tag({"tag_id": "abc", "name": " "})

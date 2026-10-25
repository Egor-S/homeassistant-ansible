# -*- coding: utf-8 -*-
# Copyright (c) 2026, Egor Sklyarov
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

import pytest

from ansible_collections.egors.homeassistant.plugins.modules.onboarding import (
    derive_client_id,
    is_valid_client_id,
    parse_steps,
    pending_steps,
    redirect_uri,
)


@pytest.mark.parametrize("url", ["http://127.0.0.1:8123", "http://127.0.0.1:8123/", "http://127.0.0.1:8123//"])
def test_derive_client_id(url):
    assert derive_client_id(url) == "http://127.0.0.1:8123/"


@pytest.mark.parametrize("client_id, expected", [
    ("http://127.0.0.1:8123/", True),
    ("https://ha.example.com", True),
    ("foo", False),
    ("ftp://ha.example.com/", False),
    ("http://", False),
])
def test_is_valid_client_id(client_id, expected):
    assert is_valid_client_id(client_id) is expected


def test_redirect_uri():
    assert redirect_uri("http://127.0.0.1:8123/") == "http://127.0.0.1:8123/?auth_callback=1"


def test_parse_steps():
    payload = [{"step": "user", "done": True}, {"step": "core_config", "done": False}]
    assert parse_steps(payload) == {"user": True, "core_config": False}


@pytest.mark.parametrize("payload", [None, {"message": "x"}, "text", [{"done": True}], ["user"]])
def test_parse_steps_malformed(payload):
    assert parse_steps(payload) is None


def test_pending_steps_fresh():
    steps = {"integration": False, "analytics": False, "core_config": False, "user": False}
    assert pending_steps(steps) == ["user", "core_config", "analytics", "integration"]


def test_pending_steps_partial_and_unknown():
    steps = {"user": True, "core_config": False, "analytics": True, "integration": False, "zeta": False}
    assert pending_steps(steps) == ["core_config", "integration", "zeta"]


def test_pending_steps_done():
    assert pending_steps({"user": True, "core_config": True, "analytics": True, "integration": True}) == []

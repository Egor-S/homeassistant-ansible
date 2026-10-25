# -*- coding: utf-8 -*-
# Copyright (c) 2026, Egor Sklyarov
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

import pytest

from ansible_collections.egors.homeassistant.plugins.modules.onboarding import (
    parse_steps,
    pending_steps,
)


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

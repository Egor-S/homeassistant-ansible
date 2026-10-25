# -*- coding: utf-8 -*-
# Copyright (c) 2026, Egor Sklyarov
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

from ansible_collections.egors.homeassistant.plugins.modules.logger_level import LEVELS, level_name


def test_level_names():
    assert [level_name(LEVELS[name]) for name in LEVELS] == list(LEVELS)
    assert level_name(0) == "0"
    assert level_name(25) == "25"

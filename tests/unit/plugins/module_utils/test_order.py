# -*- coding: utf-8 -*-
# Copyright (c) 2026, Egor Sklyarov
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

import pytest

from ansible_collections.egors.homeassistant.plugins.module_utils.order import new_order


def test_wanted_first_then_the_rest():
    assert new_order(["a", "b", "c", "d"], ["c", "a"]) == ["c", "a", "b", "d"]
    assert new_order(["a", "b"], ["b", "b"]) == ["b", "a"]
    assert new_order(["a", "b"], []) == ["a", "b"]


def test_unknown_ids():
    with pytest.raises(ValueError, match="x, y"):
        new_order(["a"], ["x", "a", "y"])

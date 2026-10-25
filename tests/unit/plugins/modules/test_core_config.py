# -*- coding: utf-8 -*-
# Copyright (c) 2026, Egor Sklyarov
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

import pytest

from ansible_collections.egors.homeassistant.plugins.modules.core_config import (
    compute_changes,
    desired_config,
    normalize_config,
)

RAW = {
    "latitude": 0, "longitude": 0, "elevation": 0, "radius": 100, "location_name": "Home",
    "time_zone": "UTC", "language": "en", "country": None, "currency": "EUR",
    "external_url": None, "internal_url": None,
    "unit_system": {"length": "km", "temperature": "°C"},
    "components": ["a", "b"], "version": "2026.10.4",
}


def test_normalize_drops_unsupported_and_coerces():
    config = normalize_config(RAW)
    assert "components" not in config and "version" not in config
    assert config["unit_system"] == "metric"
    assert config["latitude"] == 0.0 and isinstance(config["latitude"], float)
    assert config["country"] is None


@pytest.mark.parametrize("length, expected", [("km", "metric"), ("mi", "us_customary")])
def test_unit_system(length, expected):
    assert normalize_config(dict(RAW, unit_system={"length": length}))["unit_system"] == expected


def test_desired_config_only_provided_and_empty_url_clears():
    params = {"url": "x", "location_name": "Cabin", "external_url": "", "internal_url": None, "radius": 0}
    assert desired_config(params) == {"location_name": "Cabin", "external_url": None, "radius": 0}


def test_compute_changes():
    current = normalize_config(RAW)
    assert compute_changes(current, {}) == {}
    assert compute_changes(current, {"location_name": "Home", "external_url": None, "latitude": 0.0}) == {}
    assert compute_changes(current, {"location_name": "Cabin", "unit_system": "metric", "country": "DE"}) == {
        "location_name": "Cabin", "country": "DE"}

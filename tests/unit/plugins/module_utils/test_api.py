# -*- coding: utf-8 -*-
# Copyright (c) 2026, Egor Sklyarov
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

import pytest

from ansible_collections.egors.homeassistant.plugins.module_utils.api import (
    MIN_HA_VERSION,
    derive_client_id,
    is_valid_client_id,
    is_version_supported,
    parse_version,
    redirect_uri,
    websocket_url,
)


@pytest.mark.parametrize("version, expected", [
    ("2026.10.4", (2026, 10, 4)),
    ("2026.11.0b1", (2026, 11, 0)),
    ("2026.12.0.dev20261101", (2026, 12, 0)),
    ("2027.1", (2027, 1, 0)),
    ("garbage", (0, 0, 0)),
])
def test_parse_version(version, expected):
    assert parse_version(version) == expected


def test_parse_version_orders_numerically():
    assert parse_version("2026.10.0") > parse_version("2026.9.9")


@pytest.mark.parametrize("version, expected", [
    (MIN_HA_VERSION, True),
    ("2026.10.4", True),
    ("2027.1.0b0", True),
    ("2026.9.3", False),
    ("2025.12.0", False),
])
def test_is_version_supported(version, expected):
    assert is_version_supported(version) is expected


@pytest.mark.parametrize("url, expected", [
    ("http://127.0.0.1:8123", "ws://127.0.0.1:8123/api/websocket"),
    ("http://127.0.0.1:8123/", "ws://127.0.0.1:8123/api/websocket"),
    ("https://ha.example.com", "wss://ha.example.com/api/websocket"),
    ("https://ha.example.com/sub/", "wss://ha.example.com/sub/api/websocket"),
])
def test_websocket_url(url, expected):
    assert websocket_url(url) == expected


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

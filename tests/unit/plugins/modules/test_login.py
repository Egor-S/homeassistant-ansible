# -*- coding: utf-8 -*-
# Copyright (c) 2026, Egor Sklyarov
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from ansible_collections.egors.homeassistant.plugins.modules.login import (
    parse_timestamp,
    stale_token_ids,
    token_name,
)

NOW = datetime(2026, 10, 25, 12, 0, tzinfo=timezone.utc)


@pytest.mark.parametrize("value, expected", [
    # Format of auth/refresh_tokens on HA 2026.10.4.
    ("2026-10-25T15:14:05.279676+00:00", datetime(2026, 10, 25, 15, 14, 5, 279676, tzinfo=timezone.utc)),
    ("2026-10-24T12:00:00+00:00", datetime(2026, 10, 24, 12, 0, tzinfo=timezone.utc)),
    ("2026-10-24T12:00:00.123456Z", datetime(2026, 10, 24, 12, 0, 0, 123456, tzinfo=timezone.utc)),
    ("2026-10-24T12:00:00", datetime(2026, 10, 24, 12, 0, tzinfo=timezone.utc)),
    (1792843200, datetime(2026, 10, 24, 12, 0, tzinfo=timezone.utc)),
    ("garbage", None),
    (None, None),
])
def test_parse_timestamp(value, expected):
    assert parse_timestamp(value) == expected


def token(token_id, created_at, client_name=None, token_type="long_lived_access_token"):
    if client_name is None:
        client_name = token_name("Ansible login", parse_timestamp(created_at) or NOW, "abc123")
    return dict(id=token_id, created_at=created_at, client_name=client_name, type=token_type)


def test_token_name():
    assert token_name("Ansible login", NOW, "3f9a1c") == "Ansible login 2026-10-25T12:00:00Z 3f9a1c"


def test_token_name_is_unique():
    assert token_name("Ansible login", NOW) != token_name("Ansible login", NOW)


def test_stale_token_ids():
    tokens = [
        token("old", "2026-10-23T12:00:00+00:00"),
        token("exactly", "2026-10-24T12:00:00+00:00"),
        token("young", "2026-10-25T11:00:00+00:00"),
        token("manual", "2026-01-01T00:00:00+00:00", client_name="Ansible login"),
        token("other-prefix", "2026-01-01T00:00:00+00:00", client_name="Other 2026-01-01T00:00:00Z abc123"),
        token("trailing", "2026-01-01T00:00:00+00:00", client_name="Ansible login 2026-01-01T00:00:00Z abc123 x"),
        token("session", "2026-01-01T00:00:00+00:00", token_type="normal"),
        token("unknown-date", "garbage", client_name="Ansible login 2026-01-01T00:00:00Z abc123"),
    ]
    assert stale_token_ids(tokens, "Ansible login", 1, NOW) == ["old", "exactly"]


def test_stale_token_ids_escapes_prefix():
    tokens = [token("a", "2026-01-01T00:00:00+00:00", client_name="AnsibleXlogin 2026-01-01T00:00:00Z abc123")]
    assert stale_token_ids(tokens, "Ansible.login", 1, NOW) == []


def test_stale_token_ids_longer_lifespan_keeps_more():
    tokens = [token("a", "2026-10-23T12:00:00+00:00"), token("b", "2026-10-15T12:00:00+00:00")]
    assert stale_token_ids(tokens, "Ansible login", 7, NOW) == ["b"]

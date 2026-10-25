# -*- coding: utf-8 -*-
# Copyright (c) 2026, Egor Sklyarov
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

import pytest

from ansible_collections.egors.homeassistant.plugins.modules.http_config import (
    desired_config,
    normalize_config,
    plan,
)

META = {"created_at": "2026-10-25T15:13:42+00:00", "error": None, "error_message": None}
STABLE = dict(META, server_port=8123, cors_allowed_origins=["https://cast.home-assistant.io"],
              login_attempts_threshold=-1, ip_ban_enabled=True, ssl_profile="modern", use_x_frame_options=True)
PROXIED = dict(STABLE, use_x_forwarded_for=True, trusted_proxies=["10.0.0.0/8", "172.16.0.1/32"])


def params(**kwargs):
    return dict({"url": "x", "token": "t", "wait_timeout": 180}, **kwargs)


def test_normalize_fills_unset_keys_and_sorts_sets():
    config = normalize_config(dict(PROXIED, trusted_proxies=["172.16.0.1", "10.0.0.0/8", "10.0.0.0/8"]))
    assert config["trusted_proxies"] == ["10.0.0.0/8", "172.16.0.1/32"]
    assert config["server_host"] == [] and config["ssl_certificate"] is None
    assert "created_at" not in config


def test_normalize_treats_missing_as_empty_or_false():
    assert normalize_config(STABLE) == normalize_config(dict(STABLE, trusted_proxies=[], use_x_forwarded_for=False))


def test_desired_keeps_stable_values_and_drops_meta():
    desired = desired_config(STABLE, params(use_x_forwarded_for=True, trusted_proxies=["172.16.0.1"]))
    expected = {key: value for key, value in STABLE.items() if key not in META}
    expected.update(use_x_forwarded_for=True, trusted_proxies=["172.16.0.1/32"])
    assert desired == expected


@pytest.mark.parametrize("key, empty", [("trusted_proxies", []), ("server_host", []), ("ssl_certificate", "")])
def test_desired_empty_value_removes_key(key, empty):
    stable = dict(PROXIED, server_host=["0.0.0.0"], ssl_certificate="/ssl/cert.pem")
    assert key not in desired_config(stable, params(**{key: empty}))


def test_desired_empty_cors_is_a_value():
    assert desired_config(STABLE, params(cors_allowed_origins=[]))["cors_allowed_origins"] == []


def test_desired_rejects_bad_proxy():
    with pytest.raises(ValueError):
        desired_config(STABLE, params(trusted_proxies=["10.0.0.1/8"]))


def state(stable=None, pending=None, active="stable"):
    return {"stable": stable or STABLE, "pending": pending, "active_config_type": active}


def test_plan_unchanged():
    assert plan(state(), desired_config(STABLE, params(ip_ban_enabled=True))) is None
    # Proxies in another order and without the mask are the same set.
    assert plan(state(PROXIED), desired_config(PROXIED, params(trusted_proxies=["172.16.0.1", "10.0.0.0/8"]))) is None


def test_plan_configure():
    assert plan(state(), desired_config(STABLE, params(ip_ban_enabled=False))) == "configure"


def test_plan_ignores_failed_pending():
    failed = dict(PROXIED, error="not_promoted")
    assert plan(state(pending=failed), desired_config(STABLE, params())) is None
    assert plan(state(pending=failed), desired_config(STABLE, params(
        use_x_forwarded_for=True, trusted_proxies=["10.0.0.0/8", "172.16.0.1"]))) == "configure"


def test_plan_clears_untested_pending_when_stable_is_desired():
    assert plan(state(pending=PROXIED, active="pending"), desired_config(STABLE, params())) == "clear"


def test_plan_promotes_running_trial():
    desired = desired_config(STABLE, params(use_x_forwarded_for=True, trusted_proxies=["10.0.0.0/8", "172.16.0.1"]))
    assert plan(state(pending=PROXIED, active="pending"), desired) == "promote"
    # A trial that is staged but not running must be tried (restart) first.
    assert plan(state(pending=PROXIED, active="stable"), desired) == "configure"

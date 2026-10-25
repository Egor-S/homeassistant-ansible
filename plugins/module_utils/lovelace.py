# -*- coding: utf-8 -*-
# Copyright (c) 2026, Egor Sklyarov
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

"""Dashboards (``lovelace/dashboards/*``, ``lovelace/config*``) and dashboard resources (``lovelace/resources/*``)."""

from __future__ import annotations

from ansible_collections.egors.homeassistant.plugins.module_utils.api import HomeAssistantAPIError, HomeAssistantError

# The dashboard at /lovelace: its content can be managed, its metadata can not.
DEFAULT_URL_PATH = "lovelace"
SETTINGS = ("title", "icon", "show_in_sidebar", "require_admin")


def normalize_dashboard(entry):
    result = {"url_path": entry.get("url_path"), "dashboard_id": entry.get("id")}
    for field in SETTINGS:
        result[field] = entry.get(field)
    return result


def dashboard_changes(params, current):
    """Changed settings; ``icon: ""`` removes the icon."""
    changes = {}
    for field in SETTINGS:
        if params.get(field) is None:
            continue
        value = (params[field] or None) if field == "icon" else params[field]
        if current.get(field) != value:
            changes[field] = value
    return changes


def get_config(module, url_path):
    """Content of a dashboard, or ``None`` if it has none yet."""
    try:
        return module.ws.call("lovelace/config", url_path=url_path)
    except HomeAssistantAPIError as exc:
        if exc.code == "config_not_found":
            return None
        module.fail_json(msg="Home Assistant rejected lovelace/config: %s" % exc.message, error_code=exc.code)
    except HomeAssistantError as exc:
        module.fail_json(msg=str(exc))


def normalize_resource(entry):
    return {"resource_id": entry.get("id"), "url": entry.get("url"), "type": entry.get("type")}

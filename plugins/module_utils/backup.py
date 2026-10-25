# -*- coding: utf-8 -*-
# Copyright (c) 2026, Egor Sklyarov
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

"""Logic of the ``backup_config`` module: flat options <-> the nested ``backup/config/*`` settings.

``backup/config/update`` merges ``create_backup`` and ``schedule`` field by field but replaces ``retention``
as a whole, so retention is always sent complete. The stored backup password is returned by
``backup/config/info`` in plain text; it is compared but never reported.
"""

from __future__ import annotations

from ansible_collections.egors.homeassistant.plugins.module_utils.helpers import to_time

# option -> (section, field, kind); kind "set" compares as a set, "clear" turns "" into None.
OPTIONS = {
    "agent_ids": ("create_backup", "agent_ids", "set"),
    "include_database": ("create_backup", "include_database", "value"),
    "include_folders": ("create_backup", "include_folders", "set"),
    "name": ("create_backup", "name", "clear"),
    "password": ("create_backup", "password", "clear"),
    "retention_copies": ("retention", "copies", "int"),
    "retention_days": ("retention", "days", "int"),
    "schedule_recurrence": ("schedule", "recurrence", "value"),
    "schedule_days": ("schedule", "days", "set"),
    "schedule_time": ("schedule", "time", "time"),
    "automatic_backups_configured": (None, "automatic_backups_configured", "value"),
}
DAYS = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]


def _get(config, section, field):
    return (config.get(section) or {}).get(field) if section else config.get(field)


def _desired(kind, value):
    if kind == "set":
        return sorted(set(value))
    if kind == "clear":
        return value or None
    if kind == "int":
        return None if value == 0 else value
    if kind == "time":
        return to_time(value) if value else None
    return value


def _current(kind, value):
    return sorted(set(value)) if kind == "set" and value is not None else value


def flatten(config):
    """The settings as the module's options; the password is reported as ``password_set``."""
    result = dict((option, _current(kind, _get(config, section, field)))
                  for option, (section, field, kind) in OPTIONS.items() if option != "password")
    result["password_set"] = bool(_get(config, "create_backup", "password"))
    return result


def compute_update(params, config):
    """``(payload, changed_options)`` for ``backup/config/update``; raises ``ValueError`` for an invalid time."""
    payload, changed = {}, []
    for option, (section, field, kind) in OPTIONS.items():
        if params.get(option) is None:
            continue
        value = _desired(kind, params[option])
        if _current(kind, _get(config, section, field)) == value:
            continue
        changed.append(option)
        if section:
            payload.setdefault(section, {})[field] = value
        else:
            payload[field] = value
    if "retention" in payload:
        payload["retention"] = dict(config.get("retention") or {}, **payload["retention"])
    return payload, changed


def predict(config, payload):
    result = dict(config)
    for key, value in payload.items():
        result[key] = dict(config.get(key) or {}, **value) if isinstance(value, dict) else value
    return result

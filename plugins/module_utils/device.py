# -*- coding: utf-8 -*-
# Copyright (c) 2026, Egor Sklyarov
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

"""Logic of the ``device`` modules: settings of a device registry entry."""

from __future__ import annotations

from ansible_collections.egors.homeassistant.plugins.module_utils.registry import normalize_name

REPORTED = ("name", "manufacturer", "model", "entry_type", "via_device_id", "config_entries")


def normalize(entry):
    """Device registry entry reduced to what the modules manage and report."""
    result = {"device_id": entry.get("id"), "name_by_user": entry.get("name_by_user") or None,
              "area_id": entry.get("area_id"), "labels": sorted(set(entry.get("labels") or [])),
              "disabled_by": entry.get("disabled_by")}
    for field in REPORTED:
        result[field] = entry.get(field)
    result["identifiers"] = [list(i) for i in entry.get("identifiers") or []]
    return result


def matches_name(entry, name):
    """A device matches by the name its integration gave it or by the one the user gave it."""
    wanted = normalize_name(name)
    return any(normalize_name(n) == wanted for n in (entry.get("name"), entry.get("name_by_user")) if n)


def compute_changes(params, current):
    """``(changes, predicted)``: the update payload for the provided options, and the entry after it."""
    changes = {}
    for field in ("name_by_user", "area_id"):
        if params.get(field) is not None:
            value = params[field] or None
            if current[field] != value:
                changes[field] = value
    if params.get("labels") is not None:
        value = sorted(set(params["labels"]))
        if current["labels"] != value:
            changes["labels"] = value
    if params.get("disabled") is not None and params["disabled"] != (current["disabled_by"] is not None):
        changes["disabled_by"] = "user" if params["disabled"] else None
    return changes, dict(current, **changes)

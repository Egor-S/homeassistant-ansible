# -*- coding: utf-8 -*-
# Copyright (c) 2026, Egor Sklyarov
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

"""Logic of the ``entity`` module: settings of an entity registry entry."""

from __future__ import annotations

# Clearable strings: "" sends None, which restores the integration's default.
STRINGS = ("name", "icon", "area_id", "device_class")
LISTS = ("labels", "aliases")
# Option -> registry field; True sets "user", False clears whoever disabled or hid the entity.
FLAGS = {"disabled": "disabled_by", "hidden": "hidden_by"}


def normalize(entry):
    """Entity registry entry reduced to what the module manages and reports."""
    result = dict((k, entry.get(k)) for k in ("entity_id",) + STRINGS)
    result["labels"] = sorted(set(entry.get("labels") or []))
    # A None alias stands for the entity's own name; only explicit aliases are managed.
    result["aliases"] = sorted(set(a for a in entry.get("aliases") or [] if a is not None))
    for field in ("disabled_by", "hidden_by", "original_name", "original_icon", "original_device_class",
                  "device_id", "platform", "unique_id"):
        result[field] = entry.get(field)
    return result


def compute_changes(params, current):
    """``(changes, predicted)``: the update payload for the provided options, and the entry after it."""
    changes = {}
    for field in STRINGS:
        if params.get(field) is not None:
            value = params[field] or None
            if current[field] != value:
                changes[field] = value
    for field in LISTS:
        if params.get(field) is not None:
            value = sorted(set(params[field]))
            if current[field] != value:
                changes[field] = value
    for option, field in FLAGS.items():
        if params.get(option) is not None and params[option] != (current[field] is not None):
            changes[field] = "user" if params[option] else None
    if params.get("new_entity_id") is not None and params["new_entity_id"] != current["entity_id"]:
        changes["new_entity_id"] = params["new_entity_id"]
    predicted = dict(current, **dict((k, v) for k, v in changes.items() if k != "new_entity_id"))
    if "new_entity_id" in changes:
        predicted["entity_id"] = changes["new_entity_id"]
    return changes, predicted


def update_payload(changes, raw_aliases):
    """Changes as sent to ``config/entity_registry/update``; keeps the entity's own name among the aliases."""
    payload = dict(changes)
    if "aliases" in payload and None in (raw_aliases or []):
        payload["aliases"] = [None] + payload["aliases"]
    return payload

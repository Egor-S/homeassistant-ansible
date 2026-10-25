# -*- coding: utf-8 -*-
# Copyright (c) 2026, Egor Sklyarov
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

"""Field specs of the helper storage collections (``input_boolean``, ``counter``, ...), shared by their
modules and ``helper_info``. Helpers replace the whole item on update, see ``registry.py``."""

from __future__ import annotations

import re

from ansible_collections.egors.homeassistant.plugins.module_utils.registry import Registry

WEEKDAYS = ("monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday")
_CLOCK = re.compile(r"^(\d+):(\d{1,2})(?::(\d{1,2}))?$")


def _clock(value):
    """``H:MM`` or ``H:MM:SS`` -> ``(hours, minutes, seconds)``; ``ValueError`` otherwise."""
    match = _CLOCK.match(str(value).strip())
    if not match:
        raise ValueError("expected H:MM or H:MM:SS, got %r" % (value,))
    hours, minutes, seconds = (int(g or 0) for g in match.groups())
    if minutes > 59 or seconds > 59:
        raise ValueError("minutes and seconds must be below 60, got %r" % (value,))
    return hours, minutes, seconds


def to_duration(value):
    """A timer duration (seconds, ``H:MM`` or ``H:MM:SS``) as Home Assistant stores it: ``H:MM:SS``."""
    if isinstance(value, bool):
        raise ValueError("expected seconds or H:MM:SS, got %r" % (value,))
    if isinstance(value, int) or str(value).strip().isdigit():
        total = int(value)
    else:
        try:
            hours, minutes, seconds = _clock(value)
        except ValueError:
            raise ValueError("expected seconds, H:MM or H:MM:SS, got %r" % (value,))
        total = hours * 3600 + minutes * 60 + seconds
    hours, rest = divmod(total, 3600)
    return "%d:%02d:%02d" % (hours, rest // 60, rest % 60)


def to_time(value):
    """A time of day (``H:MM`` or ``H:MM:SS``, up to ``24:00``) as Home Assistant stores it: ``HH:MM:SS``."""
    hours, minutes, seconds = _clock(value)
    if hours > 24 or hours == 24 and (minutes or seconds):
        raise ValueError("a time of day is at most 24:00, got %r" % (value,))
    return "%02d:%02d:%02d" % (hours, minutes, seconds)


def to_time_ranges(ranges):
    """Schedule time ranges as Home Assistant stores them: times as ``HH:MM:SS``, sorted by start, no empty data."""
    result = []
    for item in ranges:
        entry = {"from": to_time(item["from"]), "to": to_time(item["to"])}
        if item.get("data"):
            entry["data"] = item["data"]
        result.append(entry)
    return sorted(result, key=lambda r: r["from"])


HELPERS = {
    "input_boolean": dict(strings=("icon",), values=("initial",)),
    "input_button": dict(strings=("icon",)),
    "input_number": dict(strings=("icon", "unit_of_measurement"), values=("min", "max", "step", "initial", "mode"),
                         required=("min", "max")),
    "input_text": dict(strings=("icon", "pattern", "initial", "unit_of_measurement"), values=("min", "max", "mode")),
    "input_select": dict(strings=("icon", "initial"), values=("options",), required=("options",)),
    "counter": dict(strings=("icon",), ints=("minimum", "maximum"), values=("initial", "step", "restore")),
    "input_datetime": dict(strings=("icon", "initial"), values=("has_date", "has_time")),
    "timer": dict(strings=("icon",), values=("duration", "restore"), convert={"duration": to_duration}),
    "schedule": dict(strings=("icon",), values=WEEKDAYS, convert=dict((day, to_time_ranges) for day in WEEKDAYS)),
}


def helper_registry(module, domain):
    spec = HELPERS[domain]
    return Registry(module, domain, domain + "_id", spec.get("strings", ()), ints=spec.get("ints", ()),
                    values=spec.get("values", ()), required=spec.get("required", ()), entry_key="id", replace=True,
                    convert=spec.get("convert"))

# -*- coding: utf-8 -*-
# Copyright (c) 2026, Egor Sklyarov
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

"""Generic logic for Home Assistant registry resources (areas, floors, labels, ...).

A resource is described by the WebSocket command prefix (``config/area_registry``), the name of
its id field (``area_id``) and its managed fields: ``strings`` (clearable, ``""`` clears) and
``lists`` (compared as sets). ``name`` is always managed and required for creation.
"""

from __future__ import annotations

import re

_SPACES = re.compile(r"\s+")


def normalize_name(name):
    """Casefold, strip and collapse internal whitespace; used to match names."""
    return _SPACES.sub(" ", name.strip()).casefold()


def normalize_entry(entry, id_field, strings, lists):
    """Registry entry reduced to managed fields; lists sorted, absent strings as ``None``."""
    result = {id_field: entry.get(id_field), "name": entry.get("name")}
    for field in strings:
        result[field] = entry.get(field)
    for field in lists:
        result[field] = sorted(set(entry.get(field) or []))
    return result


def desired_values(params, strings, lists):
    """Provided managed options as ``{field: value}``; ``""`` becomes ``None``, lists become sorted sets."""
    desired = {}
    for field in strings:
        if params.get(field) is not None:
            desired[field] = params[field] or None
    for field in lists:
        if params.get(field) is not None:
            desired[field] = sorted(set(params[field]))
    return desired


def find_entry(entries, id_field, entry_id=None, name=None):
    """Find by id if given, else by normalized name; ``None`` if missing."""
    if entry_id is not None:
        return next((e for e in entries if e.get(id_field) == entry_id), None)
    wanted = normalize_name(name)
    return next((e for e in entries if normalize_name(e.get("name") or "") == wanted), None)


def compute_changes(current, desired):
    """Fields of ``desired`` (normalized) that differ from the normalized ``current``."""
    return dict((k, v) for k, v in desired.items() if current.get(k) != v)


class Registry:
    def __init__(self, module, prefix, id_field, strings=(), lists=()):
        self.module = module
        self.prefix = prefix
        self.id_field = id_field
        self.strings = tuple(strings)
        self.lists = tuple(lists)

    def normalize(self, entry):
        return normalize_entry(entry, self.id_field, self.strings, self.lists)

    def list_entries(self):
        return self.module.call(self.prefix + "/list")

    def info(self, result_key):
        """Implementation of the ``*_info`` modules: list, filter by id/name, exit."""
        params = self.module.params
        entries = self.list_entries()
        if params.get(self.id_field) is not None:
            entries = [e for e in entries if e.get(self.id_field) == params[self.id_field]]
        if params.get("name") is not None:
            wanted = normalize_name(params["name"])
            entries = [e for e in entries if normalize_name(e.get("name") or "") == wanted]
        self.module.exit_json(changed=False, **{result_key: [self.normalize(e) for e in entries]})

    def ensure(self, result_key):
        """Implementation of the resource modules (``state`` present/absent): converge and exit."""
        module = self.module
        params = module.params
        entry_id = params.get(self.id_field)
        name = params.get("name")
        if name is not None and not normalize_name(name):
            module.fail_json(msg="name must not be empty")
        entry = find_entry(self.list_entries(), self.id_field, entry_id, name)
        before = self.normalize(entry) if entry else {}
        desired = desired_values(params, self.strings, self.lists)

        if params["state"] == "absent":
            after, changed = {}, entry is not None
            if changed and not module.check_mode:
                module.call(self.prefix + "/delete", **{self.id_field: entry[self.id_field]})
        elif entry is None:
            if entry_id is not None:
                module.fail_json(msg="%s %r does not exist; omit %s to create it by name"
                                 % (self.id_field, entry_id, self.id_field))
            if name is None:
                module.fail_json(msg="name is required to create")
            payload = dict((k, v) for k, v in desired.items() if v)
            payload["name"] = name.strip()
            changed = True
            after = self.predict(None, payload)
            if not module.check_mode:
                after = self.write("/create", payload, desired)
        else:
            changes = compute_changes(before, desired)
            # Matched by name: the name already agrees (up to case/whitespace), do not rename.
            if entry_id is not None and name is not None and name.strip() != before["name"]:
                changes["name"] = name.strip()
            changed = bool(changes)
            after = self.predict(before, changes)
            if changed and not module.check_mode:
                payload = dict(changes, **{self.id_field: before[self.id_field]})
                after = self.write("/update", payload, desired)

        result = {"changed": changed, result_key: after}
        if module._diff:
            result["diff"] = {"before": before, "after": after}
        module.exit_json(**result)

    def predict(self, before, changes):
        """Entry as it would look after applying ``changes`` (check mode)."""
        base = dict(before) if before else dict(self.normalize({}), name=None)
        base.update(changes)
        return self.normalize(base)

    def write(self, suffix, payload, desired):
        entry = self.normalize(self.module.call(self.prefix + suffix, **payload))
        for field, value in desired.items():
            if entry.get(field) != value:
                self.module.warn("Home Assistant stored %s=%r instead of the requested %r; it may not "
                                 "exist and was dropped." % (field, entry.get(field), value))
        return entry

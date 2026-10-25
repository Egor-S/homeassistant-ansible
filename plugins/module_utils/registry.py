# -*- coding: utf-8 -*-
# Copyright (c) 2026, Egor Sklyarov
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

"""Generic logic for Home Assistant registry resources (areas, floors, labels, ...) and storage collections (zones, ...).

A resource is described by the WebSocket command prefix (``config/area_registry``), the name of
its id field (``area_id``) and its managed fields: ``strings`` (clearable, ``""`` clears),
``lists`` (compared as sets), ``ints`` (``""`` clears, ``0`` is a value) and ``values`` (compared as
given, typed by the argument spec). ``name`` is always managed and required for creation.

Storage collections differ from registries: their entries carry the id as ``id`` (``entry_key``) while
commands take ``<domain>_id``, and names need not be unique. Some (the helpers) replace the whole item
on update (``replace``): the payload is then the current entry with the changes applied, and a cleared
field is left out so that Home Assistant falls back to its default.
"""

from __future__ import annotations

import re

_SPACES = re.compile(r"\s+")


def normalize_name(name):
    """Casefold, strip and collapse internal whitespace; used to match names."""
    return _SPACES.sub(" ", name.strip()).casefold()


def to_int_or_none(value):
    """``""`` -> ``None``; an int or an integer string -> ``int``; anything else (also bool) -> ``ValueError``."""
    if value == "":
        return None
    if isinstance(value, bool) or not isinstance(value, (int, str)):
        raise ValueError(value)
    return int(value)


def normalize_entry(entry, id_field, strings, lists, ints=(), values=(), entry_key=None):
    """Registry entry reduced to managed fields; lists sorted, absent strings as ``None``."""
    result = {id_field: entry.get(entry_key or id_field), "name": entry.get("name")}
    for field in tuple(strings) + tuple(ints) + tuple(values):
        result[field] = entry.get(field)
    for field in lists:
        result[field] = sorted(set(entry.get(field) or []))
    return result


def desired_values(params, strings, lists, ints=(), values=()):
    """Provided managed options as ``{field: value}``; ``""`` becomes ``None``, lists become sorted sets.

    Raises ``ValueError`` for an ``ints`` value that is not an integer.
    """
    desired = {}
    for field in values:
        if params.get(field) is not None:
            desired[field] = params[field]
    for field in ints:
        if params.get(field) is not None:
            desired[field] = to_int_or_none(params[field])
    for field in strings:
        if params.get(field) is not None:
            desired[field] = params[field] or None
    for field in lists:
        if params.get(field) is not None:
            desired[field] = sorted(set(params[field]))
    return desired


def find_entries(entries, id_field, entry_id=None, name=None):
    """All entries with the id if given, else with the normalized name."""
    if entry_id is not None:
        return [e for e in entries if e.get(id_field) == entry_id]
    wanted = normalize_name(name)
    return [e for e in entries if normalize_name(e.get("name") or "") == wanted]


def find_entry(entries, id_field, entry_id=None, name=None):
    """Find by id if given, else by normalized name; ``None`` if missing."""
    return next(iter(find_entries(entries, id_field, entry_id, name)), None)


def compute_changes(current, desired):
    """Fields of ``desired`` (normalized) that differ from the normalized ``current``."""
    return dict((k, v) for k, v in desired.items() if current.get(k) != v)


class Registry:
    """``unclearable`` fields can't be removed once set; ``required`` fields are needed besides ``name`` to create.

    ``convert`` maps a field to a function that turns a provided value into the form Home Assistant stores
    (raising ``ValueError`` for an invalid one), so that it compares equal to the stored value.
    """

    def __init__(self, module, prefix, id_field, strings=(), lists=(), ints=(), values=(), entry_key=None,
                 unclearable=(), required=(), replace=False, convert=None):
        self.module = module
        self.prefix = prefix
        self.id_field = id_field
        self.strings = tuple(strings)
        self.lists = tuple(lists)
        self.ints = tuple(ints)
        self.values = tuple(values)
        self.entry_key = entry_key or id_field
        self.unclearable = tuple(unclearable)
        self.required = tuple(required)
        self.replace = replace
        self.convert = convert or {}

    def normalize(self, entry):
        return normalize_entry(entry, self.id_field, self.strings, self.lists, self.ints, self.values, self.entry_key)

    def list_entries(self):
        return self.module.call(self.prefix + "/list")

    def info(self, result_key, id_param=None):
        """Implementation of the ``*_info`` modules: list, filter by id/name, exit."""
        params = self.module.params
        id_param = id_param or self.id_field
        entries = self.list_entries()
        if params.get(id_param) is not None:
            entries = [e for e in entries if e.get(self.entry_key) == params[id_param]]
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
        matches = find_entries(self.list_entries(), self.entry_key, entry_id, name)
        if len(matches) > 1:
            module.fail_json(msg="%d entries are named %r; select one with %s"
                             % (len(matches), name, self.id_field), matches=[self.normalize(e) for e in matches])
        entry = matches[0] if matches else None
        before = self.normalize(entry) if entry else {}
        try:
            desired = desired_values(params, self.strings, self.lists, self.ints, self.values)
        except ValueError as e:
            module.fail_json(msg="expected an integer or an empty string, got %s" % e)
        for field, convert in self.convert.items():
            if desired.get(field) is not None:
                try:
                    desired[field] = convert(desired[field])
                except ValueError as e:
                    module.fail_json(msg="invalid %s: %s" % (field, e))
        for field in self.unclearable:
            if field in desired and desired[field] is None:
                module.fail_json(msg="%s can not be removed, only changed" % field)

        if params["state"] == "absent":
            after, changed = {}, entry is not None
            if changed and not module.check_mode:
                module.call(self.prefix + "/delete", **{self.id_field: before[self.id_field]})
        elif entry is None:
            if entry_id is not None:
                module.fail_json(msg="%s %r does not exist; omit %s to create it by name"
                                 % (self.id_field, entry_id, self.id_field))
            missing = ([] if name is not None else ["name"]) + [f for f in self.required if f not in desired]
            if missing:
                module.fail_json(msg="%s %s required to create" % (" and ".join(missing), "is" if len(missing) == 1 else "are"))
            payload = dict((k, v) for k, v in desired.items() if v is not None and v != [])
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
                payload = dict(changes)
                if self.replace:
                    payload = dict((k, v) for k, v in entry.items() if k != self.entry_key)
                    payload.update(changes)
                    payload = dict((k, v) for k, v in payload.items() if v is not None)
                payload[self.id_field] = before[self.id_field]
                after = self.write("/update", payload, desired)

        result = {"changed": changed, result_key: after}
        if module._diff:
            result["diff"] = {"before": before, "after": after}
        module.exit_json(**result)

    def predict(self, before, changes):
        """Entry as it would look after applying ``changes`` (check mode)."""
        base = dict(before) if before else dict(self.normalize({}), name=None)
        base.update(changes)
        base[self.entry_key] = base.pop(self.id_field)
        return self.normalize(base)

    def write(self, suffix, payload, desired):
        entry = self.normalize(self.module.call(self.prefix + suffix, **payload))
        for field, value in desired.items():
            if entry.get(field) != value:
                self.module.warn("Home Assistant stored %s=%r instead of the requested %r; it may not "
                                 "exist and was dropped." % (field, entry.get(field), value))
        return entry

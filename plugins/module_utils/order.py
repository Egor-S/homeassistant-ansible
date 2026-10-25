# -*- coding: utf-8 -*-
# Copyright (c) 2026, Egor Sklyarov
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

"""Ordering of areas and floors (``config/<x>_registry/reorder``), which needs every ID exactly once."""

from __future__ import annotations


def new_order(current, wanted):
    """``wanted`` first, in its order, then the others in their current order. ``ValueError`` for unknown IDs."""
    unknown = [i for i in wanted if i not in current]
    if unknown:
        raise ValueError(", ".join(unknown))
    seen = []
    for item in wanted:
        if item not in seen:
            seen.append(item)
    return seen + [i for i in current if i not in seen]


def ensure_order(module, prefix, id_field):
    current = [e[id_field] for e in module.call("config/%s_registry/list" % prefix)]
    try:
        order = new_order(current, module.params["order"])
    except ValueError as e:
        module.fail_json(msg="unknown %s: %s" % (id_field, e))
    changed = order != current
    if changed and not module.check_mode:
        module.call("config/%s_registry/reorder" % prefix, **{id_field + "s": order})
    result = dict(changed=changed, order=order)
    if module._diff:
        result["diff"] = dict(before=dict(order=current), after=dict(order=order))
    module.exit_json(**result)

# -*- coding: utf-8 -*-
# Copyright (c) 2026, Egor Sklyarov
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

"""Logic of the ``user`` modules. Only these two groups are ever sent: Home Assistant does not answer
``config/auth/update`` with an unknown group."""

from __future__ import annotations

GROUP_ADMIN = "system-admin"
GROUP_USER = "system-users"
# Option -> field of config/auth/list and config/auth/update.
FLAGS = {"active": "is_active", "local_only": "local_only"}


def is_normalized(username):
    """Home Assistant's rule for usernames (``strip().casefold()``)."""
    return username == username.strip().casefold() and username != ""


def normalize(user):
    return {"user_id": user.get("id"), "username": user.get("username"), "name": user.get("name"),
            "admin": GROUP_ADMIN in (user.get("group_ids") or []), "active": user.get("is_active"),
            "local_only": user.get("local_only"), "owner": user.get("is_owner")}


def find_user(users, username):
    return next((u for u in users if u.get("username") == username and not u.get("system_generated")), None)


def compute_changes(params, current):
    """Update payload for ``config/auth/update`` and the predicted user."""
    changes, predicted = {}, dict(current)
    if params["name"] is not None and params["name"] != current["name"]:
        changes["name"] = predicted["name"] = params["name"]
    if params["admin"] is not None and params["admin"] != current["admin"]:
        changes["group_ids"] = [GROUP_ADMIN if params["admin"] else GROUP_USER]
        predicted["admin"] = params["admin"]
    for option, field in FLAGS.items():
        if params[option] is not None and params[option] != current[option]:
            changes[field] = predicted[option] = params[option]
    return changes, predicted

# -*- coding: utf-8 -*-
# Copyright (c) 2026, Egor Sklyarov
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

"""Voice assistants that entities are exposed to: module option -> Home Assistant assistant ID."""

from __future__ import annotations

ASSISTANTS = {"conversation": "conversation", "alexa": "cloud.alexa", "google_assistant": "cloud.google_assistant"}


def argument_spec():
    return dict((option, dict(type="bool")) for option in ASSISTANTS)

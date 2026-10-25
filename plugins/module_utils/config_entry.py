# -*- coding: utf-8 -*-
# Copyright (c) 2026, Egor Sklyarov
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

"""Config entries (integrations and config-flow helpers) and their flows over REST.

A flow is a sequence of steps: a ``form`` takes the fields of its ``data_schema``, a ``menu`` takes
``next_step_id``. The stored ``data`` of an entry can't be read back, so entries are matched by domain and title.
"""

from __future__ import annotations

from ansible_collections.egors.homeassistant.plugins.module_utils.registry import normalize_name

ENTRY_FIELDS = ("entry_id", "domain", "title", "state", "source", "disabled_by", "supports_options")
# Aborts that mean the integration is already set up (and allows no second entry).
ALREADY = ("already_configured", "single_instance_allowed", "already_in_progress")


def normalize_entry(entry):
    return dict((k, entry.get(k)) for k in ENTRY_FIELDS)


def find_entries(entries, domain, title):
    return [e for e in entries if e.get("domain") == domain and normalize_name(e.get("title") or "") == normalize_name(title)]


def describe_step(step):
    """A form or menu as a short text for error messages, without defaults or suggested values (may be secret)."""
    if step.get("type") == "menu":
        return "menu %r with options %s" % (step.get("step_id"), ", ".join(step.get("menu_options") or []))
    fields = ["%s%s" % (f.get("name"), "" if f.get("required") else "?") for f in step.get("data_schema") or []]
    return "form %r with fields %s" % (step.get("step_id"), ", ".join(fields) or "(none)")


class FlowError(Exception):
    pass


def run_flow(rest, path, init, steps):
    """Drive a flow to its end. ``rest(path, method, data) -> (status, payload)``.

    Returns the final step (``create_entry`` or ``abort``). Raises ``FlowError`` and aborts the flow on errors,
    on steps HA asks for that ``steps`` does not have, and on external (OAuth) or progress steps.
    """
    status, step = rest(path, "POST", init)
    if status != 200 or not isinstance(step, dict):
        raise FlowError("starting the flow failed with HTTP %s: %s" % (status, _message(step)))
    remaining = list(steps)
    while True:
        kind = step.get("type")
        if kind in ("create_entry", "abort"):
            return step
        flow_path = "%s/%s" % (path, step["flow_id"])
        if kind not in ("form", "menu"):
            _abort(rest, flow_path)
            raise FlowError("step %r of type %s is not supported (it needs a browser or waits for a device)"
                            % (step.get("step_id"), kind))
        if step.get("errors"):
            _abort(rest, flow_path)
            raise FlowError("Home Assistant rejected the input for %s: %s" % (describe_step(step), step["errors"]))
        if not remaining:
            _abort(rest, flow_path)
            raise FlowError("the flow asks for %s, but steps has no more entries" % describe_step(step))
        user_input = remaining.pop(0)
        status, step = rest(flow_path, "POST", user_input)
        if status != 200 or not isinstance(step, dict):
            _abort(rest, flow_path)
            raise FlowError("step failed with HTTP %s: %s" % (status, _message(step)))


def _abort(rest, flow_path):
    rest(flow_path, "DELETE", None)


def _message(payload):
    return payload.get("message", payload) if isinstance(payload, dict) else payload


def current_values(step):
    """Current values a form shows: ``suggested_value`` if set, else ``default``. Fields without one are left out."""
    values = {}
    for field in step.get("data_schema") or []:
        suggested = (field.get("description") or {}).get("suggested_value")
        value = suggested if suggested is not None else field.get("default")
        if value is not None:
            values[field["name"]] = value
    return values


def run_options_flow(rest, path, entry_id, steps, check_mode):
    """Walk an options flow, comparing each step's input with the values the form shows.

    Each form is submitted with its current values plus the input, since submitting replaces the options.
    If no input differs by the last given step, or in check mode, the flow is cancelled instead of finished.
    Returns the names of the changed fields as ``step_id.field``. Raises ``FlowError`` (the flow is cancelled).
    """
    status, step = rest(path, "POST", {"handler": entry_id})
    if status != 200 or not isinstance(step, dict):
        raise FlowError("starting the options flow failed with HTTP %s: %s" % (status, _message(step)))
    changed = []
    remaining = list(steps)
    while True:
        kind = step.get("type")
        if kind in ("create_entry", "abort"):
            if kind == "abort":
                raise FlowError("the options flow aborted: %s" % step.get("reason"))
            return changed
        flow_path = "%s/%s" % (path, step["flow_id"])
        if kind not in ("form", "menu"):
            _abort(rest, flow_path)
            raise FlowError("step %r of type %s is not supported" % (step.get("step_id"), kind))
        if step.get("errors"):
            _abort(rest, flow_path)
            raise FlowError("Home Assistant rejected the input for %s: %s" % (describe_step(step), step["errors"]))
        if not remaining:
            _abort(rest, flow_path)
            if changed:
                raise FlowError("the options flow asks for %s, but steps has no more entries" % describe_step(step))
            return changed
        user_input = remaining.pop(0)
        if kind == "form":
            names = [f.get("name") for f in step.get("data_schema") or []]
            unknown = sorted(k for k in user_input if k not in names)
            if unknown:
                _abort(rest, flow_path)
                raise FlowError("%s has no fields %s" % (describe_step(step), ", ".join(unknown)))
            current = current_values(step)
            changed += ["%s.%s" % (step.get("step_id"), k) for k, v in sorted(user_input.items())
                        if current.get(k) != v]
            payload = dict(current, **user_input)
        else:
            payload = user_input
        if not remaining and (check_mode or not changed):
            _abort(rest, flow_path)
            return changed
        status, step = rest(flow_path, "POST", payload)
        if status != 200 or not isinstance(step, dict):
            _abort(rest, flow_path)
            raise FlowError("step failed with HTTP %s: %s" % (status, _message(step)))

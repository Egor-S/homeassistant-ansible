# -*- coding: utf-8 -*-
# Copyright (c) 2026, Egor Sklyarov
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

"""Automations, scripts and scenes over the REST config editor (``/api/config/<domain>/config/<id>``).

Home Assistant stores the posted configuration as given (in ``automations.yaml``, ``scripts.yaml`` and
``scenes.yaml``) and reloads the domain afterwards, so the configuration is compared as a whole document.
Automations and scenes carry their id inside the stored value as ``id``; it is not part of the compared config.
"""

from __future__ import annotations

from ansible.module_utils.six.moves.urllib.parse import quote


def strip_id(value):
    return dict((k, v) for k, v in value.items() if k != "id")


class ConfigEditor:
    def __init__(self, module, domain, id_param, id_in_value):
        self.module = module
        self.domain = domain
        self.id_param = id_param
        self.id_in_value = id_in_value

    def path(self, item_id):
        return "/api/config/%s/config/%s" % (self.domain, quote(item_id, safe=""))

    def request(self, item_id, method="GET", data=None):
        status, payload = self.module.rest(self.path(item_id), method=method, data=data)
        if status == 404 and method == "GET":
            return None
        if status != 200:
            message = payload.get("message") if isinstance(payload, dict) else payload
            self.module.fail_json(msg="Home Assistant rejected %s %s %s: %s" % (method, self.domain, item_id, message),
                                  status=status)
        return payload

    def get(self, item_id):
        value = self.request(item_id)
        if value is None:
            return None
        return strip_id(value) if self.id_in_value else value

    def ensure(self):
        module = self.module
        params = module.params
        item_id = params[self.id_param]
        before = self.get(item_id)
        if params["state"] == "absent":
            after, changed = None, before is not None
            if changed and not module.check_mode:
                self.request(item_id, method="DELETE")
        else:
            after = strip_id(params["config"]) if self.id_in_value else params["config"]
            if self.id_in_value and params["config"].get("id") not in (None, item_id):
                module.fail_json(msg="config.id %r differs from %s %r" % (params["config"]["id"], self.id_param, item_id))
            changed = before != after
            if changed and not module.check_mode:
                self.request(item_id, method="POST", data=after)
        result = {"changed": changed, self.id_param: item_id, "config": after or {}}
        if module._diff:
            result["diff"] = {"before": before or {}, "after": after or {}}
        module.exit_json(**result)

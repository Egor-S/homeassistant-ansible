# -*- coding: utf-8 -*-
# Copyright (c) 2026, Egor Sklyarov
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

"""Home Assistant REST + WebSocket client shared by the modules."""

from __future__ import annotations

import json
import ssl
import time
import traceback

from ansible.module_utils.basic import AnsibleModule, env_fallback, missing_required_lib
from ansible.module_utils.six.moves.urllib.error import HTTPError
from ansible.module_utils.six.moves.urllib.parse import urlencode, urlparse
from ansible.module_utils.urls import open_url

try:
    import websocket
except ImportError:
    HAS_WEBSOCKET = False
    WEBSOCKET_IMPORT_ERROR = traceback.format_exc()
else:
    HAS_WEBSOCKET = True
    WEBSOCKET_IMPORT_ERROR = None

# Oldest HA release this collection is tested against. Older releases only trigger a warning.
MIN_HA_VERSION = "2026.10.0"


class HomeAssistantError(Exception):
    """Transport-level failure (connection, auth, unexpected response)."""


class HomeAssistantAPIError(HomeAssistantError):
    """Error reported by HA for a WebSocket command or REST call."""

    def __init__(self, code, message):
        super().__init__("%s: %s" % (code, message))
        self.code = code
        self.message = message


def endpoint_argument_spec():
    return dict(
        url=dict(type="str", required=True, fallback=(env_fallback, ["HASS_URL"])),
        validate_certs=dict(type="bool", default=True),
        timeout=dict(type="int", default=10),
    )


def connection_argument_spec():
    spec = endpoint_argument_spec()
    spec["token"] = dict(type="str", required=True, no_log=True, fallback=(env_fallback, ["HASS_TOKEN"]))
    return spec


def parse_version(version):
    """Parse an HA version like ``2026.10.4`` or ``2026.11.0b1`` into a comparable tuple."""
    parts = []
    for part in str(version).split(".")[:3]:
        digits = ""
        for char in part:
            if not char.isdigit():
                break
            digits += char
        parts.append(int(digits) if digits else 0)
    while len(parts) < 3:
        parts.append(0)
    return tuple(parts)


def is_version_supported(version):
    return parse_version(version) >= parse_version(MIN_HA_VERSION)


def rest_request(base_url, path, method="GET", data=None, token=None, form=False, timeout=10, validate_certs=True):
    """Perform a REST call and return ``(status, decoded_json_or_None)``.

    HTTP error statuses are returned, not raised; connection problems raise HomeAssistantError.
    """
    headers = {"Accept": "application/json"}
    body = None
    if token:
        headers["Authorization"] = "Bearer %s" % token
    if data is not None:
        if form:
            body = urlencode(data)
            headers["Content-Type"] = "application/x-www-form-urlencoded"
        else:
            body = json.dumps(data)
            headers["Content-Type"] = "application/json"
    url = base_url.rstrip("/") + path
    try:
        response = open_url(url, data=body, headers=headers, method=method, timeout=timeout,
                            validate_certs=validate_certs, follow_redirects="none")
        status = response.getcode()
        raw = response.read()
    except HTTPError as exc:
        status = exc.code
        raw = exc.read() if exc.fp is not None else b""
    except Exception as exc:  # URLError, socket errors, timeouts
        raise HomeAssistantError("Request to %s failed: %s" % (url, exc))
    try:
        payload = json.loads(raw) if raw else None
    except ValueError:
        payload = raw.decode("utf-8", "replace")
    return status, payload


def derive_client_id(url):
    """Default OAuth client ID: the base URL with exactly one trailing slash."""
    return url.rstrip("/") + "/"


def is_valid_client_id(client_id):
    parsed = urlparse(client_id)
    return parsed.scheme in ("http", "https") and bool(parsed.netloc)


def redirect_uri(client_id):
    return client_id.rstrip("/") + "/?auth_callback=1"


def _error_message(payload):
    if isinstance(payload, dict):
        return payload.get("message") or payload.get("error_description") or payload.get("error") or payload
    return payload


def exchange_code(base_url, code, client_id, **kwargs):
    """Exchange an authorization code; return the ``/auth/token`` payload (access and refresh token)."""
    status, payload = rest_request(base_url, "/auth/token", method="POST", form=True, data=dict(
        grant_type="authorization_code", code=code, client_id=client_id), **kwargs)
    if status != 200 or not isinstance(payload, dict) or "access_token" not in payload:
        raise HomeAssistantError("Token exchange failed with HTTP %s: %s" % (status, _error_message(payload)))
    return payload


def login_flow(base_url, username, password, client_id, **kwargs):
    """Log in with the ``homeassistant`` auth provider; return an authorization code."""
    status, payload = rest_request(base_url, "/auth/login_flow", method="POST", data=dict(
        client_id=client_id, handler=["homeassistant", None], redirect_uri=redirect_uri(client_id)), **kwargs)
    if status != 200 or not isinstance(payload, dict) or "flow_id" not in payload:
        raise HomeAssistantError("Starting the login flow failed with HTTP %s: %s" % (status, _error_message(payload)))
    status, payload = rest_request(base_url, "/auth/login_flow/%s" % payload["flow_id"], method="POST", data=dict(
        client_id=client_id, username=username, password=password), **kwargs)
    if status != 200 or not isinstance(payload, dict):
        raise HomeAssistantError("Login failed with HTTP %s: %s" % (status, _error_message(payload)))
    if payload.get("type") == "create_entry":
        return payload["result"]
    if payload.get("step_id") == "mfa":
        raise HomeAssistantError("Login as %s needs multi-factor authentication, which is not supported; "
                                 "use a long-lived access token instead." % username)
    raise HomeAssistantError("Login as %s failed: %s" % (username, payload.get("errors") or payload))


def revoke_token(base_url, refresh_token, **kwargs):
    """Revoke a refresh token (and its access tokens). HA answers 200 even for unknown tokens."""
    status, payload = rest_request(base_url, "/auth/revoke", method="POST", form=True,
                                   data=dict(token=refresh_token), **kwargs)
    if status != 200:
        raise HomeAssistantError("Revoking the session failed with HTTP %s: %s" % (status, _error_message(payload)))


def websocket_url(base_url):
    url = base_url.rstrip("/")
    if url.startswith("https://"):
        url = "wss://" + url[len("https://"):]
    elif url.startswith("http://"):
        url = "ws://" + url[len("http://"):]
    return url + "/api/websocket"


class WebSocketClient:
    """Minimal synchronous HA WebSocket API client."""

    def __init__(self, base_url, token, timeout=10, validate_certs=True):
        self.base_url = base_url
        self.token = token
        self.timeout = timeout
        self.validate_certs = validate_certs
        self.ha_version = None
        self._conn = None
        self._next_id = 1

    def connect(self):
        sslopt = None if self.validate_certs else {"cert_reqs": ssl.CERT_NONE, "check_hostname": False}
        url = websocket_url(self.base_url)
        try:
            self._conn = websocket.create_connection(url, timeout=self.timeout, sslopt=sslopt)
            message = self._receive()
            if message.get("type") != "auth_required":
                raise HomeAssistantError("Unexpected first WebSocket message: %r" % message)
            self.ha_version = message.get("ha_version")
            self._send({"type": "auth", "access_token": self.token})
            message = self._receive()
        except HomeAssistantError:
            self.close()
            raise
        except Exception as exc:
            self.close()
            raise HomeAssistantError("WebSocket connection to %s failed: %s" % (url, exc))
        if message.get("type") != "auth_ok":
            self.close()
            raise HomeAssistantError("WebSocket authentication failed: %s" % message.get("message", message))
        self.ha_version = message.get("ha_version", self.ha_version)
        return self

    def close(self):
        if self._conn is not None:
            try:
                self._conn.close()
            except Exception:
                pass
            self._conn = None

    def __enter__(self):
        return self.connect()

    def __exit__(self, *args):
        self.close()

    def _send(self, message):
        self._conn.send(json.dumps(message))

    def _receive(self):
        return json.loads(self._conn.recv())

    def wait_closed(self, timeout):
        """Wait for the server to close the connection (e.g. on restart); return False on timeout."""
        if self._conn is None:
            return True
        deadline = time.time() + timeout
        self._conn.settimeout(1)
        while time.time() < deadline:
            try:
                opcode = self._conn.recv_data()[0]
            except websocket.WebSocketTimeoutException:
                continue
            except Exception:  # connection reset or closed without a close frame
                opcode = websocket.ABNF.OPCODE_CLOSE
            if opcode == websocket.ABNF.OPCODE_CLOSE:
                self.close()
                return True
        return False

    def call(self, command, **params):
        """Send a command and return its ``result``; raise HomeAssistantAPIError on failure."""
        if self._conn is None:
            raise HomeAssistantError("WebSocket is not connected")
        message_id = self._next_id
        self._next_id += 1
        message = dict(params, id=message_id, type=command)
        try:
            self._send(message)
            while True:
                reply = self._receive()
                # Skip anything that is not the answer to this command (e.g. pongs, events).
                if reply.get("id") == message_id and reply.get("type") == "result":
                    break
        except Exception as exc:
            raise HomeAssistantError("WebSocket command %s failed: %s" % (command, exc))
        if not reply.get("success"):
            error = reply.get("error") or {}
            raise HomeAssistantAPIError(error.get("code", "unknown_error"), error.get("message", "Unknown error"))
        return reply.get("result")


class HomeAssistantModule(AnsibleModule):
    """AnsibleModule with HA connection options and a lazily connected WebSocket client."""

    def __init__(self, argument_spec, **kwargs):
        spec = connection_argument_spec()
        spec.update(argument_spec)
        super().__init__(argument_spec=spec, **kwargs)
        if not HAS_WEBSOCKET:
            self.fail_json(msg=missing_required_lib("websocket-client"), exception=WEBSOCKET_IMPORT_ERROR)
        self._ws = None

    @property
    def ws(self):
        if self._ws is None:
            client = WebSocketClient(self.params["url"], self.params["token"], timeout=self.params["timeout"],
                                     validate_certs=self.params["validate_certs"])
            try:
                client.connect()
            except HomeAssistantError as exc:
                self.fail_json(msg=str(exc))
            self._ws = client
            if client.ha_version and not is_version_supported(client.ha_version):
                self.warn("Home Assistant %s is older than the oldest supported release %s; "
                          "the module may not work as expected." % (client.ha_version, MIN_HA_VERSION))
        return self._ws

    def call(self, command, **params):
        """Run a WebSocket command, failing the module on any error."""
        try:
            return self.ws.call(command, **params)
        except HomeAssistantAPIError as exc:
            self.fail_json(msg="Home Assistant rejected %s: %s" % (command, exc.message), error_code=exc.code)
        except HomeAssistantError as exc:
            self.fail_json(msg=str(exc))

    def rest(self, path, method="GET", data=None):
        """Authenticated REST call: ``(status, decoded_json)``; transport errors fail the module."""
        try:
            return rest_request(self.params["url"], path, method=method, data=data, token=self.params["token"],
                                timeout=self.params["timeout"], validate_certs=self.params["validate_certs"])
        except HomeAssistantError as exc:
            self.fail_json(msg=str(exc))

    def call_optional(self, command, **params):
        """Like ``call``, but return ``None`` when Home Assistant answers ``not_found``."""
        try:
            return self.ws.call(command, **params)
        except HomeAssistantAPIError as exc:
            if exc.code == "not_found":
                return None
            self.fail_json(msg="Home Assistant rejected %s: %s" % (command, exc.message), error_code=exc.code)
        except HomeAssistantError as exc:
            self.fail_json(msg=str(exc))

    def exit_json(self, **kwargs):
        if self._ws is not None:
            self._ws.close()
        super().exit_json(**kwargs)

    def fail_json(self, msg, **kwargs):
        if getattr(self, "_ws", None) is not None:
            self._ws.close()
        super().fail_json(msg=msg, **kwargs)

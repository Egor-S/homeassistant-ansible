# -*- coding: utf-8 -*-
# Copyright (c) 2026, Egor Sklyarov
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

"""Print the refresh tokens of the user owning the token as JSON: list_tokens.py URL (token on stdin)."""

from __future__ import annotations

import json
import sys

import websocket


def main():
    url = sys.argv[1].rstrip("/").replace("http://", "ws://", 1).replace("https://", "wss://", 1)
    conn = websocket.create_connection(url + "/api/websocket", timeout=10)
    try:
        conn.recv()
        conn.send(json.dumps({"type": "auth", "access_token": sys.stdin.read().strip()}))
        reply = json.loads(conn.recv())
        if reply.get("type") != "auth_ok":
            sys.exit("auth failed: %s" % reply)
        conn.send(json.dumps({"id": 1, "type": "auth/refresh_tokens"}))
        print(json.dumps(json.loads(conn.recv())["result"]))
    finally:
        conn.close()


if __name__ == "__main__":
    main()

# -*- coding: utf-8 -*-
# Copyright (c) 2026, Egor Sklyarov
# GNU General Public License v3.0+ (see LICENSE or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations


class ModuleDocFragment:

    # Options shared by all modules that talk to an onboarded Home Assistant.
    DOCUMENTATION = r"""
options:
  url:
    description:
      - Base URL of the Home Assistant instance, for example V(http://homeassistant.local:8123).
      - If not set, the value of the E(HASS_URL) environment variable is used.
    type: str
    required: true
  token:
    description:
      - Access token used to authenticate, usually the RV(egors.homeassistant.login#module:token) returned by
        M(egors.homeassistant.login), or a long-lived access token created in the Home Assistant user profile
        and kept in Ansible Vault.
      - If not set, the value of the E(HASS_TOKEN) environment variable is used.
    type: str
    required: true
  validate_certs:
    description:
      - Whether to validate TLS certificates when O(url) uses HTTPS.
    type: bool
    default: true
  timeout:
    description:
      - Timeout in seconds for network operations.
    type: int
    default: 10
requirements:
  - websocket-client
notes:
  - "Modules run on the controller; use C(delegate_to: localhost) or a host with C(ansible_connection=local)."
  - Only the newest Home Assistant release is supported. Older releases cause a warning.
"""

    # Options for modules that do not need a token (onboarding).
    ENDPOINT = r"""
options:
  url:
    description:
      - Base URL of the Home Assistant instance, for example V(http://homeassistant.local:8123).
      - If not set, the value of the E(HASS_URL) environment variable is used.
    type: str
    required: true
  validate_certs:
    description:
      - Whether to validate TLS certificates when O(url) uses HTTPS.
    type: bool
    default: true
  timeout:
    description:
      - Timeout in seconds for individual network operations.
    type: int
    default: 10
notes:
  - "Modules run on the controller; use C(delegate_to: localhost) or a host with C(ansible_connection=local)."
"""

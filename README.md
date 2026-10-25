# Ansible Collection: egors.homeassistant

> **Status: MVP / work in progress.** Interfaces may change.

Ansible modules to provision and configure [Home Assistant](https://www.home-assistant.io/)
over its REST and WebSocket APIs. Modules run on the controller, compare the
current state with the desired one and apply changes only when needed (check
mode and `--diff` supported).

## Requirements

- ansible-core >= 2.20 (tested with 2.20 and 2.21)
- Python package `websocket-client` on the controller
- A recent Home Assistant release (only the newest release is supported)

## Installation

```shell
pip install websocket-client
ansible-galaxy collection install git+https://github.com/Egor-S/homeassistant-ansible.git
```

## Planned modules

- `onboarding` - complete first-run onboarding and create a long-lived token
- `core_config` - core configuration (partial state)
- `area` - manage a single area
- `area_info` - list areas

See [docs/design.md](docs/design.md) for design decisions.

## Example (placeholder)

```yaml
- name: Configure Home Assistant
  hosts: localhost
  gather_facts: false
  module_defaults:
    group/egors.homeassistant.all:
      url: http://homeassistant.local:8123
      token: "{{ hass_token }}"
  tasks:
    - name: Ensure area exists
      egors.homeassistant.area:
        name: Living room
        state: present
```

## License

GPL-3.0-or-later

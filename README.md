# Homelab

Ansible-managed homelab running on Proxmox.

## Nodes
- ops-01: 192.168.137.101 — Ansible controller, GitHub runner
- app-01: 192.168.137.102 — Docker apps
- rpi-01: DNS, AdGuard

## Quick start
ansible-playbook playbooks/bootstrap.yml
# test

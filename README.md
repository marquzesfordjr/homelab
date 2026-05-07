# Homelab

Ansible-managed homelab running on Proxmox cluster.

## Infrastructure

### Nodes
| Host | IP | Role |
|------|----|------|
| pxm01 | 192.168.137.241 | Proxmox Node 1 |
| pxm02 | 192.168.137.242 | Proxmox Node 2 |
| ops-01 | 192.168.137.101 | Ansible controller, GitHub runner |
| rpi-01 | 192.168.137.50 | Raspberry Pi 5 w/ POE HAT/SSD - AdGuard, NAS |

### LXC Containers
| CT | Hostname | IP | Service |
|----|----------|----|---------|
| 200 | caddy | 192.168.137.200 | Reverse proxy |
| 201 | vaultwarden | 192.168.137.201 | Password manager |
| 202 | authentik | 192.168.137.202 | Identity provider |
| 203 | homarr | 192.168.137.203 | Dashboard |
| 204 | grafana | 192.168.137.204 | Metrics dashboards |
| 205 | prometheus | 192.168.137.205 | Metrics collection |
| 206 | uptime-kuma | 192.168.137.206 | Uptime monitoring |
| 207 | code-server | 192.168.137.207 | VS Code in browser |
| 208 | opencanary | 192.168.137.208 | Honeypot |
| 209 | tailscale | 192.168.137.209 | VPN subnet router |
| 210 | stremio | 192.168.137.210 | Stremio server + MediaFusion |

### Network
- Subnet: 192.168.137.0/24
- Gateway: 192.168.137.1 (TP-Link travel router)
- DNS: 192.168.137.50 (AdGuard Home)
- WiFi AP: 192.168.137.2 (TP-Link AXE75)
- Remote access: Tailscale

## Services
- **Homarr** — https://homarr.local
- **Vaultwarden** — https://vaultwarden.local
- **Grafana** — https://grafana.local
- **Uptime Kuma** — https://uptime.local
- **Code Server** — https://code.local
- **OpenCanary** — https://opencanary.local
- **Authentik** — https://authentik.local
- **Proxmox** — https://192.168.137.241:8006

## Quick Start
```bash
# Deploy all services
ansible-playbook playbooks/docker.yml -i inventories/hosts.yml

# Deploy specific service
ansible-playbook playbooks/deploy_homarr.yml -i inventories/hosts.yml

# Run backup
bash scripts/backup.sh
```

## Backups
Automated nightly backups at 3am to Pi NAS (`/mnt/ssd/share/backups`).
7 days retention.

## Access
- Local: 192.168.137.0/24
- Remote: Tailscale VPN
- SSH: YubiKey 5 NFC required from MacBook

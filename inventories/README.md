# Homelab

Ansible-managed homelab running on Proxmox cluster.

## Infrastructure

### Nodes
| Host | IP | Role |
|------|----|------|
| pxm01 | 192.168.137.241 | Proxmox Node 1 (16GB RAM) |
| pxm02 | 192.168.137.242 | Proxmox Node 2 (8GB RAM) |
| ops-01 | 192.168.137.101 | Ansible controller, GitHub runner |
| rpi-01 | 192.168.137.50 | Raspberry Pi 5 — AdGuard, NAS |

### LXC Containers (pxm01)
| CT | Hostname | IP | Service |
|----|----------|----|---------|
| 200 | caddy | 192.168.137.200 | Reverse proxy |
| 201 | vaultwarden | 192.168.137.201 | Password manager |
| 202 | homeassistant | 192.168.137.202 | Home Assistant |
| 203 | glance | 192.168.137.203 | Dashboard |
| 204 | grafana | 192.168.137.204 | Metrics dashboards |
| 205 | prometheus | 192.168.137.205 | Metrics collection |
| 206 | uptime-kuma | 192.168.137.206 | Uptime monitoring |
| 207 | code-server | 192.168.137.207 | VS Code in browser |
| 208 | nextcloud | 192.168.137.208 | Cloud storage |
| 209 | tailscale | 192.168.137.209 | VPN subnet router |
| 210 | stremio | 192.168.137.210 | Stremio + MediaFusion |

### VMs (pxm01)
| VM | Hostname | IP | Service |
|----|----------|----|---------|
| 100 | opnsense | 192.168.137.100 | Firewall + IDS |

### VMs (pxm02)
| VM | Hostname | IP | Service |
|----|----------|----|---------|
| 300 | elk | 192.168.137.110 | ELK Stack SOC |
| 302 | almalinux | 192.168.137.130 | RHCSA Practice |

### Network
- Subnet: 192.168.137.0/24 (flat, VLAN migration pending)
- Gateway: 192.168.137.1 (TP-Link travel router)
- DNS: 192.168.137.50 (AdGuard Home)
- WiFi AP: 192.168.137.2 (TP-Link AXE75)
- Firewall: 192.168.137.100 (OPNsense)
- Remote access: Tailscale

## Services
- **Glance** — http://192.168.137.203:8080
- **Vaultwarden** — https://vaultwarden.local
- **Grafana** — https://grafana.local
- **Uptime Kuma** — https://uptime.local
- **Code Server** — https://code.local
- **Nextcloud** — http://192.168.137.208:8080
- **Home Assistant** — http://192.168.137.202:8123
- **Proxmox** — https://192.168.137.241:8006
- **OPNsense** — https://192.168.137.100
- **Kibana** — http://192.168.137.110:5601
- **AdGuard** — http://192.168.137.50

## Security
- OPNsense firewall with Suricata IDS/IPS
- YubiKey FIDO2 SSH authentication (MacBook)
- Tailscale zero-trust VPN with ACL policies
- ELK Stack centralized logging
- Vaultwarden self-hosted secrets management
- Automated nightly backups to Pi NAS

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

## Pending
- VLAN migration (192.168.20.x for homelab, 192.168.40.x for trusted)
- Nextcloud NFS storage fix
- SSH hardening (disable password auth)
- Proxmox 2FA
- Tailscale 2FA
- RHCSA practice on AlmaLinux VM

## Access
- Local: 192.168.137.0/24
- Remote: Tailscale VPN
- SSH: YubiKey 5 NFC (MacBook), password (Windows PC)

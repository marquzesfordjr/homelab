# Homelab Infrastructure

Full ground-up rebuild completed — dedicated firewall hardware, proper VLAN segmentation, 3-node Proxmox cluster, and a complete security/monitoring stack.

## Network

**IP Scheme:** 10.x.x.x, VLAN ID = second octet

| VLAN | Name | Subnet | Gateway |
|---|---|---|---|
| 10 | Management | 10.10.1.0/24 | 10.10.1.1 |
| 20 | Homelab | 10.20.0.0/24 | 10.20.0.1 |
| 30 | IoT | 10.30.0.0/24 | 10.30.0.1 |
| 40 | Trusted | 10.40.0.0/24 | 10.40.0.1 |
| 50 | Lab | 10.50.0.0/24 | 10.50.0.1 |

## Physical Hardware

| Device | Model | IP | Role |
|---|---|---|---|
| Protectli FW4B | Dedicated firewall | 10.10.1.1 | OPNsense + Suricata IDS |
| pxm01 | ThinkCentre M910q | 10.10.1.241 | Proxmox Node 1 (16GB RAM) |
| pxm02 | ThinkCentre M910q | 10.10.1.242 | Proxmox Node 2 (16GB RAM) |
| pxm03 | ThinkCentre M910q | 10.10.1.243 | Proxmox Node 3 (8GB RAM) |
| Pi | Raspberry Pi 5 | 10.20.0.50 | AdGuard DNS Primary + kiosk display |
| Omada Switch | TP-Link SG2210P | 10.10.1.3 / 10.20.0.3 | Main VLAN trunk switch |
| Netgear Switch | GS308EP | 10.40.0.4 | PoE switch (Pi, PS5) |
| AP | TP-Link AXE75 | 10.30.0.2 | WiFi (3 SSIDs, WPA3/WPA2) |
| 2TB External Drive | USB | mounted on pxm02 | Nextcloud data + PBS datastore |

## LXC Containers

| CT | Hostname | IP | Node | Service |
|---|---|---|---|---|
| 100 | ansible-01 | 10.20.0.100 | pxm01 | Ansible controller |
| 200 | caddy | 10.20.0.200 | pxm01 | Reverse proxy + auto TLS |
| 201 | vaultwarden | 10.20.0.201 | pxm01 | Password manager (HTTPS) |
| 202 | homeassistant | 10.20.0.202 | pxm02 | Smart home |
| 203 | glance | 10.20.0.203 | pxm02 | Dashboard |
| 204 | grafana | 10.20.0.204 | pxm01 | Metrics visualization |
| 205 | prometheus | 10.20.0.205 | pxm01 | Metrics collection |
| 206 | uptime-kuma | 10.20.0.206 | pxm02 | Uptime monitoring + ntfy |
| 208 | nextcloud | 10.20.0.208 | pxm02 | Cloud storage (2TB drive) |
| — | adguard-backup | 10.20.0.51 | Pi (bare-metal) | AdGuard backup DNS |

## VMs

| VM | Hostname | IP | Node | Disk | Service |
|---|---|---|---|---|---|
| 900 | pbs | 10.20.0.90 | pxm02 | 32GB OS + 500GB datastore | Proxmox Backup Server |
| 510 | nessus | 10.50.0.10 | pxm03 | 40GB | Vulnerability scanning |

## Security Stack

- **Suricata IDS** — running on OPNsense WAN, ET Open rulesets (attack_response, exploit, malware, scan, web_server, trojan)
- **Nessus Essentials** — baseline scan complete, findings patched via Ansible fleet-wide update
- **SSH hardening** — key-only auth, YubiKey (SK) support, strong ciphers, login banners, fail-safe MaxAuthTries
- **Vaultwarden** — HTTPS via Caddy, self-hosted password manager
- **Tailscale** — subnet router on OPNsense, all 5 VLANs advertised, ACL-restricted family devices

## Backup Strategy

- **PBS (Proxmox Backup Server)** — dedicated VM on pxm02, 500GB datastore on separate physical disk from OS
- Daily automated backups of all LXCs/VMs (excluding PBS itself) via `vzdump` scheduled job, 3am
- **Nextcloud → NAS backup** — nightly rsync from Pi's Samba share into Nextcloud storage
- **Weekly OS patching** — Ansible cron job, Sundays 5am, auto-reboot if kernel update requires it

## Software & Tools

Proxmox VE, Ansible, AdGuard Home, Caddy, Prometheus + Grafana, Uptime Kuma, Vaultwarden, Glance, Home Assistant, Nextcloud, OPNsense, Suricata, Tailscale, Watchtower, Proxmox Backup Server, Nessus Essentials, YubiKey 5 NFC

## Key Lessons From This Rebuild

1. **VLAN membership must be Untagged (not Tagged) on ports connecting non-VLAN-aware devices** — this single setting caused most cross-device connectivity failures across nodes, VMs, and switch management interfaces this round.
2. **Nessus needs a real VM, not an LXC** — kernel-level scanning requirements make containers unreliable.
3. **Proxmox's default apt/pkg repos are paid-enterprise by default** — switch to `pve-no-subscription` / `pbs-no-subscription` on every node/PBS instance immediately after install.
4. **Any VLAN with restrictive firewall rules needs an explicit DNS (port 53) exception** to the AdGuard IPs, positioned above the block rule.
5. **Check actual node disk/RAM capacity before placing large VMs** — pxm03's real 68GB root volume (not the expected ~230GB) caused a PBS placement failure; always verify with `lsblk`/`vgs` before sizing.
6. **PBS should never back up itself in the same job** — exclude the PBS VM ID from its own backup job to avoid resource contention and filesystem lock issues.
7. **Tailscale route advertisement must be set in the plugin's persistent config, not just via CLI** — CLI-only `--advertise-routes` gets wiped on service restart/reboot.

## Remaining / Optional

- Wazuh — deliberately skipped for now
- Stremio — not needed currently
- AlmaLinux/RHEL Lab VMs — available for RHCSA practice
- Omada switch TRUSTED-VLAN (10.40.0.3) management reachability — cosmetic issue, workaround in place (monitor via 10.20.0.3 instead)

---

## Update — Firewall Hardware Replacement & Service Expansion

### Firewall: Protectli FW4B → Custom J4105 Mini PC

**New hardware:** Intel J4105 Quad Core, 4x Intel i226-V 2.5GbE NICs (`igc0-3`), 8GB DDR4, 240GB mSATA. OPNsense reinstalled fresh (UFS), config rebuilt from scratch after repeated failed restore attempts.

**Critical hardware bug found and fixed:** Intel i225-V/i226-V controllers have a documented firmware/EEE (Energy Efficient Ethernet) power-management bug causing random link drops and dropped VLAN tags under normal traffic. Confirmed via `tcpdump -e` packet capture — frames arrived genuinely untagged despite correct switch-side VLAN config.

**Fix applied** — added to `/boot/loader.conf.local`:
hw.igc.disable_aspm=1
dev.igc.0.eee_control=0
dev.igc.1.eee_control=0
dev.igc.2.eee_control=0
dev.igc.3.eee_control=0
dev.igc.0.fc=0
dev.igc.1.fc=0
dev.igc.2.fc=0
dev.igc.3.fc=0
hw.pci.do_power_nodriver=3

**Known permanent fix (deferred):** Intel firmware NVM 2.22+ resolves this at the hardware level; board likely shipped with buggy 2.13/2.14. Flashing via `nvmupdate64e` deferred to a future session.

**2.5G LAN limitation confirmed, not a bug:** WAN negotiates 2.5G successfully; LAN caps at 1G because the Omada SG2210P switch is Gigabit-only on every port (confirmed via spec sheet). TP-Link Omada ES210X-M2 (8x 2.5G + 2x 10G SFP+) identified as the fix — purchase pending. Netgear GS308EP retained for PoE.

**New interface assignments:** `igc0` = LAN, `igc1` = WAN, `igc2`/`igc3` unused.

### Home Assistant: LXC → HAOS VM

Migrated from containerized Home Assistant (CT 202) to full Home Assistant OS as a Proxmox VM via the community-scripts Helper Script — same VM ID and IP (202 / 10.20.0.202), no prior data to migrate. HACS reinstalled. Official Tuya cloud integration used for Eightree smart plugs.

**Known gap:** official Tuya integration doesn't expose power/energy entities for the Eightree ET01BG plugs, though the Smart Life app confirms hardware support. LocalTuya with manual DP mapping is the fix — deferred.

### New LXC Services Deployed (10.20.0.210-219)

| Service | IP | Status |
|---|---|---|
| Fail2Ban | 10.20.0.210 | Deployed, superseded by CrowdSec |
| CrowdSec (central) | 10.20.0.211 | Fully deployed — agents + firewall bouncers on Caddy, pxm01/02/03; enrolled in CrowdSec Console |
| Navidrome (was Infisical) | 10.20.0.212 | Deployed, no library populated |
| Netdata | 10.20.0.213 | Deployed |
| PeaNUT | 10.20.0.214 | Deployed, dormant — no UPS yet |
| Ghostfolio (was OctoPrint) | 10.20.0.215 | Deployed, SSL config fixed |
| Seanime | 10.20.0.216 | Deployed |
| Willow | 10.20.0.217 | Deployed, needs ESP32 hardware |
| WorldMonitor | 10.20.0.218 | Deployed, built from source |
| Actual Budget | 10.20.0.219 | Deployed, HTTPS via Caddy, bank sync deferred |

### DNS Hardening — Verified Working End-to-End

- Port 53 NAT redirect to AdGuard on IoT/TRUSTED/HOMELAB regardless of client DNS config
- DoT/DoH blocked on IoT/TRUSTED/HOMELAB; LAB intentionally open for security testing
- Verified: hardcoded `nslookup ... 8.8.8.8` confirmed intercepted (visible in AdGuard query log); DoT/DoH connections confirmed blocked
- Upstream tuned to Cloudflare (1.1.1.1, 1.0.0.1) based on real multi-position latency testing

### Planned / Deferred

- UPS purchase (CyberPower CP800AVR)
- 2.5G switch purchase (Omada ES210X-M2)
- i226-V NIC firmware update (NVM 2.22+)
- LocalTuya DP mapping for energy monitoring
- n8n deployment (notification consolidation, CrowdSec alert enrichment, budget CSV automation)
- Eightree plugs re-paired to IoT VLAN (deferred to apartment move)

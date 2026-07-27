# Homelab Ground-Up Rebuild Runbook

**Status: Core rebuild COMPLETE.** This doc now serves as both the original plan and a record of what was actually built, including deviations, gotchas, and remaining work.

**Goal:** Rebuild the entire homelab from scratch with network segmentation designed in from day one, on dedicated hardware, instead of retrofitted onto a live flat network.

**Core principle for this rebuild:** Network and VLANs get finalized and tested FIRST, on dedicated firewall hardware, before any services exist. Services get deployed onto a network that's already proven to work — never the other way around.

**IP scheme actually used:** `10.x.x.x` (not `192.168.x.x` as originally drafted below — upgraded mid-planning for more headroom and closer alignment with enterprise/DoD conventions). See the corrected addressing table in Phase 2.

---

## Hardware Inventory (as deployed)

- [x] Protectli Vault FW4B — dedicated OPNsense firewall, 4x Intel NIC (igb0-3), UFS filesystem
- [x] 3rd ThinkCentre M910q — pxm03, i5-6500T, **8GB RAM** (not 16GB as originally assumed — pxm01/pxm02 are 16GB, pxm03 is 8GB; this changed the node workload distribution, see Phase 4)
- [x] DeskPi RackMate T2 (12U, 10.23" depth)
- [x] Netgear GS308EP (PoE switch — powers Pi, hosts PS5)
- [x] TP-Link Omada SG2210P (main VLAN trunk switch, 8x PoE+ ports, 61W budget)
- [x] Raspberry Pi 5 + PoE HAT + GeekPi 7" touchscreen (kiosk display, stays in-rack)
- [x] Tower/desktop UPS (NOT rack-mounted — 10" rack won't fit standard rack-mount UPS units)
- [x] TP-Link Archer AXE75/AXE5400 access point (existing hardware, not part of original hardware list but configured this round — see Phase 2.6)

---

## Phase 0 — Backup Everything Before Touching Hardware ✅ DONE

---

## Phase 1 — Physical Layer ✅ DONE

### 1.1 Final Rack Layout (top to bottom) — matches original plan

| U | Item |
|---|---|
| 1-2 | Omada SG2210P |
| 3-4 | Netgear GS308EP |
| 5 | Protectli FW4B |
| 6 | Raspberry Pi 5 + PoE HAT + touchscreen |
| 7-8 | pxm01 |
| 9-10 | pxm02 |
| 11 | pxm03 |
| 12 | Free |

### 1.2 Final Switch Port Map (Omada SG2210P, physical ports 8→1)

| Port | Device | PVID | Frame Type |
|---|---|---|---|
| 8 | Protectli LAN (igb1) | 10 | Tagged Only |
| 7 | pxm01 | 10 | Admit All |
| 6 | pxm02 | 10 | Admit All |
| 5 | pxm03 | 10 | Admit All |
| 4 | Netgear uplink | 10 | Tagged Only |
| 3 | AP | 30 | Admit All |
| 2 | Free (IoT growth) | — | — |
| 1 | PC | 40 | Admit All |

### 1.3 Netgear GS308EP port map

| Port | Device | PVID | Frame Type |
|---|---|---|---|
| 1 | Raspberry Pi (PoE) | 20 | Admit All |
| 2 | Uplink to Omada (port 4) | 10 | Tagged Only |
| 3 | PS5 | 30 | Admit All |
| 4-8 | Free | — | — |

⚠️ **Known issue (unresolved):** Netgear's management IP (`10.40.0.4`) responds inconsistently from cross-VLAN sources despite working fine when queried directly from OPNsense. Root cause suspected to be that the Netgear's management interface isn't actually bound to a tagged VLAN 40 the way Omada's is — it just has an IP in that range without real VLAN membership. Low priority (data-plane traffic through the switch works fine); parked for a dedicated troubleshooting session.

---

## Phase 2 — Network Foundation ✅ DONE (with real IP scheme + hard-won fixes below)

### 2.1 OPNsense on Protectli — as built
- [x] Fresh OPNsense install, UFS filesystem, amd64
- [x] WAN = igb0 (DHCP from Verizon CR1000A, direct — travel router retired from the chain)
- [x] LAN = igb1 (untagged, holds a legacy flat IP `10.10.0.1/24` — kept for direct-connect troubleshooting access, otherwise unused)

### 2.2 Actual VLAN / addressing scheme (10.x.x.x, not 192.168.x.x)

| VLAN | Name | Subnet | Gateway | Purpose |
|---|---|---|---|---|
| 10 | Management | 10.10.1.0/24 | 10.10.1.1 | Switches, Proxmox nodes, Protectli MGMT |
| 20 | Homelab | 10.20.0.0/24 | 10.20.0.1 | All LXCs/services, Pi/AdGuard |
| 30 | IoT | 10.30.0.0/24 | 10.30.0.1 | AP SSIDs, PS5 |
| 40 | Trusted | 10.40.0.0/24 | 10.40.0.1 | PC, switch management IPs |
| 50 | Lab | 10.50.0.0/24 | 10.50.0.1 | Nessus VM, future AlmaLinux VMs |

**Note:** MGMT ended up at `10.10.1.x` rather than `10.10.0.x` — a conflict arose between the untagged LAN interface (`10.10.0.1`, kept for direct-connect access) and the tagged MGMT VLAN interface trying to also use `10.10.0.1`. Resolved by shifting MGMT to the `.1.x` range.

### 2.3 Firewall rules — actual final ruleset per VLAN

- **MGMT:** pass any
- **HOMELAB:** pass any, plus explicit ICMP-allow exceptions added later for Uptime Kuma to monitor switch IPs cross-VLAN
- **IOT:** pass any, PLUS two mandatory explicit allow rules for DNS (UDP/TCP port 53) to `10.20.0.50` and `10.20.0.51` placed **above** any restrictive rule — IoT devices need DNS access to AdGuard even if you want to otherwise restrict IoT's reach into HOMELAB
- **TRUSTED:** pass any
- **LAB:** pass any, PLUS the same explicit DNS-to-AdGuard allow rules as IoT (LAB devices also need to reach `10.20.0.50/51` on port 53 specifically)

⚠️ **Hard lesson:** any VLAN with `block → private ranges` or `block → HOMELAB` rules will also block DNS to AdGuard unless you add explicit pass rules for UDP/TCP port 53 to the AdGuard IPs, positioned above the block rule. This bit us twice (IoT and LAB) during the rebuild. Do this proactively for any future restricted VLAN.

### 2.4 Switch Configuration — the critical gotcha

- [x] VLANs 10/20/30/40/50 created on both Omada and Netgear switches
- [x] Trunk ports (Protectli, inter-switch uplink) = **Tagged Only**, tagged on all VLANs

**🔑 THE KEY FIX — spent multiple sessions on this across the whole project, finally solved this round:**
Proxmox node ports (and any port connecting a device with a non-VLAN-aware NIC, e.g. a bare-metal server sending untagged management traffic) must be:
- PVID = the VLAN they belong to (e.g. 10 for MGMT)
- Frame Type = **Admit All**
- Membership in **that specific VLAN = Untagged** (not Tagged!)
- Membership in all *other* VLANs the port needs to carry (for VM/LXC traffic) = Tagged

The switch needs to **strip the VLAN tag on egress** to a device that can't understand tags. Setting the port's own VLAN as Tagged (instead of Untagged) causes exactly this symptom: ARP requests go out fine, but replies never make it back to the device — one-way traffic that looks like a routing problem but is actually this specific membership setting.

### 2.5 DNS — final IPs
- [x] Pi/AdGuard primary: `10.20.0.50`
- [x] AdGuard backup: `10.20.0.51` (moved from an initial `.207` LXC-style IP to this dedicated address)
- [x] Both set as DHCP DNS options across all VLANs (with the port-53 firewall exceptions noted above for restricted VLANs)

---

### 2.6 Access Point (TP-Link Archer AXE75/AXE5400) ✅ DONE

- [x] Configured in **Router mode with DHCP OFF** (not AP mode — this hardware's AP mode is unreliable, see below)
- [x] LAN IP: `10.30.0.2/24`, gateway `10.30.0.1`, AP Isolation OFF
- [x] 3 SSIDs configured: hidden personal network, "Private" (actually the guest network, named misleadingly on purpose), "SmartHome" (IoT)
- [x] Security: WPA3-Personal + WPA2-PSK (transition mode) on all three

⚠️ **Known hardware limitation:** this consumer-grade router does **not** support per-SSID VLAN tagging (confirmed directly by TP-Link support staff in their forums — no home/consumer TP-Link router does, only their business Omada EAP line does). All 3 SSIDs land on VLAN 30 regardless of name. Real per-network isolation would require replacing this AP with an Omada EAP-series unit in the future.

⚠️ **Known firmware bug:** the web admin login page enters a refresh/login-loop, especially after being connected through a switch (vs. direct connection) or after periods of inactivity. This is a widely-reported, longstanding TP-Link firmware issue across their consumer router line, not specific to this setup. Workaround: complete all config changes in the first few minutes immediately after a power cycle/reboot, when the session is briefly stable. The Tether mobile app is sometimes more reliable than the web UI for quick changes.

---

## Phase 3 — Proxmox Cluster ✅ DONE

- [x] Fresh Proxmox VE install on all 3 ThinkCentres, ext4 filesystem
- [x] Node management IPs on VLAN 10: `pxm01=10.10.1.241`, `pxm02=10.10.1.242`, `pxm03=10.10.1.243`
- [x] 3-node cluster formed, real quorum confirmed (`pvecm status` → Quorate: Yes)
- [x] Switched all 3 nodes from Proxmox's default enterprise repos (which 401 without a paid subscription) to the free `pve-no-subscription` repo — needed on every node before `apt update` will work
- [x] vmbr0 set VLAN-aware (`bridge-vlan-aware yes`) on all 3 nodes — required for LXC/VM VLAN tagging to work at all

---

## Phase 4 — Infrastructure as Code ✅ DONE

### 4.1 Node/ID/IP convention actually used

| ID range | Role | IP pattern |
|---|---|---|
| 100-109 | Infrastructure (Ansible controller, etc.) | 10.20.0.1xx |
| 200-219 | Homelab services (VLAN 20 LXCs) | 10.20.0.2xx |
| 500-599 | Lab VMs (VLAN 50) | 10.50.0.xx |
| 900-909 | VMs — Wazuh, PBS (planned) | 10.20.0.9x |

### 4.2 Final node/service distribution (adjusted once pxm03's real 8GB RAM was confirmed — original plan assumed 16GB)

| Node | RAM | Hosts |
|---|---|---|
| pxm01 | 16GB | Ansible (100), Caddy (200), Vaultwarden (201), Grafana (204), Prometheus (205), AdGuard backup (was 207, moved to 10.20.0.51) |
| pxm02 | 16GB | Home Assistant (202), Glance (203), Uptime Kuma (206), Nextcloud (208) |
| pxm03 | 8GB | Nessus VM (510) — lighter workload matching its smaller RAM |

### 4.3 Ansible controller
- [x] CT 100, Debian 12, `10.20.0.100`
- [x] SSH key-based auth throughout — controller's own key pushed to every host via `authorized_key` module in one Ansible run

### 4.4 Deployment order used
1. Docker install across all LXCs (`docker.yml`) — one playbook, all hosts, single run
2. AdGuard backup
3. Vaultwarden
4. Caddy
5. Prometheus, Grafana, Uptime Kuma, Glance, Home Assistant, Nextcloud

### 4.5 Known LXC/Docker gotchas hit during this rebuild (fix proactively next time)
- **Overlayfs permission denied** inside unprivileged LXCs running Docker — fix: `pct set <ID> --features nesting=1,keyctl=1` on every Docker-hosting container, done *before* first `docker compose up`
- **Watchtower `WATCHTOWER_NOTIFICATIONS=false`** crashes on current Watchtower versions — omit the variable entirely instead of setting it to false
- **Watchtower Docker API version mismatch** inside some containers — add `DOCKER_API_VERSION=1.43` to Watchtower's environment
- **Glance mounting its config as a directory instead of a file** — happens if the compose file references a config path before the file actually exists; explicitly create the config file with content in the same Ansible play, before `docker compose up`
- **Privileged flag syntax** — this Proxmox version uses `--unprivileged 0`, not `--privileged` (used for Home Assistant, Nextcloud)

### 4.6 Ongoing automation
- [x] Watchtower on all LXCs — nightly 4am container updates
- [x] Weekly OS package update cron (`update_packages.yml`, Sundays 5am) via Ansible on the controller — kept weekly (not daily) deliberately, since OS-level updates carry more regression risk than container updates and weekly gives a window to catch problems

---

## Phase 5 — Security Stack

- [x] SSH hardening via Ansible (`harden_ssh.yml`) run against all nodes/LXCs/Pi: disabled password auth, `PermitRootLogin prohibit-password`, `MaxAuthTries 3`, disabled X11/agent forwarding, strong ciphers/MACs only, login banner
- [x] SSH key-based auth confirmed working everywhere before password auth was disabled (correct order — verify keys work FIRST, then lock the door)
- [x] Nessus VM deployed — CT-then-VM lesson: **Nessus needs a real VM, not an LXC** (raw socket/kernel access requirements make LXC containers unreliable for scanning). Original LXC attempt was destroyed and rebuilt as VM 510.
- [x] Nessus network troubleshooting chain (in order encountered): wrong VLAN tag on first LXC attempt → subnet mismatch when manually testing a non-standard IP scheme → LAB VLAN firewall block rule silently catching DNS traffic → **empty `nameservers` array in netplan** (final root cause — system had internet + could resolve via explicit `nslookup <ip> <server>` but not through the default resolver, because netplan's nameservers list was empty despite gateway/routing being correct)
- [x] Nessus Essentials activation — old code from a previous session had expired/was invalid (400 Bad Request via `nessuscli fetch --register`); resolved by registering a fresh code
- [x] Dedicated Nessus SSH scan key generated separately from personal SSH key (`nessus_scan_key`) and pushed to every host via one Ansible `authorized_key` command — keeps personal key out of Nessus's credential store
- [ ] **Not yet done:** Suricata IDS/IPS on Protectli
- [ ] **Not yet done:** Wazuh deployment (VM + agents)
- [ ] **Not yet done:** First Nessus scan launch + findings review

---

## Phase 6 — Remote Access ✅ DONE

- [x] os-tailscale plugin installed directly on OPNsense — subnet router for all 5 VLANs, no intermediate LXC needed this time (matches the plan)
- [x] Authenticated via `tailscale up --reset --advertise-routes=... --accept-routes` from OPNsense shell
- [x] Routes approved in Tailscale admin console
- [x] ACLs updated with new 10.x IPs (was `192.168.137.x` in the old policy) — `tag:admin`/`tag:homelab` full access, `tag:family` restricted to AdGuard DNS port 53 and Stremio ports
- [x] OPNsense node tagged `tag:homelab` in Tailscale admin
- [x] Verified reachable from external device (phone on cellular)

---

## Phase 7 — Monitoring & Dashboard ✅ DONE (added this round, wasn't in original plan)

- [x] Uptime Kuma monitors configured for all services + ping monitors for nodes/switches/OPNsense
- [x] ntfy.sh push notifications wired into Uptime Kuma
- [x] Grafana connected to Prometheus data source, Node Exporter dashboard imported (ID 1860)
- [x] Node Exporter deployed to every host (nodes, LXCs, Ansible controller, Pi) via Ansible
- [x] Pi kiosk display: Uptime Kuma public status page in Chromium kiosk mode
  - **Gotcha:** this Pi had **three separate, conflicting autostart mechanisms** left over from prior sessions (a labwc autostart script, an XDG `.config/autostart/dashboard.desktop` entry, AND an Openbox autostart script/`kiosk.sh` pair) — only the Openbox one was actually active. Editing the other two had zero effect and wasted real time. **Lesson: when a kiosk Pi won't pick up a new URL, check ALL of labwc/XDG-autostart/Openbox, not just one.**
  - Custom CSS applied to the status page for a cleaner look on the small 7" display

## Phase 8 — Documentation & Final Validation

- [ ] Update README in GitHub repo with new architecture diagram/table
- [ ] Update or write the SSP (System Security Plan) reflecting the new build
- [ ] Full end-to-end test: every service reachable, every VLAN behaving per firewall rules, remote access working, backups running, monitoring showing green across the board
- [ ] Take a fresh OPNsense config backup and commit reference copy (redacted of secrets) to repo

---

## Remaining Work (as of this update)

1. **Nextcloud** — point storage at the 2TB external drive (not yet mounted/connected), set up desktop + mobile sync
2. **Proxmox Backup Server** — new VM/LXC, storage pool, backup job schedule. Plan: PBS storage on a *different* node's local disk than the workloads it's backing up, to avoid a single-node failure wiping both live data and its backup
3. **Wazuh** — VM deployment + agents on every host
4. **Suricata** — IDS/IPS on Protectli
5. **First Nessus scan** — launch, review findings, write up baseline doc (same pattern as `security/nessus/scan-2026-06-20.md`)
6. **Omada/Netgear management VLAN 40 reachability** — cosmetic/management-only issue, data plane unaffected, needs a dedicated session (see Phase 1.3 note)
7. **README + SSP updates** in the GitHub repo

---

## Key Lessons — Original Plan (confirmed correct in practice)

1. **Dedicated firewall hardware, not a Proxmox VM sharing NICs with everything else** — this genuinely eliminated the USB-NIC bottleneck and most bridge/VLAN-aware complexity from the previous build.
2. **VLANs designed and tested before any service is deployed** — held up well; the one-off exceptions (LAB/IoT DNS rules) were caught and fixed quickly because the foundation was already solid.
3. **Nodes go straight onto the Management VLAN** — no flat-network staging period needed.
4. **DNS (Pi/AdGuard) gets its final IP from day one** — mostly true; AdGuard backup still moved once (from `.207` to `.51`) but this was a deliberate cleanup, not an emergency migration.
5. **3-node cluster from the start** — real quorum confirmed working; survived a node reboot cleanly.
6. **Security tooling built in as each piece comes online** — partially achieved (SSH hardening, Nessus); Suricata/Wazuh still pending.

## New Lessons From This Rebuild (add to next runbook)

1. **The single most valuable networking fix:** on any switch port connecting a device with a non-VLAN-aware NIC, that port's own "home" VLAN must be **Untagged** membership, not Tagged — even though PVID correctly stamps incoming frames, the switch also needs to *strip* the tag on the way back out, and only Untagged membership does that. This single setting caused the vast majority of "ARP works one way but not the other" symptoms across nodes, the Nessus VM, and general troubleshooting this round.
2. **Nessus needs a real VM, not an LXC.** Don't attempt the container route again — go straight to a VM.
3. **Check for empty `nameservers` arrays in netplan** whenever a Linux VM has working connectivity/routing but DNS resolution silently fails through the default resolver while explicit `nslookup <ip> <server>` works fine.
4. **Any firewall rule set that blocks a VLAN from reaching another VLAN needs an explicit carve-out for port 53 to your DNS servers**, positioned above the block — otherwise devices on that VLAN lose DNS entirely, which looks like "no internet" even though routing/NAT is fine.
5. **Proxmox's default apt repos are the paid enterprise ones and will 401 without a subscription.** Switch to `pve-no-subscription` on every node immediately after Proxmox install, before the first `apt update`.
6. **When a kiosk/autostart Pi won't pick up a new config, check every autostart mechanism, not just one** — labwc, XDG `.config/autostart`, and Openbox can all coexist on the same Pi from different setup sessions, and only one is actually active.
7. **Consumer-grade WiFi routers (TP-Link Archer/AXE line) do not support per-SSID VLAN tagging**, confirmed directly by TP-Link support — only their Omada EAP business line does. Plan hardware purchases accordingly if true network-level guest/IoT isolation over WiFi is a requirement, not just differently-named SSIDs.
8. **Confirm actual node RAM before planning workload distribution** — assumed all 3 ThinkCentres were 16GB; pxm03 was actually 8GB, which changed which services could reasonably run there.

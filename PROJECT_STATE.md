# Device Monitor — Project State

## Last updated

6 September 2026

## Current version / branch / environment

Development branch:

`v2.8-development`

Active Windows checkout:

`C:\Users\apg19\Downloads\opnsense-devicemonitor-upstream`

Primary deployment target:

OPNsense 26.7.2_2

Latest confirmed completed identity-work commit:

`c92b61b` — `feat: add identity conflict email alerts`


## Current objective

v2.8 Infrastructure Services Phase 3 is implemented and live validated.

Phase 3 adds SMB/NFS, RDP/VNC/WinRM, SNMP, LDAP/LDAPS/Kerberos
and VPN discovery using bounded protocol verification, existing targeted
Nmap evidence and authoritative local WireGuard runtime state.

Automatic infrastructure discovery does not perform a fresh Nmap sweep
across all known devices.
## Previously completed

- v2.8 IP & MAC Conflicts supports All/Unresolved/Resolved filtering through the Status selector and clickable Unresolved/Resolved summary links.

- v2.8 IP & MAC Conflicts heading shows separate Unresolved and Resolved counts; filtering remains through the Status selector.

- v2.8 IP & MAC Conflicts heading now shows separate Unresolved and Resolved counts.

- v2.8 IP & MAC Conflicts table now shows an explicit Unresolved/Resolved status badge.

- v2.8 IP & MAC Conflicts resolution filter implemented for All, Unresolved and Resolved events.

- v2.8 IP & MAC Conflicts Resolve/Reopen API and UI implemented; event history is preserved through the existing `resolved_at` field.

- v2.7 release preparation completed: version metadata, English/Czech version history, installation references and automated identity regression coverage are current.

- Added automated v2.7 identity regression coverage using isolated temporary SQLite databases.

- v2.7 README/version-history documentation updated for identity anomaly detection and IP & MAC Conflicts.

- Phase F.2 IPv6 identity-conflict detection completed and validated.
- Device Monitor IP & MAC Conflicts API/runtime completed and validated.
- IP & MAC Conflicts UI deployed and validated on OPNsense.
- IP & MAC Conflicts UI committed as `418ea5c`.
- Full Device Monitor scans completed successfully with deployed identity detection enabled.
- No identity anomalies were recorded during the validated scans.

## Current Settings-page work

The current local `settings.volt` diff includes Settings UI restructuring and About-page metadata changes, including:

- Monitoring tab
- Nmap Scanning tab
- removal/replacement of the previous Other Settings tab arrangement
- developer attribution
- development repository link
- Licensing & Compatibility section heading


## Current validation

Current validated work:

- `git diff --check`: PASS
- Licensing & Compatibility source inspection: PASS
- deployment to OPNsense: PASS
- live browser validation of all Settings tabs after deployment: PASS
- populated IP & MAC Conflicts row rendering using browser-only synthetic API data: PASS
- IP & MAC Conflicts expandable details rendering: PASS
- browser refresh restored the real empty-state API view: PASS
- GitHub push to `origin/v2.8-development`: PASS
- CI workflow includes `v2.8-development` for push and pull requests: PASS
- GitHub Actions CI run for `cf1a90e`: PASS
- v2.8 identity-email `git diff --check`: PASS
- live `scan_network.py` Python syntax validation: PASS
- isolated identity-email sent/skipped/invalid-result handling: PASS
- live `notify_identity_email.php` PHP syntax validation: PASS
- live synthetic IP & MAC conflict email delivery: PASS
- configured recipient validation: PASS
- final subject validation: `OPNsense: IP & MAC conflict alert (1 conflict)`: PASS
- final live email pluralisation validation (`conflict` / `conflicts`): PASS
- final live email font consistency validation (Arial body / monospace technical values): PASS
- final live email value-column alignment validation: PASS
- final live email visual consistency validation: PASS
- identity-conflict email commit `c92b61b`: PASS
- push of `c92b61b` to `origin/v2.8-development`: PASS
- GitHub Actions CI run `33970099256` for `c92b61b`: PASS
- observational-only message wording and IP/MAC evidence rendering: PASS
- Phase 3 single-host Nmap regression: PASS
- Phase 3 Nmap serialization and SMB-Nmap serialization: PASS
- Phase 3 lightweight protocol-probe worker bound (maximum 12): PASS
- Phase 3 protocol regression for SMB, NFS, RDP, VNC, WinRM, LDAP, SNMP/Kerberos/VPN classification and WireGuard runtime discovery: PASS
- Phase 3 strong-Nmap-evidence handling (`open|filtered` and unidentified services rejected): PASS
- isolated three-host real-network Phase 3 test: PASS
- isolated real-network test preserved the live Device Monitor database: PASS
- automatic fresh Phase 3 Nmap sweep removed after performance validation: PASS
- Phase 3 live deployment with pre-deployment SQLite backup: PASS
- live `--discover-services` execution: exit 0
- live Phase 3 RDP discovery: `192.168.20.111:3389/tcp` — verified
- live Phase 3 SMB discovery: `192.168.20.111:445/tcp` — verified, SMB 3.1.1
- live Phase 3 SNMP discovery: `192.168.20.214:161/udp` — structured Nmap service evidence
- live Phase 3 WireGuard discovery: `192.168.20.254:51821/udp` — authoritative runtime evidence
- Infrastructure Services Phase 3 UI groups and column alignment visually validated: PASS

## Infrastructure service discovery — Phase 1

Phase 1 is implemented and validated live.

Implemented and verified:

- persistent infrastructure-service inventory
- protocol-verified DHCP discovery
- protocol-verified DNS discovery
- OPNsense-configured DNS resolvers included as candidates
- DHCP and DNS availability lifecycle handling
- `last_verified` persistence
- automatic discovery rate-limited to 3600 seconds
- manual `--discover-services` mode
- Devices page Services badges

Validated live inventory:

- DHCP `192.168.20.254` — UDP/67 — verified
- DNS `192.168.20.1` — UDP/53 — verified
- DNS `192.168.20.2` — UDP/53 — verified
- DNS `192.168.20.101` — UDP/53 — verified

Automatic discovery rate limiting was validated with an immediate repeat
returning `RAN=False`.

The Devices UI was visually validated after correcting the Services/VLAN
column alignment.

## Known unresolved issues

- No known unresolved Phase 1 DHCP/DNS service-discovery issues remain.
- No known unresolved v2.8 identity-conflict email issues remain.
- Device Monitor version-display review remains separate.
- `.gitattributes` line-ending maintenance remains outside this feature.

## Current operating values

- monitored interface: IGC1
- scan interval: 300 seconds
- infrastructure-service discovery interval: 3600 seconds

## Infrastructure Services page

A dedicated Infrastructure Services page is implemented and visually
validated.

The page:

- reads the persistent `device_services` inventory through a read-only API
- groups services by infrastructure role
- shows IP, hostname, status, port/protocol, interface/VLAN, detection method,
  confidence, product/version and last verified time
- includes service-type, status and text-search filters
- shows both available and unavailable known services
- currently displays the verified DHCP and DNS Phase 1 inventory
- is designed to automatically accommodate later NTP, SSH, Web/Admin and other
  infrastructure-service discovery phases

The page is available from:

`Services -> Device Monitor -> Infrastructure Services`

Menu registration, routing, API loading and UI rendering were validated live.
Toolbar selector alignment was corrected and visually approved.

## Infrastructure service discovery — Phase 2

Phase 2 is implemented and validated live.

Protocol-verified discovery now includes:

- NTP using a real NTP request/response
- SSH using the SSH server identification banner
- Web/Admin services using real HTTP/HTTPS responses

Nmap evidence may identify non-standard SSH or web ports, but a service is
not marked verified until its protocol probe succeeds.

Validated live Phase 2 inventory:

- 2 NTP endpoints
- 7 SSH endpoints
- 14 HTTP/HTTPS endpoints

Observed verified products included OpenSSH, Dropbear, nginx, TP-LINK HTTPD,
GoAhead-Webs and OPNsense web services.

The Infrastructure Services page now displays DHCP, DNS, NTP, SSH and
Web/Admin Services. All service groups use consistent column positions.

## Infrastructure service discovery — Phase 3

Phase 3 is implemented and validated live.

Supported service roles now include:

- SMB and NFS file services
- RDP, VNC and WinRM remote access
- SNMP management
- LDAP and LDAPS directory services
- Kerberos authentication services
- VPN endpoints

Evidence handling is intentionally conservative:

- SMB, NFS, RDP, VNC, WinRM and LDAP/LDAPS use protocol-specific verification.
- SNMP, Kerberos and non-local VPN identification require structured Nmap
  service evidence; an open port alone is not sufficient.
- `open|filtered` Nmap results are not treated as proof of a service.
- local OPNsense WireGuard is discovered from authoritative `wg` runtime state.
- automatic Phase 3 discovery reuses existing targeted Nmap evidence and does
  not launch a fresh Nmap sweep across all known devices.
- any Nmap invocation used by Phase 3 remains limited to one literal IPv4
  target at a time.

Live Phase 3 inventory validated:

- RDP `192.168.20.111:3389/tcp` — verified
- SMB `192.168.20.111:445/tcp` — verified, SMB 3.1.1
- SNMP `192.168.20.214:161/udp` — discovered from Nmap service evidence
- WireGuard `192.168.20.254:51821/udp` — authoritative OPNsense runtime evidence

The Infrastructure Services page was visually validated with the new
File / NAS Services, Remote Access, SNMP / Management and VPN Endpoints
groups.

## Known unresolved issues

- No known unresolved Phase 1 DHCP/DNS discovery issues remain.
- No known unresolved Phase 2 NTP/SSH/Web discovery issues remain.
- `.gitattributes` line-ending maintenance remains outside feature commits.

## Infrastructure Services usability foundations

Infrastructure Services usability improvements are implemented and validated.

Added:

- Discover Now button with automatic refresh after discovery
- consolidated evidence for duplicate service endpoints
- Available, Unavailable and Stale presentation states
- Stale after two missed hourly verification windows
- consolidated service counts
- consistent column positions across all service groups
- Last Verified timestamps wrap cleanly
- IPv4 column accommodates addresses such as `192.168.xxx.xxx` without wrapping

Discover Now was tested successfully against the live service inventory.

## Known unresolved issues

- No known unresolved Phase 1 DHCP/DNS discovery issues remain.
- No known unresolved Phase 2 NTP/SSH/Web discovery issues remain.
- No known unresolved Infrastructure Services usability issues remain.
- No known unresolved Phase 3 infrastructure-service discovery issues remain.
- `.gitattributes` maintenance remains outside feature commits.

## Next step

Validate Phase 3 service lifecycle transitions across later discovery cycles,
including available-to-unavailable and stale-state handling.

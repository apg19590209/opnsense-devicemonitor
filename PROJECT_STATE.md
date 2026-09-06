# Device Monitor — Project State

## Last updated

7 September 2026

## Current version / branch / environment

Development branch:

`v2.8-development`

Active Windows checkout:

`C:\Users\apg19\Downloads\opnsense-devicemonitor-upstream`

Primary deployment target:

OPNsense 26.7.2_2

Latest confirmed completed identity-work commit:

`5188dcb` — `Fix friendly name and detected hostname separation`


## Current objective

v2.8 version/display consistency, Kea DHCP hostname enrichment and
friendly-name/hostname separation are implemented and live validated.

Device identity presentation now keeps the two concepts separate:

- `hostname` is detected network evidence from Kea/DHCP and other discovery.
- `custom_hostname` is a user-assigned Friendly Name overlay.
- Saving, clearing and subsequent scans do not overwrite the detected hostname.
- Devices shows separate Friendly Name and Hostname columns plus First Seen and Last Seen.
- Infrastructure Services can show a Friendly Name while retaining the detected hostname.

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
- Phase 3 Nmap serialisation and SMB-Nmap serialisation: PASS
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
- isolated Phase 3 active-service lifecycle regression using temporary SQLite: PASS
- Phase 3 Available -> Unavailable transition across all 8 actively verified service methods: PASS
- Phase 3 Unavailable -> Available recovery: PASS
- Phase 3 failed verification preserves the last known-good `last_verified`: PASS
- Phase 3 successful recovery refreshes `last_verified`: PASS
- Infrastructure Services actual UI stale-state JavaScript regression: PASS
- exact two-hour stale boundary: PASS
- older-than-two-hours, missing and invalid `last_verified` values derive Stale: PASS
- explicit Unavailable status takes precedence over derived Stale: PASS
- permanent Phase 3 infrastructure-service Python regression added: PASS
- permanent Infrastructure Services stale-state JavaScript regression added: PASS
- permanent Phase 3 regression validates no automatic fresh Nmap identification: PASS
- permanent Phase 3 regression validates one literal IPv4 per Nmap invocation: PASS
- permanent Phase 3 regression validates serial Nmap and SMB execution: PASS
- permanent Phase 3 regression validates lightweight worker bound of 12: PASS
- permanent Phase 3 regression validates strong Nmap evidence handling: PASS
- permanent Phase 3 regression validates Available -> Unavailable -> Available recovery: PASS

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
- No known unresolved Device Monitor version-display issues remain.

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

## v2.8 metadata, hostname and friendly-name work

Completed and validated:

- version metadata and user-facing v2.8 wording are consistent
- About-page summary and `IP and MAC` wording are current
- Kea DHCP hostname enrichment is implemented and live validated
- five active named Kea leases were confirmed to populate detected hostnames
- Friendly Name is stored separately in `custom_hostname`
- detected Hostname remains in `hostname`
- Friendly Name save, persistence across scan, and clear behaviour were validated live
- clearing a Friendly Name now reports `Friendly name cleared`
- Devices exposes Friendly Name, Hostname, First Seen and Last Seen separately
- CSV export includes Friendly Name, Hostname, First Seen and Last Seen
- Infrastructure Services search/display supports Friendly Name without hiding Hostname
- PHP syntax, Python syntax, gettext catalogues and `git diff --check` passed
- live Device Monitor daemon remained running during deployment
- stale Infrastructure Services were traced to the daemon having been cleanly stopped;
  restarting it restored scheduled discovery, so no stale-state source fix was required

Files changed for hostname/friendly-name task:

- `src/opnsense/mvc/app/controllers/OPNsense/DeviceMonitor/Api/DevicesController.php`
- `src/opnsense/mvc/app/models/OPNsense/DeviceMonitor/DeviceMonitor.php`
- `src/opnsense/mvc/app/views/OPNsense/DeviceMonitor/devices.volt`
- `src/opnsense/mvc/app/views/OPNsense/DeviceMonitor/infrastructureservices.volt`
- `src/opnsense/mvc/app/languages/en_US_devicemonitor.po`
- `src/opnsense/mvc/app/languages/cs_CZ_devicemonitor.po`
- `src/opnsense/scripts/OPNsense/DeviceMonitor/scan_network.py`

Related completed commits already on `origin/v2.8-development`:

- `9f27bcd` — `Add Kea DHCP hostname enrichment to device discovery`
- `7550774` — `Update Device Monitor v2.8 UI wording and about description`
- `f714254` — `Display device friendly names with hostname fallback`

Commit `5188dcb` supersedes the fallback behaviour from `f714254`
by preserving Friendly Name and detected Hostname as separate identity fields.

## UK English standardisation

Repository-wide English-language review completed and validated.

- user-visible English, documentation and project-owned comments use UK English
- technical syntax and externally defined identifiers remain unchanged, including CSS/JS
  `color`/`center`, `grep --color`, the OPNsense `en_US` locale filename and `LICENSE`
- user-facing `License` was changed to `Licence`
- the official legal name `BSD 2-Clause License` remains unchanged
- README and About-page licence metadata were corrected from MIT to BSD 2-Clause License
  to match the repository `LICENSE` file
- repository-wide residual spelling audit found no remaining US-English prose requiring change
- Python syntax validation passed
- PHP syntax validation passed
- English and Czech gettext catalogues compiled successfully; only the existing optional
  gettext header warnings for Last-Translator, Language-Team and Language remain
- `git diff --check` passed

Files changed for this task:

- `.github/workflows/ci.yml`
- `DECISIONS.md`
- `Makefile`
- `PROJECT_STATE.md`
- `README.md`
- `README_CZ.md`
- `src/opnsense/mvc/app/languages/cs_CZ_devicemonitor.po`
- `src/opnsense/mvc/app/languages/en_US_devicemonitor.po`
- `src/opnsense/mvc/app/models/OPNsense/DeviceMonitor/DeviceMonitor.php`
- `src/opnsense/mvc/app/views/OPNsense/DeviceMonitor/devices.volt`
- `src/opnsense/mvc/app/views/OPNsense/DeviceMonitor/settings.volt`
- `src/opnsense/scripts/OPNsense/DeviceMonitor/scan_network.py`

## v2.8 release-readiness review

Release-facing metadata and documentation have been reviewed and corrected.

- `defaults.json` remains authoritative at version `2.8`
- English and Czech gettext metadata remain at Device Monitor 2.8
- English and Czech README version histories now include v2.8
- English and Czech installation instructions now target the `v2.8` tag from
  `apg19590209/opnsense-devicemonitor`
- stale v2.7 installation references and the obsolete upstream direct-download
  reference were removed
- stale `Device Monitor version-display review remains separate` state was resolved
- About heading changed from `v2.8 Development & Enhancements` to
  `v2.8 Features and Enhancements`
- the new About heading was added to both gettext catalogues
- English and Czech gettext catalogues compile successfully; only the existing
  optional gettext header warnings remain
- live About page was deployed without a service restart and visually validated
- live About page displays `v2.8 Features and Enhancements`, `Licence`, and
  `BSD 2-Clause License`
- repository release-reference residual audit found no remaining stale v2.7
  installation or obsolete development-heading references
- release-readiness changes committed as `e308f9f`
- GitHub Actions Device Monitor CI #51 for `e308f9f`: PASS
- final release candidate commit `abe1ccb` passed GitHub Actions Device Monitor CI #52
- annotated `v2.8` release tag created at `abe1ccb7306a4a35e60221d41212beff22aa52d9` and pushed to `origin`
- GitHub release `Device Monitor v2.8` published from the validated `v2.8` tag
- public `refs/tags/v2.8.zip` archive verified successfully

## Known unresolved issues

- No known unresolved Phase 1 DHCP/DNS discovery issues remain.
- No known unresolved Phase 2 NTP/SSH/Web discovery issues remain.
- No known unresolved Infrastructure Services usability issues remain.
- No known unresolved Phase 3 infrastructure-service discovery issues remain.
- No known unresolved Friendly Name / detected Hostname separation issue remains.

## Next step

Perform post-release v2.8 installation and upgrade smoke validation.

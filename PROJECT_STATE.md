# Device Monitor — Project State

## Last updated

5 September 2026

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

v2.8 IP & MAC identity-conflict email alerts are complete and validated.

Implementation, live deployment, real-email validation, repository commit, remote push and GitHub CI validation have all passed.
## Previously completed

- v2.8 Identity Events supports All/Unresolved/Resolved filtering through the Status selector and clickable Unresolved/Resolved summary links.

- v2.8 Identity Events heading shows separate Unresolved and Resolved counts; filtering remains through the Status selector.

- v2.8 Identity Events heading now shows separate Unresolved and Resolved counts.

- v2.8 Identity Events table now shows an explicit Unresolved/Resolved status badge.

- v2.8 Identity Events resolution filter implemented for All, Unresolved and Resolved events.

- v2.8 Identity Events Resolve/Reopen API and UI implemented; event history is preserved through the existing `resolved_at` field.

- v2.7 release preparation completed: version metadata, English/Czech version history, installation references and automated identity regression coverage are current.

- Added automated v2.7 identity regression coverage using isolated temporary SQLite databases.

- v2.7 README/version-history documentation updated for identity anomaly detection and Identity Events.

- Phase F.2 IPv6 identity-conflict detection completed and validated.
- Device Monitor Identity Events API/runtime completed and validated.
- Identity Events UI deployed and validated on OPNsense.
- Identity Events UI committed as `418ea5c`.
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
- populated Identity Events row rendering using browser-only synthetic API data: PASS
- Identity Events expandable details rendering: PASS
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

## Next step

Proceed to Phase 2 infrastructure discovery: NTP, SSH and Web/Admin services.

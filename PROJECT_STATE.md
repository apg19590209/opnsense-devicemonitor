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

## Known unresolved issues

- No known unresolved v2.8 identity-conflict email alert issues remain.
- Separate unstaged IP & MAC Conflicts UI terminology changes and `.gitattributes` maintenance remain outside commit `c92b61b`.
## Current operating values

Previously established:

- monitored interface: IGC1
- scan interval: 300 seconds

Current numeric security-scan queue rate limit should be confirmed from current source/configuration before being recorded here.

## Next step

Review and validate the remaining unstaged IP & MAC Conflicts UI terminology changes before committing them.

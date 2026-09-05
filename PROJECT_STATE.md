# Device Monitor — Project State

## Last updated

5 September 2026

## Current version / branch / environment

Development branch:

`v2.7-development`

Active Windows checkout:

`C:\Users\apg19\Downloads\opnsense-devicemonitor-upstream`

Primary deployment target:

OPNsense 26.7.2_2

Latest confirmed completed identity-work commit:

`418ea5c` — `feat: add identity events UI`

## Current objective

Close out the completed and pushed Device Monitor Settings UI work.

Current local work is in:

`src/opnsense/mvc/app/views/OPNsense/DeviceMonitor/settings.volt`

The Settings-page changes are committed and pushed to `origin/v2.7-development`, and have been deployed and visually validated on OPNsense.

## Previously completed

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

For the current Settings-page work:

- `git diff --check`: PASS
- Licensing & Compatibility source inspection: PASS
- deployment to OPNsense: PASS
- live browser validation of all Settings tabs after deployment: PASS
- GitHub push to `origin/v2.7-development`: PASS

## Known unresolved issues

- Populated Identity Events row/details rendering has not yet been observed because the event table is currently empty.

## Current operating values

Previously established:

- monitored interface: IGC1
- scan interval: 300 seconds

Current numeric security-scan queue rate limit should be confirmed from current source/configuration before being recorded here.

## Next step

Push the project-state closeout commit to `origin/v2.7-development`.

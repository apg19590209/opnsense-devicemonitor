# Device Monitor — Project State

## Last updated

September 2026

## Current version / branch / environment

Development branch:

`v2.7-development`

Primary deployment target:

OPNsense 26.7.2_2

Latest confirmed completed identity-work commit:

`418ea5c` — `feat: add identity events UI`

## Current phase or objective

Phase G — expose Device Monitor identity anomaly events through the OPNsense API/UI.

Current subtask:

Validate the deployed identity-detection runtime through one normal Device Monitor scan.

## Work completed

- Phase F.2 IPv6 identity-conflict detection completed and validated.
- Existing Device Monitor API/UI pattern inspected.
- Local `identityeventsAction()` added to `DevicesController.php`.
- Project-control information split into purpose-specific Markdown files.
- Live `identityeventsAction()` API endpoint validated successfully.
- Identity-event runtime/schema deployed to OPNsense and `device_identity_events` created successfully.
- Identity Events UI deployed and validated on OPNsense.
- Identity Events UI committed as `418ea5c`.

## Files changed

Current/recent files relevant to this checkpoint:

- `src/opnsense/mvc/app/controllers/OPNsense/DeviceMonitor/Api/DevicesController.php`
- `src/opnsense/mvc/app/controllers/OPNsense/DeviceMonitor/IndexController.php`
- `src/opnsense/mvc/app/models/OPNsense/DeviceMonitor/Menu/Menu.xml`
- `src/opnsense/mvc/app/views/OPNsense/DeviceMonitor/identityevents.volt`
- `PROJECT_STATE.md`

## Validation performed

Identity Events API/runtime:

- `DevicesController.php` PHP syntax validation
- live `/api/devicemonitor/devices/identityevents` request
- development and installed `scan_network.py` Python syntax validation
- `init_db()` execution
- live `device_identity_events` schema inspection

Identity Events UI:

- `Menu.xml` XML validation
- `IndexController.php` PHP syntax validation on OPNsense
- `git diff --check`
- live `/ui/devicemonitor/index/identityevents` browser validation

## Validation results

- Identity Events API endpoint: PASS
- API empty-state response (`rows: []`, `total: 0`): PASS
- identity-event database schema creation: PASS
- Python runtime syntax validation: PASS
- `Menu.xml` validation: PASS
- `IndexController.php` syntax validation: PASS
- Identity Events live page rendering: PASS
- `git diff --check`: PASS
- normal full Device Monitor scan with deployed identity detection: NOT YET PERFORMED

## Current operating values

Values previously established for the current environment:

- monitored interface: IGC1
- scan interval: 300 seconds

Current numeric security-scan queue rate limit should be confirmed from current source/configuration before being recorded here.

## Known unresolved issues

- Deployed identity-detection runtime has not yet been exercised by a normal full Device Monitor scan.
- Populated Identity Events row/details rendering has not yet been observed because the event table is currently empty.

## Next step

Run one normal Device Monitor scan on OPNsense and inspect the result for identity-detection errors and newly recorded identity events.

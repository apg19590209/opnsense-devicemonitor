# Device Monitor — Project State

## Last updated

September 2026

## Current version / branch / environment

Development branch:

`v2.7-development`

Primary deployment target:

OPNsense 26.7.2_2

Latest confirmed completed identity-work commit:

`548bb3b` — `feat: detect non-link-local IPv6 identity conflicts`

## Current phase or objective

Phase G — expose Device Monitor identity anomaly events through the OPNsense API/UI.

Current subtask:

Begin Identity Events UI/menu implementation using the validated read-only API endpoint.

## Work completed

- Phase F.2 IPv6 identity-conflict detection completed and validated.
- Existing Device Monitor API/UI pattern inspected.
- Local `identityeventsAction()` added to `DevicesController.php`.
- Project-control information split into purpose-specific Markdown files.
- Live `identityeventsAction()` API endpoint validated successfully.
- Identity-event runtime/schema deployed to OPNsense and `device_identity_events` created successfully.

## Files changed

Current/recent working-tree files relevant to this checkpoint:

- `src/opnsense/mvc/app/controllers/OPNsense/DeviceMonitor/Api/DevicesController.php`
- `PROJECT_RULES.md`
- `PROJECT_STATE.md`
- `DECISIONS.md`
- `SYSTEM_MAP.md`

## Validation performed

Phase F.2:

- Python syntax compile
- synthetic IPv6 identity tests
- live read-only Hostwatch validation

Current Phase G API work:

- local diff inspection
- `git diff --check`

## Validation results

Phase F.2 validation passed.

Current Phase G API endpoint:

- local diff inspection: PASS
- `git diff --check`: PASS
- PHP syntax validation: PASS
- runtime/API behaviour validation: PASS

## Current operating values

Values previously established for the current environment:

- monitored interface: IGC1
- scan interval: 300 seconds

Current numeric security-scan queue rate limit should be confirmed from current source/configuration before being recorded here.

## Known unresolved issues

- Identity Events UI/menu work has not started.

## Next step

Inspect the existing Device Monitor UI/menu pattern and identify the smallest safe change required to add an Identity Events view.

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

Validate the newly added read-only `identityeventsAction()` API endpoint before any UI work proceeds.

## Work completed

- Phase F.2 IPv6 identity-conflict detection completed and validated.
- Existing Device Monitor API/UI pattern inspected.
- Local `identityeventsAction()` added to `DevicesController.php`.
- Project-control information split into purpose-specific Markdown files.

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
- PHP syntax validation: NOT YET PERFORMED
- runtime/API behaviour validation: NOT YET PERFORMED

## Current operating values

Values previously established for the current environment:

- monitored interface: IGC1
- scan interval: 300 seconds

Current numeric security-scan queue rate limit should be confirmed from current source/configuration before being recorded here.

## Known unresolved issues

- `identityeventsAction()` has not yet passed PHP syntax validation.
- The new endpoint has not yet been exercised through the actual OPNsense API.
- Identity Events UI/menu work has not started.

## Next step

Copy the modified `DevicesController.php` to `/tmp` on OPNsense and run `php -l` against that temporary copy.

Do not replace the live controller yet.
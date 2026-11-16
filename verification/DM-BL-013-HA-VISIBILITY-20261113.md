# DM-BL-013 HA role visibility — source validation

**Date:** 13 November 2026
**Host:** `.23`, `OPNsense.internal`, FreeBSD 15.1-RELEASE-p6
**Scope:** Devices and Settings HA-role visibility, source only. No install, uninstall, service
action, reboot, monitoring activation, settings write, failover, production access, commit, push or
publication occurred.

## Existing status source

The visibility code does not introduce a second CARP detector. Both pages call the pre-existing
read-only `ConfigController::getcarpstatusAction()` endpoint (`/api/devicemonitor/config/getcarpstatus`).
That endpoint already parsed `/sbin/ifconfig -a` and `/conf/config.xml` for Settings → HA / CARP.

Source trace:

* `ConfigController.php` parses the monitored interfaces and applies the same MASTER-over-BACKUP
  precedence as `detect_carp_role()` in `scan_network.py`.
* `ha_carp_enabled` and `ha_role_override` are applied exactly as the daemon applies them:
  detected `role` remains the observed CARP state, while `mode` records automatic or overridden
  effective mode; awareness-off retains the detected role but pauses nothing.
* `role_available` requires both readable `ifconfig` output and readable `/conf/config.xml`, so a
  detector/config failure cannot become a false non-HA result.
* `role_mixed`, `carp_aware`, `ha_status`, `node`, `paused_activities` and `last_scan` extend the
  existing response. `node` is the local hostname; `last_scan` is the latest existing
  `[YYYY-MM-DD HH:MM:SS] Scan completed successfully` line emitted by `monitor_daemon.py`.
  Neither is synthesised. The reader searches the log backwards in bounded chunks so a valid
  record beyond a fixed tail window is still found.

## BACKUP activity evidence

The paused list is derived from the same `service_observation_allowed()` verdict used by the
daemon, not from the UI's interpretation of a role string.

| Displayed paused activity | Daemon source evidence |
|---|---|
| Visibility priming | `prime_selected_interface_visibility()` calls the gate and returns before probing (`scan_network.py:9045-9068`). |
| Service discovery | `run_scheduled_service_discovery()` is called only inside `if allowed` (`scan_network.py:9554-9555`). |
| Service alerts | `process_service_alerts()` is in the same allowed branch; the standby branch records only node-local ageing (`scan_network.py:9557-9567`). |
| Identity conflict alerts | Both identity delivery legs are guarded by `allowed` (`scan_network.py:9509-9519`). |
| New device alerts | Announcement and queueing are guarded; BACKUP logs `not announced` instead (`scan_network.py:9574-9600`). |
| Automatic targeted Nmap scans | The queued-scan drain requires `allowed` (`scan_network.py:9613-9619`). Manual targeted scans are a separate command path and are not CARP-gated. |

Continuation wording is also source-backed: the normal inventory/identity path continues,
`age_stale_service_state_on_standby()` runs on the standby branch, and
`monitor_daemon.py:210-211` invokes the opt-in scheduled port-discovery command independently of
the service-observation gate.

## State model and refresh behaviour

The API/UI state matrix is covered by 12 PHP response cases and 16 JavaScript state cases:
MASTER, BACKUP, non-HA, unavailable detector, unreadable configuration, mixed MASTER/BACKUP,
master override, backup override, awareness off, override plus detector failure, override plus
awareness off, legacy response fallback, structured found/no-scan/unreadable history, and Devices/
Settings consistency, refresh-failure and no-Apply transitions.

Both views use the same renderer inputs and request path. The notice loads at page start and every
30 seconds without Apply. Settings' existing HA / CARP tab now uses the same loader; its previous
duplicate `loadHaStatus()` reference was removed. That obsolete identifier was a real regression in
the first draft and would have aborted the ready handler.

On a failed refresh, both role, effective mode and the HA/CARP VIP table are replaced with explicit
unknown/unavailable values. A monotonically increasing request token also prevents a slower,
superseded success from restoring an old MASTER state after a newer failure. Settings initialises
that token before its first request, avoiding the JavaScript hoisting trap where `++undefined`
would make every response appear superseded.

## Historical previews (superseded by R3)

The deterministic previews below were recorded for the earlier 1,784,478-byte `709288cd…`
candidate. They are retained as history and no longer describe the current fail-open or API
fetch-failure wording. The current R3 previews appear under “Review correction R3”. Neither set is
a browser screenshot.

```text
PREVIEW_MASTER={"status":"master","tone":"info","role":"MASTER","mode":"MASTER","node":"dm-node.test","ownership":"Displayed data belongs to this node only and is not merged from the CARP peer.","paused":[],"pausedHeading":"Paused on this BACKUP node","pausedNote":"A paused activity is not an empty result.","continuation":"Local inventory and identity recording, node-local ageing, and scheduled port discovery continue.","message":"No Device Monitor activities are paused by HA gating.","lastScan":"Last successful local scan: 13-11-2026 08:25:16"}
PREVIEW_BACKUP={"status":"backup","tone":"warning","role":"BACKUP","mode":"BACKUP","node":"dm-node.test","ownership":"Displayed data belongs to this node only and is not merged from the CARP peer.","paused":["Visibility priming","Service discovery","Service alerts","Identity conflict alerts","New device alerts","Automatic targeted Nmap scans"],"pausedHeading":"Paused on this BACKUP node","pausedNote":"A paused activity is not an empty result.","continuation":"Local inventory and identity recording, node-local ageing, and scheduled port discovery continue.","message":"","lastScan":"Last successful local scan: 13-11-2026 08:25:16"}
PREVIEW_UNAVAILABLE={"status":"unavailable","tone":"danger","role":"Unavailable","mode":"Unavailable","node":"dm-node.test","ownership":"Displayed data belongs to this node only and is not merged from the CARP peer.","paused":[],"pausedHeading":"Paused on this BACKUP node","pausedNote":"A paused activity is not an empty result.","continuation":"Local inventory and identity recording, node-local ageing, and scheduled port discovery continue.","message":"HA role status is unavailable. Confirm CARP and the effective mode before relying on this view. Fail-open observation gating is active.","lastScan":"Last successful local scan: 13-11-2026 08:25:16"}
PREVIEW_REFRESH_FAILURE={"status":"unavailable","tone":"danger","role":"Unavailable","mode":"Unavailable","node":"unknown","ownership":"Displayed data belongs to this node only and is not merged from the CARP peer.","paused":[],"pausedHeading":"Paused on this BACKUP node","pausedNote":"A paused activity is not an empty result.","continuation":"Local inventory and identity recording, node-local ageing, and scheduled port discovery continue.","message":"HA role status is unavailable. Confirm CARP and the effective mode before relying on this view. Fail-open observation gating is active.","lastScan":"No successful local scan recorded."}
```

This historical block is retained verbatim as the earlier review record.

## Validation

* `php tests/test_ha_role_visibility.php` — `HA_ROLE_VISIBILITY=PASS cases=12`
* `node tests/test_ha_role_visibility.js` — `HA_ROLE_VISIBILITY_JS=PASS cases=16`, including
  failure clearing and superseded-response rejection
* `python3 tests/test_carp_role_gate.py` — `CARP_ROLE_GATE=PASS`
* `python3 tests/test_non_ha_operation.py` — `NON_HA_OPERATION=PASS`
* `python3 tests/test_integration_reconciliation.py` — `INTEGRATION_RECONCILIATION=PASS cases=6`
* all 11 `tests/test_*.js` UI suites (including HA visibility) — PASS
* all 13 source PHP files — syntax PASS
* `python3 tests/test_translated_javascript.py` — `TRANSLATED_JAVASCRIPT=PASS`
* `python3 tests/test_ci_config.py` — `CI_CONFIG=PASS cases=10`
* `python3 tests/test_catalogue_determinism.py` — `CATALOGUE_DETERMINISM=PASS cases=2`
* `python3 tests/test_release_manifest.py` — `V2140_RELEASE_MANIFEST=PASS`
* `python3 tests/test_release_inputs.py` — `RELEASE_INPUTS=PASS cases=7`
* bundle safety, reproducibility and determinism — `PASS` (8, 9 and 4 cases)
* source-catalogue language acceptance with source views and staged source catalogues —
  `LANGUAGE_ACCEPTANCE=PASS languages=9 gaps=1 engine=interpolate failures=0`; the gap is the
  known `nl_NL` selector omission. Running against the older installed views/catalogues is not
  an acceptance run for this checkout and reports expected drift.
* `git diff --check` — PASS

The host's installed plugin catalogues/views are older than this checkout, so a runtime
Phalcon/Volt language pass would test obsolete files. The source-catalogue run above is the
appropriate non-deploying check for this task. No browser rendering or live role transition was
exercised.

## Candidate and preservation

The affected manifest rows, release inputs and installer pins were regenerated. Two independent
stage builds produced byte-identical candidates:

* 1,784,478 bytes
* SHA-256 `709288cd4984c640c7d33a623db6f71a7f7fde6119153ba7ed4f3833e5a078a9`
* 60 archive members

Durable evidence:
`/root/dm-validation-2140/dm-bl-013-ha-role-visibility-20261112T221335Z/`.
The prior HA candidate `2dab13858648651d82c56ab73bcdb08ed60710022bdcabc47524ff4af4fac4e8`
and all earlier candidates remain untouched. The latest candidate has not been installed and
DM-BL-013 remains OPEN for MASTER-only, live CARP-transition and delivery-path coverage. Historical
monitoring-activation attribution remains UNKNOWN.

### Candidate provenance

`2dab1385…` is the first HA-visibility candidate (1,783,454 bytes). It was superseded by the
1,784,478-byte `709288cd…` build. Sixteen archive members changed between them: the Devices and
Settings views, all eleven language catalogues, `install-unattended.sh`, the runtime manifest and
the release-inputs file. The source changes corrected the Settings HA-tab handler from the removed
`loadHaStatus()` to `loadHaNodeVisibility()`, added request-generation guards so superseded
responses cannot restore stale status, and narrowed the paused label from “Targeted Nmap scans” to
“Automatic targeted Nmap scans”; the catalogue and pin changes follow from those source edits.
Member-level provenance is retained under
`/root/dm-validation-2140/dm-bl-013-ha-messaging-r3-20261112T225433Z/provenance/`.

## Review correction R3 (13 November 2026)

The earlier sections and the 1,784,478-byte `709288cd…` build are retained as history. Two
pre-commit review findings changed the source:

* `lastSuccessfulLocalScan()` matched `DD-MM-YYYY … - Scan completed successfully`, but the
  daemon actually emits `[YYYY-MM-DD HH:MM:SS] Scan completed successfully`. The old regression
  fixture copied the wrong format, so the notice would always report no history. The parser now
  matches the emitted format and searches backwards in bounded chunks, with a regression proving a
  success older than the previous 256 KiB tail is found.
* The fail-open flag is now set only when the CARP detector is unavailable while
  `/conf/config.xml` is readable. An unreadable configuration produces an unavailable notice
  without claiming that observation continues.

The Devices notice distinguishes readable history with no success (`last_scan_state=none`) from an
unreadable history (`unavailable`) and from a failed API request (`scan_fetch_failed`). The API
fetch-failure state never infers CARP gating or observation policy. The backend detector-failure
state reports observation continuation only from the backend response field.

Current R3 deterministic previews (not browser screenshots):

```text
PREVIEW_MASTER={"status":"master","tone":"info","role":"MASTER","mode":"MASTER","node":"dm-node.test","ownership":"Displayed data belongs to this node only and is not merged from the CARP peer.","paused":[],"pausedHeading":"Paused on this BACKUP node","pausedNote":"A paused activity is not an empty result.","continuation":"Local inventory and identity recording, node-local ageing, and scheduled port discovery continue.","message":"No Device Monitor activities are paused by HA gating.","lastScan":"Last successful local scan: 2026-11-13 08:25:16"}
PREVIEW_BACKUP={"status":"backup","tone":"warning","role":"BACKUP","mode":"BACKUP","node":"dm-node.test","ownership":"Displayed data belongs to this node only and is not merged from the CARP peer.","paused":["Visibility priming","Service discovery","Service alerts","Identity conflict alerts","New device alerts","Automatic targeted Nmap scans"],"pausedHeading":"Paused on this BACKUP node","pausedNote":"A paused activity is not an empty result.","continuation":"Local inventory and identity recording, node-local ageing, and scheduled port discovery continue.","message":"","lastScan":"Last successful local scan: 2026-11-13 08:25:16"}
PREVIEW_UNAVAILABLE={"status":"unavailable","tone":"danger","role":"Unavailable","mode":"Unavailable","node":"dm-node.test","ownership":"Displayed data belongs to this node only and is not merged from the CARP peer.","paused":[],"pausedHeading":"Paused on this BACKUP node","pausedNote":"A paused activity is not an empty result.","continuation":"Local inventory and identity recording, node-local ageing, and scheduled port discovery continue.","message":"HA role status is unavailable. Confirm CARP and the effective mode before relying on this view. Device Monitor reports that observation continues while the CARP role is unknown.","lastScan":"Last successful local scan: 2026-11-13 08:25:16"}
PREVIEW_REFRESH_FAILURE={"status":"fetch_failed","tone":"danger","role":"Unavailable","mode":"Unavailable","node":"unknown","ownership":"Displayed data belongs to this node only and is not merged from the CARP peer.","paused":[],"pausedHeading":"Paused on this BACKUP node","pausedNote":"A paused activity is not an empty result.","continuation":"Local inventory and identity recording, node-local ageing, and scheduled port discovery continue.","message":"HA status could not be retrieved, so the current CARP gating state is unknown.","lastScan":"Scan history was not retrieved because the HA status request failed."}
```

The fetch-failure preview contains no fail-open claim: a failed request cannot establish backend
observation policy. The backend-unavailable preview states it only because the backend explicitly
returned `role_unknown_observation_continues=true`.

Browser rendering could not be performed against the isolated fixture: the `.23` host has no
Chromium, Firefox, WebKit, headless screenshot tool, Playwright or Selenium.
FreeBSD Chromium's dry-run requires 144 packages and about 3 GiB while about 1.1 GiB was free, so
no package was installed. The self-contained simulated fixture is at
`/root/dm-validation-2140/dm-bl-013-ha-messaging-r3-20261112T225433Z/isolated-browser-fixtures/notice-fixture.html`;
it is explicitly labelled simulated and supports Devices/Settings, MASTER/BACKUP/backend-unavailable/
fetch-failure, English/German and refresh transitions. Its English/German strings mirror the
checked-in catalogues, but remain fixture input rather than a rendered result. **No browser
screenshots were captured by the agent, and no layout, narrow-screen, translation-rendering or
browser-transition claim is made from the agent's own run.** An operator-supplied review of the
isolated fixture was subsequently received (see "Operator browser review" below); it remains
fixture-only evidence.

The fixture's two dictionaries, four states and two view selectors passed
`FIXTURE_STATIC_CHECK=PASS languages=2 states=4 views=2`; this validates fixture completeness only,
not rendering.

The final candidate was rebuilt twice with byte-identical results:

* 1,795,230 bytes
* SHA-256 `e7dcb7f88ec8f98ca4455542f2106416e2447740c95c818ff2cfdd31d4ef3124`
* 60 archive members
* durable evidence: `/root/dm-validation-2140/dm-bl-013-ha-messaging-r3-20261112T225433Z/`

The intervening HA candidates remain preserved: `2dab1385…` (1,783,454 bytes), `709288cd…`
(1,784,478 bytes), `e789fb96…` (1,794,206 bytes) and `f51f1adf…` (1,794,206 bytes). The final
candidate was installed on testbed `.23` on 13 November 2026; it has not been installed on
production. DM-BL-013 remains OPEN; historical monitoring-activation attribution remains UNKNOWN.

## Operator browser review of the isolated fixture (13 November 2026)

An operator reviewed the isolated simulated fixture (`notice-fixture.html`) in a browser and
supplied the following observations. The agent did not observe the browser session and no
screenshots are retained in the repository; these are operator attestations.

* MASTER and BACKUP notices render clearly.
* Fetch-failure and backend-unavailable states display distinct messages.
* German Settings and English Devices wrap correctly at narrow widths.
* The simulated MASTER-to-BACKUP transition ends in the correct BACKUP view.

These are isolated-fixture checks only. They do not establish live CARP behaviour, a live role
transition, production rendering or full-matrix acceptance, and no live browser check or CARP
change was performed. DM-BL-013 remains OPEN for the live MASTER-only, HA-transition and
delivery-path coverage.

## `.23` testbed deployment (13 November 2026)

The exact candidate was staged and preflighted on `.23`:

```text
VERIFY_OK=4
CHECK_OK version=2.14.0 predecessor=2.14.0 files=63 core_locales=10 prunable=0 daemon_running=1 host=OPNsense.internal legacy_prunable=0 retained=0
```

The preflight left every live payload hash, `config.json`, `devices.db`, `/conf/config.xml` and the
installer-backup directory unchanged and created no staging directory. The authorised install then
returned:

```text
BACKUP_READY=/var/backups/devicemonitor/install-v214.lulG0h
INSTALL_OK version=2.14.0 files=63 core_locales=10 pruned=0 backup=/var/backups/devicemonitor/install-v214.lulG0h daemon_restarted=1 unchanged=36 repaired=0
```

Post-install checks: 63/63 installed record rows matched; the 42-row release manifest matched with
zero mismatches; SQLite `integrity_check`/`quick_check` = `ok` with 21 tables and 26 device rows;
`config.json` (`027594eb…`), `devices.db` (`796d28c7…`) and `/conf/config.xml` (`e86a7058…`) were
byte-identical to the pre-install state; `/etc/rc.conf.d/devicemonitor` remained present; monitoring
remained `enabled=0`; no WAL/SHM, scan, notification or Nmap process appeared; configd and the
daemon were running; and the kernel boot time was unchanged, so no reboot occurred. The installer's
own backup (`plan` = 63 rows, 19 core-locale files) verified with zero mismatches and contains the
pre-install configuration and consistent database copy.

Operator inspection URLs:

* Devices: `https://192.168.20.23/ui/devicemonitor/index/devices`
* Settings: `https://192.168.20.23/ui/devicemonitor/index/settings`

This is lifecycle testing on the existing development host, not a pristine OPNsense installation.
No live CARP transition or MASTER-only/delivery path was exercised. Durable evidence:
`/root/dm-validation-2140/dm-bl-013-ha-deploy-23-20261112T234608Z/`.

## Compact summary revision (13 November 2026)

The Devices and Settings notice is now collapsed by default. A native `type="button"` toggle with
`aria-expanded`/`aria-controls` switches between Show details and Hide details; the 30-second
refresh updates the visible facts, summary and warning without changing the user's expansion state.
The summary keeps node identity, detected role, effective mode and the actual monitoring-enabled
state visible, reports HA-paused activity counts separately from monitoring being disabled, and
surfaces detected/effective role differences plus unavailable or fetch-failure warnings. The
expanded area retains the ownership statement, full explanation, paused list, continuation,
monitoring-disabled explanation and last successful scan.

`getcarpstatus` now also returns the read-only `monitoring_enabled` value from the existing
configuration. New labels are translated in all eleven catalogues; static coverage checks every
message id used by the two views. Focused API/UI tests pass, including disabled and enabled
monitoring, role differences, unavailable/fetch-failure warnings, native-button keyboard access,
both expansion states, immediate refresh updates and expansion preservation. The language-
acceptance harness was deferred because the current price-gate window was premium; no bypass was
used.

This revision is source-only: it is not built into the installed `e7dcb7f8…3124` candidate. No
install, production change, commit, push or publication occurred.

## Automatic HA relevance detection (13 November 2026)

The compact notice now uses a positive non-HA predicate rather than treating every `role=none`
result as standalone. `getcarpstatus` reports `non_ha_confirmed=true` only when all of the following
are true: `/sbin/ifconfig -a` exits zero and returns readable output; `/conf/config.xml` is readable;
at least one configured monitored interface resolves to a device; no CARP VIP is configured; no
monitored device reports a CARP MASTER or BACKUP state; and `ha_role_override` is `auto`. An explicit
override, unreadable detector input, unreadable configuration, an unresolved monitored interface,
configured CARP VIPs or any CARP state all retain HA relevance.

When that predicate is positive, Devices and Settings hide the HA-specific detected/effective role
facts, HA summary, ownership statement, warning and paused-activity explanation. The persistent
notice title, node identity and monitoring enabled/disabled state remain visible. The expanded area
continues to show the independent monitoring-disabled explanation when applicable and the latest
successful local scan from the existing daemon log. A missing scan history, unreadable history and
failed API retrieval remain distinct. The native Show details / Hide details toggle remains available
and its expansion state is not reset by the 30-second refresh.

The Settings → HA / CARP tab remains accessible. On confirmed non-HA with no explicit override, the
tab shows `No CARP configuration detected` and disables `ha_carp_enabled` and
`ha_notify_failover` without rewriting their saved values. The role override remains visible and
editable, and choosing an explicit value re-enables the CARP-dependent controls while retaining a
clear override warning. Detector/API failure, unreadable input and any explicit override are never
presented as non-HA: the controls remain available, HA content remains visible in warning form, and
the failure is labelled unknown. CARP awareness disabled remains distinct from the detected CARP
role and effective mode; a detected BACKUP with awareness disabled reports no paused activities and
explains that effective observation continues.

The isolated fixture supports `view=devices|settings`, `lang=en_US|de_DE`, `expanded=1`,
`state=master|backup|non_ha|non_ha_monitoring_disabled|awareness_off|override|backend_unavailable|fetch_failed`
and transitions to BACKUP, non-HA and fetch failure. It contains no credentials, production data,
live API calls or external URLs. It was checked from a clean extraction with `sha256sum -c
SHA256SUMS` and `FIXTURE_STATIC_CHECK=PASS languages=2 states=8 views=2`. Updated package:

* `/root/dm-validation-2140/dm-bl-013-ha-relevance-fixture-20261113T004225Z/devicemonitor-ha-relevance-fixture-20261113.tar.gz`
* 373,094 bytes, 18 archive members
* SHA-256 `687cc9f22d6bb2a9c3c5a47d1e13563471516cf2892922e8520b06ea08a8fbe5`

Focused validation passed: `php -l`; PHP API cases `17`; JavaScript state/behaviour cases `23`,
including keyboard access, both expansion states, refresh preservation, non-HA control gating,
override editability and detector/API failure; `NON_HA_OPERATION`; integration reconciliation `6`
cases; translated JavaScript for all catalogues plus edge cases; CI configuration `10` cases;
catalogue determinism; locale merge; `msgfmt --check` for all eleven catalogues; fixture static
check; and `git diff --check`. Durable log:
`/root/dm-validation-2140/dm-bl-013-ha-relevance-fixture-20261113T004225Z/validation-automatic-relevance-20261113T005000Z.log`
(SHA-256 `7c415ee4a20a5c62ca7a216a8aabb307c827476495b5471ccced0eba8ef177cd`).

`tests/test_language_acceptance.py` remains deferred because the documented price gate was in a
premium window at 11:46–11:48 AEDT; no bypass was used. Browser visual acceptance of this updated
fixture remains pending because `.23` has no browser/screenshot toolchain and the operator has not
yet reviewed this revision. No live CARP transition was performed. This revision is source-only and
is not installed on `.23` or production; the installed `.23` payload remains the earlier
`e7dcb7f8…3124` candidate. DM-BL-013 remains **OPEN**, and historical monitoring-activation
attribution remains **UNKNOWN** rather than a confirmed automatic-activation defect.

## Compact one-line and timezone revision (13 November 2026)

Operator browser review confirmed that the toggle expanded correctly, but the collapsed notice still
repeated content and occupied three lines. The two views now share a single compact summary line:

```text
dm-node.test · MASTER · Monitoring enabled
dm-node.test · BACKUP · Monitoring enabled · Some activities paused
dm-node.test · Monitoring disabled
```

Confirmed non-HA omits the HA role altogether. BACKUP adds only the short `Some activities paused`
indicator. Monitoring is stated once in the compact line and is no longer repeated in the expanded
area. Unavailable status, detector-fetch failure, awareness-off and active role-override warnings
remain outside the hidden details region and therefore visible while collapsed.

Expanded details now contain the detected role and effective mode once, the node-local ownership
explanation, a `Paused activities` list only when activities are actually paused, a `Continuing
activities` explanation only when the backend establishes a continuation state, and the last
successful local scan. The former repeated monitoring note, generic `No activities paused` message
and duplicated detected/effective role text in the warning were removed. The native button,
`aria-expanded`/`aria-controls`, refresh updates and expansion preservation are unchanged. Flex
wrapping and `overflow-wrap` retain natural narrow-screen behavior.

`getcarpstatus` now returns `last_scan_timezone` only when `/conf/config.xml` contains a valid
`<system><timezone>` value. The UI renders the scan as, for example,
`Last successful local scan: 2026-11-13 08:25:16 (Australia/Sydney)`. A missing or invalid configured
zone returns no label and the view says `Timezone unavailable`; it never assumes UTC or hard-codes an
abbreviation. This was verified against the installed `.23` configuration (`Australia/Sydney`) and
with an invalid-zone unit case.

Focused validation passed: `php -l`; PHP API cases `18`; JavaScript state/behaviour cases `23`;
non-HA operation; integration reconciliation; translated JavaScript; CI configuration; catalogue
determinism; locale merge; sidecar catalogue; `msgfmt --check` for all eleven catalogues; fixture
static check; inline-script syntax; and `git diff --check`. Durable log:
`/root/dm-validation-2140/dm-bl-013-ha-compact-line-20261113T010100Z/validation-compact-line-20261113T010500Z.log`
(SHA-256 `103f41ec1f1a69f74ec0a5ce1e360ba660f11ee88474964c83df6ce07169e7f8`).

The updated self-contained fixture is at
`/root/dm-validation-2140/dm-bl-013-ha-compact-line-20261113T010100Z/devicemonitor-ha-compact-line-fixture-20261113.tar.gz`:
373,818 bytes, 18 members, SHA-256
`7376a65a3a0640496926461fdbb76272421c9839ed9e6d630e0aac77d91acbab`. The reseal followed the
addition of inline JavaScript syntax validation to `fixture-static-check.js`; only that checker and
its recorded log changed (`notice-fixture.html` remains `9dfa112d…a18fa`). It verifies from a clean
extraction with `sha256sum -c SHA256SUMS`, `INLINE_JS_SYNTAX=PASS scripts=1`,
`FIXTURE_STATIC_CHECK=PASS languages=2 states=8 views=2`, archive path checks, no symlinks, and no
live network calls, credentials, production data or production addresses. Verification log:
`/root/dm-validation-2140/dm-bl-013-ha-compact-line-20261113T010100Z/fixture-reseal-verification-20261113T010823Z.log`.
The previous `c34d3414…1c88` and earlier `687cc9f2…fbe5` archives remain preserved.

`tests/test_language_acceptance.py` remains deferred because the documented price gate was in a
premium window at 11:56–12:06 AEDT; no bypass was used. Browser visual acceptance of this revised
fixture remains pending because `.23` has no browser/screenshot toolchain. This revision is
source-only: it is not installed on `.23` or production. The installed `.23` payload remains the
earlier `e7dcb7f8…3124` candidate. DM-BL-013 remains **OPEN**, and historical monitoring-activation
attribution remains **UNKNOWN**.

## Review correction R5 — browser findings

An operator browser review of the R4 fixture reported three issues. They are fixture/source findings
unless explicitly described as live; the agent did not perform a live browser or CARP test.

* Confirmed non-HA expanded details still exposed the role facts and CARP-peer wording. The role
  facts were visible because the fixture's `.dm-ha-node-role-facts { display:flex; }` author rule
  overrode the `hidden` attribute; the fixture now has an explicit `[hidden]` rule. Both views also
  retain the same defensive rule. The ownership sentence now uses the existing `Node-local Device
  Monitor data` wording when `non_ha_confirmed` is true and no override applies; the CARP-peer
  sentence remains for MASTER, BACKUP, unknown and override states. The last scan remains visible.
* `Service observation: observing` was misleading when monitoring was disabled. The Settings row is
  now `HA policy permission`; its values are `permitted` and `paused by HA policy`. This describes
  the HA policy gate only. Actual monitoring state remains independently visible in the compact
  notice as `Monitoring enabled`, `Monitoring disabled`, or `Monitoring status unknown`.
* Narrow fixture tabs clipped HA / CARP and About because the fixture's `.tabs` row used
  `overflow-x:auto` with no wrapping. The fixture now uses `flex-wrap:wrap`. Source inspection shows
  the real Settings view uses Bootstrap `nav-tabs` and has no corresponding no-wrap/overflow rule,
  so the clipping was fixture-only and no Settings CSS change was made.

Affected checks passed: PHP HA visibility (18 cases), JavaScript HA visibility (23 cases), non-HA
operation, integration reconciliation, translated JavaScript, CI configuration, catalogue
determinism, locale merge, sidecar catalogue, all eleven `msgfmt --check` runs, fixture static check,
inline-JS syntax and `git diff --check`. Validation log:
`/root/dm-validation-2140/dm-bl-013-ha-compact-line-20261113T010100Z/validation-ha-details-20261113T012124Z.log`
(SHA-256 `d9f25d10ef488b9cd9b0697549fd89666a8bef5663af0e3068b2e670e71f1739`).

The refreshed fixture archive is at
`/root/dm-validation-2140/dm-bl-013-ha-compact-line-20261113T010100Z/devicemonitor-ha-compact-line-fixture-20261113.tar.gz`:
374,294 bytes, 18 members, SHA-256
`40b2e6b3548b0d664665fa5021989ac660d9613bd72d99c8f741b23facff450b`. It verifies from a clean
extraction with manifest, static, path, symlink and no-live-call checks. Verification log:
`/root/dm-validation-2140/dm-bl-013-ha-compact-line-20261113T010100Z/fixture-reseal-verification-20261113T012225Z.log`
(SHA-256 `317b4de93f2ca1fddeb9f961ae2453633f3294220bb90b63d6535f80297f2a44`). The prior
`7376a65a…acbab` archive is preserved under `.../preserved-7376a65a/`; the earlier fixtures remain
preserved. Language acceptance remains deferred by the price gate; browser acceptance of this
refreshed fixture remains pending. DM-BL-013 remains **OPEN**; historical activation attribution
remains **UNKNOWN**.

## Operator screenshot review — sampled fixture states (13 November 2026)

The operator supplied a screenshot review of the R5 isolated browser fixture (`374,294` bytes,
SHA-256 `40b2e6b3548b0d664665fa5021989ac660d9613bd72d99c8f741b23facff450b`). The review passed for
the sampled states exercised:

* MASTER, both collapsed and expanded.
* BACKUP, both collapsed and expanded.
* Confirmed non-HA with monitoring disabled.
* An active role override.
* Narrow-screen tab wrapping.
* The simulated MASTER-to-fetch-failure transition.

This is operator attestation of isolated simulated fixtures, not an agent-observed browser session.
No exact observation timestamp was supplied and none is inferred. The sampled review does not
establish the full state matrix, keyboard acceptance, live CARP behaviour, a live role transition,
production rendering, delivery paths or MASTER-only operation. DM-BL-013 therefore remains
**OPEN**, and historical monitoring-activation attribution remains **UNKNOWN**.

## Final reproducible source candidate (13 November 2026)

The final source-only candidate was built twice from the same working tree with separate stage,
output and allow-list paths:

* 1,827,998 bytes
* SHA-256 `2d2c0a884ef169a4f9609a84f2860918bd7fc8432dfb23be52c4b9d6f35d8874`
* 60 archive members
* byte-identical builds C and D
* durable evidence: `/root/dm-validation-2140/dm-bl-013-final-20261113T013258Z/`

The release manifest and release-input pins were regenerated before this build and verify against
the current payload. Review found that the first final build (`a35b16bb…e6c8`) still carried
worktree permission bits into the archive: a locally regenerated manifest was `0600`, and clean
checkouts under a different umask produced other modes. The builder now derives `0644`/`0755` from
the Git index, and the determinism test deliberately varies both timestamps and worktree modes.
The superseded `a35b16bb…e6c8` and `e7dcb7f8…3124` identities remain recorded in
`release/bundle-digest.txt`; their artifacts and evidence remain preserved. This final candidate is
source-only and has not been installed on `.23` or production. The installed `.23` payload remains
`e7dcb7f8…3124`.

The premium price gate was active at 12:33 AEDT during finalisation. Language acceptance remains
deferred without a bypass; all non-gated static, unit, integration, catalogue, release and
reproducibility checks are still required before this candidate is proposed for commit.

## Appliance CARP configuration vs monitoring-scope readiness (13 November 2026)

The automatic-relevance predicate described earlier in this record was too narrow. It required at
least one resolved monitored interface before it would confirm non-HA, which conflated two separate
questions: whether the appliance has any CARP configuration, and whether the selected monitoring
scope is ready and its effective roles are known. Read-only inspection of `.23` established:

* `/conf/config.xml` was readable and contained zero `<virtualip><vip>` nodes and zero CARP VIPs;
* `/sbin/ifconfig -a` was readable and contained zero `carp:` state lines;
* the configured interface map was `lo0=lo0`, `lan=re0`, `wan=iwm0_wlan0`, `opt1=vlan0.50`;
* the Device Monitor configuration had `enabled=0`, `monitored_interfaces=''`, `ha_carp_enabled=1`,
  and `ha_role_override=auto`; and
* the previously captured installed-candidate response returned `role=none`, `mode=none`,
  `non_ha_confirmed=false`, `ha_relevant=true`, `monitored_interfaces=[]`, and `vips=[]`.

That result correctly showed that monitoring scope was empty, but it did not use the independently
positive appliance-wide evidence to make the HA controls irrelevant. The source candidate now
returns the evidence as separate fields: `appliance_carp_state`,
`appliance_non_ha_confirmed`, `carp_vip_count`, `carp_runtime_available`,
`carp_runtime_present`, `monitoring_scope_ready`, `monitoring_scope_reason`, and
`monitoring_roles_known`. `appliance_carp_state=absent` requires readable configuration,
readable `ifconfig`, no configured CARP VIP, and no CARP runtime state anywhere on the appliance.
It does not require a monitored interface. `non_ha_confirmed=true` additionally requires the role
override to remain `auto`, so an explicit MASTER or BACKUP override still wins.

When CARP is configured or active but no monitored interface is selected, the response keeps
`non_ha_confirmed=false` and reports `carp_present_no_monitored_interfaces`; the UI displays a
specific unconfirmed-scope explanation. Unreadable configuration, a failed detector, or either
kind of input failure leaves `appliance_carp_state=unknown` and cannot confirm non-HA. An empty
monitoring selection alone is never treated as proof of appliance-wide absence.

The actual `.23` source-harness response now reports `appliance_carp_state=absent`,
`non_ha_confirmation=appliance_non_ha`, `non_ha_confirmed=true`, `ha_relevant=false`,
`monitoring_scope_ready=false`, `monitoring_scope_reason=no_monitored_interfaces`, and
`monitoring_roles_known=false`. Focused API coverage has 23 cases, including the live XML/interface
shape, CARP VIP configured with an empty scope, CARP `INIT`, detector failure, unreadable
configuration, and an active override. Renderer coverage has 25 cases and confirms the compact
confirmed non-HA summary omits the HA role while the CARP-present/empty-scope state remains visible
as unconfirmed. All eleven catalogues pass `msgfmt --check`.

The replacement source-only candidate is 1,850,019 bytes with SHA-256
`c2405fccc43c1c1d6a44d4cdd9af0c5d2927778e42b9e3ecfa0c375eefcaf7d4`. Two independent checkout
builds and the recorded-digest check are byte-identical. Durable evidence, including the read-only
config evidence, captured source response, validation log, original candidate and checksum file, is
under `/root/dm-validation-2140/dm-bl-013-appliance-carp-scope-20261113T024619Z/`. The previous
`97ac0283…3ace` candidate remains preserved. No install, service action, settings change,
monitoring activation, reboot, production contact, commit, push or publication was performed.
DM-BL-013 remains **OPEN**, and historical monitoring-activation attribution remains **UNKNOWN**.

## HA role override wording and standard select treatment (13 November 2026)

The Settings → HA / CARP role override now presents the stored values with clearer labels:

* `auto`: **Automatic (use CARP role)**
* `master`: **Force MASTER behaviour**
* `backup`: **Force BACKUP behaviour**

The help text is **“Overrides Device Monitor behaviour only; does not change the firewall’s CARP
role.”** The misleading “never observe” claim has been removed; the BACKUP override does not stop
all inventory activity. The underlying `auto`, `master` and `backup` values, their collection in
`collectConfigData()`, and the existing daemon and controller behaviour are unchanged. All eleven
catalogues contain translated entries for the four revised strings.

The control now uses OPNsense’s existing Bootstrap-select treatment (`selectpicker`,
`data-style="btn-default"`) instead of a bare native `form-control` select. No custom dropdown or
control-specific font CSS was added. The installed OPNsense theme associates the page font and
15px control size with `select` and `.btn`, and standard core pages use the same `selectpicker`
integration. Consequently the closed control and the opened option list for this control are both
rendered through the theme’s standard Bootstrap-select elements rather than the browser/OS-native
option popup. Other native selects elsewhere on the page were deliberately left unchanged.

An agent browser screenshot was not captured: the `.23` host does not carry Chromium, Firefox,
WebKit, Playwright, Selenium or a headless screenshot tool. The source/CSS comparison therefore
proves the standard classes and inherited typography, but it is not a pixel-level browser check.

### Operator-supplied live Settings screenshot evidence

The operator reported a live Settings screenshot review on 13 November 2026. The supplied evidence
shows the compact and expanded non-HA notices rendering correctly, irrelevant HA controls appearing
disabled, and the role override remaining available. This is an operator attestation, not an
agent-observed browser session. No screenshot file, browser/version or exact observation timestamp
was supplied or retained. The screenshot reflects the previously deployed live Settings and does
not validate the revised labels or new select treatment; visual acceptance of this revision remains
pending.

Static and isolated validation passed: 25 JavaScript behaviour cases, 23 PHP API cases, all eleven
`msgfmt --check --check-format` catalogue builds, catalogue determinism, translated-JavaScript
checks, sidecar-catalogue checks, PHP view syntax, JavaScript syntax, `git diff --check`, and
runtime language acceptance against isolated newly compiled catalogues (9 languages, 10 pages, 529
keys each). No deployment, service action, settings change, monitoring activation, commit, push or
publication was performed by this revision.

## Selectpicker lifecycle correction and `.23` deployment (13 November 2026)

The role-override control was present in the source as Bootstrap-select markup, but it relied only
on the library's window-load data hook. That hook can run after the asynchronous settings request
has already written the saved role with `.val(...)`; the hidden native select and the generated
toggle can then disagree. The library also creates its generated toggle with `tabindex="-1"`, so a
keyboard user could not tab to the role override even though the native select carried an
accessible name.

The Settings view now explicitly initialises `#ha_role_override`, refreshes it after the
asynchronous configuration value is assigned and after the HA-control disabled state changes, and
keeps the generated toggle in sync with the native select's disabled state. The toggle receives
`tabindex="0"` when enabled and an accessible name containing both the control label and selected
value. The underlying option values and `collectConfigData()` remain unchanged, so `auto`, `master`
and `backup` values are preserved. The refresh helper does not submit a form or invoke a save
button, and the page's existing `.dm-pane-form` submit handler continues to prevent implicit form
submission. Bootstrap-select's generated button is `type="button"`; opening it therefore cannot
submit the pane form. These checks are source/isolated-JavaScript validation, not a live browser
keyboard test.

Candidate `dm-v2.14.0-runtime.tar.gz` is 1,850,019 bytes with SHA-256
`10ff1509efce5bc109860fa9c8e645e906468cf764b02d6dcaaa1c77886efd47`. Two separate stage builds
were byte-identical and the clean-checkout determinism suite passed. The runtime manifest,
release-input pin and inline installer pins were regenerated; the prior c2405fcc… candidate remains
preserved in `release/bundle-digest.txt` history and its earlier evidence directory.

The non-mutating staged-installer preflight returned `CHECK_OK version=2.14.0 predecessor=2.14.0
files=63 core_locales=10 prunable=0 daemon_running=1 host=OPNsense.internal legacy_prunable=0
retained=0`. The authorised `.23` installation returned `INSTALL_OK version=2.14.0 files=63
core_locales=10 pruned=0 backup=/var/backups/devicemonitor/install-v214.tqCqe5
daemon_restarted=1 unchanged=39 repaired=0`. Post-install verification found all 63 installed
record rows matching, SQLite integrity `ok`, the installed Settings hash matching the candidate,
and byte-identical `config.json` (`027594eb…`), `devices.db` (`796d28c7…`) and `/conf/config.xml`
(`e86a7058…`). Monitoring, monitored-interface selection, email and webhook settings remained
disabled, no CARP VIP was present, and the Device Monitor and configd services were running. No
reboot occurred. This is lifecycle testing on the existing development host, not a pristine
OPNsense installation.

The live Settings URL for operator inspection is
`https://192.168.20.23/ui/devicemonitor/index/settings`.
The operator reviewed visual details and Escape on the predecessor, then confirmed
final-candidate keyboard behaviour below; the agent has no browser on `.23` and makes no pixel-level
or native-popup claim. Durable evidence is under
`/root/dm-validation-2140/dm-bl-013-ha-selectpicker-20261113T151521Z/`.

### Operator verification and keyboard correction

The operator supplied a live review of the deployed `10ff1509…` Settings page on 13 November 2026.
The opened dropdown font matched the surrounding UI, all three revised labels displayed correctly,
and Escape closed the dropdown. A Space-to-open attempt was unsuccessful; the operator could not
establish the preceding focus/keyboard conditions. No precise observation timestamp was supplied,
and this is not full keyboard acceptance.

Source inspection against the installed Bootstrap-select 1.13.18 found a concrete defect. When the
dropdown is closed, its type-ahead branch consumes Space and Enter and calls `preventDefault()`
before native button activation can open the menu. The initial lifecycle candidate also set
`tabindex="0"` directly on the generated toggle, bypassing the plugin's native-select focus proxy.
The final source supersedes that approach: the native `#ha_role_override` select carries
`tabindex="0"`, the plugin manages the generated toggle, and a namespaced closed-state handler opens
the menu on Space or Enter while leaving those keys to plugin selection behaviour when the menu is
open. The handler does not write the saved value, submit the form, or invoke a save button.

The corrected source builds reproducibly at 1,850,531 bytes with SHA-256
`2f69a69751755891578fb53a3d15f27be1200798b89a0f23ad24137d75d5ef33`. It was deployed to `.23`
with a clean preflight and a fresh installer backup. All 63 installed hashes matched, SQLite
integrity remained `ok`, and `config.json`, `devices.db` and `/conf/config.xml` remained
byte-identical. The saved role override remained `auto`, monitoring and notification gates remained
disabled, and Device Monitor and configd stayed healthy; no reboot occurred. Isolated UI tests pass
25 JavaScript cases, 23 PHP cases, and the static selectpicker checks. The operator subsequently
confirmed, without an observation timestamp being recorded, that Space and Enter open the deployed
dropdown, Escape closes it, and the saved value remains `Automatic (use CARP role)`. DM-BL-013
remains **OPEN** pending production MASTER, HA-transition and delivery-path validation. Historical
monitoring-activation attribution remains **UNKNOWN**.

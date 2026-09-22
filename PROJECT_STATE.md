# Device Monitor — Project State

## Last updated

22 September 2026

## Current version / branch / environment

Development branch:

`v2.9-development`

Authoritative development checkout (FreeBSD 15.1-RELEASE amd64):

`/root/src/opnsense-devicemonitor-upstream`

Previous Windows checkout (retained as fallback/reference only; no longer
authoritative):

`C:\Users\apg19\Downloads\opnsense-devicemonitor-upstream`

Primary deployment target (final runtime/deployment validation target):

OPNsense 26.7.2_2

Latest completed v2.9 implementation commit:

`d8421ca` — `feat: clarify physical device identity management` (final
pre-release Physical Devices UX redesign; read-model enrichment `67a476c`,
documentation `97abb98`)

Latest repository commit (HEAD):

`d0fe7af` — `docs: prevent redundant finalisation checks`

Workflow state:

- FreeBSD migration complete: development is now performed on the physical
  OPNsense testbed `192.168.20.23` (FreeBSD 15.1-RELEASE amd64). Normal project
  commands run on the native FreeBSD toolchain (`/bin/sh`, `/usr/local/bin/bash`,
  `/usr/local/bin/git`, `/usr/local/bin/php`, `/usr/local/bin/python3`)
- previous Windows checkout
  `C:\Users\apg19\Downloads\opnsense-devicemonitor-upstream` is retained as
  fallback/reference only and is no longer authoritative; Debian WSL remains
  secondary/fallback only and is not an authoritative Device Monitor checkout
- repository-local Cline workflow rules (`.clinerules/00-project-control.md`,
  `.clinerules/10-workflow-and-finalisation.md`) committed as `0b6496a`
- workstation-local access rules (`.clinerules/90-local-remote-access.md`)
  exist on this host and are excluded through `.git/info/exclude`; they
  must remain untracked and must never be added, committed or pushed
- Git author identity is configured repository-locally
- GitHub CLI (`gh`) is installed and authenticated as `apg19590209` with default
  repository `apg19590209/opnsense-devicemonitor`; GitHub/CI operations are
  available from this checkout
- unattended OPNsense SSH access is available and validated through
  `ssh opnsense-dm`; OPNsense remains the final runtime/deployment validation
  target
- branch `v2.9-development`; worktree clean and synced with
  `origin/v2.9-development` before this documentation edit


## Device Monitor: stabilise VLAN filtering

Repaired the Network Identities VLAN multi-select and its sticky header.

- Root cause: the VLAN checklist wrapped checkboxes in `<a href="#">` anchors
  (unreliable single-click toggling and page jumps) and `persistVlans()` re-rendered
  the whole table on every checkbox change. The sticky summary/toolbar/thead stack
  was positioned from a fixed `padding-top` offset rather than the measured natural
  flow gap, so it could jump upward and cover the navigation tabs.
- Interaction change: checkboxes are now native `<label>` items that only update a
  pending selection; explicit **Apply** and **Clear** buttons commit the selection
  once. `applyFilters()` preserves vertical and horizontal scroll position around the
  single re-render, and `updateStickyOffsets()` now derives the sticky offsets from a
  measured `getBoundingClientRect()` gap so the header stays below the page
  navigation area and never covers the tabs.
- Status filtering, filtered summary counters, refresh behaviour and VLAN label
  formatting are unchanged. No API, route, database, scanner or stored-data changes.
- Files changed: `src/opnsense/mvc/app/views/OPNsense/DeviceMonitor/devices.volt`,
  `src/opnsense/mvc/app/languages/cs_CZ_devicemonitor.po`,
  `src/opnsense/mvc/app/languages/en_US_devicemonitor.po`,
  `docs/USER_MANUAL.md`, `.github/workflows/ci.yml`,
  `tests/test_devices_page_vlan.js` (new).
- Tests: added `tests/test_devices_page_vlan.js`; full Node/Python/PHP suite,
  `py_compile`, `php -l`, `sh -n`, `msgfmt` and `git diff --check` all PASS.
- Deployed to testbed `192.168.20.23` with rollback backup retained at
  `/tmp/dm_deploy_backup_20260922075730`. Production `192.168.20.254` untouched;
  daemon, database, config.json and config.xml unchanged.
- Next step: authenticated testbed visual acceptance.


## Device Monitor: correct identities filter layout

Corrected the remaining authenticated visual defects in the Network Identities
VLAN filter without regressing the Apply/Clear interaction.

- Root cause (layout): a custom measured-gap sticky stack (`updateStickyOffsets()`
  with a cached `getBoundingClientRect()` gap) plus global `scroll-snap` let body
  rows overlap the column header, reordered the summary/toolbar/thead during
  scroll, left blank space below the title, and let the tabs scroll out of view.
- Root cause (count): `updateVlanLabel()` derived the button from the applied
  `activeVlans` state instead of the pending checkbox state, so the button could
  read "2 VLANs" while only one checkbox was selected.
- Change: removed all custom sticky positioning and `scroll-snap` (CSS and JS); the
  page now renders in natural DOM order and filtering preserves scroll position.
  `updateVlanLabel()` now counts checked VLANs ("All VLANs" / "1 VLAN" / "N VLANs")
  and is invoked on every checkbox change without filtering.
- Files changed: `src/opnsense/mvc/app/views/OPNsense/DeviceMonitor/devices.volt`,
  `tests/test_devices_page_vlan.js`, `DECISIONS.md` (Decision 28).
- Tests: `tests/test_devices_page_vlan.js` extended (layout order, sticky removal,
  VLAN count state); full Node/Python/PHP suite, lint, `py_compile`, `sh -n`,
  `msgfmt`, Volt compile and `git diff --check` all PASS.
- Next step: authenticated testbed visual acceptance (top/middle/lower table,
  pending count, Apply, Clear, scroll preservation, tab visibility).


## Device Monitor: stable identities table header (DM-STICKY2)

Reintroduced a correct, stable sticky region on the Network Identities page
after the previous fragile custom sticky stack was removed.

- Root cause: removing the measured-gap sticky stack (`9701d1d`, Decision 28)
  fixed the overlap/jumping/tab coverage but also let the useful column header
  scroll away with long device lists. The page relies on normal document
  scrolling with the OPNsense top navbar fixed at ~62px, and no table ancestor
  clips the content, so CSS `position: sticky` is safe.
- Change: one sticky wrapper (`#devices-sticky-header`) now pins the summary
  counters and the VLAN/status toolbar, and the column headings
  (`#grid-devices thead th`) stick immediately below it. Offsets use CSS custom
  properties (`--devices-sticky-top`, `--devices-sticky-thead-top`) recalculated
  from live measurements on load, resize and genuine toolbar-height changes
  (`ResizeObserver`); measuring never triggers a table render. No scroll-snap,
  pseudo-element shield, cached one-shot geometry or `scrollIntoView` is used.
  Filtering, VLAN pending/applied semantics, Apply/Clear single-render and
  scroll preservation are unchanged.
- Files changed: `src/opnsense/mvc/app/views/OPNsense/DeviceMonitor/devices.volt`,
  `tests/test_devices_page_vlan.js`, `DECISIONS.md` (Decision 29),
  `docs/USER_MANUAL.md`.
- Tests: 11 Node (UI), 13 Python and 11 PHP tests PASS; `php -l`, `py_compile`,
  `sh -n`, `msgfmt`, Volt compile and `git diff --check` PASS.
- Next step: authenticated testbed visual acceptance (sticky counters/toolbar/
  headings while scrolling, no row show-through, tabs not covered, pending VLAN
  count, Apply/Clear single-render without viewport jump, resize behaviour).


## Device navigation and terminology consolidation

Consolidated the Device Monitor submenu and terminology. Implemented, validated
and deployed to the testbed `192.168.20.23`. Production `192.168.20.254` was
not touched; no scan, provider, daemon or database behaviour was changed.

- Single **Devices** submenu entry replaces the separate **Devices** and
  **Physical Devices** entries (`Menu.xml`).
- Two tab-style views link between the existing routes:
  - **Network Identities** (`/ui/devicemonitor/index/devices`) — the MAC-level
    discovered-device table.
  - **Device Profiles** (`/ui/devicemonitor/index/physicaldevices`) — the
    user-confirmed real-world device grouping (formerly "Physical Devices").
- Terminology: "Physical Devices" → "Device Profiles", "Physical Device" →
  "Device Profile", "Create Device" → "Create Profile", "Device Summary" →
  "Profile Summary", "All/Current/Archived Devices" → "All/Current/Archived
  Profiles"; "Current Identities", "Previous Identities", "Add Identity" and
  "Unlink Identity" retained.
- All internal routes, URLs, controller actions, API endpoints, model methods,
  JSON fields and database identifiers remain unchanged (including
  `index/physicaldevices`, `physicaldevices`, `listphysicaldevices`,
  `createphysicaldevice`, `linkphysicaldeviceidentity`,
  `removephysicaldeviceidentity`, `physical_devices` and
  `physical_device_memberships`). No database migration.

Files changed: `Menu.xml`, `devices.volt`, `physicaldevices.volt`,
`devicehistory.volt`, `changesummary.volt`, `DeviceMonitor.php` (two
change-summary description strings), both gettext catalogues, the new
`tests/test_device_navigation.js`, `.github/workflows/ci.yml`,
`docs/USER_MANUAL.md`, and `DECISIONS.md` (Decision 27 supersedes the earlier
"Physical Device is retained" wording).

Validation (local): Python compile, PHP lint, shell syntax, gettext
(`msgfmt --check`), `git diff --check`, 10 Node (UI) tests, 13 Python tests and
11 PHP tests — all PASS.

Deployment (`192.168.20.23`, guarded): 8 runtime files (`Menu.xml`, four
`.volt` views, `DeviceMonitor.php`, both compiled `.mo` catalogues) deployed
with candidate/pre/post SHA256 parity and timestamped `cp -p` rollback backups.
Menu cache and Volt template cache invalidated; no service restart; daemon
unchanged. Unauthenticated route smoke check: HTTP 302 (no PHP fatal) for both
`/ui/devicemonitor/index/devices` and `/ui/devicemonitor/index/physicaldevices`.
Read-only DB safety unchanged (`devices.db`, `config.json`, `/conf/config.xml`
hashes identical to the pre-deployment state).

Next step: confirm the GitHub Actions CI run for this commit passes.

## Device navigation visual-acceptance follow-up

Applied a minimal follow-up to `cc7255e` to correct confirmed visual issues on
the Device Profiles view. Testbed `192.168.20.23` only; production
`192.168.20.254` was not touched. No routes, APIs, database, scanner, daemon,
config or existing profile data were changed.

- Device Profiles route now renders the same standard page heading as Network
  Identities (`Services: Device Monitor: Devices`) by setting `title` and
  `headTitle` in `IndexController::physicaldevicesAction()`.
- Device Profiles summary stat label changed from "Devices" to "Profiles"
  (`physicaldevices.volt`); a new `Profiles` msgid was added to both gettext
  catalogues (`en_US` → "Profiles", `cs_CZ` → "Profily").
- Network Identities explanatory text was already present from `cc7255e` and is
  unchanged.

Files changed: `IndexController.php`, `physicaldevices.volt`, both gettext
catalogues, `tests/test_device_navigation.js` (new heading check) and
`tests/test_physical_devices_page.js` (new summary-label checks).

Validation (local): Python compile, PHP lint, shell syntax, gettext
(`msgfmt --check`), `git diff --check`, 9 Node (UI) tests, 11 Python tests and
9 PHP tests — all PASS.

Deployment (`192.168.20.23`, guarded): 4 runtime files (`IndexController.php`,
`physicaldevices.volt`, both compiled `.mo` catalogues) deployed with
candidate/pre/post SHA256 parity and timestamped `cp -p` rollback backups.
Volt template cache entry for `physicaldevices.volt` cleared; menu cache not
affected (no `Menu.xml` change); no service restart. Unauthenticated route
smoke check: HTTP 302 for both `/ui/devicemonitor/index/devices` and
`/ui/devicemonitor/index/physicaldevices`. Deployed view verified to contain
the `Profiles` summary label; deployed controller verified to set the standard
heading; compiled `.mo` verified to contain `Profiles`/`Profily`. Read-only DB
safety unchanged (`devices.db`, `config.json`, `/conf/config.xml` hashes
identical to pre-deployment state).

Next step: commit, push and confirm the GitHub Actions CI run passes.

## v2.9 development — Pi-hole and Unbound experimental opt-in

Marked Pi-hole and Unbound hostname enrichment as **Experimental** and made Unbound
opt-in (disabled by default).

- New `unbound_enabled` setting (default `"0"`) wired through `defaults.json`,
  `ConfigController.php` (read/save/validation), the Settings Monitoring UI, and
  provider construction in `scan_network.py`.
- `get_unbound_hostnames()` is only called when `unbound_enabled` is set; a missing
  key after an upgrade means disabled.
- Pi-hole config fields (`pihole_enabled`, `pihole_url`, `pihole_password`) are now
  forwarded through `load_config()` so the runtime honours the GUI setting
  (previously these fields were never read from `config.json`).
- Experimental badges and descriptions added to the Settings UI (Pi-hole and
  Unbound), English/Czech gettext catalogues, README/README_CZ, and the user manual.
- `DECISIONS.md` Decision 26 records the change and supersedes Decision 24's
  "always available / no enable-disable setting" wording.
- New regression tests: `tests/test_pihole_config.php`,
  `tests/test_unbound_config.php`, Unbound opt-in coverage in
  `tests/test_unbound_provider.py`, and provider default coverage in
  `tests/test_fresh_install_defaults.py`.

Validation and deployment: see the commit for this change.


## Completed work — fail-closed monitored-interface scoping

Completed 21 September 2026 (commit message: "Device Monitor: enforce fail-closed
interface scoping").

- **Fail-closed monitored-interface scoping**: new `monitored_interfaces` setting
  (`defaults.json`, `ConfigController.php`), Settings UI with a fail-closed warning
  (`settings.volt`), and `scan_network.py` scoping (`resolve_monitored_networks`,
  `ip_is_in_scope`, `scoped_device_macs`, `get_hostwatch_devices(networks)`). An
  empty selection is refused and there is no LAN fallback.
- **Scoped status counters / identity events / notification cleanup / Nmap queue**
  (`scan_network.py`), plus a starvation fix: out-of-scope queued scans no longer
  consume the in-scope batch limit.
- **Superseded LAN-only Hostwatch priming** with selected-interface/subnet priming
  (`DECISIONS.md` Decision 25).
- **Filtered Devices-page summary counters** (`devices.volt`) with CI coverage
  (`tests/test_devices_page_summary.js`, `.github/workflows/ci.yml`).
- **Documentation**: `docs/USER_MANUAL.md`, `README.md`, `README_CZ.md` and gettext
  catalogues updated.
- **Deployment**: `devices.volt` deployed to the OPNsense testbed (SHA-256
  verified). Device Monitor daemon remains disabled/stopped; the live database was
  not modified.
- **Validation**: Node UI suite 9/9 PASS, PHP lint PASS, Python compile PASS, shell
  syntax PASS, `git diff --check` PASS.

## Current objective

`DM-BL-001` — User-confirmed physical-device identity grouping — is implemented
and complete. Its **Create**, **list existing groups**, **Link** and **Remove**
flows, plus member-count display, have all been live-validated on the physical
OPNsense testbed `192.168.20.23` (see "DM-BL-001 live validation, purge and
link-safety UX" below). Inactive identities are intentionally rejected as
physical-device group seeds; this is confirmed, expected behaviour and not a
defect. Its same-physical-device Link safety UX (commit `14ee00f`) is deployed
and live-confirmed.

The associated Device Monitor UI consistency work is complete and live-validated
on `192.168.20.23`: app-wide compact status/action sizing was visually
normalized, the compact Device Monitor selects were converted to OPNsense's
`bootstrap-select`/`selectpicker` pattern, and the dynamic Physical Device
`#physical-device-select` now uses selectpicker with AJAX refresh and preserved
option ordering. Live Firefox visual validation passed on `192.168.20.23`.

No new product-backlog feature is designated as the next implementation task;
`PRODUCT_BACKLOG.md` remains authoritative for deferred work.

Stage 2 — dedicated Physical Devices page redesign — is in progress:

- Unit 1 (read path): `247d30c` — `getPhysicalDevicesOverview()` + `GET
  /api/devicemonitor/devices/physicaldevices` (active + archived groups with
  full membership history). CI `35496385491`: PASS.
- Unit 2 (page): `92fb429` — dedicated **Physical Devices** page
  (`physicaldevices.volt`, menu entry, route `/ui/devicemonitor/index/physicaldevices`).
  CI `35497551473`: PASS.
- Unit 3 (Device Details summary): `bb0cbee` — Device Details grouping is now a
  compact read-only **Physical Device** summary linking to the dedicated page;
  create/link/remove management removed from Device Details. CI `35498323464`: PASS.
- Unit 4 (Devices-page badge): `184819e` — the Devices-page **Physical Device**
  badge now routes to `/ui/devicemonitor/index/physicaldevices?group=<id>`.
  CI `35498804635`: PASS.

Stage 2 (dedicated Physical Devices page redesign) is complete.

**Description:** Add an explicit user-controlled physical-device grouping layer
above existing MAC identities so multiple legitimate MAC addresses can be
identified as belonging to the same physical device.

**Benefit:** Reduces false interpretation of legitimate multiple MAC identities
while preserving the exact MAC, lifecycle, identity-event and activity history
already recorded by Device Monitor.

**Current design:** Grouping is additive only. Existing device rows, lifecycle
ownership, returning-device resolution and identity-conflict detection remain
authoritative and are not merged or rewritten. Membership changes are auditable
and reversible.

**Implementation status:** All four DM-BL-001 implementation units are
complete, committed, deployed and validated. The additive `physical_devices` and
`physical_device_memberships` schema, active-membership uniqueness protection,
read-only `getPhysicalDeviceForMac()` access, explicit model operations to
create a physical-device group, link a known identity and soft-remove a
membership, and the corresponding explicit Devices API actions are now
present. Removed memberships retain their history. The production grouping
baseline was left at zero: a temporary GUI test group was created during Create
validation and later intentionally purged (see "DM-BL-001 live validation, purge
and link-safety UX" below). Existing discovery, lifecycle, identity and
pre-existing UI behaviour remains unchanged. Read-model
commit `4f866ba`; write-model commit `f6d547f`; API commit `752ee59`; GitHub
Actions runs `34693021844`, `34693933012` and `34694963846`: PASS. The live API
controller deployment was hash-verified and retained rollback backup
`DevicesController.php.pre-dmbl001-api-20260912-225811`.

Unit 4 — the `Physical Device / Related Identities` section on the Device
Details page — is complete:

- commit `be9b686` — `feat: add physical device grouping UI`
- implemented in
  `src/opnsense/mvc/app/views/OPNsense/DeviceMonitor/devicehistory.volt`
- permanent regression coverage in `tests/test_physical_device_ui.js`
- CI step `Validate physical-device UI` added to `.github/workflows/ci.yml`
- GitHub Actions run `34696074421` for `be9b686`: PASS
- deployed `devicehistory.volt` SHA256
  `39291eb3614a3241329ae5ddb279fd8de4fe9d078f1cd3ef1cb6d4c5e55b9d29`
- deployed hash matches the repository file exactly
- live GUI validation: Device Details displayed the new Physical Device /
  Related Identities panel correctly for an ungrouped MAC
- at the time of Unit 4, Create/Link/Remove write flows were deliberately
  **not** exercised against production; the later Create validation and the
  intentional purge of its temporary test group are recorded below
- current production baseline (after that purge) remains `physical_devices` = 0
  and `physical_device_memberships` = 0

Unit 5 — grouping-eligibility refinement — is complete, deployed and
live-validated:

- commit `c28c14d04d84465fc6d726d8ce038e7e4ef0b519` —
  `fix: enforce physical device grouping eligibility`
- exactly three implementation files changed:
  `.github/workflows/ci.yml`,
  `src/opnsense/mvc/app/models/OPNsense/DeviceMonitor/DeviceMonitor.php`,
  `tests/test_device_lifecycle_actions.php`
- admission rules now require a current, active, resolved device identity to
  create a group, and a current, resolved device record to link an identity;
  unresolved or non-current identities (historical-only, deleted-only,
  lifecycle-only and `return_pending`) are rejected, and an inactive current
  identity is accepted only when the group already has an active current
  resolved member
- local lint and regression validation passed: `php -l` for both changed PHP
  files, the full `tests/test_device_lifecycle_actions.php` suite, plus
  `tests/test_physical_device_api.php` and `tests/test_physical_device_ui.js`
- GitHub Actions run `34734837042` for `c28c14d`: PASS, including the new CI
  step `Validate device lifecycle actions` (step 15), which executed and passed
- removal behaviour remains admission-independent, as deliberately covered by
  the regression suite; no last-active-member removal guard was added
- the grouping lifecycle behaviour approved in `DECISIONS.md` §18 is now
  **implemented and deployed**, with live validation where safe (Unit 6 below)
- still unresolved and out of scope: per-member UI/API state
- deployment status: **DEPLOYED to OPNsense on 13 September 2026** via the
  guarded procedure (staged hash + pre-state hash + backup hash + post-deploy
  hash verified inside a single success/failure guard chain); deployed
  `DeviceMonitor.php` SHA256
  `ac3c1b418ded15342bad12c37757ca681954144e2fd0952a345b80b05f305b74` matches the
  repository source exactly and permissions remain `644 root:wheel`
- rollback backup retained:
  `/usr/local/opnsense/mvc/app/models/OPNsense/DeviceMonitor/DeviceMonitor.php.pre-dmbl001-eligibility-20260913-134556`
  (verified pre-deployment live SHA256
  `938aedbaadccbdbf1d2d782c2e5e2d43a57d3425096959287164ab6b8f40688b`)
- live validation: PHP syntax check PASS on the deployed file; class loads
  (`CLASS_OK`); `getGroupingEligibility()` present; `service devicemonitor
  status` running; Device Monitor API and UI paths return HTTP 302 (no PHP
  fatal); no new Device Monitor or PHP errors (the only two log error lines
  date from 8–9 September)
- no service restart/reload was required or performed: the model is loaded per
  web request and `opcache.validate_timestamps => On`, and the Python daemon
  does not use PHP
- live grouping data (read-only): 45 devices (32 active), `return_pending` 0,
  `lifecycle_id` NULL 0, `physical_devices` 0, active memberships 0, lifecycles
  45 active / 0 archived, `deleted_devices` 1; 32 identities are eligible group
  seeds, 13 are inactive current resolved identities, 0 are lifecycle-only
  historical and 1 is deleted-only historical
- live create/link/remove **write** branches were deliberately not exercised:
  no live groups exist and creating them would add production groupings without
  user intent, so those branches remain regression-validated only via
  `tests/test_device_lifecycle_actions.php`

Unit 6 — the `DECISIONS.md` §18 grouping lifecycle behaviour — is implemented,
deployed and live-validated where safe:

- commit `d0f82b8e74513a6c09881b33f0095da3ccda6757` —
  `fix: enforce physical device grouping lifecycle`
- exactly two files changed (424 insertions, no deletions):
  `src/opnsense/mvc/app/models/OPNsense/DeviceMonitor/DeviceMonitor.php` (+106)
  and `tests/test_device_lifecycle_actions.php` (+318)
- implemented behaviour: removing the final active membership remains allowed and
  is never blocked; membership removal remains a soft-close that preserves
  history; a group reaching zero active memberships now archives automatically
  via `archived_at` with no unarchive path; `deleteDevice()` soft-closes the
  deleted MAC's active memberships and then archives any affected empty group;
  `clearAll()` applies equivalent set-based semantics; no group or membership row
  is ever deleted
- the grouping admission rules introduced by `c28c14d` are unchanged, and the
  protected lifecycle/API/UI regressions still pass
- local validation: 13 PASS markers in `tests/test_device_lifecycle_actions.php`,
  including the new `DEVICE_PHYSICAL_GROUP_EMPTY_ARCHIVAL`,
  `DEVICE_PHYSICAL_GROUP_DELETE_CLEANUP` and
  `DEVICE_PHYSICAL_GROUP_CLEARALL_CLEANUP`; `tests/test_device_timeline.php`,
  `tests/test_device_timeline_history_preservation.php`,
  `tests/test_physical_device_api.php` and `tests/test_physical_device_ui.js`
  all pass
- GitHub Actions run `34738596652` for `d0f82b8`: PASS, including the
  `Validate device lifecycle actions` step (step 15)
- deployment status: **DEPLOYED to OPNsense on 13 September 2026** via the
  guarded procedure (staged hash + expected-predecessor hash + backup hash +
  post-deploy hash verified inside a single success/failure guard chain);
  deployed SHA256
  `2d903bb0a886da88d351754ed8fec5228b25a33f6b21225903cc230b268592fc` matches the
  repository source exactly and permissions remain `644 root:wheel`
- rollback backup retained:
  `/usr/local/opnsense/mvc/app/models/OPNsense/DeviceMonitor/DeviceMonitor.php.pre-dmbl001-lifecycle-20260913-150103`
  (verified predecessor SHA256
  `ac3c1b418ded15342bad12c37757ca681954144e2fd0952a345b80b05f305b74`)
- live validation: PHP lint PASS; class loads (`CLASS_OK`); the §18 helpers and
  all three call sites are present in the deployed file; `service devicemonitor
  status` running; API and UI paths return HTTP 302 (no PHP fatal); no new
  Device Monitor or PHP errors; no service restart was required or performed
  (model loaded per web request, `opcache.validate_timestamps => On`, and the
  Python daemon does not use PHP)
- live grouping state before and after deployment is unchanged: one active
  user-created group (`Daikin Controller Entry`, id 1) with one open membership
  for `b4:8c:9d:73:20:98` (active, resolved, lifecycle 12); zero archived groups,
  zero empty active groups and zero orphan active memberships
- live-observed: deployed bytes equal the validated source; the existing active
  group was not archived by the emptiness rule; the archive predicate currently
  matches no group
- regression-validated only (no safe live fixture): non-final versus final member
  removal archival, `deleteDevice()` membership closure plus archival, and
  `clearAll()` equivalent semantics — all covered by the `d0f82b8` suite
- admission behaviour is unchanged (the `c28c14d` helper and guards are present
  in the deployed file); no orphan-membership backfill was performed
- observations retained without adding scope: the set-based
  `archiveEmptyPhysicalDevices()` can archive any active group with zero open
  memberships, not only groups touched by the current delete/clear operation;
  legacy orphan memberships are not retroactively repaired by this unit; the
  Devices-page grouping indicator that was then future UI work is delivered by
  Unit 7 below

Unit 7 — Devices-page Physical Device grouping indicator — is implemented,
deployed and live-validated:

- commit `7ca0fb9f575525b848d395a9d9c9f9f4b02eadf1` —
  `feat: show physical device grouping on Devices page`
- five files changed (325 insertions, 1 deletion): `.github/workflows/ci.yml`,
  `src/opnsense/mvc/app/models/OPNsense/DeviceMonitor/DeviceMonitor.php`,
  `src/opnsense/mvc/app/views/OPNsense/DeviceMonitor/devices.volt`,
  `tests/test_device_lifecycle_actions.php` and the new
  `tests/test_devices_page_grouping.js`; only the model and the view are
  deployable
- GitHub Actions run `34741415761` for `7ca0fb9`: PASS, including the new
  `Validate devices page grouping indicator` step (step 15) and
  `Validate device lifecycle actions` (step 16)
- read path: `getDevices()` loads grouping metadata with a single bulk query
  keyed by MAC (active memberships of non-archived groups) and merges it per row;
  there is no per-row `getPhysicalDeviceForMac()` call
- UI: a compact `Physical Device` column after `Status`; grouped rows show a
  clickable badge `Name · N identity|identities` and ungrouped rows show a quiet
  em-dash; the badge links to
  `/ui/devicemonitor/index/devicehistory?mac=<mac>#physical-device-grouping`;
  no grouping create/link/remove controls were added to the Devices table
- deployment status: **DEPLOYED to OPNsense on 13 September 2026** via the
  guarded procedure (staged hash + predecessor hash + backup hash + post-deploy
  hash verified inside one success/failure guard chain); deployed SHA256
  `ac5aa08d47eb8d165fd04d4732356f2b44c70f62bd5ed4e0ae53556818907110`
  (`DeviceMonitor.php`) and
  `a8ccde0833f0524bbfcba0b3a562be477cf4310c6c1463fb588a16d5f491f7ad`
  (`devices.volt`) both match the repository source exactly; permissions remain
  `644 root:wheel`
- rollback backups retained:
  `DeviceMonitor.php.pre-dmbl001-devices-ui-20260913-160832` (predecessor
  `2d903bb0a886da88d351754ed8fec5228b25a33f6b21225903cc230b268592fc`) and
  `devices.volt.pre-dmbl001-devices-ui-20260913-160832` (predecessor
  `e14ccd0f3d3a9d3aa300c5dfcec12a34e8a24f154e08fee958084a83d4248091`, which
  matched the repository version at every earlier commit checked — no live drift)
- live validation: PHP lint PASS; class loads (`CLASS_OK`); the deployed view
  contains the column, grouping helper, badge and `#physical-device-grouping`
  fragment and no grouping-management controls; the Device History page still
  carries the grouping anchor; API and UI routes return HTTP 302 (no PHP fatal);
  no new PHP or Device Monitor errors; no service restart was required or
  performed
- live grouping data at the time of this deployment (read-only, unchanged by
  this deployment): one active group (`Daikin Controller Entry`, id 1) with one
  open membership for `b4:8c:9d:73:20:98`; the deployed read-path query returned
  `b4:8c:9d:73:20:98 | 1 | Daikin Controller Entry | 1`, so that device presented
  as grouped with one identity while sampled devices remained ungrouped. That
  group was subsequently intentionally purged (see "DM-BL-001 live validation,
  purge and link-safety UX" below); the current live baseline is 0/0
- authenticated visual click-through of the live page was not performed by Cline
  (no GUI/API credentials available); the items above are the executed live
  evidence, and user confirmation of the rendered column and badge is advisable
- grouping admission (`c28c14d`) and lifecycle (`d0f82b8`) write semantics are
  unchanged, and no database write occurred during this deployment

## Stage 3 — Device Details / lifecycle usability redesign

Stage 3 is complete. Stage 1 (UI/header consistency) and Stage 2 (device
identity/grouping redesign) remain complete; Stage 2 is deployed and GUI
validated on `192.168.20.23`.

Design:

- Device Details is reframed as a concise operational summary of one MAC
  identity and its lifecycle context, with explicit navigation to Device
  Activity and grouping management rather than duplicating those pages.
- Panel order is now: Device Summary, Physical Device, Lifecycle History, Notes.
- Device Summary leads with **IP Address**, then **Friendly Name**, **Hostname**
  (with its source, when known), **MAC Address**, **Vendor**; the second column
  shows **Status**, **VLAN**, **First Seen**, **Last Seen**, **Current
  Lifecycle**. The separate Notes-count row was removed (notes live in the
  Notes panel).
- Lifecycle History gained a plain-language explanation and reordered columns
  (**Lifecycle, Status, IP Address, Friendly Name, Hostname, Vendor, VLAN,
  First Seen, Last Seen, Notes, Actions**); the Lifecycle column now shows the
  lifecycle number (`#n`).
- Returning-device semantics and controls (Start New Lifecycle / Relink) are
  unchanged; timestamped lifecycle comments remain historical.

Terminology:

- The user-facing term **Physical Device** is retained. The underlying model
  (one real-world device with multiple network identities/interfaces) is
  already described in `DECISIONS.md` §17 and the user manual, and members are
  already labelled "identities". No backend/database identifier was renamed.
- `DM-BL-004` (Unbound) and `DM-BL-007` (Pi-hole) are already complete in this
  repository and were deliberately not modified; they remain outside the
  Stage 3 release boundary, so `PRODUCT_BACKLOG.md` was left unchanged (it
  already records no open backlog items).

Files changed:

- `src/opnsense/mvc/app/views/OPNsense/DeviceMonitor/devicehistory.volt`
- `src/opnsense/mvc/app/languages/en_US_devicemonitor.po`
- `src/opnsense/mvc/app/languages/cs_CZ_devicemonitor.po`
- `tests/test_device_details_ui.js` (new)
- `.github/workflows/ci.yml`
- `docs/USER_MANUAL.md`

Implementation commit:

- `5c45464` — `feat: redesign Device Details summary and lifecycle presentation`

Validation:

- full Node (UI) suite: PASS (incl. new `test_device_details_ui.js`)
- full PHP suite: PASS
- full Python suite: PASS
- PHP lint / Python compile / shell syntax / gettext (`msgfmt -c`): PASS
- `git diff --check`: PASS
- GitHub Actions: PASS (run `35502449067`)

Deployment (`192.168.20.23`):

- guarded deployment of `devicehistory.volt` and both compiled `.mo` catalogues
  (candidate/pre/post SHA256, timestamped `cp -p` rollback backups): PASS
- no `Menu.xml` change, so the OPNsense menu cache was not invalidated
- stale compiled `devicehistory.volt` Volt template removed to force recompilation
- no service restart / php-fpm reload / daemon change (file-only deployment)
- read-only DB safety counts unchanged by the deployment
- unauthenticated route smoke check (HTTP 302, no PHP fatal): PASS

GUI validation:

- authenticated visual click-through was not performed by Cline (no GUI
  credentials); a human validation checklist is provided in the final report.

## TESTBED environment and migration state

The Device Monitor testbed/development environment has been migrated to the
physical OPNsense host `192.168.20.23`.

- OPNsense `26.7.4`
- management and current LAN interface: `re0` `192.168.20.23/24`
- repository: `/root/src/opnsense-devicemonitor-upstream`
- branch: `v2.9-development`
- repository and GitHub origin verified synchronized at migration completion
- deployed Device Monitor files verified identical to the authoritative checkout
- testbed runtime state migrated from the former `192.168.56.2` VM:
  8 devices and 8 lifecycles
- automatic Device Monitor monitoring is deliberately disabled because `re0`
  is attached to the live `192.168.20.0/24` LAN; it must not be enabled until
  an intentionally isolated test interface/network is provided
- production OPNsense `192.168.20.254` was not modified by this migration
- retired and deleted VirtualBox VMs:
  `FreeBSD-15.1-DeviceMonitor`,
  `FreeBSD-15.1-DeviceMonitor-30G`, and
  `OPNsense-Testbed` (`192.168.56.2`)
- migration-critical runtime state is stored outside Git in:
  `/var/db/devicemonitor/config.json` and
  `/var/db/devicemonitor/devices.db`
## DM-BL-001 live validation, purge and link-safety UX

DM-BL-001 is complete, committed and deployed. Its live GUI validation —
completed on the testbed `192.168.20.23` — is recorded as follows.

### Create flow — live-validated

- **Create Physical Device** was manually validated through the OPNsense GUI.
- The resulting temporary test group (`Daikin Controller Entry`) existed only to
  validate the Create write flow and was later **intentionally TRUE-DELETED** as
  an authorised direct DB maintenance action, after: exact-state verification, a
  SQLite online backup, backup `PRAGMA integrity_check`, a guarded
  `BEGIN IMMEDIATE` transactional deletion (1 row from
  `physical_device_memberships`, 1 row from `physical_devices`, each guarded),
  and a post-delete `PRAGMA integrity_check`.
- Purge backup retained:
  `/var/backups/devicemonitor/devices.db.pre-test-group-purge-20260913-133147`
  (SHA256 `64b237651a5a14a8aeb90ac451e9a214689d64d845a6f71d6cf2d6871c60ed80`).
- The test group no longer exists and production retains no grouping rows.

### Full write-flow validation — live-validated on testbed

The complete DM-BL-001 grouping workflow was live-validated on the physical
OPNsense testbed `192.168.20.23`:

- **Create Physical Device**: PASS
- **Existing-group list** (dropdown): PASS
- **Member count** display: PASS
- **Link identity**: PASS
- **Remove identity**: PASS
- **Inactive identity rejection**: PASS — inactive identities intentionally
  cannot seed a physical-device group; this is confirmed, expected behaviour
  and not a defect

### Link-safety UX — deployed

- commit `14ee00f` — `fix: clarify physical device identity linking`
- changes: persistent helper warning adjacent to the Link Identity controls
  (`#physical-device-link-guidance`) and a strengthened SAME-physical-hardware
  `confirm()`; assertions added to `tests/test_physical_device_ui.js`
- no backend, schema, API or grouping-eligibility semantics changed; Create and
  Remove semantics are unchanged
- GitHub Actions run `34760874169` for `14ee00f`: PASS
- deployed `devicehistory.volt` SHA256
  `1d2498a353313c731d01fa2cb7f3ce75680512e16911868ce97175fba3f4d641` matches the
  repository source exactly; permissions remain `644 root:wheel`
- rollback backup retained:
  `devicehistory.volt.pre-dmbl001-linksafety-20260913-135353` (verified
  pre-deployment live SHA256
  `39291eb3614a3241329ae5ddb279fd8de4fe9d078f1cd3ef1cb6d4c5e55b9d29`, which
  equalled the predecessor commit `d83cd194` version — no live drift)
- no service restart was required or performed (the Volt view is loaded per
  request and the Python daemon does not use PHP)
- live baseline at this point: `physical_devices` = 0 and
  `physical_device_memberships` = 0; live `PRAGMA integrity_check` = ok

### Next environment objective

`192.168.20.23` is the physical Device Monitor testbed, but it is not isolated:
its `re0` interface sits on the live `192.168.20.0/24` LAN, so Device Monitor
automatic monitoring remains deliberately disabled. A genuinely isolated
interface/network remains the next environment objective before further
consequential live experimentation. No new product-backlog feature is designated
as the next implementation task.

The CrowdSec false-positive SSH brute-force defect caused by Device Monitor
service discovery is complete, deployed and validated live. After receiving a
valid SSH banner, the probe now sends a standards-compliant
`SSH_MSG_DISCONNECT` before closing. The existing `ssh_banner` service identity
and CrowdSec configuration remain unchanged.

Commit: `5d55be4` — `fix: cleanly disconnect SSH service probes`
CI: run `34684029960` — PASS.

## UI consistency and selectpicker conversion

App-wide compact status/action visual normalization and the conversion of
compact Device Monitor selects to OPNsense's `bootstrap-select`/`selectpicker`
pattern are complete and live-validated on the testbed `192.168.20.23`.

- App-wide compact status/action sizing was visually normalized; the approved
  compact status scale is 13px font / line-height 1.5 / padding 1px 5px /
  3px radius / 1px transparent border.
- Static compact selects converted to selectpicker:
  - `devices.volt` `#filter-status` (`btn-default btn-sm`)
  - `infrastructureservices.volt` `#services-type-filter`,
    `#services-status-filter` (`btn-default btn-sm`); `#services-type-filter`
    is AJAX-populated and now refreshes the selectpicker after appending types
  - `identityevents.volt` `#identity-events-status`, `#identity-events-limit`
    (`btn-default btn-xs`)
  - `scanhistory.volt` `#scan-history-limit` (`btn-default btn-xs`)
- Dynamic Physical Device `#physical-device-select` (`devicehistory.volt`)
  converted to selectpicker (`btn-default btn-xs`), initialized after DOM
  insertion and refreshed after the AJAX group list loads; option ordering
  (placeholder, existing groups, `+ Create new physical device...` last) is
  preserved.
- Live Firefox visual validation on `192.168.20.23`: PASS (Devices, Infrastructure
  Services, Identity Events, Nmap Scan History, and Device Details).
- Obsolete native-select vertical-metric CSS (heights, paddings, line-heights,
  and the `form-control input-sm` select styling) removed across the affected
  views.
- New regression coverage: `tests/test_selectpicker_static.js`; extended
  `tests/test_physical_device_ui.js`; CI step added in
  `.github/workflows/ci.yml`.
- The five affected views were deployed to the testbed with SHA256 verification
  and a rollback backup retained at
  `/root/dm-selectpicker-backup-20260918-123459`.

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

## Settings-page work (committed)

The Settings UI restructuring and About-page metadata changes described below
are present in the committed tree. There is no current uncommitted
`settings.volt` change: the worktree was verified clean at `0b6496a`. That work
included:

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
- SSH clean-disconnect focused regression: PASS
- SSH disconnect-send failure remains non-fatal after valid banner verification: PASS
- live OPNsense SSH self-probe still identifies OpenSSH correctly: PASS
- live sshd log now records `Received disconnect ... Device Monitor service probe complete [preauth]`: PASS
- no new self-generated `Connection closed by 192.168.20.254 ... [preauth]` after deployment: PASS
- GitHub Actions CI run `34684029960` for `5d55be4`: PASS

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

## AdGuard Home DNS rewrite hostname enrichment

Optional AdGuard Home DNS rewrite hostname enrichment is implemented and
validated on `v2.8-development`. The released `v2.8` tag remains unchanged.

- feature is disabled by default
- users explicitly configure their own AdGuard Home HTTPS URL, username and password
- automatic hostname precedence is:
  `AdGuard rewrite > Dnsmasq > Kea > ISC > Hostwatch`
- `custom_hostname` remains a separate user-controlled Friendly Name and is untouched
- only literal IPv4 rewrite answers are accepted
- CNAME/non-IP and IPv6 answers are ignored
- conflicting domains for the same IPv4 address are skipped as ambiguous
- scanner independently enforces HTTPS even if `config.json` is manually edited
- TLS certificate verification remains enabled through the system trust store
- HTTP redirects are disabled so the Basic Authorization header cannot be forwarded
- API/network/JSON failures are fail-soft and do not abort normal device scanning
- credentials are not placed on command lines or written to Device Monitor logs
- configuration validation rejects HTTP URLs, embedded credentials, query/fragment components and missing credentials when enabled
- live OPNsense deployment completed with pre-deployment backup and SHA256 verification
- no service restart was required; `scan_network.py` is invoked on demand through
  `actions_devicemonitor.conf`
- live authenticated AdGuard helper returned five expected IPv4 rewrite mappings
- live Device Monitor log reported `AdGuard DNS rewrites: 5 IPv4 hostname mappings`
- database hostnames for all five mapped devices matched the configured rewrites

Files changed:

- `.github/workflows/ci.yml`
- `DECISIONS.md`
- `PROJECT_STATE.md`
- `src/opnsense/mvc/app/controllers/OPNsense/DeviceMonitor/Api/ConfigController.php`
- `src/opnsense/mvc/app/models/OPNsense/DeviceMonitor/defaults.json`
- `src/opnsense/mvc/app/views/OPNsense/DeviceMonitor/settings.volt`
- `src/opnsense/scripts/OPNsense/DeviceMonitor/scan_network.py`
- `tests/test_adguard_config.php`
- `tests/test_adguard_rewrites.py`

Validation:

- Python candidate syntax: PASS
- PHP controller candidate syntax: PASS
- AdGuard Python regression suite: PASS
- existing Phase 3 Python regression suite: PASS
- PHP controller rejection tests on OPNsense, including unsafe URL components: PASS
- valid-save PHP test deliberately skipped when using the real live model
- `git diff --check`: PASS apart from existing CRLF/LF informational warnings
- live deployed SHA256 values matched the local candidate files exactly
- implementation commit `e854f0b` pushed to `origin/v2.8-development`
- GitHub Actions Device Monitor CI run `34177589841` for `e854f0b`: PASS

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

## Product backlog

- `PRODUCT_BACKLOG.md` remains the authoritative list of deferred Device Monitor work.
- `DM-BL-002` and `DM-BL-003` are complete and have been removed from the open backlog.
- `DM-BL-004` (Unbound) is functionally complete with regression coverage and
  testbed smoke validation; real-environment validation against actual Unbound
  data remains deferred because no suitable real Unbound data exists in the
  current environment (FUNCTIONALLY COMPLETE / VALIDATION DEFERRED).
- `DM-BL-001` is implemented, fully live-validated on the testbed
  `192.168.20.23`, and is no longer an open backlog feature (see the DM-BL-001
  live-validation section above).
- No open backlog items currently remain.
- Architectural constraints remain in `DECISIONS.md`; environment facts remain
  in `SYSTEM_MAP.md`.

## Hostname Source provenance

- Added persistent hostname_source provenance.
- Precedence remains AdGuard > Dnsmasq > Kea > ISC > Hostwatch.
- Friendly Name remains independent.
- UI and CSV expose hostname source.
- Migration, regression tests, PHP syntax, live deployment, GUI and CSV validation all passed.
- Implementation commit b5adf85 pushed to origin/v2.8-development.
- GitHub Actions run 34216125993: PASS.

## Hostwatch liveness fallback

- Added bounded ICMP confirmation for stale Hostwatch observations.
- Recent Hostwatch remains authoritative; no Nmap or subnet sweep is used.
- Previously-online devices get a 30-minute grace after failed probe.
- Recently-seen offline devices can recover by ping within 120 minutes.
- Both update-only and full-scan paths validated live against quiet Omada APs.
- Regression test passes on OPNsense.
- Decision 12 records the architecture change.
- Implementation commit b5a1ca4 pushed to origin/v2.8-development.
- GitHub Actions run 34223697871: PASS.

## Quiet LAN visibility discovery

- Added bounded LAN visibility priming before Hostwatch ingestion in full scans.
- LAN IPv4 address and prefix are read from `/conf/config.xml`.
- IPv4 networks larger than `/24` are rejected.
- Each usable address is probed with one ICMP echo using at most 32 workers and
  a 2-second subprocess timeout.
- OPNsense's own LAN IPv4 address is excluded.
- No Nmap scan is performed and no Device Monitor device row is created directly.
- `--update-only` remains passive and does not run subnet visibility priming.
- New regression test: `tests/test_hostwatch_lan_visibility.py`.
- Existing hostname-provenance and liveness-fallback regressions continue to pass.
- CI now includes the LAN visibility regression.
- Candidate and live `scan_network.py` SHA256 hashes matched exactly after deployment.
- Live full scans successfully probed 253 usable LAN targets.
- Previously-unseen static TP-Link devices `.250`, `.251` and `.252` are now
  present in Hostwatch and Device Monitor and are active.
- Decision 13 records the architecture and safety constraints.
- Implementation commit `f39b90c` pushed to `origin/v2.8-development`.
- GitHub Actions Device Monitor CI run `34299991865`: PASS.

## Known unresolved issues

- No known unresolved Phase 1 DHCP/DNS discovery issues remain.
- No known unresolved Phase 2 NTP/SSH/Web discovery issues remain.
- No known unresolved Infrastructure Services usability issues remain.
- No known unresolved Phase 3 infrastructure-service discovery issues remain.
- No known unresolved Friendly Name / detected Hostname separation issue remains.
- No known unresolved AdGuard DNS rewrite hostname-enrichment issue remains.

## Device lifecycle history and notes

- Added persistent device lifecycle history; lifecycle records are archived rather
  than deleted.
- A previously known MAC that returns after removal is marked `return_pending`.
  The user must explicitly choose either Start New Lifecycle or Relink Previous
  Lifecycle; returning devices are not automatically assigned a new lifecycle.
- Original lifecycle `first_seen` values and earliest-known MAC history are
  preserved.
- Added Device Details page reached from the Devices page.
- Device Details contains Device Summary, lifecycle-aware Notes, and Lifecycle
  History.
- Notes are individual timestamped lifecycle records with retained edit history.
- User-facing note removal is Archive, not Delete; archived notes remain in
  history and archived lifecycle notes are read-only.
- Device Summary online/offline status uses the device `is_active` state and is
  kept separate from lifecycle active/archived state.
- Stored UTC timestamps are displayed in the configured OPNsense local timezone,
  including daylight-saving changes.
- Removed the obsolete Device Comments popup/editor and its dead JavaScript from
  the Devices page.
- Standardised ordinary Device Monitor status labels to the approved compact
  scale — 13px font, line-height 1.5, padding 1px 5px, 3px radius, 1px
  transparent border — across relevant views.
- Device Details UI, note create/edit/archive history, ONLINE/OFFLINE display,
  legacy-popup removal, and test-data cleanup were validated live.
- Returning-device lifecycle behaviour is covered by regression tests; no live
  `return_pending` device was available for a natural UI validation.
- Python lifecycle-return regression and PHP lifecycle/comment-action regression
  suites pass.
- Final local validation: `git diff --check`, Python syntax, and lifecycle-return
  regression all pass.
- Final live validation: DeviceMonitor model, Devices API controller, and Index
  controller PHP syntax all pass; lifecycle/comment-action regression passes in
  full against the deployed model.
- Lifecycle/history implementation committed as `fc17e07`:
  `feat: add device lifecycle history and notes`.
- `v2.8-development` pushed successfully to `origin`; local and remote branches
  were confirmed synchronized.
- GitHub Actions for the pushed lifecycle/history change completed successfully.
- No known lifecycle/history implementation defect remains.
- Natural GUI validation of a real `return_pending` device remains deferred until
  one occurs; regression coverage for that workflow passes.
- `PRODUCT_BACKLOG.md` remains authoritative for deferred work; no open backlog
  items currently remain.

## v2.9 development — DM-BL-002 complete

`DM-BL-002` — Device activity and identity timeline — is implemented, deployed
and validated live on OPNsense.

Implemented:

- append-only `device_activity_events` history for meaningful state changes that
  would otherwise be lost from mutable current-state rows
- historical IP, detected hostname, hostname-source and Interface/VLAN transitions
- infrastructure-service availability/status transitions
- standalone per-device Activity Timeline page linked from Device Details
- read-only timeline API aggregating lifecycle, note/version, activity, identity,
  targeted Nmap and service-discovery history
- preserved lifecycle archive history when an archived lifecycle is relinked
- preserved identity-resolution history when a resolved identity issue is reopened
- historical Friendly Name changes with active-lifecycle synchronization
- no duplicate activity rows for unchanged Friendly Name or repeated identity-reopen
  operations
- no retroactive fabrication of historical transitions that were never stored

Validated:

- Python device-activity and infrastructure-service regressions: PASS
- PHP timeline aggregation regression: PASS
- PHP history-preservation regression: PASS
- timeline-page JavaScript regression and syntax validation: PASS
- repository `git diff --check`: PASS
- guarded live deployment with pre-deployment hash verification and rollback backup:
  PASS
- live PHP and Python syntax validation: PASS
- live `device_activity_events` table and service-status trigger initialization: PASS
- live GUI multi-source timeline rendering: PASS
- live newest-first ordering: PASS
- live Activity Timeline -> Device Details navigation: PASS

Related v2.9 commits:

- `ec36c6c` — `feat: record device activity state changes`
- `f0a4f65` — `feat: record service availability transitions`
- `dd4ce35` — `feat: add device activity timeline API`
- `bcc4205` — `fix: map edited note history in timeline`
- `0067a62` — `feat: add device activity timeline page`
- `d93ddfd` — `fix: preserve device timeline history`

The guarded live deployment retained rollback backup:

`/root/dm-bl002-predeploy-20260912-122105-85254`

## v2.9 development — DM-BL-003 complete

`DM-BL-003` — Infrastructure-service change alerts — is implemented, deployed
and validated live on OPNsense.

Implemented:

- persistent independent high-water marks for `device_services` and
  `device_activity_events`, seeded to current maxima on upgrade so historical
  rows do not generate an alert flood
- trusted alert candidates only from `verified` or `authoritative`
  infrastructure-service evidence
- configurable email controls for newly verified services, established services
  becoming unavailable, and unavailable services recovering
- generic `SERVICE_CHANGED` events retained as history-only in this version
- batched infrastructure-service email helper using the existing Device Monitor
  email transport
- non-blocking `flock` serialization for service-alert processing
- retry-safe cursor advancement that retains selected events after failed
  delivery while allowing safe-prefix housekeeping
- Recent Service Changes on the existing Infrastructure Services page
- History links from Recent Service Changes to the per-device Activity Timeline
- transition alert metadata now carries current trusted confidence, product and
  version values into the email payload

Validated:

- focused service-alert regression suite: PASS
- real Unix `flock` regression in GitHub Actions: PASS
- GitHub Actions run `34675820735`: PASS
- Recent Service Changes GitHub Actions run `34677469500`: PASS
- metadata-fix GitHub Actions run `34679430429`: PASS
- guarded initial live deployment: PASS
- initial live `service_alert_state` cursor seeded to source maxima `3282,16`: PASS
- live Infrastructure Services Recent Service Changes rendering: PASS
- live Recent Service Changes -> Activity Timeline navigation: PASS
- live Settings email controls and persisted configuration: PASS
- direct service-alert helper delivery through configured sendmail transport: PASS
- guarded live orchestration replay selected exactly one real
  `SERVICE_AVAILABLE` event and returned the cursor to `3282,16`: PASS
- post-fix recovery email displayed `Confidence: verified`, `Product: SMB` and
  `Version: max 3.1.1`: PASS
- no known DM-BL-003 implementation defect remains

Related v2.9 commits:

- `e74ce03` — `feat: add infrastructure service alert cursor state`
- `2f5d889` — `feat: read pending infrastructure service alerts`
- `c786ada` — `feat: add infrastructure service alert filtering`
- `ae2ded5` — `feat: configure infrastructure service alerts`
- `1fab4e8` — `feat: add infrastructure service alert email helper`
- `44a681b` — `feat: process infrastructure service alerts`
- `0f12c25` — `test: cover infrastructure service alert processing`
- `63f2c6d` — `ci: enable v2.9 development validation`
- `b0be04a` — `feat: show recent infrastructure service changes`
- `c00c41a` — `fix: include service metadata in transition alerts`

Guarded live rollback backups retained:

- `/root/dm-bl003-predeploy-20260912-162016-14325`
- `/root/dm-bl003-metadata-predeploy-20260912-170019-72771`

## v2.9 development — DM-BL-006 complete

`DM-BL-006` — Device Change Summary dashboard — is implemented, deployed and
live-validated on the physical OPNsense testbed `192.168.20.23` (Firefox GUI
validation PASS).

Implemented:

- read-only aggregation of existing authoritative Device Monitor history
- no parallel event-summary/event-store table
- no database schema or index changes
- no runtime database writes introduced by Change Summary
- read-only Change Summary API (GET, no state changes)
- supported time windows:
  - Since last review
  - Last 24 hours
  - Last 7 days
  - Last 30 days
  - Custom range up to 90 days
- category filtering
- pagination
- summary counters
- explicit browser-local last-reviewed marker
- localStorage key: `devicemonitor.changeSummary.lastReviewed`
- browser-local presentation of `occurred_at_utc` (UTC remains authoritative
  internally for sorting/filtering; the browser handles timezone/DST)
- stable display row numbering (newest = total; earliest filtered event = #1)
- full sticky Change Summary UI stack with sticky-gap opacity fixes

Authoritative sources used:

- device: `devices.first_seen`
- lifecycle: `device_lifecycles.first_seen` / `created_at`,
  `device_lifecycles.archived_at`, relevant `device_activity_events`
- identity: `device_identity_events.detected_at`,
  `device_identity_events.resolved_at`, relevant `device_activity_events`
- physical_device: `physical_devices.created_at`,
  `physical_devices.archived_at`, `physical_device_memberships.added_at`,
  `physical_device_memberships.removed_at`
- user_history: `device_comment_versions.action`
- infrastructure: `device_services.first_detected`, relevant
  `device_activity_events`

Intentionally unsupported / not fabricated:

- vendor-change history
- timestamped generic "device became inactive" transition where no
  authoritative event exists
- ordinary Nmap executions
- raw heartbeats
- repeated online observations
- `last_seen` refresh traffic

Validated:

- Change Summary menu/page: PASS
- read-only change aggregation: PASS
- full sticky Change Summary stack and opaque sticky-gap handling: PASS
- no row bleed / no vertical sticky jump: PASS
- Period/category filtering, counters, pagination: PASS
- browser-local timezone display (AEST observed in browser): PASS
- row numbering (newest-first; earliest filtered event = #1): PASS
- no heartbeat/raw-scan noise: PASS
- query timings: 24h ~10 ms, 7d ~11 ms, 30d ~10 ms
- production `192.168.20.254` untouched

## v2.9 development — DM-BL-005 complete

`DM-BL-005` — generic hostname-provider framework — is implemented, deployed and
validated on the physical OPNsense testbed `192.168.20.23`.

Implemented:

- centralized hostname enrichment behind a small Python provider abstraction
  (`HostnameProvider` with `name` + `lookup(device)`; plus
  `MappingHostnameProvider` for dict-backed sources)
- deterministic, centralized precedence via `build_hostname_providers` /
  `resolve_hostname` (strongest-first): AdGuard > Dnsmasq > Kea > ISC, with
  Hostwatch as the observational base value
- shared normalization (`normalize_hostname`): strip surrounding whitespace and
  a trailing dot
- provider failure isolation (a failing provider is logged and skipped; it
  cannot break the device scan)
- empty provider result is not an error and does not erase an already-resolved
  hostname
- `custom_hostname` (Friendly Name) remains independent of provider enrichment
- existing `apply_hostname_provenance` retained as a compatibility wrapper
- no schema changes

Validated:

- new hostname-provider framework regression suite: PASS
- existing hostname provenance / AdGuard / Hostwatch / device-activity /
  lifecycle-return / liveness regressions: PASS
- full Python test suite: PASS
- guarded live deployment of `scan_network.py` with hash verification: PASS
- live Python syntax check and import-based framework smoke test: PASS
- production `192.168.20.254` untouched

`DM-BL-007` (Pi-hole) can now implement the same `name` + `lookup` interface and
register in the provider list without modifying core selection logic.

## v2.9 development — DM-BL-007 complete

`DM-BL-007` — optional Pi-hole hostname enrichment — is implemented, deployed and
offline-validated on the physical OPNsense testbed `192.168.20.23`.

Implemented:

- Pi-hole provider (`get_pihole_hostnames`) using the generic DM-BL-005
  `HostnameProvider` framework (no Pi-hole logic inside `resolve_hostname`)
- Pi-hole v6 REST API, DHCP leases endpoint (`GET /api/dhcp/leases`) with
  session auth (`POST /api/auth` + `X-FTL-SID` header)
- disabled by default; settings `pihole_enabled`, `pihole_url`,
  `pihole_password` (app password) added to defaults.json, ConfigController
  validation/save, and the Settings UI
- HTTPS-only, TLS verification enabled, bounded timeout, no credential logging
- deterministic precedence: AdGuard > Dnsmasq > Kea > ISC > Pi-hole > Hostwatch
- normalization and provenance reuse the existing framework (`source=pihole`)
- provider failure / empty result never erases a retained hostname
- no schema changes

Validated:

- new Pi-hole provider regression suite (12 checks): PASS
- existing hostname-provider framework / hostname provenance / AdGuard /
  Hostwatch / device-activity / lifecycle / liveness regressions: PASS
- full Python/PHP/JS test suites: PASS
- guarded live deployment of `scan_network.py`, `ConfigController.php`,
  `defaults.json` and `settings.volt` with hash verification: PASS
- live syntax checks + import-based Pi-hole smoke test (disabled/missing-config/
  fixture lookup): PASS
- production `192.168.20.254` untouched

REAL_PIHOLE_VALIDATION = PASS (corrective TLS fix; see below).

## v2.9 development — DM-BL-007 Python 3.13 TLS corrective fix

The DM-BL-007 Pi-hole provider failed on Python 3.13 because the stock Pi-hole v6
local CA (`/etc/pihole/tls_ca.crt`) is `CA:TRUE` but lacks the X.509 Key Usage
extension that Python 3.13 strict verification requires, producing
`CERTIFICATE_VERIFY_FAILED`.

Corrective fix (Pi-hole provider only):

- in `get_pihole_hostnames()`, immediately after
  `context = ssl.create_default_context()`, clear only the
  `ssl.VERIFY_X509_STRICT` flag when available
- normal CA-chain validation (`ssl.CERT_REQUIRED`) and hostname verification
  (`check_hostname = True`) remain enabled
- no other TLS context or provider changed; no `CERT_NONE` or unverified context

Validated:

- Pi-hole provider regression suite (13 checks, incl. a strict-flag-clearing
  regression test): PASS
- hostname-provider framework / hostname provenance / AdGuard / Unbound
  regressions: PASS
- `python3 -m py_compile` and `git diff --check`: PASS
- real Pi-hole v6 validation PASS (one MAC hostname mapping returned); TLS chain
  and hostname verification remained enabled
- guarded deployment of `scan_network.py` with SHA256 match and syntax check: PASS
- production `192.168.20.254` untouched

## v2.9 development — DM-BL-004 complete

`DM-BL-004` — OPNsense/Unbound hostname enrichment — is implemented, deployed and
offline-validated on the physical OPNsense testbed `192.168.20.23`.

Implemented:

- Unbound provider (`get_unbound_hostnames`) using the generic DM-BL-005
  `HostnameProvider` framework (no Unbound logic inside `resolve_hostname`)
- authoritative local source: OPNsense Unbound host overrides (A records) and
  host aliases read from `/conf/config.xml` (no network access, no per-device
  DNS query)
- native, always-on (no enable/disable setting; no provider configuration)
- deterministic precedence: AdGuard > Dnsmasq > Kea > ISC > Unbound > Pi-hole >
  Hostwatch
- normalization and provenance reuse the existing framework (`source=unbound`)
- wildcard overrides supply no name; aliases resolve to their host override
- provider failure / empty result never erases a retained hostname
- no schema changes

Validated:

- new Unbound provider regression suite (13 checks): PASS
- existing hostname-provider framework / hostname provenance / Pi-hole / AdGuard
  / Hostwatch / device-activity / lifecycle / liveness regressions: PASS
- full Python test suite: PASS
- guarded live deployment of `scan_network.py` with hash verification: PASS
- live Python syntax check + import-based Unbound smoke test (no-source/fixture/
  precedence): PASS
- production `192.168.20.254` untouched

REAL_UNBOUND_VALIDATION = NOT PERFORMED (the implemented provider reads local
OPNsense `/conf/config.xml`, and the current testbed has no suitable real
Unbound source data).

## Infrastructure Services tabs and sticky headers

The Infrastructure Services page (Services → Device Monitor → Infrastructure
Services) now presents each service category in its own tab, with sticky page
controls and table headers.

Implemented:

- one tab per service category (DHCP Servers, DNS Servers, NTP Servers, SSH
  Servers, Web / Admin Services, File / NAS Services, Remote Access, Directory
  / Authentication, SNMP / Management, VPN Endpoints) plus a leading Recent
  Service Changes tab; categories derive from the existing `groupTitle()`
  mapping and preserve its order
- client-side tab switching (no additional API requests on tab change)
- sticky page heading, toolbar, tab strip and active table column headers,
  reusing the Change Summary sticky-header approach
- all existing data, counts, badges, status indicators, filters, buttons and
  discovery behaviour preserved; no backend, API, schema or detection changes

Files changed:

- `src/opnsense/mvc/app/views/OPNsense/DeviceMonitor/infrastructureservices.volt`
- `docs/USER_MANUAL.md`

Validated:

- full Python, Node (Bun) and PHP test suites: PASS
- JavaScript syntax build check (Bun): PASS
- Volt template compile check (Phalcon): PASS
- guarded live deployment of `infrastructureservices.volt` with hash
  verification: PASS (rollback backup retained at
  `/root/devicemonitor_backup/infrastructureservices.volt.pre-infratabs-20260920-043318`)
- LIVE_VISUAL_VALIDATION = PASS (visual QA on the `.23` testbed: tab layout,
  tab switching, and sticky controls/table headers correct; no bleed-through
  or vertical jumping; no defects observed)
- production `192.168.20.254` untouched

## Device Monitor UI consistency — Stage 1 (page headers)

Completed the first staged Device Monitor UI-consistency pass (low-risk
presentation/layout only).

- IP and MAC Conflicts (`identityevents.volt`) and Nmap Scan History
  (`scanhistory.volt`) table headers were converted from the nested-scroll
  sticky (`max-height` + `overflow-y: auto`, transparent `th`) to the proven
  Change Summary sticky-stack pattern: normal page scrolling, opaque header
  backgrounds, sticky `header.page-content-head`, gap cover, and table
  `thead th` sticky immediately beneath the controls heading.
- Removed the redundant in-page `Device Monitor – <Page>` banners from Devices,
  Change Summary, Infrastructure Services, IP and MAC Conflicts, Nmap Scan
  History and Settings; the OPNsense breadcrumb is now the primary page
  identity. Useful stats/controls/tab strips were retained.
- Removed the ordinary-page version display from the Devices header and the
  Settings page heading; version/repository/licensing information remains in
  Settings → About.
- Device Details now uses a single `Device Details` heading (redundant
  `Device Monitor –` prefix removed).
- The per-device activity page and its Device Details navigation button now
  use the visible label `Device Activity` (page heading, section heading and
  button label; internal identifiers remain `activitytimeline`).
- Device Details device-summary field order now leads with `IP Address`,
  followed by `Hostname`, `MAC Address`, `Vendor`, `Status`, `First Seen`,
  `Last Seen`, then the remaining fields (Friendly Name, VLAN, Current
  Lifecycle, Notes). Presentation-only; no backend/API/schema changes.
- Updated `docs/USER_MANUAL.md` to match the heading convention, terminology,
  field order and sticky behaviour.

Files changed: eight `.volt` views, the en_US and cs_CZ gettext catalogues,
`tests/test_change_summary_ui.js`, and `docs/USER_MANUAL.md`.

Validation:

- full Python suite: PASS
- Node (UI) suite: PASS
- PHP suite: PASS
- PHP lint / Python compile / shell syntax / gettext (`msgfmt`): PASS
- Volt template compile check (Phalcon): PASS
- `git diff --check`: PASS
- guarded testbed deployment of the eight changed `.volt` files (candidate/
  pre/post SHA256, timestamped `cp -p` rollback backups): PASS
- LIVE_VISUAL_VALIDATION = PASS (user-confirmed on the .23 testbed)
- production `192.168.20.254` untouched

## Physical Devices UX redesign (final pre-release)

Implemented the approved human-friendly Physical Devices redesign
(`v2.9-development`) without changing the underlying model, write actions,
lifecycle semantics or database schema.

- Unit 1 (read model): `getPhysicalDevicesOverview()` now enriches every
  identity with mac, friendly name, IP, hostname, hostname source, online
  state and last seen, and derives per-device current/previous identity counts,
  online/offline status and last seen. Read-only.
- Unit 2 (page): `physicaldevices.volt` now shows one panel per real-world
  device (Device Name, current identities, status, last seen) expanding to a
  Device Summary + Current Identities + Previous Identities layout.
  `devicehistory.volt` compact summary and the `devices.volt` badge wording
  were aligned; the obsolete `Grouped` badge fallback was removed.
- Translations (`en_US`/`cs_CZ`), `docs/USER_MANUAL.md` and the stale
  DECISIONS.md §18 status banner were reconciled.

Files changed: `DeviceMonitor.php`, `physicaldevices.volt`,
`devicehistory.volt`, `devices.volt`, both gettext catalogues, and the focused
UI/API/overview regression tests.

Validation: PHP suite, Node (UI) suite, PHP lint, gettext (`msgfmt -c`) and
`git diff --check` PASS locally; GitHub Actions PASS for commits `67a476c`
(run `35508985779`), `d8421ca` (run `35509262180`) and `97abb98`
(run `35509328114`).

Deployment (`192.168.20.23`, guarded): `DeviceMonitor.php`, three `.volt`
views and both compiled `.mo` catalogues deployed with candidate/pre/post
SHA256 parity and timestamped `cp -p` rollback backups (tag `uxredesign`).
Affected Volt template caches cleared; `Menu.xml` unchanged so the menu cache
was not invalidated; no service restart. Read-only DB safety counts unchanged
(`devices=8`, `physical_devices=1`, `physical_device_memberships=3`,
`device_lifecycles=8`). Unauthenticated route smoke check: HTTP 301→302, no
PHP fatal.

Authenticated GUI acceptance on `192.168.20.23`: PASS (human GUI checklist
completed against the redesigned Physical Devices page and Device Details
summary).

## v2.9 RC freeze

Release-candidate freeze is COMPLETE.

- RC candidate: `d0fe7afa587a28bf5418f75eb499f58a847b7ca6` (`v2.9-development`,
  `docs: prevent redundant finalisation checks`; final rules/documentation
  commit over the complete v2.9 implementation).
- Physical Devices GUI acceptance on `192.168.20.23`: PASS.
- Whole-plugin regression (local): PASS — Python compile, PHP lint, shell
  syntax, gettext (`msgfmt -c`), `git diff --check`, 8 PHP tests, 8 Node (UI)
  tests, 12 Python tests; 0 failures.
- GitHub Actions CI for `d0fe7af`: PASS (run `35510393264`).
- Pi-hole: COMPLETE. Unbound: FUNCTIONALLY COMPLETE / VALIDATION DEFERRED
  (non-blocking).
- Production `192.168.20.254` remained untouched until the explicit v2.9
  promotion authorisation (recorded below).

## v2.9 production promotion

Production promotion is COMPLETE.

- Frozen RC `d0fe7afa587a28bf5418f75eb499f58a847b7ca6` promoted to production
  `192.168.20.254` (OPNsense 26.7.4).
- Deployment: guarded install of 19 runtime files (17 changed + 2 new views
  `changesummary.volt`, `physicaldevices.volt`); candidate SHA256 == installed
  SHA256 for all; root:wheel, 644 (755 for `scan_network.py`).
- DB backup: `/var/db/devicemonitor/devices.db.pre-v29promo-20260921-002343`;
  17 runtime rollback backups `<file>.pre-v29promo-20260921-002343`.
- Menu cache cleared (Menu.xml changed); no service restart (daemon
  `monitor_daemon.py` unchanged); no stale Volt cache to clear.
- DB safety: pre/post counts identical (52 devices, 52 lifecycles, 607 activity
  events, 0 physical devices/comments/memberships); integrity ok.
- Technical validation: PASS. Production GUI smoke validation: PASS (human).
  Full Physical Device write workflow: PASS on testbed `192.168.20.23`;
  production write workflow not repeated (avoids modifying live data).
  Production data preservation: PASS.

Next step: none required — v2.9 is promoted to production and validated.

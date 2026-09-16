# Device Monitor — Project State

## Last updated

16 September 2026

## Current version / branch / environment

Development branch:

`v2.9-development`

Authoritative development checkout (FreeBSD 15.1-RELEASE amd64):

`/home/dmdev/src/opnsense-devicemonitor-upstream`

Previous Windows checkout (retained as fallback/reference only; no longer
authoritative):

`C:\Users\apg19\Downloads\opnsense-devicemonitor-upstream`

Primary deployment target (final runtime/deployment validation target):

OPNsense 26.7.2_2

Latest completed v2.9 implementation commit:

`14ee00f` — `fix: clarify physical device identity linking` (DM-BL-001
same-physical-device Link safety UX; deployed to OPNsense)

Latest repository commit:

`docs: record DM-BL-001 link safety deployment` (deployment reconciliation of
the `14ee00f` Link safety UX)

Workflow state:

- FreeBSD migration complete: development is now performed on the FreeBSD
  15.1-RELEASE amd64 development VM. VS Code Remote-SSH uses a
  Linuxulator-hosted VS Code Server, while normal project commands run on the
  native FreeBSD toolchain (`/bin/sh`, `/usr/local/bin/bash`,
  `/usr/local/bin/git`, `/usr/local/bin/php`, `/usr/local/bin/python3`,
  `/usr/local/bin/node`)
- previous Windows checkout
  `C:\Users\apg19\Downloads\opnsense-devicemonitor-upstream` is retained as
  fallback/reference only and is no longer authoritative; Debian WSL remains
  secondary/fallback only and is not an authoritative Device Monitor checkout
- repository-local Cline workflow rules (`.clinerules/00-project-control.md`,
  `.clinerules/10-workflow-and-finalisation.md`) committed as `0b6496a`
- workstation-local access rules (`.clinerules/90-local-remote-access.md`)
  exist on the FreeBSD VM and are excluded through `.git/info/exclude`; they
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


## Current objective

`DM-BL-001` — User-confirmed physical-device identity grouping — is implemented
and complete. Its **Create** write flow has been manually live-validated through
the GUI, and the resulting temporary test group was intentionally purged; the
live grouping baseline is `physical_devices` = 0 and
`physical_device_memberships` = 0. Its same-physical-device Link safety UX
(commit `14ee00f`) is deployed and live-confirmed.

Remaining validation scope is limited to the live **Link** and **Remove**
physical-device grouping write flows, which are **deferred/pending**. They must
not be recorded as PASS or complete until actually executed and observed, and
they must not be simulated by fabricating grouping data. They remain pending
only because no legitimate pair of MAC identities currently known to belong to
the same physical hardware is available; production history will not be
contaminated to satisfy a test. The isolated OPNsense testbed for Device Monitor
validation is now established and production-isolated (see "TESTBED environment
and production isolation" below); no new product-backlog feature is designated as
the next implementation task.

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

DM-BL-001 is complete, committed and deployed. Its remaining live GUI
validation is recorded as follows.

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

### Link / Remove flows — deferred validation (pending)

- The live **Link** and **Remove** GUI write flows remain **PENDING/unvalidated**.
- Reason: no legitimate pair of MAC identities known to belong to the same
  physical hardware is currently available in the environment.
- Production history will **not** be contaminated by fabricating a grouping to
  satisfy a test. These flows remain regression-validated only (via
  `tests/test_device_lifecycle_actions.php` and
  `tests/test_physical_device_api.php`) until a legitimate same-physical-device
  pair becomes available.
- They should be completed only when such a pair exists, preferably in the
  forthcoming isolated OPNsense testbed.

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

Establish an isolated OPNsense testbed for Device Monitor validation before
further consequential live-production experimentation. No new product-backlog
feature is designated as the next implementation task.

`DM-BL-004` — OPNsense/Unbound hostname enrichment — remains deferred because
Unbound is not currently used in this environment.

The CrowdSec false-positive SSH brute-force defect caused by Device Monitor
service discovery is complete, deployed and validated live. After receiving a
valid SSH banner, the probe now sends a standards-compliant
`SSH_MSG_DISCONNECT` before closing. The existing `ssh_banner` service identity
and CrowdSec configuration remain unchanged.

Commit: `5d55be4` — `fix: cleanly disconnect SSH service probes`
CI: run `34684029960` — PASS.

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
- `DM-BL-004` remains deferred because Unbound is not used in this environment.
- `DM-BL-001` is implemented and is no longer an open backlog feature; its Link
  and Remove live GUI validation remains deferred until a legitimate
  same-physical-device MAC pair is available (see the DM-BL-001 live-validation
  section above).
- Open backlog items are now `DM-BL-004`, `DM-BL-005`, `DM-BL-006` and `DM-BL-007`.
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
- Standardised ordinary Device Monitor status labels to 12px across relevant
  views.
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
- `PRODUCT_BACKLOG.md` remains authoritative for deferred work; open items are
  `DM-BL-004`, `DM-BL-005`, `DM-BL-006` and `DM-BL-007`.

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

## Next step

`DM-BL-001` is complete: its **Create** flow was live-validated and its
temporary test group was intentionally purged. The **Link** and **Remove** live
GUI write flows remain **deferred validation items** — they must not be recorded
as PASS or complete until actually executed, and must not be simulated by
fabricating grouping data. Complete them only when a legitimate
same-physical-device MAC pair becomes available.

The Device Monitor testbed has been migrated to `192.168.20.23` (see
"TESTBED environment and production isolation" above), so the deferred DM-BL-001
Link and Remove live GUI write-flow validation can be attempted on the testbed
instead of in production.

The migration checkpoint is complete and development runs from the FreeBSD
authoritative checkout.

`DM-BL-006` — Device change summary dashboard — is **not** the current objective.
It remains an open `PRODUCT_BACKLOG.md` candidate, to be considered only after
`DM-BL-001` validation is closed and its `PROJECT_RULES.md` feature-design gate
(Description, Benefit, UI placement, real-data testability) is satisfied.

`DM-BL-004`, `DM-BL-005` and `DM-BL-007` also remain open and deferred for their
recorded reasons (`DM-BL-004`: Unbound is not used in this environment;
`DM-BL-005`: implement only once enough independent hostname providers justify
the abstraction; `DM-BL-007`: lower priority than hostname provenance and native
OPNsense/Unbound enrichment).

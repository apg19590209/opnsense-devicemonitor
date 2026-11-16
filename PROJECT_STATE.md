# Device Monitor — Project State

## Current state

**v2.14.0 HA upgrade completed — `.252` BACKUP then `.253` MASTER (16 November 2026):** the
published archive (`abab6ad7…`, 1,792,158 bytes) was hash-verified on both nodes and installed with
`INSTALL_OK version=2.14.0 files=60 core_locales=9 pruned=2 daemon_restarted=1 unchanged=45
repaired=0` on each (`.252` backup `install-v214.xjt4CT`, `.253` backup `install-v214.idIpzT`), with
`RETIRED_CORE=nl_NL` on both. Precheck on each host reported `prunable=2` — the Dutch sidecar and the
retired `notify_identity_mail.php` only. Post-install: scanner `ecd31899…`, `config.json` and
`/conf/config.json` byte-identical to pre-state, `devices.db` integrity `ok`, daemon running, and the
Dutch sidecar, plugin-created Dutch core catalogue and identity helper all absent. `.252` completed a
normal standby cycle (BACKUP suppression, standby ageing 0/0) before `.253` was touched; `.253`
completed a MASTER cycle afterwards. Final roles: **`.253` MASTER advskew 0** and **`.252` BACKUP
advskew 100**, VIP `.254` owned by `.253`. No forced failover, CARP change, reboot, manual scan or
notification test; monitoring, recipients and notification settings unchanged on both nodes.
Rollback: the installer backups above plus the pre-install `config.json`, `/conf/config.xml`, install
record and `devices.db` copies under `/root/dm-v2.14.0-pre-*` on each node. Evidence (sealed):
`/root/dm-validation-2140/dm-v2.14.0-ha-upgrade-252-253-20261116T101536Z/`. The accepted UNVALIDATED identity limitation, D1, the four-frame webhook PASS and the
unperformed Nmap/ageing/failover-email items are unchanged by this upgrade.


**v2.14.0 PUBLISHED (16 November 2026).** Tag `v2.14.0` (annotated object
`da9c3b698634f6c1a726cca97f026d9f171444f9`) targets the approved commit
`ee38d070ae7980edbabf822b7540c9e795f7f6f6`. Release: https://github.com/apg19590209/opnsense-devicemonitor/releases/tag/v2.14.0; non-draft, non-prerelease. Assets:
`dm-v2.14.0-runtime.tar.gz` 1,792,158 bytes, SHA-256
`abab6ad7a46d2a12d9176d6752421fde88a7460395df167d096055a4e00e0207`, and `SHA256SUMS`. The published
archive was re-downloaded and matches the approved candidate byte-for-byte; the release body equals
the prepared notes. DM-BL-010's publication obligation is discharged — the header fix is now in a
published release. Issue #5 received a factual reply
(https://github.com/apg19590209/opnsense-devicemonitor/issues/5#issuecomment-6912981224) and
remains **OPEN** pending the reporter's functional confirmation; the reply states the warnings were
harmless and that no reinstall is needed for them.

**Release limitations accepted by the user; none of these tests passed.** Targeted Nmap /
new-device delivery and live ageing transitions remain **unperformed**; the isolated ageing 21/21 result is not live acceptance. **Deviation D1** is
retained: the four-frame CARP failover webhook result is genuine evidence obtained under a procedure
deviation, and the single-write A1 path remains unproven. Historical monitoring-activation
attribution remains **UNKNOWN** and cannot be established from existing evidence. Live identity
acceptance remains **UNVALIDATED** under the user's standing acceptance.

**Unchanged delivery paths — operator-confirmed, not re-tested:** generic email and generic webhook
delivery are unchanged by this release and the operator has confirmed they work (attestation only).
The only delivery behaviour this release changed is identity-conflict alerting, which is the accepted
UNVALIDATED limitation above. Failover email is tracked separately and is **unexercised**: `.252` has
no sendmail, so failover email was never producible there.


**Dutch deferral installed on `.23` (16 November 2026):** candidate
`dm-v2.14.0-runtime.tar.gz` 1,792,158 bytes, SHA-256 `c620e892a9cac0fdb126e7d64b7359a21e636e3b68d0488ac0d2c2d724abf205`,
installed under a fail-closed guard (`--check` `files=60 core_locales=9 prunable=1`). Result:
`INSTALL_OK version=2.14.0 files=60 core_locales=9 pruned=1 retired_core=1 unchanged=60 repaired=0
daemon_restarted=1`; installer backup `/var/backups/devicemonitor/install-v214.ozDITV`. Both Dutch
runtime artefacts are gone (sidecar pruned, plugin-created core catalogue retired with a rollback copy);
all 41 manifest targets and the ten shipped sidecar catalogues verify; `config.json` (`027594eb…`) and
`/conf/config.xml` (`e86a7058…`) are byte-identical; monitoring and every channel remain disabled;
`devices.db` integrity `ok`. Residual `/usr/local/opnsense/mvc/app/languages/nl_NL/LC_MESSAGES/` holds
four pre-existing manual `.pre-*` backups from earlier work, not runtime artefacts. The release
language requirement is corrected to ten shipped locales / eight translated runtime languages, the CI
runtime matrix no longer includes `nl_NL`, and historical nine-language results are preserved as
history. Live identity acceptance remains **UNVALIDATED**; D1 preserved; DM-BL-013 **OPEN**;
publication **NO-GO**. Evidence: `/root/dm-validation-2140/dm-bl-013-dutch-deferral-install-23-20261116T083540Z/` (sealed 12/12).


**Dutch deferral implemented in source/package (16 November 2026; candidate built, NOT installed):**
`release/supported-locales.sh` is now the single shipped-locale policy (`en_US cs_CZ de_DE fr_FR es_ES
it_IT pt_BR ru_RU ja_JP zh_CN`; `nl_NL` excluded) and is sourced by both `install-unattended.sh` and
`release/build-bundle.sh`, which no longer uses `find src -name '*.po'`. The Dutch `.po` is retained
unchanged in the repository as deferred source (`e3e09a11…`). Installer target counts are derived from
the payload (41 rows + 10 sidecars + 9 core catalogues = **60**, 61 fresh) instead of hardcoded.
Upgrade/repair retirement: the sidecar is removed by the existing Decision 61/62 prune
(`prunable=1`); the plugin-created core catalogue is retired only when `core-locale/<lang>.state`
records `pristine=absent` **and** the file still matches the recorded installed digest — otherwise it
is retained and reported (`NOTICE: retained core catalogue …`). Package-owned or independently
modified `OPNsense.mo` files are never deleted. New `tests/test_dutch_deferral.py` (11 cases) covers
policy, source retention, no-discovery, derived counts, manifest absence and fresh/upgrade/repair
behaviour including both retention paths. Language acceptance over the eight supported translated
languages now reports `LANGUAGE_ACCEPTANCE=PASS languages=8 gaps=0 engine=runtime failures=0`
(Dutch rendering remains technical evidence only). Candidate: `/root/dm-backups/dm-bl-013-dutch-deferral-candidate-20261116T083000Z/dm-v2.14.0-runtime.tar.gz`,
1,792,158 bytes, SHA-256 `c620e892a9cac0fdb126e7d64b7359a21e636e3b68d0488ac0d2c2d724abf205`,
59 members, deterministic rebuild identical; `--check` on `.23` reports
`files=60 core_locales=9 prunable=1`. Nothing deployed; DM-BL-013 remains **OPEN**; publication
**NO-GO**; D1 preserved; live identity acceptance remains **UNVALIDATED**.


**Dutch disposition superseded by governing operator intent (16 November 2026, documentation only):**
the user has confirmed the governing requirement — **the Dutch plugin translation must not become
available until Dutch is selectable in OPNsense**, and successful catalogue rendering does not satisfy
that condition. The recorded history is preserved unchanged: DM-BL-008a remains **closed as dropped
(on withdrawal) for the current release** on 28 September 2026 (commit `c93085d`), and the entry's
"the `nl_NL` catalogue stays in the eleven-catalogue payload" scope note is superseded by this
intent. It is **not** re-recorded as "closed by platform dependency". Read together with the O2/W2
records in `verification/locales/deferrals.md`, the current delivery contradicts the intent.

*Discrepancy (exact).* Dutch is still delivered: `install-unattended.sh:153` lists `nl_NL` in the
compile loop and installs `/usr/local/opnsense/mvc/app/languages/nl_NL/LC_MESSAGES/devicemonitor.mo`;
because OPNsense ships no Dutch core catalogue (`nl_NL` is not in `get_locale_list()`,
`/usr/local/etc/inc/system.inc:255-285`), `install-unattended.sh:163-172` runs
`merge-opnsense-catalog.sh --plugin-only` and installs
`/usr/local/share/locale/nl_NL/LC_MESSAGES/OPNsense.mo` (installed `555e23b8…`,
`pkg which` → not owned). `/var/backups/devicemonitor/core-locale/nl_NL.state` records
`pristine=absent`, so the core file is plugin-created and safe to delete. The archive carries the
catalogue through `src/**/*.po` in the bundle allow-list, not through a manifest row.

*Retained evidence, not support.* The `nl_NL` runtime result (10/10 pages, 528 keys, 0 failures,
`LANGUAGE_ACCEPTANCE=PASS languages=1 gaps=1 failures=0`) is **technical rendering evidence only**.
It is not supported-language acceptance, not one of the nine release languages, and not a reason to
**Release language requirement (corrected 16 November 2026 by operator decision).** The release
ships **ten locales** (`en_US cs_CZ de_DE fr_FR es_ES it_IT pt_BR ru_RU ja_JP zh_CN`) and requires
**eight translated languages** to render through the production
Phalcon/Volt/ViewTranslator path — `de_DE fr_FR es_ES it_IT pt_BR ru_RU ja_JP zh_CN` — with
`en_US` as the reference set and `cs_CZ` installed and checked as part of the shipped ten.
**Dutch (`nl_NL`) is source-only and deferred under DM-BL-008a**: it is not shipped, not selectable,
not a release language, and its rendering evidence remains technical only. The earlier "nine-language"
wording described the set that included Dutch and is superseded; historical runs that reported nine
languages remain valid history of that period.

*Smallest next fix (documented, not executed).* Remove `nl_NL` from the installer locale list and
from the bundle's catalogue set so it is neither compiled nor installed; keep the `.po` in the
repository as deferred source; keep the `--plugin-only` merge fallback for genuinely core-less
locales; and let the existing install machinery delete the plugin-created core file on upgrade
(`pristine=absent`), while **never** touching package-owned `OPNsense.mo` files. Documentation now
states Dutch as deferred. Re-open only if OPNsense core offers `nl_NL`.


**Core-catalogue "drift" corrected in the records — expected core-domain wording (16 November 2026,
documentation only):** the seven reported entries are message ids carried by both the plugin and the
OPNsense core catalogues with different wording; Decision 35's core-first merge preserves the core wording
by design, so they are **expected core-domain wording differences**, not missing translations or
unresolved product drift. `de_DE State`→`Zustand`, `es_ES Language`→`Lenguaje`, `es_ES Virtual IP`→`Virtual IP`,
`ru_RU Unknown`→`Неизвестный`, `ru_RU Virtual IP`→`Виртуальный IP-адрес`, `ru_RU minutes`→`мин`,
`ja_JP State`→`ステート`, `zh_CN Virtual IP`→`虚拟IP` in the core (`lang.query()`) domain; the sidecar
(`devicemonitor_t()`) domain keeps the plugin values. Canonical invocation
`python3 tests/test_language_acceptance.py --engine runtime --views <abs source views>` (default
`--installed-po /usr/local/opnsense/mvc/app/languages`) returns
`LANGUAGE_ACCEPTANCE=PASS languages=9 gaps=1 engine=runtime failures=0`, with the seven as warnings. The
earlier fatal classification came from pointing `--installed-po` at the source tree, which ships no
compiled `.mo`, so plugin coverage was unknown. These seven are **removed from the release-blocker list**
under Decision 35. `--strict` findings remain supplemental diagnostics; `nl_NL` selectability and any
other language defect are **not waived**. Evidence (sealed): `/root/dm-validation-2140/dm-bl-013-catalogue-drift-correction-20261116T072923Z/CORRECTION-ADDENDUM.md`. No catalogue
edit, package regeneration, installation, commit, push or publication.


**Ordering-fix candidate installed on `.23` (16 November 2026):**
`dm-v2.14.0-runtime.tar.gz` 1,841,827 bytes, SHA-256 `93c673d9fe87b767fb809593ad366bb4e09d82fd507607216c27f57db5810ad6`, installed under full
preflight and the single conditional guard; `--check` reported `files=62 prunable=0` before and
installation returned `INSTALL_OK version=2.14.0 files=62 core_locales=10 pruned=0
unchanged=61 repaired=0 daemon_restarted=1`. All 41 manifest targets hash-match; the installed
scanner is `ecd31899abb6365960d48c8b347c27e217f8d0641512e062b715ee208d3d7090`; the retired
identity-email helper remains absent and is absent from the new 64-line install record.
`config.json` (`027594eb…`) and `/conf/config.xml` (`e86a7058…`) are byte-identical; monitoring
stayed disabled and every channel stayed off; `devices.db` and the hostwatch DB both passed
`integrity_check` and row counts were unchanged (26 devices / 2 identity events / 0 Nmap history);
no scan, Nmap, email or webhook occurred. Installer backup:
`/var/backups/devicemonitor/install-v214.wH9DgM`. Evidence directory (sealed 13/13):
`/root/dm-validation-2140/dm-bl-013-identity-event-order-install-23-20261115T222532Z/`. **Live identity acceptance remains UNVALIDATED** by user decision and is never recorded as
PASS. Email/webhook/external delivery, live ageing, direction-A procedure compliance (D1) and the
five-language core catalogue drift remain open. DM-BL-013 remains **OPEN**; publication **NO-GO**.


**Ordering-fix candidate prepared (15 November 2026, not installed):**
`/root/dm-backups/dm-bl-013-identity-event-order-candidate-20261115T111500Z/dm-v2.14.0-runtime.tar.gz`
— 1,841,827 bytes, SHA-256 `93c673d9fe87b767fb809593ad366bb4e09d82fd507607216c27f57db5810ad6`,
59 members, 41 manifest rows, deterministic rebuild identical, installed scanner would be
`ecd31899…`. Regression extended with a `full_scan`-level case that delivers the cycle's own
rotation event and fails against a late-snapshot copy of the scanner (verified). `--check` on `.23`:
`files=62 prunable=0` (the identity-email helper is already absent), which is the expected result.
Earlier candidates are byte-identical. **Installation of these bytes is not authorised**; the
`.23`-only plan with stop gates and rollback is `INSTALL-AND-ROLLBACK-PLAN-23.md` in that directory.
Live identity acceptance remains **UNVALIDATED** (user-accepted, not a release blocker); email/webhook/
external delivery, live ageing, direction-A procedure compliance (D1) and the core catalogue drift remain
open. **Nothing deployed**; DM-BL-013 **OPEN**; publication **NO-GO**.


**Rotation-alert ordering defect (15 November 2026, source-only fix, not deployed):**
`identity_event_start_id` — the high-water mark `get_new_high_identity_events()` filters on — was
read **after** the device loop (`scan_network.py`), so the high-severity `IP_IDENTITY_CHANGED` event
that `detect_mac_rotation()` records inside that loop was never eligible for notification. Rotation
events were therefore permanently silent-to-alert, while still being recorded. **Correction to the
earlier finding:** the rotation path was never silent — it records a high-severity event; what was
broken was alert selection. **Affected versions (source evidence):** `v2.12.1` (rotation call at
`:9182`, snapshot at `:9224`) and the 2.14.0 line, including the installed `cd82a60c…`;
`v2.13`/`v2.13.2` contain the snapshot but no rotation classifier, so they are not affected.
Fix: take the snapshot before any producer runs; `tests/test_identity_event_capture_order.py`
reproduces the defect and pins no-replay, dedupe, severity filtering and the producer ordering.
**Live identity acceptance remains UNVALIDATED** and is recorded as not a release blocker; that
decision stands. Evidence wording corrected: an empty `mailq` and the absence of a mail process at
inspection time do **not** prove no transient email attempt occurred; the zero-identity-email
claim rests on the structural absence of the email leg, with external email delivery **UNTESTED**.
**Nothing is deployed**, and D1 remains recorded.


**Source-only correction — identity-conflict alerts restored to webhook-only (15 November 2026):**
commit `a12ede8` had re-added an identity-conflict email leg without a recorded decision,
contradicting `DECISIONS.md` 36. Option A withdrew it: `should_send_identity_mail()`,
`send_identity_mail()` and `notify_identity_mail.php` are removed; the "Also email identity
conflict alerts" checkbox, its JS load/save wiring and the catalogue strings exclusive to it are
removed; `identity_email_enabled` remains a stored preference that `ConfigController` preserves
untouched; the identity webhook keeps its gates, high-severity filter, HA suppression and
`notified_at`-on-success-only semantics. New-device email/webhook, scan-result email and targeted
Nmap were deliberately left unchanged; Nmap's dependence on `email_enabled`/`email_to` is
implementation coupling, not a recorded requirement, and is documented separately in the
identity/Nmap procedure. Manifest drops from 42 to 41 rows and the installer guards, pinned inputs
and runtime-manifest digests were regenerated with the shipped tooling. `install-unattended.sh
--check` on `.23` reports `CHECK_OK … files=62 … prunable=1` with the prune plan naming only
`notify_identity_mail.php`, so upgrades and repair installs retire the helper through the existing
Decision 61/62 record-diff rule with no new mechanism. **Nothing is deployed**: expected
identity-conflict email count after the fix is **zero**, the identity/Nmap and live-ageing criteria
remain **UNTESTED**, D1 remains recorded, and publication stays **NO-GO**.


Last updated: 13 November 2026

Branches: `main` (HEAD `e9ec5486a8cc9e87e3b6d3cf6098f26ed15e1370`, the Device Monitor
2.14.0 source line including the DM-BL-009 closeout documentation and the integrated DM-BL-010
catalogue-header correction), `release/2.13` (HEAD `6bd122e`) and
`fix/pruning-remediation-20261103` (HEAD `b2c74fc`, the 2.13.3 remediation). The
`integration/dm-bl-009-reconcile-20261105` history was fast-forwarded into `main` on
7 November 2026. The latest published GitHub release is **v2.14.0** (published 16 November 2026); v2.12.1 was the latest before it.
`baseline/2.12` (`d04739a`) holds the recovered pre-HA 2.12 tree;
`feature/async-db-v2.11` (`0ad95b0`) is the historical v2.11 development branch.
The active development checkout is `fix/dm-bl-012-uninstaller-20261112` at
`22884cdbc75204182ab214c8e38947c4aee723f1`; the HA role-visibility changes described below remain
uncommitted in that checkout.
The DM-BL-010 catalogue-header correction is integrated into `main` by PR #7 at
`e9ec5486a8cc9e87e3b6d3cf6098f26ed15e1370`; its exact-candidate Phase 1 repair/acceptance run
passed on `.23`. It is not tagged or published: v2.12.1 remains the latest release and 2.14.0 is
still unpublished. The reviewed documentation candidate is
`4611447089e2482a0c6af7a1844e9f6fa16c84d1` (tree
`e3d551967fcd673cefd9031448c0e1791db2a2ab`), one docs-only commit ahead of `main`; its CI run
`42368818807` passed. A validation-closure pass on 7 November 2026 then strengthened the monitoring
guard, added Phase 2A and production-engine language evidence, and changed publication to **NO-GO**
pending the then-open DM-BL-011/012/013 gates. DM-BL-011 was **CLOSED** on 13 November 2026 by
explicit operator acceptance of the historical byte-evidence limitation; no historical byte-identity
claim is made. DM-BL-012 was closed on 12 November 2026; DM-BL-013 remains **OPEN**.
A second P1 run on 15 November 2026 proved the daemon-triggered CARP failover webhook on both nodes and both legs (4 frames, isolated capture, full restoration) but deviated from `P1-PROCEDURE-REV1.md` §2.5: it applied the A2 `.252 100→0` write after A1 had transferred the VIP, where the procedure required a single revert of `.253`. The four-frame notification evidence stands; the run is not a clean procedural qualification and the single-write A1 path remains unproven. See the P1 run 2 entry and reconciliation package referenced in `PRODUCT_BACKLOG.md` DM-BL-013. A P1 transition attempt on 14 November 2026 stopped before any VIP change: the executor called the unregistered action name `vip.configure`; the registered action is `interface vip configure` (stock page path). This is an executor-call defect, not a node or configd fault; restoration was re-confirmed with a corrected XML comparator. See `PRODUCT_BACKLOG.md` DM-BL-013 (15 November 2026 entry) and `/root/dm-validation-2140/dm-bl-013-configd-diagnosis-20261115T0815Z/ROOT-CAUSE-REPORT.md`. A controlled production CARP transition (14 November 2026) closed the daemon-triggered failover-webhook *demotion* path and stable-cycle suppression only; its return leg produced one frame, not two, and no `.253` frame (reconciled in `ADDENDUM-1-RECONCILIATION.md`). Email and the remaining delivery/UI criteria are still open (see `PRODUCT_BACKLOG.md`, DM-BL-013). The final release commit must include the
current uncommitted records, the guard fix and its CI wiring, be reviewed, integrated without
rewriting history, and pass exact-SHA CI.

On 8 November 2026 an expressly authorised real-host uninstall/fresh-install attempt ran on `.23`
with the exact 2.14.0 candidate. The install and registration checks passed, but the run was aborted
before reboot after a configuration save enabled monitoring and caused one scan to probe
`.252`/`.253`. The daemon was stopped and the verified recovery restored the accepted 2.14.0 data,
configuration, 63-target manifest and disabled settings. DM-BL-012 remained **OPEN** until the
12 November 2026 operator-accepted `.23` lifecycle closure; the 8 November attempt did
not establish reboot persistence or an authenticated UI pass. Two uninstaller defects were found:
the menu-cache path is wrong and `php-fpm` is not a service on this OPNsense host. See
`verification/DM-BL-012-FRESH-23-ATTEMPT-20261108.md`.

### 2.14.0 — main source and `.23` deployment; not yet published

| Item | Value |
|---|---|
| Branch | `main` at `e9ec5486a8cc9e87e3b6d3cf6098f26ed15e1370`; PR #6 fast-forwarded the reviewed `integration/dm-bl-009-reconcile-20261105` history from `d5d73ed` to `282517744260920b18c9217efd09ce738af21d70`, and PR #7 added the DM-BL-010 catalogue-header correction |
| Payload | `release/v2.14.0-runtime.manifest`, 42 rows; 63 generated targets on an upgrade and 64 on a fresh install |
| Bundle | `dm-v2.14.0-runtime.tar.gz`, 1,729,177 bytes, SHA-256 `90afa55dd826c0dc3be8a23902b809baa465e25191dc372dc6cc2ef4e57fc243`; 60 members; four byte-identical builds. The earlier 1,725,593-byte `5149bfd4…` main-integration bundle and its evidence remain preserved as superseded |
| Lifecycle candidate | `dm-v2.14.0-runtime-residual-repair.tar.gz`, 1,731,225 bytes, SHA-256 `3675c7271ad3bbd3a04c325c9f7b03bfea80a19e6ff913c2c3114b78eaa46891`; 60 members. It supersedes the preserved `772a6660…` menu-cache/php-fpm repair candidate and adds uninstaller removal of `devicemonitor_locale.inc` and `actions_devicemonitor_update.conf`. `BUNDLE_DETERMINISM=PASS` (two clean checkouts, canonical headers, recorded digest) |
| Timestamp candidate | `dm-v2.14.0-runtime.tar.gz`, 1,735,321 bytes, SHA-256 `ecaecb04814af41479e1b6e614b05a63de9676158870d749ab51b63d5eee87df`; 60 members. It adds canonical UTC presence/service timestamps, historical-zone/DST-aware conservative reads of legacy mixed rows, fall-back-safe cutoffs, and the UTC/AEDT/DST/expiry regressions. Two independent stage builds were byte-identical. It was installed on production CARP BACKUP `.252` on 13 November 2026 and observed through two normal cycles; see the `.252` section below. The `b5ffae79…` and `19f7583a…` timestamp-review candidates, `3675c7271…` lifecycle candidate and all earlier artifacts remain preserved. |
| HA visibility candidate | `dm-v2.14.0-runtime.tar.gz`, 1,795,230 bytes, SHA-256 `e7dcb7f88ec8f98ca4455542f2106416e2447740c95c818ff2cfdd31d4ef3124`; 60 members. It adds the persistent HA/node notice, reuses the existing `getcarpstatus` source for both Devices and Settings, distinguishes detected role from effective mode, exposes the exact BACKUP-paused activities including automatic targeted Nmap, and clears stale status on refresh failure. The reviewed build removes the obsolete Settings loader, ignores superseded responses, initialises refresh state before first use, parses the actual daemon scan-log format with bounded reverse history lookup, separates missing/unreadable history and API fetch failure, and reports fail-open observation only from a confirmed backend detector-failure state. Two independent stage builds were byte-identical. It was installed on testbed `.23` on 13 November 2026 and has not been installed on production or live-CARP-tested; the intervening `2dab1385…`, `709288cd…`, `e789fb96…` and `f51f1adf…` candidates and all earlier artifacts remain preserved as superseded. |
| CI | Exact-candidate CI run `42358468231`: **success**; exact-main CI is recorded separately below. Linux CI does not execute the FreeBSD installer-jail or live-service scenarios |
| Reviewed-candidate CI | Run `42368818807` at `4611447089e2482a0c6af7a1844e9f6fa16c84d1`: **success**. Logs repeat the release-input, manifest, locale-merge, ten-case predecessor and bundle-determinism passes and reproduce 1,729,177 bytes / `90afa55d…`. The native runtime matrix remained skipped on the GitHub runner for missing assets; a separate local production-engine run subsequently passed (see below) |
| Main integration CI | Exact-main workflow-dispatch run `42359428985` at `e9ec5486a8cc9e87e3b6d3cf6098f26ed15e1370`: **success**. Logs report `RELEASE_INPUTS=PASS cases=7` and `V2140_RELEASE_MANIFEST=PASS`; the DM-BL-010 candidate bundle is 1,729,177 bytes / `90afa55d…`. Historical DM-BL-009 run `42342362864` remains recorded in `verification/MAIN-INTEGRATION-2.14.0-20261107.md` |
| Native runtime closure | **PASS** on 7 November 2026: `LANGUAGE_ACCEPTANCE=PASS languages=9 gaps=1 engine=runtime failures=0`, 10 pages and 490 keys per language through Phalcon/Volt/ViewTranslator. Report: `/root/dm-validation-2140/language-runtime-2.14.0-20261107.md`. The `nl_NL` GUI-selector gap remains documented; browser layout and wording quality are separate |
| Preserved from main | Scan-loop/state-change alert refactor, MAC-rotation policy, repeat reminders, identity email, configuration visibility, non-HA fail-open CARP behaviour and the deployment verifier |
| Preserved from 2.13.x | HA/CARP role gating, O4 ageing and standby hygiene, installer pruning evidence, repair semantics, pinned inputs, deterministic bundling and rollback verification |
| Local validation | The corrected candidate builds reproducibly; focused reconciliation, installer/pruning, Python, PHP, JavaScript, catalogue and both language-engine suites passed locally. All five upgrade FreeBSD installer-jail scenarios passed on 6 November: `check`, `install`, `repair`, `rollback` and `failclosed`. The isolated `fresh` and `fresh-rollback` scenarios also passed on 6 November: 64 targets, a 64-row record, no database/configuration, a running daemon and complete restoration to empty state after an injected failure. Rollback restored all 63 upgrade targets, the prune fixture, the record and 19 core-locale state/pristine files with zero conflicts or failures |
| Deployment | `.23` only: OPNsense `26.7.8_2`; Device Monitor 2.13.3 → 2.14.0 using the normal upgrade path (`FRESH=1` not used). The execution record is `verification/DEPLOY-2.14.0-23-PLAN.md` |
| Installation | Phase 1 exact-candidate repair: `INSTALL_OK version=2.14.0 files=63 core_locales=10 pruned=0 backup=/var/backups/devicemonitor/install-v214.Uwwqu1 daemon_restarted=1 unchanged=63 repaired=0`; see `verification/PHASE1-EXACT-CANDIDATE-23-20261107.md` |
| Real-host fresh-install attempt | **ABORTED before reboot on 8 November 2026; recovered to the accepted 2.14.0 state.** `CHECK_OK … predecessor=fresh files=64 core_locales=10` and `INSTALL_OK … files=64 core_locales=10` passed. A concurrent configuration save set `enabled=1`; one scan probed `.252`/`.253`; no email/webhook delivery occurred. Daemon stopped and recovery restored `027594eb…` / `796d28c7…`, 63 targets and `enabled=0`. DM-BL-012 remained OPEN until the 12 November 2026 operator-accepted `.23` lifecycle closure (see the closure section below). Evidence: `verification/DM-BL-012-FRESH-23-ATTEMPT-20261108.md` |
| Live rollback validation | **PASS**: preparatory restore to 2.13.3 used `JeYC44`; a fresh 2.14.0 test installation created `zGJRuq`; the live successful-install rollback restored 61 targets and the 2.13.3 record with `ROLLBACK_SUMMARY=restored=31 skipped=32 conflicts=0 failed=0` and core-locale `restored=19 removed=0 conflicts=0 failed=0`; the final 2.14.0 reinstall created `qMPS7n` |
| Acceptance | Phase 1 PASS: 42/42 manifest rows and 63/63 installer-plan/record targets matched digest/mode/owner/group; 21 `.mo` locale rows plus two `.po` source rows; ten core and eleven sidecar catalogues warning-free; nine available pristine translations preserved and `nl_NL` plugin-only as expected; `/conf/config.xml` `e86a7058…`, Device Monitor configuration `027594eb…`, logical DB `d7ed7f81…` and physical DB `796d28c7…` unchanged; SQLite `ok`; daemon `16776` → `18384` alive at 60 seconds; configd `728` → `328`; monitoring disabled with no WAL/SHM or `2525` listener. Operator-supplied authenticated evidence received 7 November 2026 (Australia/Sydney) shows Device Monitor `v2.14.0` and `v2.14.0 Features and Enhancements` in the About screenshot; the operator confirms Devices loads without error. No exact observation time was recorded |
| State after §9.3 rollback validation (historical checkpoint) | PASS: Device Monitor `2.14.0`; 63 targets and 63-row record `d891ce68…`; database `c17874a7…`, Device Monitor configuration `027594eb…` and OPNsense configuration `c2ce5800…` unchanged at that checkpoint; daemon PID `49278` → `74577`; configd PID `30312` → `32439`; daemon alive after five seconds; monitoring `enabled=0`; no WAL/SHM. The later bounded §9.4 exercise changed the physical database representation to the consistent snapshot `796d28c7…` and retained `15ce9e6c…` as the OPNsense configuration at that historical checkpoint. The operator subsequently accepted `e86a7058…` as the Phase 1 baseline, and Phase 1 retained it unchanged |
| Backups | Pre-install `/root/dm-pre-2140/runtime-data.tgz`, 7,632,213 bytes, sha256 `ff7873ce0fbc1826663aa86c3271014c9c2ad3cdb3bd7b4eacce164a4a63753e`, containing 61 payload files, 19 core-locale files, record, consistent database and configuration; installer backups `/var/backups/devicemonitor/install-v214.JeYC44`, `install-v214.zGJRuq` and `install-v214.qMPS7n`; pre-mutation recovery point `/root/dm-validation-2140/rollback/20261105T231610Z` |
| Historical pre-Phase-1 acceptance / residual gates | An earlier operator-supplied About/Features screenshot passed at that prior checkpoint, without browser Network capture. Separate Phase 1 authenticated evidence was received later on 7 November 2026 (Australia/Sydney), as recorded in the Acceptance row. Live successful-install rollback is **PASS**. The isolated fresh-install and fresh-rollback jail paths are **PASS**. The bounded §9.4 monitoring exercise is **COMPLETE / ACCEPTANCE PASS**; further execution is **unauthorised**. Live evidence covers two scheduled inventory scans, direct DMTEST-only service discovery, scope-limited visibility probing and a live-observed `notified_at` schema mutation before restoration. The two SMTP messages came from direct PHP helper calls, not daemon-generated delivery; identity/service/new-device/aged/retired and fresh-host refusal were copy-only fixtures. Under the revised 7 November objective these were then-open publication blockers, not deferred limits: DM-BL-011 (historical database-byte identity), DM-BL-012 (real-host `FRESH=1` and plugin lifecycle) and DM-BL-013 (full monitoring lifecycle/HA/delivery). DM-BL-011 was **CLOSED** on 13 November 2026 by explicit operator acceptance of the historical byte-evidence limitation, with no byte-identity claim; DM-BL-012 was **CLOSED** on 12 November 2026 by explicit operator acceptance; DM-BL-013 remains **OPEN**. DM-BL-009 is **CLOSED** because its `main` integration criterion is met |
| §9.4 monitoring execution | **COMPLETE / ACCEPTANCE PASS — further execution is unauthorised.** The supervised run completed exactly two scans (`3497 → 3499`) with DMTEST-only discovery, loopback SMTP helpers and copy-only fixtures; final acceptance restored monitoring `enabled=0`, healthy services, no test processes/listener and no WAL/SHM. Configuration `027594eb…`, record `d891ce68…`, OPNsense configuration `15ce9e6c…` and all 19 core-locale files are byte-identical. The `notified_at` migration was observed live before restoration. The original database was `c17874a7…`; the consistent snapshot and historical restored file were `796d28c7…`, with identical logical digest `10460718…`, clean integrity/quick checks and 21 schema tables; the trace is in `verification/monitoring-validation/EXECUTION-20261106.md`. No retained file contains the original bytes, so the completed exercise cannot be claimed as physically byte-identical. The guard was corrected to stop and verify writers before capture, preserve original database/WAL/SHM bytes separately, retain the SQLite snapshot as an independently verified fallback, archive the post-state database, and verify restored bytes/metadata/schema/data/integrity against the original recovery copy; snapshot equivalence cannot satisfy original-byte identity. All 35 mock/disposable-copy tests pass, but this does not retroactively prove the historical bytes. §9.4 remains paused; issue #5 remains **OPEN**. Historical byte identity is tracked as **DM-BL-011**, which was **CLOSED** on 13 November 2026 by explicit operator acceptance of the historical byte-evidence limitation; no historical byte-identity claim is made. |

### DM-BL-010 — 2.14.0 catalogue-header correction (CLOSED 16 November 2026; release tracked separately)

| Item | Value |
|---|---|
| Status | **Integrated in `main`** by PR #7 at `e9ec5486a8cc9e87e3b6d3cf6098f26ed15e1370`; **not published**. Exact-main CI run `42359428985` passed; branch CI run `42368818807` passed at reviewed candidate `4611447`; and the exact candidate passed Phase 1 on `.23`, including operator-supplied authenticated About/Features evidence received 7 November 2026 (Australia/Sydney). DM-BL-010 is **CLOSED** for implementation and validation; the fix is **not published**, and the remaining publication obligation is carried by the release tracker below, not by this defect |
| Base / candidate source | Based on `46370688fb6891a049929f2498ae62bc52b17b3e`; retained jail evidence predates the branch commit and records `CANDIDATE_SOURCE=worktree`; clean committed-tree bundle determinism passed |
| Defect | The reporter's three non-fatal `msgfmt` header warnings were reproduced exactly in the pre-repair merge path; they name `PO-Revision-Date`, `Last-Translator` and `Language-Team` and do not fail compilation |
| Correction | Catalogue generation fills only absent/empty generated header fields from real plugin metadata; existing core metadata/translations and `msgfmt --check` are preserved, incomplete/malformed inputs abort, and stderr is not broadly suppressed |
| Regression | `LOCALE_MERGE=PASS`; `RELEASE_INPUTS=PASS cases=7`; `V2140_RELEASE_MANIFEST=PASS`; `CI_CONFIG=PASS cases=7`; `CATALOGUE_DETERMINISM=PASS cases=2`; `BUNDLE_REPRODUCIBILITY=PASS cases=9`; `BUNDLE_BUILD_SAFETY=PASS cases=8` |
| Predecessors | `UPGRADE_PREDECESSORS=PASS passed=10 skipped=0`, now including the published `v2.12.1` tag; its own database code creates the starting schema |
| Candidate bundle | `dm-v2.14.0-runtime.tar.gz`, 1,729,177 bytes, SHA-256 `90afa55dd826c0dc3be8a23902b809baa465e25191dc372dc6cc2ef4e57fc243`; four builds (`build-a`…`build-d`) are byte-identical |
| Superseded evidence | Previous 2.14.0 main-integration candidate: 1,725,593 bytes, SHA-256 `5149bfd41e5842a144a9d1280c008511f20f3783932eca9beb1f48fca6173f5f`; retained, not overwritten |
| Jail validation | Existing live-2.14.0 predecessor `check`/`install`/`repair`/`rollback`/`failclosed` and fresh `fresh`/`fresh-rollback` scenarios pass. A published-v2.12.1 predecessor `check`, `install` and `rollback` pass: all 56 archive members match the tag, `devices.db` and `config.json` remain byte-identical on install, the modified legacy file is retained, and rollback restores all 63 targets, the record and 19 core-locale files |
| Evidence | `/root/dm-validation-2140/dm-bl-010-20261107/`, `/root/dm-validation-2140/phase1-90afa55d-20261107T104937Z/`, `/root/dm-backups/dm-bl-010-candidate-20261107-075441/`, `verification/DM-BL-010-CATALOGUE-HEADERS-20261107.md` and `verification/PHASE1-EXACT-CANDIDATE-23-20261107.md` |
| Live / release state | `.23` now runs the exact candidate through the same-version repair (`unchanged=63`, backup `install-v214.Uwwqu1`), with configuration, logical/physical database bytes, SQLite integrity and 19 core-locale state files preserved. Monitoring/notifications stayed disabled and services remained healthy. Operator-supplied authenticated evidence received 7 November 2026 (Australia/Sydney) covers About/Features and Devices loading only. Published v2.12.1 and all existing tags/assets are unchanged; 2.14.0 remains unpublished |

DM-BL-010 is **CLOSED** as of 16 November 2026; its correction is not yet published, which is a release-tracking matter rather than an open coding task. Phase 1 closed the exact-candidate
live repair, warning-free current-catalogue merge, translation-preservation, target/data/config,
SQLite, service and operator-supplied authenticated About/Features/Devices-loading gates. It did
not close the historical database-byte limitation (DM-BL-011), real-host `FRESH=1`/plugin lifecycle
(DM-BL-012) or the broader monitoring lifecycle/HA/delivery (DM-BL-013). The native runtime language
matrix was separately validated on 7 November. The live run had no sparse-header delta because all
63 targets were already byte-identical.

### Validation-closure checkpoint (7 November 2026)

| Item | Current result |
|---|---|
| Native runtime matrix | **PASS** — nine languages, ten pages and 490 keys per language through the production Phalcon/Volt/ViewTranslator path; `nl_NL` selector gap remains documented. Report: `/root/dm-validation-2140/language-runtime-2.14.0-20261107.md`; explanation: `verification/LANGUAGE-ACCEPTANCE-GAP-20261107.md` |
| Phase 2A guard rehearsal | **PASS** — real DB/WAL/SHM capture, mutation detection, snapshot-equivalence rejection, exact-byte restore and post-state archive. The pass found and fixed a snapshot-side-effect defect; all 35 guard tests pass locally. The suite is now wired into the validation-only CI workflow with exact `Ran 35 tests`/`OK` assertions; that new step still needs an exact-SHA run. Evidence: `verification/monitoring-validation/PHASE2A-DISPOSABLE-20261107.md` and `/root/dm-validation-2140/phase2a-guard-20261107T123250Z/` |
| Historical original bytes | **Not recovered — accepted limitation** — 128 physical database candidates and 67 archives were checked read-only; no `c17874a7…` copy exists in the searched evidence. A supplemental `/root/dm-backups` scan found no database candidate or `devices.db` archive member. Common SQLite copy transformations on a retained `796d28c7…` copy did not reproduce the hash. DM-BL-011 was **CLOSED** on 13 November 2026 by explicit operator acceptance of this historical evidence limitation; no byte-identity claim is made. Evidence: `verification/DM-BL-011-BYTE-RECOVERY-20261107.md` |
| Phase 3 infrastructure | **Still requires a disposable VM** — no `kern.vmm`, `/dev/vmm`, `vm-bhyve`, disposable VM image or approved external hypervisor is recorded. One expressly authorised `.23` attempt was aborted and recovered; `.23` remains the existing integration testbed rather than a reusable fresh-install target. `.252`/`.253` remain prohibited. Exact setup/test plan: `verification/PHASE3-DISPOSABLE-OPNSENSE-VM-PLAN-20261107.md` |
| Publication | **2.14.0 PUBLISHED on 16 November 2026** (see the v2.14.0 publication entry at the top of this file). DM-BL-013 remains **OPEN** for unperformed delivery/ageing tests and deviation D1; DM-BL-011 was **CLOSED** on 13 November 2026 by explicit operator acceptance of the historical byte-evidence limitation, and DM-BL-012 was **CLOSED** on 12 November 2026 by the operator-accepted `.23` lifecycle validation. DM-BL-013 needs approved external-delivery tests and the remaining unperformed delivery/ageing checks; DM-BL-010 is CLOSED (integrated, not yet published) and its publication is carried by the 2.14.0 release itself, alongside the final release controls. The consolidated plan is `verification/VALIDATION-CLOSURE-2.14.0-20261107.md` |
| Issue #5 | **OPEN** — the reporter confirmed successful published v2.12.1 installation and version display; service health and normal page loading remain for reporter confirmation. This is external, does not require 2.14.0 publication, and no reply has been posted |

### §9.4 residual-gap classification

| Gap | Classification | Rationale |
|---|---|---|
| Physical DB byte identity (`c17874a7…` → `796d28c7…`) | **Closed: DM-BL-011** (13 November 2026) — explicit operator acceptance of the historical physical-byte limitation; recurrence is corrected in the guard | Logical digest, schema, integrity and row counts match, so data integrity is not in question. The live replacement is traced to the historical guard's `796d28c7…` snapshot and its `08:32:04Z` recovery copy; that guard's physical expectation was the snapshot hash, not the original live hash. The original `c17874a7…` bytes were never retained, leaving the internal header/page delta unverifiable. A 7 November disposable Phase 2A rehearsal found and fixed a snapshot-side-effect defect, then passed separate DB/WAL/SHM capture, mutation detection, exact-byte restore, snapshot-equivalence rejection and post-state archiving; all 35 guard tests pass. A repeat search of retained `/root` and `/var/backups/devicemonitor` database files found no `c17874a7…` copy. The guard protects future runs but cannot retroactively prove the completed exercise. Closure accepts this historical limitation and makes no byte-identity claim. |
| Live `FRESH=1` and real OPNsense plugin registration/lifecycle | **Closed: DM-BL-012** (12 November 2026) | The disposable jail and copy-only fixtures prove call boundaries, not reboot persistence. A real-host fresh install on `.23` passed registration and startup on 8 November 2026 but was aborted before reboot after monitoring was enabled, then recovered. On 12 November 2026 the operator explicitly superseded the disposable-VM gate and accepted the residual risk. The `772a6660…` menu-cache/`php-fpm` candidate completed uninstall, fresh-state reinstall, registration, one reboot, cache/menu regeneration, data persistence and operator-attested authenticated UI checks on `.23`. The `3675c7271…` residual-cleanup candidate then repeated uninstall/reinstall and was directly tested; reboot persistence remains reused from the preceding candidate because the delta affects uninstall cleanup only. This is lifecycle testing on an existing development host, not a pristine VM. Historical monitoring activation remains **UNKNOWN**; this is an un-attributed settings write, not a confirmed automatic-activation defect, and no documented criterion requires its attribution. |
| Full reminder/ageing/CARP and daemon-generated notification/service-discovery paths | **Open: DM-BL-013** | Scheduled service discovery and ageing remain unexercised, and helper emails were direct PHP calls. **P1 run 2 (15 November 2026)** produced genuine daemon-triggered CARP failover webhooks on both nodes and both legs — 4 frames (demotion `.253` BACKUP `2026-11-14T23:59:57Z` / `.252` MASTER `2026-11-15T00:00:02Z`; return `.252` BACKUP `00:09:50Z` / `.253` MASTER `00:10:28Z`), 0 on the stable cycle — with isolated capture and full restoration. **Deviation D1:** direction A applied the A2 `.252 100→0` write after A1 had already transferred the VIP, which `P1-PROCEDURE-REV1.md` §2.5 did not authorise; the four-frame notification evidence stands but is recorded as obtained under a procedure deviation, not as a clean qualification, and the single-write A1 path remains unproven. Email delivery is **NOT EXERCISED**; identity/new-device alerts, targeted Nmap, ageing transitions and external delivery remain outstanding, and authenticated UI checks are **operator-attested PASS** for rendering, detected/effective roles, CARP awareness, Automatic override, monitoring state and device counts on `.253` MASTER and `.252` BACKUP (browser-console errors **U9: PASS for the observed workflow 15 November 2026 — operator capture visually reviewed in the originating ChatGPT conversation, Errors and Warnings enabled with no text filter, no visible messages on the four captures; operator-attested, not independent inspection, no continuous monitoring claimed**; screenshot files/hashes **U10: PASS 15 November 2026 — all four files and SHA-256 values match the operator expectations and the operator supplied per-file content observations; operator-content-attested, not independently inspected (shell/text-only, no image viewer or OCR); package `dm-bl-013-ui-screenshots-verified-20261115T020427Z`, manifest `13f73a82…`**). A 15 November read-only pass revalidated roles/health in place (`.253` MASTER, `.252` BACKUP) and found current ageing state consistent with the code (0 ageing, 0 retirement candidates; `.253` 76/50/0 available/unavailable/unknown, `.252` 71/28/11); boundary-crossing ageing transitions are now covered by an **isolated integration validation** (21/21 per node on disposable SQLite snapshots of the installed `cd82a60c…` code, injected clock, no live daemon cycle), not by live acceptance. |
| Daemon-triggered attribution of the `notified_at` migration | **Open: DM-BL-013** — not a blocker for the observed live mutation | The column was observed live-present after direct discovery and before restoration; the caller beyond the direct-discovery path was not separately instrumented. |
| External SMTP, webhook, AdGuard/Pi-hole and targeted-Nmap delivery | **Open: DM-BL-013** — intentionally excluded from the prior scope | These paths were prohibited by the authorised scope; only the loopback SMTP sink was used. |

### Release 2.13.2 — the production/CARP field line

| Item | Value |
|---|---|
| Commit | `74e1f6f` on `release/2.13`, tag `v2.13.2` (unchanged by the remediation) |
| Payload | `release/v2.13.2-runtime.manifest`, 40 rows, staged targets 61 |
| Bundle | `dm-v2.13.2-runtime.tar.gz`, 336 261 bytes, sha256 `8fd6a7a703a63b4fa23f694d6dbd9d0aa50947f60ce23f37ffbd2c67a6b16f5a` (release-line artifact; never rebuilt). The latest published GitHub release remains v2.12.1 |
| Deployed | `.253` (CARP master), `.252` (CARP standby), 40/40 manifest parity; `.23` was upgraded to 2.13.3 on 5 November 2026 |
| Rollback | `/var/backups/devicemonitor/install-v213.{6KTQFY,.HuGjkL,.ivbMZd}` |
| New behaviour | A standby ages its own inventory: `[SERVICES] Stale-state ageing (standby)` (Decision 60) |

Lineage: `2.13` (`59d6d08`, no O4 ageing, never tagged) → `2.13.1` (`19f8d4d`, tag
`v2.13.1`, O4 restored, Decision 59) → `2.13.2` (`74e1f6f`, tag `v2.13.2`, standby ageing,
Decision 60) → `2.13.3` (pruning remediation, Decision 62).

### 2.13.3 — deployed to `.23` on 5 November 2026

| Item | Value |
|---|---|
| Branch | `fix/pruning-remediation-20261103` (untagged); deployment candidate built from `eadfc577b9ef184a12edba72780ec548a8486510`. The M5 evidence checkpoint remains `a1f759e9b64a1265a951260d45845df46435b1be`; this document does not claim the branch tip will remain unchanged |
| Payload | `release/v2.13.3-runtime.manifest`, 40 rows, staged targets 61 (62 fresh) |
| Bundle | `dm-v2.13.3-runtime.tar.gz`, 1 656 468 bytes, sha256 `7f389248707cf8fa0684760820db85c0fddac4b8b3964e0563318b38b2730fe2` — deployment candidate kept at `/root/dm-deploy-2133/dm-v2.13.3-runtime.tar.gz`, **not published**; byte-identical on FreeBSD and Linux, any timezone, either tar implementation (Decision 63, 67, 68; `release/bundle-digest.txt`). Earlier identities `ce92a09a…` / 348 920, `b29e1166…` / 349 052 and `451a03f4…` / 348 932 are retired and recorded as superseded |
| Deployed | `192.168.20.23` only. `.253` and `.252` remain on 2.13.2; no release or tag was created |
| CI | Run `41986115274` at the deployed commit `eadfc577b9ef184a12edba72780ec548a8486510`: success, 64/64 steps, zero skips. The earlier validated M5 checkpoint is green in run `41977736287` |
| Live verification | PASS: 40/40 manifest rows and all 61 installed targets matched digest/mode/owner/group; the new record has 61 digest rows including 21 `.mo` targets; database and configuration are unchanged; monitoring remains disabled |
| Service lifecycle | PASS: the installer stopped/wait/started the daemon (old PID 6557 exited; replacement PID 31483 was still running after 60 seconds) and performed a real configd restart (PID 71926 → 76711, with `configctl devicemonitor status` returning `running`) |
| Permissions repaired | Six notification scripts were corrected to mode `0644`, `root:wheel`; this was the installer's non-fatal `repaired=6` result and all post-install mode/ownership checks passed |
| Backups | Installer rollback asset `/var/backups/devicemonitor/install-v213.xKjyg1`; pre-install runtime/core-catalogue backup `/root/dm-pre-2133` (archive sha256 `dfa44d4c893fbc89c22389fc813774d8b9d123b71497ef47d73bb4aeb70ed9ba`) |
| Rollback | Not invoked; this deployment does not constitute a live rollback test. Rollback evidence remains the M5 sandbox scenario |
| Installer coverage (M5) | `verification/installer-sandbox/run-installer-sandbox.sh` executes the unmodified installer from the published bundle inside a disposable FreeBSD jail: `check`, `install`, `repair`, `rollback`, `failclosed` — all PASS (`verification/REVIEW-R2-REMEDIATION-20261103.md` §Phase 3, evidence in `verification/installer-sandbox/evidence/`). Root/host-only; GitHub runners cannot create a FreeBSD jail, so it is not a CI suite |
| New behaviour | Pruning requires proof of ownership (including for bare-path records), the record covers generated targets, every executed input is pinned, a repair install is idempotent and enforces mode/ownership, rollback reports COMPLETE/INCOMPLETE and restores the record (Decisions 62-64) |

### OPNsense 26.7.8_2 update — `.23` testbed (5 November 2026)

| Item | Actual result |
|---|---|
| OS | OPNsense `26.7.8_2`; FreeBSD `15.1-RELEASE-p6 amd64`; reboot completed at 19:46:14 AEDT |
| Applied offer | `opnsense 26.7.8_2`, `opnsense-update 26.7.8`, base/kernel `26.7.8`; 48 upgrades, 7 reinstalls, no removals or downgrades |
| Device Monitor | `2.13.3`; monitoring `enabled=0`; no SQLite WAL |
| Verification | saved post-boot checker returned `POSTBOOT_RESULT=PASS`; all 61 targets matched record and pre-update snapshots; record remains `0afb4e4e68edd331f22c88ef559dd1163af0baaaba0cd77a76b3ed672c17dea7` |
| Preserved data | At OS-update acceptance, `devices.db` was `c17874a717cebe2c2e1dbaf537fd13a65b4ded47e10dfcce1849f2088136144e` and Device Monitor configuration was `8115a7eee5104e4ddad4a508caf06cbbe1822ee9722578db527104b366cb1c22`; SQLite quick/integrity checks `ok`. The pre-2.14 configuration hash was later `027594eb735cf35e4b617163106031971567d0ba74027783e42cae46d37fd47d`, which the 2.14.0 install preserved |
| Services | configd and the Device Monitor daemon running; `configctl devicemonitor status` returned `running`; `re0` retained `192.168.20.23` and HTTPS remained listening |
| Backups | `/root/dm-os-26.7.8-preupdate`; encrypted archive `/root/dm-os-26.7.8-preupdate.tar.gz.enc`, 26,470,432 bytes, sha256 `64986b9a7564b28c53200af664f4247198d125e0748baecf8732f83909749934`; Windows copy hashes confirmed by the operator; installer `/var/backups/devicemonitor/install-v213.xKjyg1` and `/root/dm-pre-2133` retained |
| OPNsense configuration | The update generated `/conf/backup/config-1793868107.8517.xml`, byte-identical to `/conf/config.xml` at OS-update acceptance time (sha256 `cbba358a646aaeb28aa63dccafdd5e971a437c21637466493e415b17b67df61b`). The later `os-git-backup` installation produced a new current configuration and automatic revisions; the 2.14.0 pre-install backup captured that post-plugin state. This remains distinct from the unchanged Device Monitor configuration |
| Host tooling repair | Codex failed after reboot because `libdbus-1.so.3` was missing; `dbus 1.16.2_4,1` was installed from the OPNsense repository and `codex-cli 0.165.0` now starts |
| Remaining warning | The update log reports one package-audit warning for `libgpg-error-1.61`; it is not a failed update or Device Monitor check and was not remediated in this task |
| Boundaries | Rollback was not invoked and is not claimed as tested by this update; `FRESH=1` remains untested; `.252`/`.253`, production, releases, tags, commits and pushes were not touched during the update |

Record: `verification/UPDATE-OPNSENSE-26.7.8-23-PLAN.md`. Post-boot evidence is retained at
`/root/dm-os-26.7.8-postboot-evidence.txt` and `/root/dm-os-26.7.8-postboot-status.txt`.

### Workspace and repository protection (3 November 2026, Decision 65)

| Item | Value |
|---|---|
| Canonical workspace | `/root/src/opnsense-devicemonitor-upstream` (`origin` = `apg19590209/opnsense-devicemonitor`) |
| Launcher | `/usr/local/bin/cline-dm` — verifies top-level and origin, prints branch/HEAD, pins `--cwd`, refuses `-c/--cwd`, `--worktree`, `--update` |
| Instructions | `.clinerules/20-workspace-authority.md` |
| Tool guard | `.clinerules/hooks/PreToolUse` — blocks repository creation/cloning, worktree creation and writes into protected checkouts |
| Commit guard | `.githooks/pre-commit` via `core.hooksPath=.githooks` — refuses commits outside the canonical top-level and any Cline-installation path |
| Preserved | `/usr/local/cline-freebsd/src/cline` (second clone carrying the untracked Cline installation) and the worktrees `/root/o3-branch`, `/root/tb-branch` — unchanged |
| Main integration | **Complete (7 November 2026):** PR #6 was fast-forwarded from `d5d73ed` to `2825177`, preserving all 54 commits and matching the reviewed tree; exact-main CI run `42342362864` passed. PR #7 then integrated the DM-BL-010 correction at `e9ec5486a8cc9e87e3b6d3cf6098f26ed15e1370`, where exact-main CI run `42359428985` passed. DM-BL-009, DM-BL-011 and DM-BL-012 are **CLOSED**; residual validation is tracked as DM-BL-013 |
| Integration path | `release/2.13` (`6bd122e`) is an **ancestor** of this branch, so integration into the release line is a plain **fast-forward with zero conflicts** — no merge and no rebase is necessary (Decision 66, `verification/RELEASE-INTEGRATION-ASSESSMENT-20261103.md`) |
| CI readiness | the validated M5 checkpoint `a1f759e9b64a` is published and green (run `41977736287`, 64/64, zero skips); H1b is closed |
| Evidence | `verification/WORKSPACE-PROTECTION-20261103.md`, `verification/REPO-CONSOLIDATION-20261103.md` |

Historical pre-deployment evidence from `.23` (then running 2.13.2), taken from this branch with
`install-unattended.sh --host $(/bin/hostname) --check`:

    VERIFY_OK=4
    NOTICE: merged the plugin keys into 10 core catalogue(s); uninstall.sh restores the pristine files
    CHECK_OK version=2.13.3 predecessor=2.13.2 files=61 core_locales=10 prunable=0 daemon_running=1 host=OPNsense.internal legacy_prunable=0 retained=0

That check stayed non-mutating: no new `/var/backups/devicemonitor/install-v213.*`
directory, `/var/db/devicemonitor/installed-manifest.txt` unchanged, no staged temp
directory left behind. The deployment then repeated the check from a fresh extraction and
obtained the same result before mutating the node.

Historical carry-over, now resolved: before 5 November the `.23` record had 40 bare paths
and no digests (`sha256 3f63e469…`). The 2.13.3 installer replaced it with the digest-bearing
form: 63 lines, 61 digest rows, 21 `.mo` targets, `sha256 0afb4e4e68edd331f22c88ef559dd1163af0baaaba0cd77a76b3ed672c17dea7`.
The old record's provenance remains unknown, but it no longer describes the live node.

## O4 divergence closed: ageing restored in 2.13.1 (3 November 2026)

The section above ("O4 ageing is absent from the running 2.12 line") is **closed**. The
restore shipped as 2.13.1 (`19f8d4d`, tag `v2.13.1`) and is running on all three nodes;
`tests/test_service_ageing.py` is green and the suite is 15 of 15. Decision 59 carries
the full record, including the correction to Decision 57 about when a standby starts
suppressing observation.

### Deployment records

| When | Version | Node | Result | Backup |
|---|---|---|---|---|
| 3 Nov 2026 00:01 | 2.13 | `.23` | INSTALL_OK files=61 | `install-v213.f0Psxp` |
| 3 Nov 2026 00:06 | 2.13 | `.253` (master) | INSTALL_OK files=61 | `install-v213.8h11R7` |
| 3 Nov 2026 00:09 | 2.13 | `.252` (standby) | INSTALL_OK files=61 | `install-v213.eLrgfA` |
| 3 Nov 2026 00:24 | 2.13.1 | `.23` | first attempt ROLLBACK_ATTEMPTED (daemon start race, installer fixed), second attempt INSTALL_OK | `install-v213.bsp83b` (rolled back), `install-v213.97t9Ns` |
| 3 Nov 2026 00:29 | 2.13.1 | `.253` (master) | INSTALL_OK files=61 | `install-v213.SAA2LN` |
| 3 Nov 2026 00:31 | 2.13.1 | `.252` (standby) | INSTALL_OK files=61 | (own `install-v213.*` dir) |
| 3 Nov 2026 00:46 | 2.13.2 | `.23` | CHECK_OK then INSTALL_OK files=61 | `install-v213.6KTQFY` |
| 3 Nov 2026 00:47 | 2.13.2 | `.253` (master) | INSTALL_OK files=61 | `install-v213.HuGjkL` |
| 3 Nov 2026 00:48 | 2.13.2 | `.252` (standby) | INSTALL_OK files=61 | `install-v213.ivbMZd` |
| 5 Nov 2026 18:31–18:32 | 2.13.3 | `.23` | CHECK_OK; INSTALL_OK files=61 pruned=0 unchanged=60 repaired=6; post-install acceptance PASS | `install-v213.xKjyg1`; pre-install `/root/dm-pre-2133` |
| 6 Nov 2026 09:21 | 2.14.0 | `.23` | CHECK_OK; INSTALL_OK files=63 pruned=0 unchanged=32 repaired=0; package/data/service acceptance PASS; authenticated UI later PASS via operator screenshot (no Network capture); rollback not invoked | `install-v214.JeYC44`; pre-install `/root/dm-pre-2140` |
| 6 Nov 2026 10:17–10:25 | 2.14.0 ↔ 2.13.3 | `.23` | preparatory reset PASS; test install PASS; successful-install live rollback PASS; final 2.14.0 reinstall PASS; monitoring disabled throughout | `install-v214.zGJRuq` (rolled back), `install-v214.qMPS7n` (final), recovery `/root/dm-validation-2140/rollback/20261105T231610Z` |

2.13.2 standby evidence: `.252` logs `[SERVICES] Stale-state ageing (standby): aged 1 row(s) to unknown, retired 0 row(s)` at 00:49:34, the first ageing cycle it has ever run while refusing service observation; `.253` keeps ageing on the discovery gate as before.

Post-deployment reconciliation: all 40 manifest rows hash-match on each node; `.253` logs
`Stale-state ageing: aged 1 row(s) to unknown, retired 0 row(s)`; standby dry-run `0/0`;
testbed backlog `38/42` (monitoring disabled there, left in place).

## M5 installer verification (5 November 2026)

The 2.13.3 installer now has executable end-to-end coverage that does not touch the node:

* `verification/installer-sandbox/run-installer-sandbox.sh all` — root-only, FreeBSD-only,
  disposable jail; five scenarios (`check`, `install`, `repair`, `rollback`, `failclosed`),
  `SANDBOX_RESULT=PASS`.
* Transcripts in `verification/installer-sandbox/evidence/<scenario>/`; design, results and
  the stated boundaries in `verification/REVIEW-R2-REMEDIATION-20261103.md` §Phase 3.
* The sandbox did not cover the daemon stop/wait/start branch or the real `service configd
  restart`. Both were exercised successfully on `.23` during the 5 November deployment, so
  those live lifecycle gaps are now closed by host evidence.
* The 2.14.0 harness later added isolated `fresh` and `fresh-rollback` scenarios. They passed on
  6 November, but live `FRESH=1` on a real OPNsense host remains untested and must not be selected
  on this existing `.23` installation. This was superseded on 12 November 2026 when the operator
  explicitly authorised the `.23` lifecycle; see the closure section below.
* Rollback was **not invoked** by the 2.13.3 deployment. The later §9.3 2.14.0 successful-install
  live rollback cycle passed on `.23`; it is separate from the historical M5 sandbox result.
* The historical pre-deployment sandbox run did not touch `.23`, `.253` or `.252`; the later
  2.13.3 deployment touched `.23` only. `.253`/`.252` remain on 2.13.2.

**Next step:** 2.14.0 publication is **NO-GO** under the revised closure objective. The exact
candidate passed Phase 1 and authenticated About/Features/Devices-loading evidence was received on
7 November 2026; Phase 2A and the native runtime matrix now pass. DM-BL-011 was **CLOSED** on
13 November 2026 by explicit operator acceptance of the historical byte-evidence limitation, with no
byte-identity claim; DM-BL-012 was closed on 12 November 2026 by the operator-accepted `.23`
lifecycle; DM-BL-013 still needs single-host monitoring tests and an isolated HA pair. Issue #5
remains OPEN pending reporter confirmation. `.23` remains on the accepted exact candidate with
monitoring disabled.

## 2.14.0 installer-jail validation (6 November 2026)

Before publication, the disposable FreeBSD jail selected the corrected 2.14.0 worktree candidate:
HEAD `eac1160557352d45648c4a25310b8daeaad440f6` plus the rollback correction, bundle
`/root/dm-backups/dm-bl009-candidate-rollback-fix-20261106-083105/dm-v2.14.0-runtime.tar.gz`
(1,725,593 bytes, sha256 `5149bfd41e5842a144a9d1280c008511f20f3783932eca9beb1f48fca6173f5f`).
Historical 2.13.3 evidence under `verification/installer-sandbox/evidence/` remains unchanged; the
new transcripts are under `verification/installer-sandbox/evidence-2.14.0/`.

All five scenarios passed. The upgrade verified 63 targets, pruned the one eligible legacy file,
retained the deliberately modified fixture, preserved the database and configuration, and validated
the About/Features endpoint binding. Rollback restored all targets, the prune fixture and the
record, then restored 19 core-locale `.state` and pristine-catalogue files with
`restored=19 removed=0 conflicts=0 failed=0`; only the expected installer backup directory
remained. The fail-closed scenario refused a tampered helper before mutation.

The earlier `530facc…` candidate and its failed rollback evidence are retained as superseded
diagnostic records; they are not the current validation result. The artifact was validated before
its integration commit, so the recorded source form is the worktree; CI status for the pushed commit
is tracked in the milestone report. No deployment, service change, monitoring activation,
production or `.252`/`.253` access occurred during that jail work. The later live deployment
exercised the real configd restart and daemon stop/wait/start lifecycle. The subsequent §9.3
successful-install live rollback cycle also passed; the later bounded §9.4 exercise verified
two monitoring cycles, DMTEST discovery and two loopback helper emails. Full reminder/ageing/
CARP behaviour and live `FRESH=1` remain separate untested paths. Full evidence and the rollback
correction are in
`verification/INSTALLER-JAIL-2.14.0-20261106.md`; the fresh results are in
`verification/FRESH-INSTALL-JAIL-2.14.0-20261106.md`; the live cycle is in
`verification/LIVE-ROLLBACK-2.14.0-23-20261106.md`. DM-BL-009 is **CLOSED**; the remaining
real-host validation was tracked as **DM-BL-012** and closed on 12 November 2026.

## 2.14.0 fresh-install jail validation (6 November 2026)

The isolated `fresh` and `fresh-rollback` scenarios ran against the unchanged 2.14.0 bundle
(1,725,593 bytes, sha256 `5149bfd41e5842a144a9d1280c008511f20f3783932eca9beb1f48fca6173f5f`)
at HEAD `690204bb1d6c402de9a2b41e16f753b37335279f`.

* `fresh`: `CHECK_OK ... predecessor=fresh files=64 core_locales=10 prunable=0 daemon_running=0 ...
  legacy_prunable=0 retained=0`; `INSTALL_OK version=2.14.0 files=64 core_locales=10 pruned=0 ...
  daemon_restarted=0 unchanged=0 repaired=0`. All 64 targets, the 64-row record, the ten pristine
  core catalogues, the rc.conf/rc.d wiring and a running daemon were verified; no `devices.db` or
  `config.json` existed.
* `fresh-rollback`: the one-shot post-mutation `configd` failure aborted non-zero;
  `ROLLBACK_STATUS=COMPLETE`, targets `restored=64 skipped=0 conflicts=0 failed=0`, core-locale
  `restored=0 removed=19 conflicts=0 failed=0`. Every originally absent path was absent again and
  only the retained installer backup directory differed.
* Both scenarios removed the jail, mounts and host stages and left the live fingerprint unchanged.
* Evidence: `/root/dm-validation-2140/jail-evidence-fresh-20261106/` (`SHA256SUMS` sha256
  `1448ec56adf75dab2461da9f0fda6447486a9258fadd4afa9c4deec70e43b05b`).

The jail-only `rc.configure_plugins` stub proves the installer's call boundary, not real OPNsense
plugin registration. A real-host `FRESH=1` attempt on `.23` on 8 November 2026 passed install and
registration checks but was aborted before reboot and recovered; it is not a lifecycle pass. A
screenshot from the operator's authenticated browser confirms both About and Features render
`v2.14.0`; no Network capture was supplied for this attempt. Real-host `FRESH=1` and plugin
lifecycle validation were tracked as **DM-BL-012** and closed on 12 November 2026.

## 2.14.0 real-host fresh-install attempt on `.23` (8 November 2026) — aborted

The authorised attempt used `/root/dm-validation-2140/dm-bl-012-fresh-20261107T202736Z/` and the
exact `90afa55d…` candidate. Uninstall, clean-predecessor preparation, `CHECK_OK`, `INSTALL_OK`,
the 64-target plan/record, all 11 plugin and 10 core catalogue recomputations, plugin registration,
configd and daemon startup passed. The initial fresh state had no `config.json` or `devices.db`.

A configuration save at `07:37:08` then created `config.json` with `enabled=1` and
`monitored_interfaces=lan`; the validation command stream did not issue that save, and the
authenticated GUI request origin was not logged. The daemon ran one scan and contacted `.252` and
`.253` for service probes. Email and webhook were disabled and no notification was sent. The daemon
was stopped, the activation evidence was preserved, and the reviewed recovery restored the accepted
data/configuration and 63-target manifest. `RECOVERY_LIVE_VERIFY=PASS` covers the recovered state.

No reboot was performed, so reboot persistence and authenticated post-reboot UI checks remain
untested. The uninstaller cleared the obsolete menu-cache path and failed on the non-existent
`php-fpm` service; both defects are recorded but not fixed in this task. DM-BL-012 remained
**OPEN** until the 12 November 2026 lifecycle closure recorded below.
Full evidence is in `verification/DM-BL-012-FRESH-23-ATTEMPT-20261108.md`.

## 2.14.0 real-host lifecycle closure on `.23` (12 November 2026) — DM-BL-012 CLOSED

The operator explicitly superseded the disposable-VM environment gate and authorised uninstall,
reinstall, necessary service actions and one reboot on the existing development host `.23`,
replacing VM snapshots with a verified pre-state backup and an executable recovery procedure. This
is the documented explicit-operator-acceptance alternative, not validation on a pristine OPNsense
VM; the residual risk of using an existing development host was accepted by the operator.

* Repair candidate `772a6660…` (menu-cache path and unsupported `php-fpm` call) ran a normal
  uninstall and exact-candidate reinstall on `.23`, then one reboot. Post-boot: 64/64 manifest
  targets, unchanged `/conf/config.xml`, `config.json` `027594eb…` and `devices.db` `796d28c7…`,
  SQLite integrity `ok`, configd and daemon running, `Monitoring DISABLED` at 19:28:56, corrected
  menu cache at `/var/lib/php/tmp/opnsense_menu_cache.xml` with all seven Device Monitor entries,
  and no scan, promiscuous or notification events.
* Residual-repair candidate `3675c7271ad3bbd3a04c325c9f7b03bfea80a19e6ff913c2c3114b78eaa46891`
  (1,731,225 bytes) removed `/usr/local/etc/inc/devicemonitor_locale.inc` and
  `/usr/local/opnsense/service/conf/actions.d/actions_devicemonitor_update.conf` on normal
  uninstall. Live uninstall exit 0 left zero of the 42 payload targets, no `php-fpm` call, unchanged
  configuration and 4/4 unrelated sentinels; reinstall exit 0 produced 64/64 targets,
  `INSTALL_OK … files=64 core_locales=10`, restored data hashes and disabled settings. No reboot was
  needed for this payload-neutral correction. The latest candidate's uninstall and reinstall were
  directly tested; reboot persistence is reused from the preceding `772a6660…` candidate because
  the delta is uninstall cleanup only and cannot affect installed payload, rc wiring, daemon start
  or reboot behaviour.
* Operator attestation recorded at 19:56:51 (+1100) states that Services → Device Monitor →
  Devices and Settings display correctly. It is an operator attestation, not a screenshot or an
  agent-observed browser check; no observation timestamp was supplied or inferred. Monitoring
  disabled was verified by the automated checks, not separately attested.
* Recovery assets: `/root/dm-validation-2140/dm-bl-012-live-23-20261112T191143/` and
  `/root/dm-validation-2140/dm-bl-012-residuals-20261112T194900/`.
* Historical monitoring-activation attribution remains **UNKNOWN**. The record is an un-attributed
  settings write and one scan, not a confirmed automatic-activation defect. The documented
  DM-BL-012 acceptance criterion is real plugin registration and a daemon surviving reboot with no
  stub claim, or explicit operator acceptance of the residual risk; attribution is not an
  acceptance criterion. Uncertainty alone does not therefore add a release blocker; DM-BL-013 remains
  the documented blocker. DM-BL-011 was **CLOSED** on 13 November 2026 by explicit operator acceptance
  of the historical byte-evidence limitation; no byte-identity claim is made.

## 2.14.0 UTC/local presence timestamp correction (12 November 2026) — DM-BL-013 OPEN

The confirmed `devices.last_seen` inconsistency was caused by two writers using different domains:
Hostwatch stores UTC, but service verification stamped its local `datetime.now()` into
`devices.last_seen` through `touch_device_last_seen()`, and into `last_verified`/`last_checked`;
the full-scan fallback was also local. The freshness reader used UTC while retirement used a local
cutoff. On `.23` (UTC+11), a local value is eleven hours ahead of UTC, so the nominal 15-minute
freshness window can remain true for about 11 hours 15 minutes. Conversely, a Hostwatch-only UTC
`last_seen` appears eleven hours older to the old local retirement cutoff and can cross the 30-day
boundary up to eleven hours early, subject to the hourly pass. Service-refreshed local retirement
and service `unavailable` ageing were local-to-local before the repair.

The affected service-presence writer is present in `v2.12`, `v2.12.1`, `v2.13.1`, `v2.13.2` and
the 2.14.0 line. `v2.13` has no service-presence writer; releases before `v2.12` predate it.
The fix writes canonical UTC from service verification, Nmap evidence and related readers, and
uses a conservative mixed-domain read for unqualified rows. Legacy local wall time is interpreted
with the timezone rules in force at that date, including both fold interpretations during an
ambiguous DST fall-back. No production database or stored timestamps were changed. The conservative
reader does not treat an ambiguous value as stale until both UTC and local interpretations pass the
cutoff, so legacy cleanup is delayed rather than accelerated. On `.23` at UTC+11 the delay is at
most eleven hours, plus one hourly scheduler interval; canonical UTC rows do not incur it at that
offset. On a negative-offset host the same dual-domain cutoff can delay canonical rows by the
absolute offset because rows carry no domain marker.

Evidence and the untouched candidate build are under
`/root/dm-validation-2140/dm-bl-013-timestamp-r3-20261112/`; the preceding review builds remain
under `/root/dm-validation-2140/dm-bl-013-timestamp-r2-20261112/` and the initial timestamp
investigation under `/root/dm-validation-2140/dm-bl-013-timestamp-20261112/`. The replacement
candidate is 1,735,321 bytes, SHA-256
`ecaecb04814af41479e1b6e614b05a63de9676158870d749ab51b63d5eee87df`, 60 members, from two
byte-identical stage builds. It supersedes the earlier timestamp-review and lifecycle candidates
only for future testing; those and every earlier artifact remain preserved. The existing production
staging/preflight belongs to the old candidate and must be refreshed before any later installation.
No install, service action, reboot, monitoring activation, production database change, commit,
push or publication occurred in this work.

This defect is tracked under **DM-BL-013 / ageing**. DM-BL-012 remains **CLOSED** by explicit
operator acceptance, and historical monitoring-activation attribution remains **UNKNOWN** rather
than a confirmed automatic-activation defect.

## Production CARP BACKUP `.252` timestamp-candidate installation (13 November 2026)

The operator authorised installation of the exact UTC timestamp candidate
`ecaecb04814af41479e1b6e614b05a63de9676158870d749ab51b63d5eee87df` on production CARP BACKUP
`.252` only. Immediately before installation, `.252` was BACKUP and `.253` remained MASTER;
`.254` was not contacted directly. The reviewed staged installer ran from 08:14:54 to 08:15:06
AEDT with exit 0. It verified 63 targets, reported database integrity `ok`, kept the Device Monitor
configuration unchanged and restarted the documented configd and Device Monitor services. `.252`
remained BACKUP and `.253` remained MASTER on 2.13.2; no failover, forced scan or notification test
was performed.

Two normal 300-second cycles completed at approximately 08:20 and 08:25 AEDT. Twenty-three local
device rows received new canonical UTC `last_seen` values, twenty-one of them during the observation
window. MASTER-only visibility, service-discovery, identity-alert, new-device, targeted-Nmap and
notification-delivery paths were not exercised. DM-BL-013 therefore remains **OPEN**. The install
and cycle evidence is under
`/root/dm-validation-2140/dm-bl-013-prod-252-install-20261112T211341Z/`; the sealed evidence digest
is `63d740365b2be61e4c0fe9a6c8688d3a33269f85a13ea1d886f4a5c37c0d2315`.

## HA role visibility on `.23` (13 November 2026) — source validated; installed on testbed

The Devices and Settings pages now share the established read-only
`/api/devicemonitor/config/getcarpstatus` status source used by Settings → HA / CARP. The API keeps
the detected CARP role (`role`) separate from the effective mode (`mode`) selected by the role
override, honours CARP awareness, reports mixed and unavailable detector states, and returns the
node hostname plus the latest successful daemon scan from the existing log. A full refresh failure
clears the role, observation and VIP rows rather than retaining an old MASTER verdict; superseded
requests cannot repopulate them after a newer failure.

On BACKUP, the notice lists only the operations gated by the daemon: visibility priming, service
discovery, service alerts, identity-conflict alerts, new-device alerts and automatic targeted Nmap
scans. Local inventory and identity recording, node-local ageing and scheduled port discovery remain
active. Manual targeted scans are not CARP-gated and are therefore not included in the paused list.

The replacement candidate is 1,795,230 bytes, SHA-256
`e7dcb7f88ec8f98ca4455542f2106416e2447740c95c818ff2cfdd31d4ef3124`, with two byte-identical stage
builds. Review corrections replaced the wrong daemon-log timestamp format with the actual bracket
format, made scan-history lookup bounded-memory and complete, and stopped an unreadable config from
being described as confirmed observation continuation. The API distinguishes readable history with
no success, unreadable history and API fetch failure. Source-catalogue language acceptance passed
for nine selectable languages with the existing `nl_NL` selector gap, and all focused API/UI, CARP,
non-HA, integration, release and bundle checks passed. The agent host had no browser, so the agent
captured no screenshots and made no browser layout claim. An operator-supplied review of the
isolated fixture on 13 November 2026 reported that MASTER and BACKUP notices render clearly,
fetch-failure and backend-unavailable messages are distinct, German Settings and English Devices
wrap correctly at narrow widths, and a simulated MASTER-to-BACKUP transition ends in the correct
BACKUP view. That review is operator attestation of isolated-fixture rendering only, not live CARP,
a live role transition or full-matrix acceptance. That source-validation pass made no install,
browser/live UI check by the agent, service action, reboot, monitoring activation, commit or
publication. The reviewed candidate was then installed on testbed `.23` on 13 November 2026
(10:49 AEDT) with 63/63 payload hashes verified, unchanged configuration and database, monitoring
still disabled and no reboot or CARP change. Evidence:
`verification/DM-BL-013-HA-VISIBILITY-20261113.md` and
`/root/dm-validation-2140/dm-bl-013-ha-messaging-r3-20261112T225433Z/`. The earlier HA candidates
`2dab1385…`, `709288cd…`, `e789fb96…` and `f51f1adf…` remain preserved.

### `.23` testbed deployment (13 November 2026)

The reviewed HA-messaging candidate `e7dcb7f8…3124` (1,795,230 bytes) was staged and preflighted
with `CHECK_OK version=2.14.0 predecessor=2.14.0 files=63 core_locales=10 prunable=0
daemon_running=1 host=OPNsense.internal legacy_prunable=0 retained=0`. The preflight changed no
payload, configuration, database or backup state. The authorised install on `.23` returned
`INSTALL_OK version=2.14.0 files=63 core_locales=10 pruned=0
backup=/var/backups/devicemonitor/install-v214.lulG0h daemon_restarted=1 unchanged=36 repaired=0`.
All 63 installed record rows matched, the retained `/etc/rc.conf.d/devicemonitor` remained present,
SQLite integrity remained `ok` with 26 device rows, and `config.json` (`027594eb…`), `devices.db`
(`796d28c7…`) and `/conf/config.xml` (`e86a7058…`) were byte-identical to the pre-install state.
Monitoring remained disabled, no scan or notification occurred, and the kernel boot time was
unchanged. This is lifecycle testing on the existing development host, not a pristine OPNsense
installation or a live CARP-transition test. Evidence:
`/root/dm-validation-2140/dm-bl-013-ha-deploy-23-20261112T234608Z/`.

A later uncommitted compact-summary revision adds the collapsed Show details/Hide details notice, the read-only monitoring-enabled state, separate HA-pause summary and role/unavailable warnings. It is source-only and is not part of the installed `e7dcb7f8…3124` candidate.

An additional source-only revision adds automatic HA relevance detection. `getcarpstatus` now
confirms non-HA only from readable `ifconfig` and `/conf/config.xml`, at least one resolved monitored
interface, no configured CARP VIP, no CARP state on monitored devices and no explicit role override.
That positive result hides HA-specific notice content while retaining the node, monitoring state and
expanded last-scan information. Other states retain the HA notice and warnings. Settings keeps the HA /
CARP tab accessible, explains `No CARP configuration detected`, disables CARP awareness and failover
notification without changing saved values, and leaves the role override editable so an active value
can be inspected or cleared. Detector/API failures remain unknown, never non-HA. CARP awareness
disabled remains distinct from detected role and effective mode. Focused PHP/JavaScript, non-HA,
integration, translation, CI, locale, fixture and diff checks passed; the updated fixture is sealed at
373,094 bytes with SHA-256
`687cc9f22d6bb2a9c3c5a47d1e13563471516cf2892922e8520b06ea08a8fbe5`. Language acceptance remains
deferred by the active premium price window, and browser visual acceptance of this revision remains
pending. This revision is source-only: it is not installed on `.23` or production, the installed `.23`
payload remains `e7dcb7f8…3124`, DM-BL-013 remains **OPEN**, and historical monitoring-activation
attribution remains **UNKNOWN**.

A later source-only compact-line revision reduces the collapsed notice to one fact line where space
allows: node identity, effective HA role (omitted when non-HA is confirmed), monitoring status, and a
short `Some activities paused` indicator only on BACKUP. Unavailable and override warnings remain
outside the collapsed details region. Expanded details now show detected/effective roles, the
node-local explanation, paused/continuing activities and the last successful scan once each; the
duplicate monitoring note and `No activities paused` message were removed. `getcarpstatus` exposes a
timezone label only from a valid `/conf/config.xml` system timezone, and the UI explicitly says
`Timezone unavailable` rather than guessing. PHP API cases (18), JS cases (23), translation, CI,
catalogue, fixture, inline-script and diff checks passed. The fixture was resealed after inline
JavaScript syntax validation was added to its static checker: 373,818 bytes, SHA-256
`7376a65a3a0640496926461fdbb76272421c9839ed9e6d630e0aac77d91acbab`. Only the checker and recorded
log changed; the fixture HTML remains `9dfa112d…a18fa`. The previous `c34d3414…1c88` archive is
preserved under `.../preserved-c34d3414/`. Language acceptance remains deferred by the premium price
window and browser acceptance of this revision remains pending. This revision is source-only, not
installed; DM-BL-013 remains **OPEN** and historical activation attribution remains **UNKNOWN**.

A further source-only review correction addresses the browser findings against that fixture. For
confirmed non-HA with no override, expanded details now replace the CARP-peer ownership sentence
with the existing node-local wording and keep the role facts hidden; the last scan remains. The
Settings HA / CARP table now labels the field `HA policy permission`, with `permitted` or `paused by
HA policy` values, so it does not imply that monitoring or service observation is actually running.
The fixture-only role-fact leakage was caused by its `display:flex` rule overriding the `hidden`
attribute and is fixed with an explicit `[hidden]` rule; the real views also carry the defensive
rule. The fixture tab row now wraps at narrow widths. The real Settings view was inspected and uses
standard Bootstrap `nav-tabs` without the fixture's horizontal-overflow rule, so no production
Settings CSS change was made. The affected PHP/JS, non-HA, integration, translation, CI, catalogue,
locale, fixture and diff checks pass. Updated archive: 374,294 bytes, SHA-256
`40b2e6b3548b0d664665fa5021989ac660d9613bd72d99c8f741b23facff450b`; the previous `7376a65a…acbab`
fixture and earlier archives remain preserved. Language acceptance remains deferred by the active
price window, browser acceptance remains pending, and this remains source-only and not installed.
DM-BL-013 remains **OPEN** and historical activation attribution remains **UNKNOWN**.

## HA notice sampled browser acceptance and final candidate (13 November 2026)

The operator supplied an isolated-fixture screenshot review of the R5 package (`374,294` bytes,
SHA-256 `40b2e6b3548b0d664665fa5021989ac660d9613bd72d99c8f741b23facff450b`). The review passed for
the sampled compact and expanded MASTER and BACKUP states, confirmed non-HA with monitoring
disabled, an active role override, narrow-screen tab wrapping, and the simulated
MASTER-to-fetch-failure transition. This is operator attestation of simulated fixtures, not an
agent-observed browser session or a live CARP test. No exact observation timestamp was supplied and
none is inferred. It does not establish the full state matrix, keyboard acceptance, live CARP,
production rendering, MASTER-only operation or delivery paths.

The final source-only candidate was rebuilt twice with separate stages and byte-identical results:
1,827,998 bytes, SHA-256
`2d2c0a884ef169a4f9609a84f2860918bd7fc8432dfb23be52c4b9d6f35d8874`, 60 members. Review of the
first final build found archive modes still depended on checkout umask and a transient `0600`
manifest permission; the builder now normalises `0644`/`0755` from the Git index, and the
determinism test varies both timestamps and worktree modes. The regenerated release manifest and
release-input pins verify against the current sources. Evidence:
`/root/dm-validation-2140/dm-bl-013-final-20261113T013258Z/`. The installed `.23` payload remains
the earlier `e7dcb7f8…3124` candidate; this final candidate has not been installed on `.23` or
production. The active premium price gate deferred language acceptance without a bypass.
DM-BL-013 remains **OPEN**, and historical monitoring-activation attribution remains **UNKNOWN**.

## Appliance CARP proof vs monitoring-scope readiness (13 November 2026)

Read-only inspection on `.23` established readable `/conf/config.xml` with zero virtual-IP nodes and
zero CARP VIPs, readable `/sbin/ifconfig -a` with zero `carp:` state lines, and an empty
`monitored_interfaces` selection with monitoring disabled. The captured installed-candidate response
returned `non_ha_confirmed=false` and `ha_relevant=true`, so the earlier candidate did not make the
requested distinction: it required a resolved monitored interface before it would use independently
positive appliance-wide evidence that CARP was absent.

The uncommitted source correction separates `appliance_carp_state`, `carp_vip_count`,
`carp_runtime_present`, `monitoring_scope_ready`, `monitoring_scope_reason`, and
`monitoring_roles_known`. Appliance-wide absence now requires readable configuration, readable
`ifconfig`, no configured CARP VIP and no runtime CARP state; it does not require a monitored
interface, but it is disabled by an explicit role override. If CARP exists while the monitored
selection is empty, `non_ha_confirmed` remains false and the scope-specific
`carp_present_no_monitored_interfaces` explanation is returned. Detector or configuration failure
leaves the appliance state `unknown` and never infers non-HA. The actual `.23` source-harness result
is `appliance_carp_state=absent`, `non_ha_confirmed=true`, `ha_relevant=false`,
`monitoring_scope_ready=false`, and `monitoring_scope_reason=no_monitored_interfaces`.

The replacement source-only candidate is 1,850,019 bytes with SHA-256
`c2405fccc43c1c1d6a44d4cdd9af0c5d2927778e42b9e3ecfa0c375eefcaf7d4`; two independent checkout
builds and the recorded-digest check are byte-identical. The previous `97ac0283…3ace` candidate and
all earlier evidence remain preserved. Evidence is under
`/root/dm-validation-2140/dm-bl-013-appliance-carp-scope-20261113T024619Z/`. No install, service
action, settings change, monitoring activation, reboot, production contact, commit, push or
publication occurred. DM-BL-013 remains **OPEN**, and historical monitoring-activation attribution
remains **UNKNOWN**.

## Selectpicker lifecycle correction and `.23` deployment (13 November 2026)

The Settings role-override Bootstrap-select now initialises explicitly instead of relying solely on
the window-load data hook. It refreshes after the asynchronous configuration value and
disabled-state changes, preserves the saved `auto`/`master`/`backup` value, and gives the generated
toggle `tabindex="0"` plus an accessible label when enabled. Opening the control cannot submit the
pane form: the library's generated toggle is `type="button"`, the refresh helper performs no submit
or save action, and the existing pane submit handler remains in place.

The candidate is 1,850,019 bytes with SHA-256
`10ff1509efce5bc109860fa9c8e645e906468cf764b02d6dcaaa1c77886efd47`; two stage builds were
byte-identical and the clean-checkout determinism suite passed. The release manifest, release-input
pin and installer pins were regenerated. The previous `c2405fcc…` candidate and all earlier evidence
remain preserved.

The `.23` preflight was clean and the install returned
`INSTALL_OK ... backup=/var/backups/devicemonitor/install-v214.tqCqe5 daemon_restarted=1
unchanged=39 repaired=0`. All 63 installed rows verified, SQLite integrity remained `ok`, the
installed Settings source matched the candidate, and `config.json`, `devices.db` and
`/conf/config.xml` remained byte-identical to their pre-install hashes. Monitoring and notifications
remained disabled; no CARP VIP, reboot, production contact, commit, push or publication occurred.
Durable evidence is under
`/root/dm-validation-2140/dm-bl-013-ha-selectpicker-20261113T151521Z/`. The live Settings URL for
operator inspection is `https://192.168.20.23/ui/devicemonitor/index/settings`.
The predecessor font, labels and Escape behaviour were reviewed,
and final-candidate keyboard confirmation is recorded below. DM-BL-013 remains
**OPEN**, and historical monitoring-activation attribution remains **UNKNOWN**.

### Live operator verification and keyboard correction

An operator review of the deployed `10ff1509…` Settings page on 13 November 2026 confirmed that the
opened dropdown font matched the surrounding UI, all three revised labels displayed correctly, and
Escape closed the dropdown. A Space-to-open attempt failed while focus/keyboard conditions were
uncertain. No exact observation time was supplied, and this is not full keyboard acceptance.

The installed Bootstrap-select 1.13.18 source shows that its closed-state type-ahead branch consumes
Space and Enter before native button activation can open the menu. The deployed candidate also set
the generated toggle's tab index directly instead of using the plugin's native-select focus proxy.
The corrected source gives the native select `tabindex="0"`, leaves the generated toggle under
plugin focus management, and adds a namespaced closed-state Space/Enter opener. When the menu is
open, those keys remain with the plugin. Saved option values, save collection and submission
behaviour are unchanged.

The corrected candidate is 1,850,531 bytes with SHA-256
`2f69a69751755891578fb53a3d15f27be1200798b89a0f23ad24137d75d5ef33`; two builds and the
clean-checkout determinism test are byte-identical. It was deployed to `.23` with a clean preflight
and a fresh installer backup. All 63 installed hashes matched, SQLite integrity remained `ok`, and
`config.json`, `devices.db` and `/conf/config.xml` remained byte-identical. The saved role override
remained `auto`, monitoring and notification gates remained disabled, and Device Monitor and configd
stayed healthy; no reboot occurred. The operator subsequently confirmed, without an observation
timestamp being recorded, that Space and Enter open the deployed dropdown, Escape closes it, and the
saved value remains `Automatic (use CARP role)`. Deployment evidence is under
`/root/dm-validation-2140/dm-bl-013-ha-keyboard-deploy-20261113T053031Z/`. DM-BL-013 remains
**OPEN** pending production MASTER, HA-transition and delivery-path validation; historical
monitoring-activation attribution remains **UNKNOWN**.

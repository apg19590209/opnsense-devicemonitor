# Device Monitor — Project State

## Current state

Last updated: 7 November 2026

Branches: `main` (HEAD `e9ec5486a8cc9e87e3b6d3cf6098f26ed15e1370`, the Device Monitor
2.14.0 source line including the DM-BL-009 closeout documentation and the integrated DM-BL-010
catalogue-header correction), `release/2.13` (HEAD `6bd122e`) and
`fix/pruning-remediation-20261103` (HEAD `b2c74fc`, the 2.13.3 remediation). The
`integration/dm-bl-009-reconcile-20261105` history was fast-forwarded into `main` on
7 November 2026. The latest published GitHub release is **v2.12.1**; 2.14.0 is not yet published.
`baseline/2.12` (`d04739a`) holds the recovered pre-HA 2.12 tree;
`feature/async-db-v2.11` (`0ad95b0`) is the historical v2.11 development branch.
The DM-BL-010 catalogue-header correction is integrated into `main` by PR #7 at
`e9ec5486a8cc9e87e3b6d3cf6098f26ed15e1370`; its exact-candidate Phase 1 repair/acceptance run
passed on `.23`. It is not tagged or published: v2.12.1 remains the latest release and 2.14.0 is
still unpublished.

### 2.14.0 — main source and `.23` deployment; not yet published

| Item | Value |
|---|---|
| Branch | `main` at `e9ec5486a8cc9e87e3b6d3cf6098f26ed15e1370`; PR #6 fast-forwarded the reviewed `integration/dm-bl-009-reconcile-20261105` history from `d5d73ed` to `282517744260920b18c9217efd09ce738af21d70`, and PR #7 added the DM-BL-010 catalogue-header correction |
| Payload | `release/v2.14.0-runtime.manifest`, 42 rows; 63 generated targets on an upgrade and 64 on a fresh install |
| Bundle | `dm-v2.14.0-runtime.tar.gz`, 1,729,177 bytes, SHA-256 `90afa55dd826c0dc3be8a23902b809baa465e25191dc372dc6cc2ef4e57fc243`; 60 members; four byte-identical builds. The earlier 1,725,593-byte `5149bfd4…` main-integration bundle and its evidence remain preserved as superseded |
| CI | Exact-candidate CI run `42358468231`: **success**; exact-main CI is recorded separately below. Linux CI does not execute the FreeBSD installer-jail or live-service scenarios |
| Main integration CI | Exact-main workflow-dispatch run `42359428985` at `e9ec5486a8cc9e87e3b6d3cf6098f26ed15e1370`: **success**. Logs report `RELEASE_INPUTS=PASS cases=7` and `V2140_RELEASE_MANIFEST=PASS`; the DM-BL-010 candidate bundle is 1,729,177 bytes / `90afa55d…`. Historical DM-BL-009 run `42342362864` remains recorded in `verification/MAIN-INTEGRATION-2.14.0-20261107.md` |
| Preserved from main | Scan-loop/state-change alert refactor, MAC-rotation policy, repeat reminders, identity email, configuration visibility, non-HA fail-open CARP behaviour and the deployment verifier |
| Preserved from 2.13.x | HA/CARP role gating, O4 ageing and standby hygiene, installer pruning evidence, repair semantics, pinned inputs, deterministic bundling and rollback verification |
| Local validation | The corrected candidate builds reproducibly; focused reconciliation, installer/pruning, Python, PHP, JavaScript, catalogue and both language-engine suites passed locally. All five upgrade FreeBSD installer-jail scenarios passed on 6 November: `check`, `install`, `repair`, `rollback` and `failclosed`. The isolated `fresh` and `fresh-rollback` scenarios also passed on 6 November: 64 targets, a 64-row record, no database/configuration, a running daemon and complete restoration to empty state after an injected failure. Rollback restored all 63 upgrade targets, the prune fixture, the record and 19 core-locale state/pristine files with zero conflicts or failures |
| Deployment | `.23` only: OPNsense `26.7.8_2`; Device Monitor 2.13.3 → 2.14.0 using the normal upgrade path (`FRESH=1` not used). The execution record is `verification/DEPLOY-2.14.0-23-PLAN.md` |
| Installation | Phase 1 exact-candidate repair: `INSTALL_OK version=2.14.0 files=63 core_locales=10 pruned=0 backup=/var/backups/devicemonitor/install-v214.Uwwqu1 daemon_restarted=1 unchanged=63 repaired=0`; see `verification/PHASE1-EXACT-CANDIDATE-23-20261107.md` |
| Live rollback validation | **PASS**: preparatory restore to 2.13.3 used `JeYC44`; a fresh 2.14.0 test installation created `zGJRuq`; the live successful-install rollback restored 61 targets and the 2.13.3 record with `ROLLBACK_SUMMARY=restored=31 skipped=32 conflicts=0 failed=0` and core-locale `restored=19 removed=0 conflicts=0 failed=0`; the final 2.14.0 reinstall created `qMPS7n` |
| Acceptance | Phase 1 PASS: 42/42 manifest rows and 63/63 installer-plan/record targets matched digest/mode/owner/group; 21 `.mo` locale rows plus two `.po` source rows; ten core and eleven sidecar catalogues warning-free; nine available pristine translations preserved and `nl_NL` plugin-only as expected; `/conf/config.xml` `e86a7058…`, Device Monitor configuration `027594eb…`, logical DB `d7ed7f81…` and physical DB `796d28c7…` unchanged; SQLite `ok`; daemon `16776` → `18384` alive at 60 seconds; configd `728` → `328`; monitoring disabled with no WAL/SHM or `2525` listener; UI source version 2.14.0, authenticated UI not observed |
| State after §9.3 rollback validation (historical checkpoint) | PASS: Device Monitor `2.14.0`; 63 targets and 63-row record `d891ce68…`; database `c17874a7…`, Device Monitor configuration `027594eb…` and OPNsense configuration `c2ce5800…` unchanged at that checkpoint; daemon PID `49278` → `74577`; configd PID `30312` → `32439`; daemon alive after five seconds; monitoring `enabled=0`; no WAL/SHM. The later bounded §9.4 exercise changed the physical database representation to the consistent snapshot `796d28c7…` and retained `15ce9e6c…` as the OPNsense configuration at that historical checkpoint. The operator subsequently accepted `e86a7058…` as the Phase 1 baseline, and Phase 1 retained it unchanged |
| Backups | Pre-install `/root/dm-pre-2140/runtime-data.tgz`, 7,632,213 bytes, sha256 `ff7873ce0fbc1826663aa86c3271014c9c2ad3cdb3bd7b4eacce164a4a63753e`, containing 61 payload files, 19 core-locale files, record, consistent database and configuration; installer backups `/var/backups/devicemonitor/install-v214.JeYC44`, `install-v214.zGJRuq` and `install-v214.qMPS7n`; pre-mutation recovery point `/root/dm-validation-2140/rollback/20261105T231610Z` |
| Historical pre-Phase-1 acceptance / residual gates | Authenticated visual About/Features rendering was **PASS on operator-supplied evidence at that earlier checkpoint**: the Settings → About page showed both Device Monitor `v2.14.0` and `v2.14.0 Features and Enhancements`; no browser Network capture was supplied. This is not a Phase 1 authenticated-UI observation; Phase 1 did not authenticate or observe the UI. Live successful-install rollback is **PASS**. The isolated fresh-install and fresh-rollback jail paths are **PASS**. The bounded §9.4 monitoring exercise is **COMPLETE / ACCEPTANCE PASS**; further execution is **unauthorised**. Live evidence covers two scheduled inventory scans, direct DMTEST-only service discovery, scope-limited visibility probing and a live-observed `notified_at` schema mutation before restoration. The two SMTP messages came from direct PHP helper calls, not daemon-generated delivery; identity/service/new-device/aged/retired and fresh-host refusal were copy-only fixtures. The remaining validation limits are separate backlog items: DM-BL-011 (historical database-byte identity), DM-BL-012 (real-host `FRESH=1` and plugin lifecycle) and DM-BL-013 (full monitoring lifecycle). DM-BL-009 is **CLOSED** because its `main` integration criterion is met |
| §9.4 monitoring execution | **COMPLETE / ACCEPTANCE PASS — further execution is unauthorised.** The supervised run completed exactly two scans (`3497 → 3499`) with DMTEST-only discovery, loopback SMTP helpers and copy-only fixtures; final acceptance restored monitoring `enabled=0`, healthy services, no test processes/listener and no WAL/SHM. Configuration `027594eb…`, record `d891ce68…`, OPNsense configuration `15ce9e6c…` and all 19 core-locale files are byte-identical. The `notified_at` migration was observed live before restoration. The original database was `c17874a7…`; the consistent snapshot and historical restored file were `796d28c7…`, with identical logical digest `10460718…`, clean integrity/quick checks and 21 schema tables; the trace is in `verification/monitoring-validation/EXECUTION-20261106.md`. No retained file contains the original bytes, so the completed exercise cannot be claimed as physically byte-identical. The guard was corrected to stop and verify writers before capture, preserve original database/WAL/SHM bytes separately, retain the SQLite snapshot as an independently verified fallback, archive the post-state database, and verify restored bytes/metadata/schema/data/integrity against the original recovery copy; snapshot equivalence cannot satisfy original-byte identity. All 35 mock/disposable-copy tests pass, but this does not retroactively prove the historical bytes. §9.4 remains paused; issue #5 remains **OPEN**. Historical byte identity is tracked as **DM-BL-011** |

### DM-BL-010 — 2.14.0 catalogue-header correction (integrated; publication pending)

| Item | Value |
|---|---|
| Status | **Integrated in `main`** by PR #7 at `e9ec5486a8cc9e87e3b6d3cf6098f26ed15e1370`; **not published**. Exact-main CI run `42359428985` passed, and the exact candidate passed Phase 1 on `.23`. DM-BL-010 remains open only for publication |
| Base / candidate source | Based on `46370688fb6891a049929f2498ae62bc52b17b3e`; retained jail evidence predates the branch commit and records `CANDIDATE_SOURCE=worktree`; clean committed-tree bundle determinism passed |
| Defect | The reporter's three non-fatal `msgfmt` header warnings were reproduced exactly in the pre-repair merge path; they name `PO-Revision-Date`, `Last-Translator` and `Language-Team` and do not fail compilation |
| Correction | Catalogue generation fills only absent/empty generated header fields from real plugin metadata; existing core metadata/translations and `msgfmt --check` are preserved, incomplete/malformed inputs abort, and stderr is not broadly suppressed |
| Regression | `LOCALE_MERGE=PASS`; `RELEASE_INPUTS=PASS cases=7`; `V2140_RELEASE_MANIFEST=PASS`; `CI_CONFIG=PASS cases=6`; `CATALOGUE_DETERMINISM=PASS cases=2`; `BUNDLE_REPRODUCIBILITY=PASS cases=9`; `BUNDLE_BUILD_SAFETY=PASS cases=8` |
| Predecessors | `UPGRADE_PREDECESSORS=PASS passed=10 skipped=0`, now including the published `v2.12.1` tag; its own database code creates the starting schema |
| Candidate bundle | `dm-v2.14.0-runtime.tar.gz`, 1,729,177 bytes, SHA-256 `90afa55dd826c0dc3be8a23902b809baa465e25191dc372dc6cc2ef4e57fc243`; four builds (`build-a`…`build-d`) are byte-identical |
| Superseded evidence | Previous 2.14.0 main-integration candidate: 1,725,593 bytes, SHA-256 `5149bfd41e5842a144a9d1280c008511f20f3783932eca9beb1f48fca6173f5f`; retained, not overwritten |
| Jail validation | Existing live-2.14.0 predecessor `check`/`install`/`repair`/`rollback`/`failclosed` and fresh `fresh`/`fresh-rollback` scenarios pass. A published-v2.12.1 predecessor `check`, `install` and `rollback` pass: all 56 archive members match the tag, `devices.db` and `config.json` remain byte-identical on install, the modified legacy file is retained, and rollback restores all 63 targets, the record and 19 core-locale files |
| Evidence | `/root/dm-validation-2140/dm-bl-010-20261107/`, `/root/dm-validation-2140/phase1-90afa55d-20261107T104937Z/`, `/root/dm-backups/dm-bl-010-candidate-20261107-075441/`, `verification/DM-BL-010-CATALOGUE-HEADERS-20261107.md` and `verification/PHASE1-EXACT-CANDIDATE-23-20261107.md` |
| Live / release state | `.23` now runs the exact candidate through the same-version repair (`unchanged=63`, backup `install-v214.Uwwqu1`), with configuration, logical/physical database bytes, SQLite integrity and 19 core-locale state files preserved. Monitoring/notifications stayed disabled and services remained healthy. Published v2.12.1 and all existing tags/assets are unchanged; 2.14.0 remains unpublished |

DM-BL-010 stays **OPEN** only because publication has not occurred. Phase 1 closed the exact-candidate
live repair, warning-free current-catalogue merge, translation-preservation, target/data/config,
SQLite and service gates. It did not close the historical database-byte limitation (DM-BL-011),
real-host `FRESH=1`/plugin lifecycle (DM-BL-012) or the broader monitoring lifecycle (DM-BL-013).
Authenticated UI rendering was not observed, and the live run had no sparse-header delta because
all 63 targets were already byte-identical.

### §9.4 residual-gap classification

| Gap | Classification | Rationale |
|---|---|---|
| Physical DB byte identity (`c17874a7…` → `796d28c7…`) | **Open: DM-BL-011** — blocks an unqualified exact-restoration claim for the completed exercise; recurrence is corrected in the guard | Logical digest, schema, integrity and row counts match, so data integrity is not in question. The live replacement is traced to the historical guard's `796d28c7…` snapshot and its `08:32:04Z` recovery copy; that guard's physical expectation was the snapshot hash, not the original live hash. The original `c17874a7…` bytes were never retained, leaving the internal header/page delta unverifiable. The corrected guard now enforces original-byte identity for future authorised runs, but cannot retroactively prove the completed exercise. |
| Live `FRESH=1` and real OPNsense plugin registration/lifecycle | **Open: DM-BL-012** | The disposable jail and copy-only fixtures prove call boundaries, not real-host registration or lifecycle. Live `FRESH=1` remains untested. |
| Full reminder/ageing/CARP and daemon-generated notification/service-discovery paths | **Open: DM-BL-013** | The two scheduled scans did not run scheduled service discovery; reminders, ageing and CARP were not exercised, and helper emails were direct PHP calls. |
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
| Main integration | **Complete (7 November 2026):** PR #6 was fast-forwarded from `d5d73ed` to `2825177`, preserving all 54 commits and matching the reviewed tree; exact-main CI run `42342362864` passed. PR #7 then integrated the DM-BL-010 correction at `e9ec5486a8cc9e87e3b6d3cf6098f26ed15e1370`, where exact-main CI run `42359428985` passed. DM-BL-009 is **CLOSED**; residual validation is tracked as DM-BL-011/012/013 |
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
  on this existing `.23` installation.
* Rollback was **not invoked** by the 2.13.3 deployment. The later §9.3 2.14.0 successful-install
  live rollback cycle passed on `.23`; it is separate from the historical M5 sandbox result.
* The historical pre-deployment sandbox run did not touch `.23`, `.253` or `.252`; the later
  2.13.3 deployment touched `.23` only. `.253`/`.252` remain on 2.13.2.

**Next step:** 2.14.0 publication remains paused pending separate authorisation. The exact candidate
passed Phase 1 on `.23`; authenticated UI confirmation is still absent, and DM-BL-011, DM-BL-012 and
DM-BL-013 remain OPEN for separately authorised validation. Issue #5 remains OPEN pending reporter
confirmation. The OPNsense 26.7.8_2 update on `.23` is complete; `.23` runs the accepted exact
2.14.0 candidate with monitoring disabled.

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
real-host validation is tracked as **DM-BL-012**.

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
plugin registration. Live `FRESH=1` remains unauthorised and untested. A screenshot from the
operator's authenticated browser confirms both About and Features render `v2.14.0`; no Network
capture was supplied. Real-host `FRESH=1` and plugin lifecycle validation remain tracked as
**DM-BL-012**.

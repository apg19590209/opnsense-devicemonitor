# Device Monitor — Project State

## Current state

Last updated: 5 November 2026

Branches: `release/2.13` (HEAD `6bd122e`, the released line) and
`fix/pruning-remediation-20261103` (the 2.13.3 remediation of the pruning review, branched
from `6bd122e`). `baseline/2.12` (`d04739a`) holds the recovered pre-HA 2.12 tree;
`feature/async-db-v2.11` (`0ad95b0`) is the historical v2.11 development branch.

### Release 2.13.2 — the production/CARP field line

| Item | Value |
|---|---|
| Commit | `74e1f6f` on `release/2.13`, tag `v2.13.2` (unchanged by the remediation) |
| Payload | `release/v2.13.2-runtime.manifest`, 40 rows, staged targets 61 |
| Bundle | `dm-v2.13.2-runtime.tar.gz`, 336 261 bytes, sha256 `8fd6a7a703a63b4fa23f694d6dbd9d0aa50947f60ce23f37ffbd2c67a6b16f5a` (published; never rebuilt) |
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
| Preserved data | `devices.db` remains `c17874a717cebe2c2e1dbaf537fd13a65b4ded47e10dfcce1849f2088136144e`; Device Monitor configuration remains `8115a7eee5104e4ddad4a508caf06cbbe1822ee9722578db527104b366cb1c22`; SQLite quick/integrity checks `ok` |
| Services | configd and the Device Monitor daemon running; `configctl devicemonitor status` returned `running`; `re0` retained `192.168.20.23` and HTTPS remained listening |
| Backups | `/root/dm-os-26.7.8-preupdate`; encrypted archive `/root/dm-os-26.7.8-preupdate.tar.gz.enc`, 26,470,432 bytes, sha256 `64986b9a7564b28c53200af664f4247198d125e0748baecf8732f83909749934`; Windows copy hashes confirmed by the operator; installer `/var/backups/devicemonitor/install-v213.xKjyg1` and `/root/dm-pre-2133` retained |
| OPNsense configuration | The update generated `/conf/backup/config-1793868107.8517.xml`, byte-identical to current `/conf/config.xml` (sha256 `cbba358a646aaeb28aa63dccafdd5e971a437c21637466493e415b17b67df61b`). This is distinct from the unchanged Device Monitor configuration |
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
| Open decision | `main` vs the validated M5 checkpoint: **14 behind / 48 ahead** against the locally recorded `origin/main`, merge base `40cced8` — DM-BL-009, still **OPEN**; re-measure before any reconciliation |
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
* Still untested: a fresh install (`FRESH=1`, which needs `rc.configure_plugins` and configd).
  It remains a separate path and was never selected on this existing installation.
* Rollback was **not invoked** by the 2.13.3 deployment. The live rollback gap remains; only
  the M5 sandbox rollback scenario has been executed.
* The historical pre-deployment sandbox run did not touch `.23`, `.253` or `.252`; the later
  2.13.3 deployment touched `.23` only. `.253`/`.252` remain on 2.13.2.

**Next step:** obtain an explicit decision on the `main` reconciliation path recorded in
DM-BL-009 before any branch integration. The OPNsense 26.7.8_2 update on `.23` is complete and does
not resolve that decision; DM-BL-009 remains OPEN.

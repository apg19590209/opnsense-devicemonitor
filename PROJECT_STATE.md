# Device Monitor — Project State

## Current state

Last updated: 5 November 2026

Branches: `release/2.13` (HEAD `6bd122e`, the released line) and
`fix/pruning-remediation-20261103` (the 2.13.3 remediation of the pruning review, branched
from `6bd122e`). `baseline/2.12` (`d04739a`) holds the recovered pre-HA 2.12 tree;
`feature/async-db-v2.11` (`0ad95b0`) is the historical v2.11 development branch.

### Release 2.13.2 — the one running in the field

| Item | Value |
|---|---|
| Commit | `74e1f6f` on `release/2.13`, tag `v2.13.2` (unchanged by the remediation) |
| Payload | `release/v2.13.2-runtime.manifest`, 40 rows, staged targets 61 |
| Bundle | `dm-v2.13.2-runtime.tar.gz`, 336 261 bytes, sha256 `8fd6a7a703a63b4fa23f694d6dbd9d0aa50947f60ce23f37ffbd2c67a6b16f5a` (published; never rebuilt) |
| Deployed | `192.168.20.23` (testbed), `.253` (CARP master), `.252` (CARP standby) — 40/40 manifest parity on each |
| Rollback | `/var/backups/devicemonitor/install-v213.{6KTQFY,.HuGjkL,.ivbMZd}` |
| New behaviour | A standby ages its own inventory: `[SERVICES] Stale-state ageing (standby)` (Decision 60) |

Lineage: `2.13` (`59d6d08`, no O4 ageing, never tagged) → `2.13.1` (`19f8d4d`, tag
`v2.13.1`, O4 restored, Decision 59) → `2.13.2` (`74e1f6f`, tag `v2.13.2`, standby ageing,
Decision 60) → `2.13.3` (pruning remediation, Decision 62).

### 2.13.3 — prepared, not deployed

| Item | Value |
|---|---|
| Branch | `fix/pruning-remediation-20261103` (untagged); validated M5 checkpoint `a1f759e9b64a1265a951260d45845df46435b1be`. This is an evidence checkpoint, not a claim that this document tracks the current branch tip; see `git log` for later work |
| Payload | `release/v2.13.3-runtime.manifest`, 40 rows, staged targets 61 (62 fresh) |
| Bundle | `dm-v2.13.3-runtime.tar.gz`, 1 656 468 bytes, sha256 `7f389248707cf8fa0684760820db85c0fddac4b8b3964e0563318b38b2730fe2` — built at `/tmp`, **not published**; byte-identical on FreeBSD and Linux, any timezone, either tar implementation (Decision 63, 67, 68; `release/bundle-digest.txt`). The archive is deliberately uncompressed (stored deflate blocks) so the identity cannot depend on the host compressor; earlier identities `ce92a09a…` / 348 920, `b29e1166…` / 349 052 and `451a03f4…` / 348 932 are retired and recorded as superseded |
| Deployed | nowhere. Deployment to `.23` is a separate gated phase; `.253` / `.252` are out of scope |
| Gates | 44 suites referenced by `.github/workflows/ci.yml` (61 steps); CI at the validated M5 checkpoint `a1f759e9b64a` is **green** — run `41977736287`, 64/64 steps, zero skips (H1b closed). Earlier failing runs #41609297193, #41611564118 and #41627234610 were fixed by Decisions 67-68 |
| Installer coverage (M5) | `verification/installer-sandbox/run-installer-sandbox.sh` executes the unmodified installer from the published bundle inside a disposable FreeBSD jail: `check`, `install`, `repair`, `rollback`, `failclosed` — all PASS (`verification/REVIEW-R2-REMEDIATION-20261103.md` §Phase 3, evidence in `verification/installer-sandbox/evidence/`). Root/host-only; GitHub runners cannot create a FreeBSD jail, so it is not a CI suite |
| New behaviour | Pruning requires proof of ownership (including for bare-path records), the record covers generated targets, every executed input is pinned, a repair install is idempotent and enforces mode/ownership, rollback reports COMPLETE/INCOMPLETE and restores the record (Decisions 62-64) |

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

Pre-deployment evidence from `.23` (running 2.13.2), taken from this branch with
`install-unattended.sh --host $(/bin/hostname) --check`:

    VERIFY_OK=4
    NOTICE: merged the plugin keys into 10 core catalogue(s); uninstall.sh restores the pristine files
    CHECK_OK version=2.13.3 predecessor=2.13.2 files=61 core_locales=10 prunable=0 daemon_running=1 host=OPNsense.internal legacy_prunable=0 retained=0

`--check` stayed non-mutating: no new `/var/backups/devicemonitor/install-v213.*`
directory, `/var/db/devicemonitor/installed-manifest.txt` unchanged (mtime 01:33:16), no
staged temp directory left behind.

Known carry-over: the record currently on `.23` has 40 bare paths and no digests.
`prune-plan.sh` reads that shape as ownership evidence (content unverifiable), and the first
2.13.3 install replaces it with the digest-bearing form. Its provenance is **not** known: the
v2.13.2 tree contains no code that writes `installed-manifest.txt`
(`git grep installed-manifest v2.13.2` → nothing), so it was produced by a step outside the
installer. Only the shape matters to pruning, and the M5 sandbox reproduces it exactly.

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
* Not covered, by design: the daemon stop/wait/start branch, a fresh install (`FRESH=1`,
  needs `rc.configure_plugins` and configd) and the real `service configd restart` (stubbed,
  and used as the failure-injection point).
* `.23` was not installed, restarted or otherwise touched; `.253`/`.252` were not touched. The
  node still runs 2.13.2 with its 40-row record, and no `install-v213.*` directory was added.

**Next step:** the gated 2.13.3 deployment to `.23` (`verification/DEPLOY-2.13.3-23-PLAN.md`,
still NOT EXECUTED) — and separately the DM-BL-009 decision on how `main` is reconciled, which
this phase deliberately leaves open.

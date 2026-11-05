# Independent review round 2 — remediation checklist (`15be258`)

Baseline: `fix/pruning-remediation-20261103` @ `15be258`. Backups:
`/root/dm-review-backups/20261103-r2` (`ROLLBACK.md`, `tree-15be258.tar.gz`,
`files-15be258.sha256`). Published identity `v2.13.2` → `74e1f6f` is not touched by this
round. No deployment, tag or release publication is in scope; `.253` / `.252` are excluded.

Scope of this round as briefed: Phase 1 (H1–H3) in full; Phase 2 onward was truncated in
the brief and is recorded here as *awaiting scope* so nothing is silently dropped.

## Phase 1 — release blockers

| # | Reviewer finding | Required outcome | Status |
|---|---|---|---|
| H1a | CI cannot run on this branch (`ci.yml:4-29` lists neither the branch nor `release/2.13` for PRs) | A supported mechanism that starts the complete workflow on the remediation branch | **done** — `workflow_dispatch:` added and `fix/pruning-remediation-20261103` added to `push.branches`; every pre-existing branch entry preserved |
| H1b | "Verify that the workflow actually starts and completes, rather than checking YAML syntax" | A real GitHub Actions run id, conclusion and per-step evidence | **done** — run `41631353930` on `fix/pruning-remediation-20261103` @ `7c9d498`: conclusion `success`, 64/64 steps, zero skips. Earlier attempts #41609297193, #41611564118 and #41627234610 failed at the bundle step and were fixed by Decisions 67-69 |
| H1c | Predecessor coverage | All eight predecessor cases pass with `skipped=0`, asserted by the suite and visible in the run log | **done** — the suite now asserts `passed == len(PREDECESSORS)` and `skipped == 0`, and the CI step greps `^UPGRADE_PREDECESSORS=PASS passed=8 skipped=0$` |
| H2a | `PLAN:148-150` recommends reinstalling the published 2.13.2 bundle; that installer accepts only 2.8…2.13.1 and aborts on 2.13.3 | Recommendation removed; rollback documented through the installer's own rollback assets | **done** — the plan now states why the published installer cannot be used and gives the asset-based procedure |
| H2b | Record restoration | A manual rollback after a *successful* install also restores the previous `installed-manifest.txt` | **done** — `prune-plan.sh backup-record` / `restore-record` (digest-verified, with a digest sidecar so a damaged backup cannot be accepted); the installer calls both, in the backup phase and in `cleanup` |
| H2c | Verification | Rollback procedure executed and verified in an isolated environment, with the transcript recorded | **done** — `tests/test_rollback_isolated.py`, 3 cases (full manual rollback, fresh-install record removal, damaged-backup refusal) |
| H3a | `release/build-bundle.sh` is not byte-reproducible across checkouts (member mtimes) | Deterministic archive: normalised mtime, owner/group, member order, ustar headers, `gzip -n`, executable bits preserved | **done** |
| H3b | CI guard only compared two builds in one checkout | CI test that builds from two separate clean checkouts and compares SHA-256 | **done** — `tests/test_bundle_determinism.py` clones the tested commit twice, stamps each checkout with a different timestamp, and requires identical bytes |
| H3c | `3131b8b4…` presented as the artifact identity | New canonical digest issued and every reference updated; `3131b8b4…` recorded as superseded | **done** — canonical identity `859c2638…` / 346 870 bytes in `release/bundle-digest.txt`; `3131b8b4…` recorded there as superseded with the reason |

## Phase 2 phase — acceptance criteria (agreed before coding)

Backups for this phase: `/root/dm-review-backups/20261103-r2-phase2` (`tree-90bfcc5.tar.gz`,
sha256 `38be5b8e0b176a1f23308cd89ec07a1f195c7d88ea4f2fdd67c41d924b5486a3`; `HASHES.txt` for the
16 files in scope; `ROLLBACK.txt`).

| # | Acceptance criterion (must be an executable test, not a static assertion) | Planned test |
|---|---|---|
| M1 | A bare-path record entry prunes **only** when the on-disk digest matches published legacy evidence; an unevidenced or modified file is retained with an explicit reason | `test_prune_plan.py::test_bare_record_requires_evidence`, `::test_bare_record_modified_retained` |
| M2 | Every unresolved restore conflict yields a non-zero helper status and an explicit `ROLLBACK_STATUS=INCOMPLETE` from the installer | `test_prune_apply.py::test_conflicts_are_failures`, `::test_restore_summary` |
| M3 | The plan's database backup is a SQLite-consistent snapshot that passes `quick_check` and preserves every row | `test_plan_sqlite_backup.py` (documented snippet, plus a live read-only run when present) |
| M4 | Post-success manual rollback restores the previous record; a fresh install's record is removed | `test_rollback_isolated.py::test_manual_rollback_restores_the_pre_install_state`, `::test_fresh_install_rollback_removes_the_new_record`, plus an explicit post-success assertion |
| M5 | The installer itself executes an install, a prune, an injected failure, a rollback and a record check in isolation | **closed** — `verification/installer-sandbox/run-installer-sandbox.sh` runs the unmodified installer from the published bundle inside a disposable FreeBSD jail: `check`, `install`, `repair`, `rollback`, `failclosed`, five scenarios, `SANDBOX_RESULT=PASS` |
| M6 | Repair behaviour for mode/ownership is defined, enforced and regression-covered; unsafe drift (e.g. 0777) never survives | `test_repair_permissions.py` + `install-unattended.sh` `repaired=` reporting |
| L5 | No temporary record file survives a failed run | `test_installer_status.py::test_failed_run_leaves_no_record_temp` (static-free check on the shipped script text is insufficient → see note) |
| L6 | A prune target modified after the plan is not deleted (or aborts the run) | `test_prune_apply.py::test_changed_target_is_not_deleted` |
| L7 | A planned prune target that was never deleted is not reported as a conflict | `test_prune_apply.py::test_untouched_prune_target_is_not_a_conflict` |
| L8 | `build-release-inputs.sh` never leaves a partial `release-inputs.sha256` | `test_release_inputs.py::test_generator_is_atomic` |
| L9 | `legacy-targets.txt` provenance names each manifest once, with the tags that carried it | `test_legacy_evidence.py::test_provenance_names_each_manifest_once` |
| L10 | The release trust boundary is documented (what the tarball digest binds, what it does not) | `DECISIONS.md` Decision 63/64 + `verification` note |
| U1 | Legacy bare-path pruning covered executably | same tests as M1 |
| U2 | Installer wiring under test | **closed** with M5 — the installer's plan/backup/delete/restore/record calls execute in the sandbox (`install`, `repair`, `rollback`) |
| U3 | `--check` non-mutation proven executably | **closed** with M5 — `check` scenario: identical snapshot before/after, no `install-v213.*` directory |
| U4 | `unchanged=60` verified executably on the target host | `test_upgrade_prediction.py` (host-only, read-only) |
| U5 | Catalogue generation and merge are deterministic | `test_catalogue_determinism.py` |
| U6 | Rollback conflict behaviour covered end to end | helper level via M2/L7; installer level **closed** with M5 — `rollback` reports `ROLLBACK_SUMMARY=restored=1 ...` / `restored=2 ...` and `ROLLBACK_STATUS=COMPLETE` |
| U7 | Plan abort conditions exercised beyond the zero-candidate case | **closed for the pinned-input path** with M5 — `failclosed` tampering with `prune-plan.sh` aborts with `ABORT: release inputs` before any mutation |
| U8 | Published 2.13.2 fallback (proven impossible) | closed by H2a |


| # | Reviewer finding | Status |
|---|---|---|
| M1 | Bare-path record entries prune without content verification (`prune-plan.sh:191-194`); branch untested | **closed** - a bare-path entry now needs a published digest match, else `RETAINED unverified` (`test_prune_plan.py::test_bare_record_requires_evidence`, `::test_bare_record_modified_retained`) |
| M2 | Rollback conflicts do not fail the rollback or raise a summary flag | **closed** - conflicts set a non-zero status, `ROLLBACK_SUMMARY=` is printed and the installer reports `ROLLBACK_STATUS=COMPLETE|INCOMPLETE` (`test_prune_apply.py::test_conflicts_are_failures`, `::test_restore_summary_counts_each_outcome`) |
| M3 | Plan §2 tars a live SQLite database | **closed** - SQLite snapshot + `quick_check`, verified on a synthetic database and read-only on the live one (`test_plan_sqlite_backup.py`, 3 cases) |
| M4 | Plan §5 claims the record never needs restoring | **closed** - `backup-record`/`restore-record` with a digest sidecar; existing-install and fresh-install cases (`test_rollback_isolated.py::test_manual_rollback_restores_the_pre_install_state`, `::test_fresh_install_rollback_removes_the_new_record`, `::test_restore_record_reports_a_damaged_backup`) |
| M5 | No test executes `install-unattended.sh`; wiring asserted textually only | **closed** — the unmodified installer executes an upgrade install (61 targets, 2 pruned), a same-version repair (`unchanged=61`, record-driven prune), an injected failure with `ROLLBACK_STATUS=COMPLETE`, and a pinned-input refusal, all inside a disposable jail. Evidence: `verification/installer-sandbox/evidence/`; the source tree is unchanged, so no sandbox mode was added to the production script |
| M6 | Repair preserves mode/owner but cannot correct drift | **closed** - `enforce-target` corrects mode and ownership, leaves a correct file untouched, and fails loudly when ownership cannot be set (`test_repair_permissions.py`, 4 cases; `repaired=` in `INSTALL_OK`) |
| L1 | `PROJECT_STATE.md:31` says 8 commits | **closed** - the false count is gone |
| L2 | `PROJECT_STATE.md:35` suite/step counts | **closed** - states 42 suites / 59 steps, measured from the workflow |
| L3 | Checklist names a non-existent test | **closed** - corrected in `PRUNING_REMEDIATION_20261103.md:39` |
| L4 | `DECISIONS.md` names the removed `release/compute-prune.sh` | **closed** - naming note added to Decision 61 |
| L5 | `$INSTALLED_LIST.new` litter after a failed run | **closed executably** — the `install`, `rollback` and `failclosed` scenarios leave no `/tmp/dm_install_v213.*` directory and no `installed-manifest.txt.new` (checked in every snapshot and by `install-verify`) |
| L6 | TOCTOU between prune plan and delete | **closed** - `delete` re-hashes against the backed-up digest and aborts (`test_prune_apply.py::test_changed_target_is_not_deleted`) |
| L7 | `ROLLBACK_CONFLICT` for targets that were never deleted | **closed** - such a target is counted `skipped` (`test_prune_apply.py::test_untouched_prune_target_is_not_a_conflict`) |
| L8 | `build-release-inputs.sh` leaves a partial file on failure | **closed** - validates first, writes to `.new`, renames (`test_release_inputs.py::test_generator_is_atomic`) |
| L9 | Evidence header attributes manifests to the wrong tags | **closed** - one line per manifest with every tag that carries it (`test_legacy_evidence.py::test_provenance_names_each_manifest_once`) |
| L10 | Wrappers shipped unpinned | **closed as documentation** - Decision 63 gains an explicit trust boundary |

## Unproven assertions (all eight, per the review)

| # | Assertion | Status |
|---|---|---|
| U1 | Pruning from a legacy bare-path record | **closed** - `test_prune_plan.py::test_bare_record_requires_evidence`, `::test_bare_record_modified_retained` |
| U2 | The installer's prune/backup/delete/rollback calls under test | **closed** with M5 — the `install`, `repair` and `rollback` scenarios execute the installer and its helper calls end to end |
| U3 | `--check` non-mutation proven automatically | **closed** with M5 — `check` scenario, byte-identical snapshot before and after; still observed by hand on `.23` |
| U4 | `unchanged=60` for the 2.13.2 → 2.13.3 upgrade | **closed on the host** - `test_upgrade_prediction.py` reports `files=61 unchanged=60 replaced=1` on `.23` (read-only); it prints an explicit SKIP where no install exists |
| U5 | Same-version repair `unchanged=61` and merged-catalogue determinism | **closed** — determinism (`test_catalogue_determinism.py`) plus the `repair` scenario's second real install reporting `unchanged=61 repaired=0` |
| U6 | Rollback conflict behaviour end-to-end | **closed at helper level** - `test_prune_apply.py::test_conflicts_are_failures`, `::test_restore_summary_counts_each_outcome`, `::test_untouched_prune_target_is_not_a_conflict`; installer-level propagation **closed** by the `rollback` scenario |
| U7 | Plan abort conditions other than the zero-candidate case | **closed for the pinned-input path** by the `failclosed` scenario (`ABORT: release inputs`, nothing mutated); no other abort path was found to exercise |
| U8 | The published 2.13.2 fallback (proven impossible) | addressed by H2a |

## Phase 1 evidence log

Filled in as each item closes; entries quote the command and its output.

### H1 — CI execution

* `.github/workflows/ci.yml`: `workflow_dispatch:` added; `fix/pruning-remediation-20261103`
  added to `push.branches`; `release/2.13`, `v2.5…v2.10-development` and
  `feature/async-db-v2.11` all preserved; `pull_request.branches` deliberately unchanged
  (it filters on the PR base branch, not the head).
* Workflow shape after the change: 55 steps, 24 `run: python3 tests/…` steps, 38 distinct suites —
  as measured at `e33ac1e`. **Corrected 3 November 2026** after the Phase 2 commits
  (`bbc58e6`, `43307b1`): the workflow now has **59 steps**, 28 `run: python3 tests/…` steps and
  **42 distinct suites**, all present on disk (`tests/test_ci_config.py`). Measured in
  `verification/RELEASE-INTEGRATION-ASSESSMENT-20261103.md` §6; the superseded counts are kept here
  rather than rewritten, and `PROJECT_STATE.md` already states 42 suites / 59 steps.
* YAML parse check: `python3 -c 'import yaml; yaml.safe_load(open(".github/workflows/ci.yml"))'`
  → valid.
* Predecessors, locally: `UPGRADE_PREDECESSORS=PASS passed=8 skipped=0`, then
  `UPGRADE_PREDECESSORS_CASES=PASS cases=2`.
* **Actual GitHub Actions execution: not performed.** This phase forbids pushing the branch
  and triggering a remote workflow, and `workflow_dispatch` on GitHub only becomes usable
  once the workflow exists on the default branch. The run is the first action of the next
  phase: `git push origin fix/pruning-remediation-20261103`, then
  `gh run watch` / `gh run list --branch fix/pruning-remediation-20261103`. Until that run
  exists, H1b stays open and no CI-green claim is made anywhere in the docs.

### H2 — Rollback through the preserved assets

* `release/prune-plan.sh`: `backup-record` and `restore-record` added. The backup writes
  `installed-manifest.txt` **and** `installed-manifest.sha256`; the restore verifies the
  backup against that recorded digest before writing, so a damaged backup is refused
  instead of restored.
* `install-unattended.sh:246-247` backs the record up before the first mutation;
  `install-unattended.sh:98-101` restores (or removes) it during `cleanup`.
* `verification/DEPLOY-2.13.3-23-PLAN.md` §5 rewritten: the invalid 2.13.2 reinstall is gone,
  replaced by `restore-targets` → `restore` → `restore-record`. §2 now snapshots
  `devices.db` with `sqlite3 .backup` instead of tarring a live database.
* Isolated rehearsal: `tests/test_rollback_isolated.py` →
  `ROLLBACK_ISOLATED=PASS cases=3` (replaced target, pruned target, modes and record all
  return to their pre-install bytes; fresh-install record removal; damaged backup refused).

### H3 — Deterministic bundles

* `release/build-bundle.sh`: fixed mtime (`touch -h -t 202601010000.00`), `ustar` format,
  `--uid 0 --gid 0 --uname root --gname wheel`, sorted allow-list, `gzip -n`; modes
  untouched so executable bits survive. `DM_BUNDLE_STAGE` / `DM_BUNDLE_OUT` /
  `DM_BUNDLE_LIST` overrides let the test build two checkouts without colliding.
* Canonical identity: `release/bundle-digest.txt` → `version 2.13.3`, `bytes 346870`,
  `sha256 859c2638663260686630ed05408ab9055877988af56a84b81a2caa34688d6e48`.
  `3131b8b4…` (346 013 bytes) is recorded there as superseded, with the reason.
* `tests/test_bundle_determinism.py` → `BUNDLE_DETERMINISM=PASS cases=2` (two clean
  checkouts with different timestamps build identical bytes; the result equals the recorded
  digest).

### Local suite state after Phase 1

Phase 1 closes at commit `e33ac1e` (branch clean, not pushed).

Live integration check from that tree, on `.23` (running 2.13.2), `--check` only:

    VERIFY_OK=4
    NOTICE: merged the plugin keys into 10 core catalogue(s); uninstall.sh restores the pristine files
    CHECK_OK version=2.13.3 predecessor=2.13.2 files=61 core_locales=10 prunable=0 daemon_running=1 host=OPNsense.internal legacy_prunable=0 retained=0

`--check` stayed non-mutating (no new `install-v213.*`, record mtime unchanged at 01:33:16, no
staged temp directory), so the new pins and the extended `prune-plan.sh` work end to end
without touching the node.

| Suite | Result |
|---|---|
| `test_ci_config.py` (new) | `CI_CONFIG=PASS cases=5` |
| `test_bundle_determinism.py` (new) | `BUNDLE_DETERMINISM=PASS cases=2` |
| `test_rollback_isolated.py` (new) | `ROLLBACK_ISOLATED=PASS cases=3` |
| `test_upgrade_predecessors.py` | `passed=8 skipped=0` |
| `test_prune_plan.py` | `PRUNE_PLAN=PASS cases=10` |
| `test_prune_apply.py` | `PRUNE_APPLY=PASS cases=4` |
| `test_release_inputs.py` | `RELEASE_INPUTS=PASS cases=5` |
| `test_installer_status.py` | `INSTALLER_STATUS=PASS cases=6` |
| `test_legacy_evidence.py` | `LEGACY_EVIDENCE=PASS cases=5` |
| `test_release_manifest.py` | `V2133_RELEASE_MANIFEST=PASS` |

### Phase 2 evidence (M1–M6, L1–L10, U1–U8)

Closed at commit `bbc58e6`; bundle identity reissued as
`451a03f4bc04542ea36c36ce7df42faaf5c3e044e574ea991e74d4f5a4570ae8` (348 932 bytes),
reproduced from two clean checkouts.

**Correction (3 November 2026, Decision 67):** that identity turned out to be timezone- and
bsdtar-dependent — it only reproduced where `touch -t` ran under AEDT and where `tar` accepted
`--uid/--gid`. The first GitHub run (#41609297193) built a 20-byte archive and failed the
digest assertion. The canonical identity is now
`ce92a09a2d0ffd79bea33ca3087137264c5ef1ff992bb983b3d7e4dbf738befd` (348 920 bytes), verified
across two checkouts, three timezones and a GNU-style header re-encoding; the superseded
value is recorded in `release/bundle-digest.txt`. The 451a03f4 value above is kept as the
record of what was believed at `bbc58e6`, not as a current claim.

**Second correction (3 November 2026, Decision 68):** `ce92a09a…` was still not portable — GNU
tar on the runner padded the archive to its 10 KiB record boundary and GNU gzip compressed the
result differently (run #41627234610 built `b29e1166…` / 349 052 bytes). The canonical
identity is now `7f389248707cf8fa0684760820db85c0fddac4b8b3964e0563318b38b2730fe2`
(1 656 468 bytes): the canonicaliser terminates with exactly two zero blocks and the bundle is
compressed by `release/bundle-gzip.py` with a fixed header and stored deflate blocks, so no host
compressor is involved. Both earlier identities remain recorded as superseded.

| Suite | Result | Covers |
|---|---|---|
| `test_prune_plan.py` | `PRUNE_PLAN=PASS cases=12` | M1, U1 (bare-path requires evidence; modified retained) |
| `test_prune_apply.py` | `PRUNE_APPLY=PASS cases=8` | M2, L6, L7, U6 |
| `test_repair_permissions.py` | `REPAIR_PERMISSIONS=PASS cases=4` | M6 |
| `test_plan_sqlite_backup.py` | `PLAN_SQLITE_BACKUP=PASS cases=3` | M3 (synthetic + live read-only) |
| `test_catalogue_determinism.py` | `CATALOGUE_DETERMINISM=PASS cases=2` | U5 (determinism half) |
| `test_rollback_isolated.py` | `ROLLBACK_ISOLATED=PASS cases=3` | M4, U6 (helper level) |
| `test_release_inputs.py` | `RELEASE_INPUTS=PASS cases=6` | L8, pins |
| `test_legacy_evidence.py` | `LEGACY_EVIDENCE=PASS cases=6` | L9 |
| `test_upgrade_prediction.py` | `UPGRADE_PREDICTION=PASS files=61 unchanged=60 replaced=1` | U4 (host only) |
| `test_bundle_determinism.py` | `BUNDLE_DETERMINISM=PASS cases=2` | H3b, H3c |
| `test_ci_config.py` | `CI_CONFIG=PASS cases=5` | H1a, test selection |
| `test_installer_status.py` | `INSTALLER_STATUS=PASS cases=6` | status contract, `repaired=` |
| `test_release_manifest.py` | `V2133_RELEASE_MANIFEST=PASS` | 2.13.2 immutability |

Live read-only check from the committed tree on `.23` (still 2.13.2):

    VERIFY_OK=4
    NOTICE: merged the plugin keys into 10 core catalogue(s); uninstall.sh restores the pristine files
    CHECK_OK version=2.13.3 predecessor=2.13.2 files=61 core_locales=10 prunable=0 daemon_running=1 host=OPNsense.internal legacy_prunable=0 retained=0

No new `/var/backups/devicemonitor/install-v213.*`, record mtime unchanged, no staged temp
directory.

### Still open after Phase 2

| Item | Reason |
|---|---|
| ~~M5, U2, U3, U7~~ | **closed in Phase 3** — the installer process now executes end to end inside a disposable jail, without adding a sandbox mode to the production script |
| ~~L5~~ | **closed in Phase 3** — no staged directory and no `installed-manifest.txt.new` survives a failed run |
| ~~U5 (arithmetic half)~~ | **closed in Phase 3** — the `repair` scenario's second real install reports `unchanged=61 repaired=0` |

## Phase 3 — M5: the installer executes end to end in an isolated environment

Baseline: `fix/pruning-remediation-20261103` @ `7c9d498` (CI run `41631353930` green, 64/64
steps, zero skips). No production change: the installer, its helper, the bundle and every
published identity are untouched by this phase.

### Why a jail rather than a sandbox mode in the script

Decision 64 left M5 open on the assumption that closing it required a sandbox mode inside
`install-unattended.sh`. That mode would change the component under review, and a `--root`
style flag in an installer whose guards all key off absolute paths is exactly the sort of
change that can weaken it. The alternative used here is strictly stronger: the unmodified
installer runs against the *real* absolute paths inside a disposable FreeBSD jail whose
filesystem is the host's toolchain mounted read-only, with a writable scratch overlay
stacked over every path the installer may write.

| Property | Implementation |
|---|---|
| Artifact under test | `release/build-bundle.sh` output, digest-checked against `release/bundle-digest.txt` before use (`7f389248…`, 1 656 468 bytes) |
| Read-only base | nullfs `ro` mounts of `/bin /sbin /lib /libexec /usr /etc`, plus `devfs` |
| Writable overlay | nullfs mounts of a scratch tree over `/usr/local/etc/{inc,rc.d}`, the plugin's MVC/locales/scripts/actions.d/widgets trees, `/usr/local/share/locale`, `/etc/rc.d`, `/etc/rc.conf.d`, `/var`, `/tmp`, `/root` |
| Identity guard | the jail carries its own hostname (`dm-m5-sandbox.internal`) and a marker file; **every** installer invocation is preceded inside the jail by a marker + hostname + uid check, so a broken jail can only produce a refusal |
| Pre-installation state | the v2.13.2 tree (`git archive v2.13.2`) applied at the modes its manifest declares, the 11 compiled catalogues, the 10 merged core catalogues built with 2.13.2-era merge code, the record/database/configuration copied from the node, and two real historical leftovers whose digests are published in `release/legacy-targets.txt` (`cs_CZ_devicemonitor.po`, `en_US_devicemonitor.po` from v2.9 — the flat layout no current release installs) |
| The single stub | `service configd` is an OPNsense host service, not payload: its rc script is replaced by a stub that records the call and fails on demand (the failure-injection point). Nothing else is stubbed |

### Scenarios and results (`SANDBOX_RESULT=PASS`, `failures=0`)

| Scenario | What the installer actually did | Verified |
|---|---|---|
| `check` | `--check` on the 2.13.2 node | `CHECK_OK version=2.13.3 predecessor=2.13.2 files=61 core_locales=10 prunable=2 daemon_running=0 host=dm-m5-sandbox.internal legacy_prunable=2 retained=0`; byte-identical snapshot before/after; no `install-v213.*` directory (U3) |
| `install` | full upgrade: replacement, prune, record | `INSTALL_OK version=2.13.3 files=61 core_locales=10 pruned=2 … unchanged=60 repaired=0`; `PRUNED=2`; both leftovers preserved digest-verified in `files/prune-*` and removed from the tree; all 61 targets re-hashed against the bundle (sources, freshly compiled catalogues, core catalogues carrying the plugin strings) with manifest mode and `root:wheel`; record has 61 digest rows; `devices.db` / `config.json` byte-identical; `unchanged=60` cross-checked against the snapshot diff; 10 pristine core catalogues preserved (M5, U2, U5) |
| `repair` | second run on the 2.13.3 node, with a compiled catalogue for a dropped locale named by digest in the record | `INSTALL_OK … pruned=1 … unchanged=61 repaired=0`; `PRUNE_PLAN=RECORD …/xx_XX/…`; the dropped catalogue is removed and the record rebuilt with 61 rows (finding #2, U5) |
| `rollback` | upgrade aborted at the first step after the prune (`service configd restart` made to fail) | exit 1, `PRUNED=2`, `ROLLBACK_SUMMARY=restored=1 skipped=60 conflicts=0 failed=0`, then `restored=2 skipped=0 conflicts=0 failed=0`, `ROLLBACK_STATUS=COMPLETE`; the pre-install state is byte-identical afterwards (`defaults.json`, both pruned leftovers, record, database); exactly one rollback directory remains; the pristine-catalogue archive matches the restored catalogues (U2, U6, L5) |
| `failclosed` | `release/prune-plan.sh` tampered with before the run | `ABORT: release inputs`, exit 1, no `INSTALL_OK`, snapshot unchanged — the pin refuses before any mutation (U7, L8) |

### Boundaries of this evidence (stated, not hidden)

* **Not a CI suite.** GitHub's runners are Linux and cannot create a FreeBSD jail, so this is
  a root/host check that regenerates evidence on demand
  (`sh verification/installer-sandbox/run-installer-sandbox.sh all`). CI keeps running the 44
  root-free suites it already runs.
* **Daemon lifecycle not exercised.** The sandbox has no running daemon, so the upgrade path
  reports `daemon_restarted=0`; the stop/wait/start branch and its 30-second start poll are
  not covered. A fresh install (`FRESH=1`) is likewise not covered — it needs
  `rc.configure_plugins` and a working configd, both host services.
* `service configd restart` is stubbed, so the installer's configd interaction is exercised
  only as a call boundary.
* The prune scenarios use real historical leftovers planted in the pre-installation state;
  they are absent on `.23` today (`prunable=0` there), so no claim is made that the field node
  has anything to prune.

### Machine-readable evidence

`verification/installer-sandbox/evidence/<scenario>/` — the installer's own transcript, the
before/after snapshots, the independent verification and the pre-installation log for each
scenario. `DM_SANDBOX_SAVE=1` refreshes those files from a fresh run.

### Documentation discrepancy found while building the pre-installation state

`PROJECT_STATE.md` and Decision 62 describe the 40-row record on `.23` as "written by the
2.13.2 installer". The v2.13.2 tree contains no code that writes
`/var/db/devicemonitor/installed-manifest.txt` (`git grep installed-manifest v2.13.2` → no
matches; that tree's `release/compute-prune.sh` does not write it either), so the record's
provenance is **unknown**. What pruning depends on is its shape, which the sandbox reproduces
byte-for-byte from the node. The claim is corrected in `PROJECT_STATE.md` rather than left
standing.


### Pre-work fact-finding (recorded before any change)

* Actions is enabled on `apg19590209/opnsense-devicemonitor` (`"enabled":true,
  "allowed_actions":"all"`), default branch `main`, repo public, `gh` authenticated with
  `repo` scope, SSH to GitHub works.
* The branch `fix/pruning-remediation-20261103` has never been pushed: `gh run list` shows
  runs only for `release/2.13`, where the two parent commits did run and pass
  (`41463136372` success for `6bd122e`, `41462310789` success for `6448a5a`).
* H3 mechanism proven before touching the repo (scratch script, two independent
  `git clone -b fix/pruning-remediation-20261103` checkouts of the same commit):
  `touch -h -t <fixed>` + `tar --format ustar --uid 0 --gid 0 --uname root --gname wheel
  -T <sorted list>` + `gzip -n` → both builds produced 345 827 bytes,
  sha256 `1aa0f8015d0a7ac074407a04a83f7940d0fbed6fe5426562def9305ab93e3366`.
  Executable bits survive (`release/prune-plan.sh`, `release/verify-release-inputs.sh`
  are 755 in the archive); an extraction passes
  `release/verify-release-inputs.sh` with `VERIFY_OK=4`.

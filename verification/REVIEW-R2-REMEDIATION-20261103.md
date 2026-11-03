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
| H1b | "Verify that the workflow actually starts and completes, rather than checking YAML syntax" | A real GitHub Actions run id, conclusion and per-step evidence | **NOT EXECUTED — blocked**: this phase forbids pushing, and a remote run cannot start without one. Verified instead: YAML parses, all 38 referenced suites exist, the trigger list is asserted, and the full python suite set runs green locally (evidence below). A push is the only remaining step |
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
| M5 | The installer itself executes an install, a prune, an injected failure, a rollback and a record check in isolation | **partial** — helper-level end-to-end (`test_rollback_isolated.py`, `test_prune_apply.py`). Running `install-unattended.sh` off-target needs a sandbox mode in the production script; see the open item |
| M6 | Repair behaviour for mode/ownership is defined, enforced and regression-covered; unsafe drift (e.g. 0777) never survives | `test_repair_permissions.py` + `install-unattended.sh` `repaired=` reporting |
| L5 | No temporary record file survives a failed run | `test_installer_status.py::test_failed_run_leaves_no_record_temp` (static-free check on the shipped script text is insufficient → see note) |
| L6 | A prune target modified after the plan is not deleted (or aborts the run) | `test_prune_apply.py::test_changed_target_is_not_deleted` |
| L7 | A planned prune target that was never deleted is not reported as a conflict | `test_prune_apply.py::test_untouched_prune_target_is_not_a_conflict` |
| L8 | `build-release-inputs.sh` never leaves a partial `release-inputs.sha256` | `test_release_inputs.py::test_generator_is_atomic` |
| L9 | `legacy-targets.txt` provenance names each manifest once, with the tags that carried it | `test_legacy_evidence.py::test_provenance_names_each_manifest_once` |
| L10 | The release trust boundary is documented (what the tarball digest binds, what it does not) | `DECISIONS.md` Decision 63/64 + `verification` note |
| U1 | Legacy bare-path pruning covered executably | same tests as M1 |
| U2 | Installer wiring under test | **open** with M5 |
| U3 | `--check` non-mutation proven executably | **open** with M5 |
| U4 | `unchanged=60` verified executably on the target host | `test_upgrade_prediction.py` (host-only, read-only) |
| U5 | Catalogue generation and merge are deterministic | `test_catalogue_determinism.py` |
| U6 | Rollback conflict behaviour covered end to end | helper level via M2/L7; installer level open with M5 |
| U7 | Plan abort conditions exercised beyond the zero-candidate case | **open** with M5 |
| U8 | Published 2.13.2 fallback (proven impossible) | closed by H2a |


| # | Reviewer finding | Status |
|---|---|---|
| M1 | Bare-path record entries prune without content verification (`prune-plan.sh:191-194`); branch untested | **closed** - a bare-path entry now needs a published digest match, else `RETAINED unverified` (`test_prune_plan.py::test_bare_record_requires_evidence`, `::test_bare_record_modified_retained`) |
| M2 | Rollback conflicts do not fail the rollback or raise a summary flag | **closed** - conflicts set a non-zero status, `ROLLBACK_SUMMARY=` is printed and the installer reports `ROLLBACK_STATUS=COMPLETE|INCOMPLETE` (`test_prune_apply.py::test_conflicts_are_failures`, `::test_restore_summary_counts_each_outcome`) |
| M3 | Plan §2 tars a live SQLite database | **closed** - SQLite snapshot + `quick_check`, verified on a synthetic database and read-only on the live one (`test_plan_sqlite_backup.py`, 3 cases) |
| M4 | Plan §5 claims the record never needs restoring | **closed** - `backup-record`/`restore-record` with a digest sidecar; existing-install and fresh-install cases (`test_rollback_isolated.py::test_manual_rollback_restores_the_pre_install_state`, `::test_fresh_install_rollback_removes_the_new_record`, `::test_restore_record_reports_a_damaged_backup`) |
| M5 | No test executes `install-unattended.sh`; wiring asserted textually only | **open (partial)** - helper-level end-to-end covers replacement, pruning, injected failure, rollback and record consistency (`test_prune_apply.py`, `test_rollback_isolated.py`), but the installer process itself is still never executed. A sandbox mode inside the production script is required; see Decision 64 residual risk |
| M6 | Repair preserves mode/owner but cannot correct drift | **closed** - `enforce-target` corrects mode and ownership, leaves a correct file untouched, and fails loudly when ownership cannot be set (`test_repair_permissions.py`, 4 cases; `repaired=` in `INSTALL_OK`) |
| L1 | `PROJECT_STATE.md:31` says 8 commits | **closed** - the false count is gone |
| L2 | `PROJECT_STATE.md:35` suite/step counts | **closed** - states 42 suites / 59 steps, measured from the workflow |
| L3 | Checklist names a non-existent test | **closed** - corrected in `PRUNING_REMEDIATION_20261103.md:39` |
| L4 | `DECISIONS.md` names the removed `release/compute-prune.sh` | **closed** - naming note added to Decision 61 |
| L5 | `$INSTALLED_LIST.new` litter after a failed run | **closed by code, unverified executably** - `cleanup` removes it; proving it needs the installer to run, i.e. M5 |
| L6 | TOCTOU between prune plan and delete | **closed** - `delete` re-hashes against the backed-up digest and aborts (`test_prune_apply.py::test_changed_target_is_not_deleted`) |
| L7 | `ROLLBACK_CONFLICT` for targets that were never deleted | **closed** - such a target is counted `skipped` (`test_prune_apply.py::test_untouched_prune_target_is_not_a_conflict`) |
| L8 | `build-release-inputs.sh` leaves a partial file on failure | **closed** - validates first, writes to `.new`, renames (`test_release_inputs.py::test_generator_is_atomic`) |
| L9 | Evidence header attributes manifests to the wrong tags | **closed** - one line per manifest with every tag that carries it (`test_legacy_evidence.py::test_provenance_names_each_manifest_once`) |
| L10 | Wrappers shipped unpinned | **closed as documentation** - Decision 63 gains an explicit trust boundary |

## Unproven assertions (all eight, per the review)

| # | Assertion | Status |
|---|---|---|
| U1 | Pruning from a legacy bare-path record | **closed** - `test_prune_plan.py::test_bare_record_requires_evidence`, `::test_bare_record_modified_retained` |
| U2 | The installer's prune/backup/delete/rollback calls under test | **open** with M5 |
| U3 | `--check` non-mutation proven automatically | **open** with M5; observed twice by hand on `.23` (no backup directory, record mtime unchanged) |
| U4 | `unchanged=60` for the 2.13.2 → 2.13.3 upgrade | **closed on the host** - `test_upgrade_prediction.py` reports `files=61 unchanged=60 replaced=1` on `.23` (read-only); it prints an explicit SKIP where no install exists |
| U5 | Same-version repair `unchanged=61` and merged-catalogue determinism | **partly closed** - determinism proven (`test_catalogue_determinism.py`: msgfmt twice and both merge branches identical); the `unchanged=61` arithmetic needs a second real install, i.e. M5 |
| U6 | Rollback conflict behaviour end-to-end | **closed at helper level** - `test_prune_apply.py::test_conflicts_are_failures`, `::test_restore_summary_counts_each_outcome`, `::test_untouched_prune_target_is_not_a_conflict`; installer-level propagation open with M5 |
| U7 | Plan abort conditions other than the zero-candidate case | **open** with M5 |
| U8 | The published 2.13.2 fallback (proven impossible) | addressed by H2a |

## Phase 1 evidence log

Filled in as each item closes; entries quote the command and its output.

### H1 — CI execution

* `.github/workflows/ci.yml`: `workflow_dispatch:` added; `fix/pruning-remediation-20261103`
  added to `push.branches`; `release/2.13`, `v2.5…v2.10-development` and
  `feature/async-db-v2.11` all preserved; `pull_request.branches` deliberately unchanged
  (it filters on the PR base branch, not the head).
* Workflow shape after the change: 55 steps, 24 `run: python3 tests/…` steps, **38 distinct
  suites**, all of them present on disk (`tests/test_ci_config.py`).
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

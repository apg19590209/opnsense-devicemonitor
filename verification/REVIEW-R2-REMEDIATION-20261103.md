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

## Phase 2 — pruning (brief truncated; scope to be supplied)

| # | Reviewer finding | Status |
|---|---|---|
| M1 | Bare-path record entries prune without content verification (`prune-plan.sh:191-194`); branch untested | awaiting scope |
| M2 | Rollback conflicts do not fail the rollback or raise a summary flag (`prune-plan.sh:278,327,336`) | awaiting scope |
| M3 | Plan §2 tars a live SQLite database | awaiting scope |
| M4 | Plan §5 claims the record never needs restoring (false for a post-success manual rollback) | awaiting scope |
| M5 | No test executes `install-unattended.sh`; wiring asserted textually only | awaiting scope |
| M6 | Repair preserves mode/owner but cannot correct drift | awaiting scope |
| L1 | `PROJECT_STATE.md:31` says 8 commits; there are 2 | awaiting scope |
| L2 | `PROJECT_STATE.md:35` "22 python suites … 8 new or rewritten" (34 suites referenced; 7 test files changed) | awaiting scope |
| L3 | Checklist `:39` names `test_rollback_restores_everything`; actual `test_rollback_restores_pruned_and_replaced` | awaiting scope |
| L4 | `DECISIONS.md:2658` still names the removed `release/compute-prune.sh` | awaiting scope |
| L5 | `$INSTALLED_LIST.new` litter after a failed run (`install-unattended.sh:394-396`) | awaiting scope |
| L6 | TOCTOU between prune plan (`:206`) and delete (`:327`) | awaiting scope |
| L7 | `ROLLBACK_CONFLICT` for planned prune targets that were never deleted (`prune-plan.sh:277-280`) | awaiting scope |
| L8 | `build-release-inputs.sh` leaves a partial `release-inputs.sha256` on failure | awaiting scope |
| L9 | `legacy-targets.txt` source header attributes manifests to the wrong tags | awaiting scope |
| L10 | `install.sh` / `uninstall.sh` shipped unpinned (root of trust = tarball digest) | awaiting scope |

## Unproven assertions (all eight, per the review)

| # | Assertion | Status |
|---|---|---|
| U1 | Pruning from a legacy bare-path record | awaiting scope |
| U2 | The installer's prune/backup/delete/rollback calls under test | awaiting scope |
| U3 | `--check` non-mutation proven automatically (not just statically + manually) | awaiting scope |
| U4 | `unchanged=60` for the 2.13.2 → 2.13.3 upgrade | awaiting scope |
| U5 | Same-version repair `unchanged=61` and merged-catalogue determinism | awaiting scope |
| U6 | Rollback conflict behaviour end-to-end | awaiting scope |
| U7 | Plan abort conditions other than the zero-candidate case | awaiting scope |
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

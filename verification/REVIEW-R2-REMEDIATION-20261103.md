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
| H1a | CI cannot run on this branch (`ci.yml:4-29` lists neither the branch nor `release/2.13` for PRs) | A supported mechanism that starts the complete workflow on the remediation branch | open |
| H1b | "Verify that the workflow actually starts and completes, rather than checking YAML syntax" | A real GitHub Actions run id, conclusion and per-step evidence captured in this file | open |
| H1c | Predecessor coverage | All eight predecessor cases pass with `skipped=0`, asserted by the suite and visible in the run log | open |
| H2a | `PLAN:148-150` recommends reinstalling the published 2.13.2 bundle; that installer accepts only 2.8…2.13.1 and aborts on 2.13.3 | Recommendation removed; rollback documented through the installer's own rollback assets | open |
| H2b | Record restoration | A manual rollback after a *successful* install also restores the previous `installed-manifest.txt` (the installer must keep a copy in the rollback directory) | open |
| H2c | Verification | Rollback procedure executed and verified in an isolated environment, with the transcript recorded | open |
| H3a | `release/build-bundle.sh` is not byte-reproducible across checkouts (member mtimes) | Deterministic archive: normalised mtime, owner/group, member order, ustar headers, `gzip -n`, executable bits preserved | open |
| H3b | CI guard only compared two builds in one checkout | CI test that builds from two separate clean checkouts and compares SHA-256 | open |
| H3c | `3131b8b4…` presented as the artifact identity | New canonical digest issued and every reference updated; `3131b8b4…` recorded as superseded unless reproduced by the corrected process | open |

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

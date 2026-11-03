# Pruning review remediation — 2.13.2 `6bd122e` → 2.13.3

Source review: the 11 findings raised against `release/2.13` HEAD `6bd122e` (pruning and
repair commits `6448a5a` / `6bd122e`).

Branch: `fix/pruning-remediation-20261103` (from `release/2.13` @ `6bd122e`).
Backups: `/root/dm-review-backups/20261103-pruning-remediation` (+ `BACKUP-DIGESTS.txt`).
Published release preserved: tag `v2.13.2` → `74e1f6f`, `release/v2.13.2-runtime.manifest`
untouched (pinned by `tests/test_release_manifest.py`); `dm-v2.13.2-runtime.tar.gz` is never
rebuilt under that name.

Each row is one review finding. Status is updated in the same commits as the fix.

| # | Finding (review of `6bd122e`) | Fix | Status |
|---|---|---|---|
| 1 | Pruning can never remove the files that justify it: no bootstrap, so legacy leftovers survive forever (Decision 61 "residual risk" is permanent, not deferred) | Trusted legacy evidence (`release/legacy-targets.txt`) built from the historical release manifests; a path is prunable only when its on-disk digest matches a published digest in an approved namespace. Ambiguous files retained and reported | done |
| 2 | Record is not the exact owned set: 40 manifest paths recorded vs 61 installed; a dropped language leaves its `.mo` and merged catalogue behind. Naive "record the plan" fix would delete the 11 `.mo` files just installed | Both sides of the diff are the running install's own target set (manifest ∪ generated catalogues); record carries digests. `tests/test_prune_plan.py` pins "current generated catalogues retained" and "dropped generated output identified" | done |
| 3 | `release/compute-prune.sh` executed without verification, while the manifest and every payload source are pinned | `release/release-inputs.sha256` covers every executed/data input; `release/verify-release-inputs.sh` enforces it; `install-unattended.sh` pins the inputs file itself and aborts before any mutation | done |
| 4 | `:46-47` claims "unchanged files are left alone"; the loop re-installs all 61 targets | Unchanged targets (`old == new`) are skipped, metadata preserved; `unchanged=<n>` reported; documentation corrected | done |
| 5 | `test_upgrade_predecessors.py` passes with all predecessors SKIPPED; 2.13.2 repair case missing | Strict by default (`SKIPPED` fails), `ALLOW_SKIPPED_PREDECESSORS=1` for deliberate local shallow runs, `2.13.2 → 2.13.2` row added | done |
| 6 | Prune rollback reads `old_hash` and never verifies it; blind `cp -p` | `prune-plan.sh restore` verifies every restored digest and exits non-zero on failure; conflicts reported separately | done |
| 7 | `pruned=<n>` counts `rm -f` calls, including already-absent files | Count only files that were actually removed | done |
| 8 | `sort`/`comm` depend on ambient locale; `grep … \|\| true` swallows real errors | `LC_ALL=C` on both sides; pipeline failures are hard errors | done |
| 9 | Release identity drift: same "2.13.2" name covers two trees, bundle digest/gate count stale, status shape changed mid-release | v2.13.3: manifest, defaults, installer, README, PROJECT_STATE, DECISIONS 62, append-only status contract + contract test | done |
| 10 | No field evidence for the prune/repair path (record stamped 28 s before the commit that permits it, no matching backup dir) | Tracked `.23` deployment plan delivered for a separate gated phase; not executed here | done |

Acceptance tests (all root-free, all in CI):

| Acceptance criterion | Test |
|---|---|
| Current installed targets are never pruned | `test_prune_plan.py::test_current_targets_never_pruned` |
| Paths outside approved namespaces are never pruned | `test_prune_plan.py::test_namespace_guard` |
| Legacy ownership requires trusted evidence | `test_prune_plan.py::test_legacy_requires_evidence` |
| Modified historical files are retained | `test_prune_plan.py::test_modified_legacy_retained` |
| Current generated catalogues are retained | `test_prune_plan.py::test_current_generated_retained` |
| Dropped generated outputs can be identified safely | `test_prune_plan.py::test_dropped_generated_identified` |
| Empty and identical records produce empty prune plans | `test_prune_plan.py::test_empty_and_identical` |
| Unverified pruning scripts cannot execute | `test_release_inputs.py::test_corrupted_helper_is_refused` |
| Failed installs restore replaced and pruned files | `test_prune_apply.py::test_rollback_restores_everything` |
| Same-version repair behaves as documented | `test_upgrade_predecessors.py` (2.13.2 row) + `test_installer_status.py` |
| No unexpected skipped predecessors in full CI | `test_upgrade_predecessors.py::test_every_predecessor_upgrades` |
| No installer mutation during `--check` | `test_installer_status.py::test_check_is_non_mutating` |

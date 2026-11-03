# Release Integration Assessment — 2.13.3 into `release/2.13` (3 November 2026)

Read-only assessment performed in `/root/src/opnsense-devicemonitor-upstream` (session entered via
`/usr/local/bin/cline-dm`). No merge, rebase, reset, cherry-pick, push, tag, release, deployment or
runtime change was made while producing the findings; this file is the only artifact, recorded in a
separate documentation-only commit.

Reference: Decision 66. Related: DM-BL-009 (still **OPEN**), Decision 63 (bundle identity),
Decision 65 (workspace authority).

## 1. Identity under assessment

| Item | Value |
|---|---|
| Branch | `fix/pruning-remediation-20261103` |
| HEAD | `3bdbb2081fbb851ebc3cde776fa36aa131f796ee` (parent `43307b1`) |
| Working tree | clean, 0 untracked, no stash |
| Remote refs at assessment | `main` = `d5d73ed`, `release/2.13` = `6bd122e` — identical to the local tracking refs, so no fetch was needed |
| Branch published? | no — `git ls-remote --heads origin` returns nothing for it |

## 2. Branch against the two candidate bases

| Base | Merge base | Behind | Ahead | Relationship |
|---|---|---|---|---|
| `origin/release/2.13` (`6bd122e`) | **`6bd122e`** — *fix(installer): accept a same-version repair install…* | **0** | **10** | strict superset: the release head is an ancestor |
| `origin/main` (`d5d73ed`) | `40cced8` — *docs: record the HA safety deployment…* | 14 | 41 | diverged (DM-BL-009) |

Branch-only commits against `release/2.13`, oldest first:
`d3c462e` (Decision 62), `15be258` (2.13.3 plan, reproducible digest, CI gate), `09b20b2`,
`e33ac1e` (Decision 63), `90bfcc5`, `d9db18c`, `bbc58e6` (Decision 64), `f1ad30c`,
`43307b1` (stat(1) dialect by OS), `3bdbb20` (workspace protection, Decision 65).

`release/2.13` carries **no** commit the branch lacks.

`main`-only commits (14) are the v2.12 development line the release branch never carried:
`8ea1203 release: v2.12`, `c494485 merge: bring v2.12 (and the About-version fix) onto main`,
`c9373b8 fix(ha)`, `a12ede8 feat(identity)`, `3ed1447 fix(config)`, `6dd57fc feat(alerts)`,
`acff225 feat(deploy)`, `d268680 fix(devicemonitor)`, `d5d73ed test: pin fail-open non-HA`,
plus docs/chore commits.

## 3. What a 2.13.3 install actually changes (`v2.13.2 → HEAD`)

| Area | Files | Note |
|---|---|---|
| `src/` | **1** | `defaults.json`: `"version": "2.13.2"` → `"2.13.3"` |
| `release/` | 9 | `prune-plan.sh` (+531), `build-legacy-evidence.sh`, `build-release-inputs.sh`, `verify-release-inputs.sh`, `legacy-targets.txt`, `v2.13.3-runtime.manifest`, `release-inputs.sha256`, `bundle-digest.txt`, `build-bundle.sh` — +979/−15 |
| `tests/` | 14 | new and rewritten suites |
| `.github/` | 1 | `ci.yml` gates and triggers |
| `verification/` | 5 | review and deployment records |

No PHP controller/view, locale catalogue or daemon-code change beyond the version string.

## 4. Conflicts

**Into `release/2.13`: none, by construction.** The release head is an ancestor, so integration is a
fast-forward. Verified without touching the repository:
`git merge-tree --write-tree --name-only release/2.13 fix/pruning-remediation-20261103` → **exit 0,
zero conflicted paths**, produced tree `f9599bce5ffd8e9ce5e4b480e400d5dce1d32835`, which is exactly
HEAD's own tree.

**Into `main` (informational only, not a candidate for this release):** 18 conflicted paths — 11
`devicemonitor.po` catalogues (`cs_CZ`, `de_DE`, `en_US`, `es_ES`, `fr_FR`, `it_IT`, `ja_JP`,
`nl_NL`, `pt_BR`, `ru_RU`, `zh_CN`) plus `PROJECT_STATE.md`, `README.md`, `install-unattended.sh`,
`release/build-bundle.sh`, `tests/test_release_manifest.py`, and
`src/opnsense/mvc/app/models/OPNsense/DeviceMonitor/defaults.json` and
`src/opnsense/scripts/OPNsense/DeviceMonitor/scan_network.py`. This analysis was run in a throwaway
`--shared` clone under `/tmp` that has been removed; the canonical repository was never written to.

## 5. Does the branch include all of v2.13.2?

Yes. `v2.13.2` (`74e1f6f`, tag object `011100a0…`) is an ancestor of both `origin/release/2.13` and
HEAD, and the branch's merge base with the release line *is* the release head `6bd122e` (which itself
sits on `0765c55` and `6448a5a`, the sibling-repair and predecessor fixes). The released
`release/v2.13.2-runtime.manifest` is untouched by the branch and still carries its 40 rows.


## 6. Bundle, pinned inputs and test wiring

| Check | Result |
|---|---|
| `release/bundle-digest.txt` | `version 2.13.3`, `bytes 348932`, `sha256 451a03f4bc04542ea36c36ce7df42faaf5c3e044e574ea991e74d4f5a4570ae8` |
| Same identity elsewhere | `PROJECT_STATE.md:33`, `verification/DEPLOY-2.13.3-23-PLAN.md:9,32`, `verification/REVIEW-R2-REMEDIATION-20261103.md:168` — all identical; `fc53aaa1…`, `859c2638…`, `3131b8b4…` appear only as documented superseded identities |
| Pinned install inputs | `sh release/verify-release-inputs.sh` → `VERIFY_OK=4`, exit 0 |
| `release/v2.13.3-runtime.manifest` vs tree | 40 rows re-hashed read-only → 40 ok, 0 mismatched |
| `release/v2.13.2-runtime.manifest` | 40 rows, unchanged from the tag |
| Workflow gates present | `^UPGRADE_PREDECESSORS=PASS passed=8 skipped=0$`; pinned install inputs; bundle determinism across checkouts; repair permissions; catalogue determinism; CI-config validation |
| Workflow shape measured today | **59 steps**, 28 `run: python3 tests/…` steps, **42 distinct suites**, 42 present on disk |
| Suites executed for this assessment | **none** (read-only; no workspace writes) |
| Remote CI for this branch | **never executed** — branch unpublished; `REVIEW-R2` H1b remains *NOT EXECUTED* |

## 7. Recommended integration path

1. **Fast-forward `release/2.13` (recommended).** Publish the branch so the workflow runs on
   `fix/pruning-remediation-20261103` (it is in `push.branches`), then fast-forward `release/2.13` to
   the chosen commit — `43307b1` (payload only) or `3bdbb20` (payload + workspace tooling; it touches
   no `src/` or `release/` file, so the bundle identity is unaffected). No merge commit, no rewritten
   history, no conflicts, and a second CI run on the `release/2.13` push.
2. **`--no-ff` merge into `release/2.13`.** Same tree, one extra merge commit. Acceptable, but it adds
   a commit with no review value when the base is already an ancestor.
3. **Pull request into `release/2.13`.** Usable for review, but note the trap: `ci.yml`
   `pull_request.branches` lists only `v2.5…v2.10-development`, so a PR with base `release/2.13`
   **starts no CI**, and the UI buttons either add a merge commit or squash/rebase the ten commits,
   which rewrites their SHAs and invalidates the evidence trail (the content digest survives, the
   commit references do not).
4. **Rebase onto `release/2.13` or `main`.** Rewrites all ten commits and, against `main`, replays
   onto the v2.12 divergence. Not recommended and not permitted under the current restrictions.
5. **Merging `main` into the branch.** Not needed for a 2.13.x patch: it would drag the v2.12 line
   into 2.13.3 and require 18 conflict resolutions. Land 2.13.3 on `release/2.13` first, then
   reconcile `release/2.13 → main` as its own reviewed change (DM-BL-009).

**Conclusion:** `release/2.13` can be fast-forwarded without conflicts. **No merge and no rebase is
necessary**, and neither was performed.

## 8. Outstanding items (nothing marked resolved)

1. **DM-BL-009 — OPEN.** `origin/main` divergence is 14 behind / 41 ahead, merge base `40cced8`.
   Recorded, not resolved.
2. **H1b — remote CI never executed.** The first authorised push is the only way to close it; until
   then no green-CI claim is made anywhere in this repository.
3. **Branch unpublished**, so the workflow gate cannot have produced a run for `3bdbb20`.
4. **Payload scope decision open:** fast-forward to `43307b1` (release line stays product-only) or to
   `3bdbb20` (workspace tooling and Decision 65 ride along). Both are fast-forwards.
5. **Suite-count correction applied** to `REVIEW-R2` (38 → 42) in the same documentation commit, to
   match the measured workflow; its older "55 steps / 24 `run:` steps" shape line is corrected
   alongside it and dated.

## 9. Acceptance checks for the documentation commit

| Check | Command | Expected |
|---|---|---|
| Identity | `git rev-parse HEAD` before/after | `3bdbb20…`, then the new docs commit |
| Pre-commit guard active | `git config core.hooksPath` | `.githooks` |
| No unqualified count | `grep -rn '38 distinct\|38 referenced' verification/` | only the dated "as measured at `e33ac1e`" mention and the "38 → 42" correction remain |
| Suite count matches workflow | `grep -oE 'tests/test_[A-Za-z0-9_]+\.py' .github/workflows/ci.yml \| sort -u \| wc -l` | `42` |
| Bundle identity intact | `cat release/bundle-digest.txt` | `451a03f4…` / 348932 |
| Pinned inputs intact | `sh release/verify-release-inputs.sh` | `VERIFY_OK=4` |
| Tag untouched | `git rev-parse v2.13.2` / `git ls-remote --tags origin refs/tags/v2.13.2` | `011100a0…` → `74e1f6f` |
| DM-BL-009 still open | `grep -n 'DM-BL-009' PRODUCT_BACKLOG.md` | header still `**OPEN**` |
| Docs-only scope | `git show --stat HEAD` | `verification/`, `PROJECT_STATE.md`, `PRODUCT_BACKLOG.md`, `DECISIONS.md` only |

## 10. Backups and rollback

Backup set: `/root/dm-docs-backup-20261103/` — `branch-3bdbb20.bundle` (complete history, verified),
`HEAD.txt` (`3bdbb20…`), copies of `PROJECT_STATE.md`, `PRODUCT_BACKLOG.md`, `DECISIONS.md`,
`verification/REVIEW-R2-REMEDIATION-20261103.md`, and `SHA256SUMS` over all of them.

Rollback, in order of blast radius:

1. This commit only: `git reset --soft HEAD~1` (documentation edits return to the index).
2. Discard the edits entirely: `git reset --hard 3bdbb20` (working tree returns to the assessed
   state; the backup copies remain authoritative for the four edited files).
3. Restore one file: verify it against `SHA256SUMS`, then
   `cp /root/dm-docs-backup-20261103/<file> .`.
4. Whole branch: `git clone /root/dm-docs-backup-20261103/branch-3bdbb20.bundle`.
5. Repository-wide: `/root/dm-consolidation-backup-20261103/upstream/upstream-all.bundle`
   (499 commits / 48 refs).

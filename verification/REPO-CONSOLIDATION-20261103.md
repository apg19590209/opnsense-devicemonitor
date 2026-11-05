# Repository Consolidation and Workspace Protection — 2026-11-03

Status: **consolidation complete (refs only)**. No push, no tag, no release, no history rewrite,
no directory removal. One decision is outstanding: `fix/pruning-remediation-20261103` has
**diverged from published `main`** (see §6).

Canonical repository: `/root/src/opnsense-devicemonitor-upstream`
(`origin` = `git@github.com:apg19590209/opnsense-devicemonitor.git`)

## 1. Inventory at start of work

| Path | Kind | Branch @ HEAD | Remote | Tree state | Unique work |
|---|---|---|---|---|---|
| `/root/src/opnsense-devicemonitor-upstream` | independent clone, own `.git` (15 MB), last fetch 2026-10-09 | `fix/pruning-remediation-20261103` @ `43307b19e692e1f12f9a34076fbff0eefcfdf14f` | `git@github.com:…/opnsense-devicemonitor.git` | clean, 0 untracked, no stash, no submodules | 9 branch commits on no remote + 16 `cline checkpoint` objects |
| `/usr/local/cline-freebsd/src/cline` | independent clone, own `.git` (6.4 MB); **`origin` is the Device Monitor repo** | `main` @ `d5d73ed` | `https://github.com/apg19590209/opnsense-devicemonitor` | clean — Cline files are *ignored*, not tracked | 0/0 vs `origin/main`; owns the two worktrees below |
| `/root/o3-branch` | linked worktree of the clone above (`gitdir: …/cline/.git/worktrees/o3-branch`) | `feature/sidecar-catalogue-20260928` @ `a59d627` = `origin` | shared object store | clean, 0 untracked | **none** (0 ahead / 0 behind) |
| `/root/tb-branch` | linked worktree of the clone above (`gitdir: …/cline/.git/worktrees/tb-branch`) | `feature/testbed-customisations-20260928` @ `d70aff4` = `origin` | shared object store | clean, 0 untracked | **none** (0 ahead / 0 behind) |

Other Git repositories on this host, **excluded** from consolidation as non-Device-Monitor:
`/root/src/cline-github`, `/root/src/cline-freebsd-port`, `/root/opencode-freebsd/bun-freebsd`,
`/root/opencode-node/opencode`.

### 1a. Identity correction (important)

`/usr/local/cline-freebsd/src/cline` is **not a separate project repository**. It is a second clone
of `apg19590209/opnsense-devicemonitor`, and the Cline installation is untracked content inside its
worktree (`apps/`, `sdk/`, `evals/`, `node_modules/`, `bun.lock`, `biome.json`, `package.json`,
`Makefile`, `.cline*`, `.clinerules/*`, …). Those paths are hidden from Git by
`.git/info/exclude`, whose first line is `/*`, with only `PRODUCT_BACKLOG.md`, `PROJECT_STATE.md`,
`.gitignore`, `verification/` and `.clinerules/general.md` re-included (negated).

Consequence: Cline content cannot be committed into Device Monitor by a plain `git add -A` in that
clone, and it was **not merged** here. `git add -f` / `git commit -a` after a forced add remain a
contamination path — see §7.

## 2. Backups (created before any mutation, verified)

Location: `/root/dm-consolidation-backup-20261103/` (7.2 MB total), `SHA256SUMS` covers 14 files.

| File | SHA256 |
|---|---|
| `upstream/upstream-all.bundle` (complete history) | `cdf6a50203fdec143a09701624220951d04b9ac17f994a397745977ee50dce6d` |
| `cline-clone/cline-clone-all.bundle` (complete history) | `69e71d7837a33e9debbb40850aee1b9efc0ef299d1856f0da8217d4bd6b880b3` |
| `worktrees/worktree-admin.tar.gz` | `8aaee04647e869a3ad87803e9cc84cfdb50a4c2a9c0dea51c8b733fe1b4a5e3f` |
| `worktrees/o3-branch-worktree.tar.gz` | `f7f7c33a48621d3fdb1949c9ada0839f0de4c6ff5d3db265c3183db7f2e98ace` |
| `worktrees/tb-branch-worktree.tar.gz` | `0cd69fbb5f242b62a5dd40b555fe4413141092fe57cd02c78450e5f52672f9fc` |

Also captured: `upstream/all-refs.txt` (48 refs), `upstream/HEAD.txt`, `upstream/status.txt` (empty),
`upstream/stash.txt` (empty), `upstream/git-config.txt`, `cline-clone/all-refs.txt` (35 refs),
`cline-clone/worktree-list.txt`, `cline-clone/info-exclude.txt`, `cline-clone/git-config.txt`.

### Restore verification (restore into empty bare repos, `+refs/*:refs/*`)

| Bundle | RESTORED refs / commits | SOURCE refs / commits |
|---|---|---|
| `upstream-all.bundle` | 49 / **499** | 48 / **499** |
| `cline-clone-all.bundle` | 35 / **446** | 35 / **446** |

`git bundle verify` reports "The bundle records a complete history" for both. A plain
`git clone <bundle>` drops the custom `refs/cline/checkpoints/*` namespace (35 upstream / 5 cline-clone
commits), so restore tests must use the `+refs/*:refs/*` refspec — recorded here so a future restore
does not under-restore.

## 3. Actions taken in the canonical repository

1. `git fetch --prune --tags origin`
   - `main`: `a9294ae..d5d73ed` (local `origin/main` had been stale since 2026-10-09)
   - **pruned** `origin/feature/o4-sidecar-views-20260928` (`8e02763`, deleted upstream after PR #3 merged)
   - new: `origin/fix/scan-loop-and-alert-noise-20261101` (`92072a5`), tags `v2.12`, `v2.13`, `v2.13.1`, `v2.13.2`
2. `git fetch origin main:main` — local `main` fast-forwarded `a9294ae → d5d73ed` (no rewrite).
3. Created local tracking branches for the only work the two worktrees held, at the **identical**
   published commits: `feature/sidecar-catalogue-20260928` → `a59d627`,
   `feature/testbed-customisations-20260928` → `d70aff4`.
4. Working tree untouched: `HEAD` still `43307b19e692e1f12f9a34076fbff0eefcfdf14f`, `git status` clean
   apart from this file.

`/usr/local/cline-freebsd/src/cline`, `/root/o3-branch` and `/root/tb-branch` were **not modified**
(no `worktree remove`, no repointing, no writes).

## 4. Unique work — final disposition

- `/root/o3-branch`: 0 unique commits, 0 uncommitted, 0 untracked, no stash → nothing to preserve
  beyond the published `a59d627`.
- `/root/tb-branch`: 0 unique commits, 0 uncommitted, 0 untracked, no stash → nothing to preserve
  beyond the published `d70aff4`.
- Canonical `fix/pruning-remediation-20261103`: 9 remediation commits on no remote —
  `d3c462e`, `15be258`, `09b20b2`, `e33ac1e`, `90bfcc5`, `d9db18c`, `bbc58e6`, `f1ad30c`, `43307b1` —
  based on `6bd122e` (`origin/release/2.13`).
- 16 further objects reachable only from `refs/cline/checkpoints/*` in the canonical clone are Cline
  session stash artefacts, preserved in the bundle, not Device Monitor history.

## 5. Containment results

- `origin/main` (`d5d73ed`) **is not** an ancestor of `43307b1`.
- `origin/release/2.13` (`6bd122e`) **is** an ancestor of `43307b1`.
- Published refs not contained in `43307b1` (expected, independent lines of work):
  `origin/main`, `origin/feature/locale-verification-20260928`,
  `origin/feature/optional-locale-installer-20260927`, `origin/feature/sidecar-catalogue-20260928`,
  `origin/feature/testbed-customisations-20260928`, `origin/fix/scan-loop-and-alert-noise-20261101`.

## 6. OUTSTANDING — divergence requiring a decision

`git rev-list --left-right --count origin/main...HEAD` → **14 / 40**.
Merge base: `40cced8` — *"docs: record the HA safety deployment and installed-bytes uplink refusal proof"*.

- 14 commits exist on `origin/main` that the branch does not contain, including `8ea1203 release: v2.12`,
  `c494485 merge: bring v2.12 (and the About-version fix) onto main`, `c9373b8 fix(ha)`,
  `a12ede8 feat(identity)`, `d268680 fix(devicemonitor)` and `d5d73ed test: pin fail-open non-HA behaviour`.
- 40 commits exist on the branch that `main` does not contain.
- **No merge, rebase or force was performed.** Both `main` and the branch are published-or-pending
  history; choosing merge vs rebase vs open a PR against `release/2.13` is an owner decision.

## 7. Outstanding findings (no action taken)

1. `/usr/local/cline-freebsd/src/cline` still has `origin` = the Device Monitor repository while
   carrying an untracked Cline installation. Repointing its remote (or copying Cline into a genuine
   Cline repository) needs the intended Cline remote URL.
2. `verification/` is re-included in that clone's `.git/info/exclude`, so this file would be visible
   there; it is committed nowhere.
3. Root filesystem is at 90 % (2.8 GiB free); keep the 7.2 MB backup set but avoid large artefacts.
4. Canonical local branches `feature/async-db-v2.11` (`0ad95b0`) and
   `feature/optional-locale-installer-20260927` (`c1fa466`) have **no upstream configured** although
   their commits are contained in published refs — cosmetic only.

## 8. Corrected CI verification context

The previous verification attempt halted because it ran in `/usr/local/cline-freebsd/src/cline`, where
`fix/pruning-remediation-20261103` and `43307b1` do not exist. Both exist here, in the canonical
repository — the work was never missing. Remote CI for this commit still cannot run until the branch
is published; `origin` has no `fix/pruning-remediation-20261103`, and no workflow run exists for
`43307b1`. Publishing is **not** authorised by this task and was not performed.

## 9. Explicitly not performed

Deployment to `.23`, `.253`, `.252`; tag creation; release publication; branch publication or
force-push; history rewrite; merging the Cline installation into Device Monitor; deletion of
`/root/o3-branch`, `/root/tb-branch` or any other directory; `git worktree remove`.

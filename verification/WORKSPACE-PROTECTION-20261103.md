# Workspace Protection and Canonical Launcher — 2026-11-03

Status: **complete**. No push, tag, release or deployment. The repository divergence remains an
open decision (`PRODUCT_BACKLOG.md` DM-BL-009). Reference: Decision 65.

Canonical workspace: `/root/src/opnsense-devicemonitor-upstream`
(`origin` = `git@github.com:apg19590209/opnsense-devicemonitor.git`)

## 1. Launcher — `/usr/local/bin/cline-dm`

Mode `0755`, POSIX `sh` (FreeBSD `/bin/sh`, no bash constructs). Behaviour:

| Step | Implementation |
|---|---|
| Enter the workspace | `cd /root/src/opnsense-devicemonitor-upstream`; a missing directory is a hard failure that names the backup |
| Verify Git identity | `.git` must exist (never `git init`); `git rev-parse --show-toplevel` must equal the canonical path |
| Verify remote identity | `origin` must contain `apg19590209/opnsense-devicemonitor` |
| Display state | prints `workspace`, `remote`, `branch`, `head`, `dirty`; warns on an unexpected branch |
| Launch | `exec /usr/local/cline-freebsd/bin/cline --cwd <canonical> "$@"` |
| Refuse drift | rejects `-c/--cwd`, `--worktree`, `--update`; never clones, initialises, switches, checks out or resets |

The Cline executable used is `/usr/local/cline-freebsd/bin/cline` (Cline CLI 3.0.62, the FreeBSD
port wrapper). `/usr/local/bin/cline` — the npm wrapper — **cannot** resolve a FreeBSD binary and is
not used:

    Could not find the Cline CLI binary for your platform.
    Your platform: freebsd x64
    Looked for: "@cline/cli-freebsd-x64"

Guard transcripts:

    $ cline-dm -c /tmp --version
    cline-dm: ERROR: the workspace is pinned to /root/src/opnsense-devicemonitor-upstream; -c/--cwd is not accepted
    $ cline-dm --worktree
    cline-dm: ERROR: --worktree creates a Git worktree, which this workspace forbids
    $ cline-dm --update
    cline-dm: ERROR: --update modifies the Cline installation, which this workspace forbids

## 2. Verified workspace selection (actual process inspection)

Launch: `cline-dm -i` under a pty (`script -q`). Launched process:

    55842 55028 /usr/local/cline-freebsd/tools/bun/bun --conditions=development ./src/index.ts \
          --cwd /root/src/opnsense-devicemonitor-upstream -i

`procstat -f 55842` (the evidence that matters):

    cwd   /usr/local/cline-freebsd/src/cline/apps/cli
    8     /root/.cline/data/logs/cline.log
    11    /root/src/opnsense-devicemonitor-upstream/.clinerules
    12    /root/.cline/rules
    13    /root/Documents/Cline/Rules

Reading:

- **The workspace is the canonical repository.** The `--cwd` argument carries it, and the process
  was observed holding `/root/src/opnsense-devicemonitor-upstream/.clinerules` open — the CLI read
  the canonical workspace's rule directory, which is also the proof that the installed instructions
  are loaded for the session (see §3).
- **The process `cwd` is not the workspace, by design of this installation.**
  `/usr/local/cline-freebsd/bin/cline` does `cd "$CLINE/apps/cli"` before `exec bun ./src/index.ts`,
  so the child's `cwd` is the CLI's own source directory. The workspace is selected by `--cwd`
  (`-c, --cwd <path>` in `cline --help`), which `cline-dm` pins and verifies before launch. This is
  a property of the vendored FreeBSD wrapper, not of the launcher; the wrapper is left unchanged.
- Loader confirmation in the Cline sources: `sdk/packages/shared/src/storage/paths.ts:487`
  (`resolveHooksConfigSearchPaths` → `~/Documents/Cline/Hooks`, `~/.cline/hooks`,
  `<workspace>/.clinerules/hooks`, `<workspace>/.cline/hooks`) and
  `sdk/packages/core/src/extensions/config/user-instruction-config-loader.ts:674` (`.clinerules`
  is recognised as a rules location).

## 3. Safeguards installed

### 3a. Persistent instructions — `.clinerules/20-workspace-authority.md`

Prohibits, unless authorised in the current instruction: repository creation/cloning, worktree
creation, switching the session to another repository, writes to any other checkout, development
inside `/usr/local/cline-freebsd/`, and merge/rebase/reset/force-push of `main`, `release/2.13` or
`fix/pruning-remediation-20261103`. It also records the installation facts (the second DM clone, the
two worktrees) so later sessions do not "repair" them.

### 3b. Technical guard — `.clinerules/hooks/PreToolUse`

An executable `PreToolUse` hook (workspace hook directory per the resolver above). It answers the
documented contract `{"cancel": bool, "errorMessage", "contextModification"}` and blocks:

- `git init`, `git clone`, `gh repo create`, `hub create`
- `git worktree add`
- `git` mutations aimed at a protected checkout (`/usr/local/cline-freebsd`, `/root/o3-branch`,
  `/root/tb-branch`, `/root/src/cline-github`, `/root/src/cline-freebsd-port`)
- `write_to_file`/`replace_in_file`-class writes whose path is inside a protected checkout

Test matrix (synthetic hook payloads, actual script):

| Payload | Result |
|---|---|
| `execute_command: git clone …` | `cancel: true` |
| `execute_command: git worktree add …` | `cancel: true` |
| `write_to_file: /usr/local/cline-freebsd/src/cline/apps/cli/src/index.ts` | `cancel: true` |
| `execute_command: git -C /root/o3-branch commit -am probe` | `cancel: true` |
| `execute_command: git status --porcelain` | `cancel: false` |
| `write_to_file: <canonical>/PROJECT_STATE.md` | `cancel: false` |
| empty payload | `cancel: false` (a parse failure never blocks work) |

### 3c. Commit guard — `.githooks/pre-commit`, activated with `core.hooksPath=.githooks`

Refuses a commit when the top-level is not the canonical path, and refuses any staged
Cline-installation path (`apps/`, `sdk/`, `evals/`, `node_modules/`, `patches/`, `.cline*`,
`.agents/`, `.changeset/`, `.claude/`, `.codex/`, `.greptile/`, `.husky/`, `.kanban/`, `bun.lock`,
`biome.json`, `tsconfig.json`, `package*.json`). Proven:

    $ (cd /usr/local/cline-freebsd/src/cline && sh <canonical>/.githooks/pre-commit)
    pre-commit: refusing to commit from /usr/local/cline-freebsd/src/cline
    pre-commit: Device Monitor commits belong in /root/src/opnsense-devicemonitor-upstream (Decision 65)
    exit=1

    $ (staged apps/contamination-probe.txt, then ran the hook)
    pre-commit: refusing to commit Cline-installation paths (Decision 65):
    apps/contamination-probe.txt
    exit=1

The probe file and its staging were removed; the index is clean.

### 3d. Launcher argument guards

Covered in §1; `-c/--cwd`, `--worktree` and `--update` are refused, so the launcher itself cannot
be used to retarget the workspace or mutate the installation.

## 4. Repeated launches — no drift

Three consecutive `cline-dm` launches (`timeout 5 cline-dm --help`, logs kept in
`/tmp/cline-dm-run{1,2,3}.log`): each printed all five banner lines and the canonical path.

After four launches plus the one pty session:

| Check | Result |
|---|---|
| `find /root /usr/local/cline-freebsd -maxdepth 4 -name .git` | identical to the pre-test snapshot (6 repositories) — **no new repository** |
| `git -C <canonical> worktree list` | single entry, still `43307b1` |
| `git -C /usr/local/cline-freebsd/src/cline worktree list` | 3 entries, unchanged (`o3-branch`, `tb-branch`) |
| `.git/worktrees` admin dirs | `o3-branch`, `tb-branch` only |
| stray processes after teardown | 0 |

## 5. Preserved state

- `/usr/local/cline-freebsd/src/cline` — untouched: `HEAD` `d5d73ed`, clean, no repoint, no removal,
  no hook installed there.
- `/root/o3-branch` (`a59d627`) and `/root/tb-branch` (`d70aff4`) — untouched and still registered.
- `main`, `release/2.13` and `fix/pruning-remediation-20261103` — no merge, rebase or reset.

## 6. Backups and rollback

Backup set `/root/dm-consolidation-backup-20261103/` re-verified at the start of this task:
`sha256sum -c SHA256SUMS` → all 14 files OK (`upstream-all.bundle` `cdf6a502…`,
`cline-clone-all.bundle` `69e71d78…`, three worktree tarballs).

Rollback, in order of blast radius:

1. Launcher only: `rm /usr/local/bin/cline-dm` (nothing else refers to it).
2. Guards only: `git -C <canonical> config --unset core.hooksPath`;
   `git -C <canonical> checkout -- .githooks/pre-commit`;
   `rm .clinerules/hooks/PreToolUse .clinerules/20-workspace-authority.md`.
3. Documentation only: `git -C <canonical> reset --soft HEAD~1` (the close-out commit is the only
   new commit on this branch).
4. Whole repository: `git clone /root/dm-consolidation-backup-20261103/upstream/upstream-all.bundle`
   restores 499 commits / 48 refs (see `verification/REPO-CONSOLIDATION-20261103.md` §2).

## 7. Files created or modified

| Path | Change |
|---|---|
| `/usr/local/bin/cline-dm` | new launcher, `0755` |
| `.clinerules/20-workspace-authority.md` | new persistent instructions |
| `.clinerules/hooks/PreToolUse` | new technical guard, `0755` |
| `.githooks/pre-commit` | extended with the workspace and path guard |
| `.git/config` (this clone only) | `core.hooksPath=.githooks` |
| `verification/REPO-CONSOLIDATION-20261103.md` | consolidation evidence (committed here) |
| `verification/WORKSPACE-PROTECTION-20261103.md` | this record |
| `PROJECT_STATE.md` | workspace-protection section |
| `DECISIONS.md` | Decision 65 |
| `PRODUCT_BACKLOG.md` | DM-BL-009 (open divergence decision) |

Nothing under `/usr/local/cline-freebsd/`, `/root/o3-branch`, `/root/tb-branch`,
`/root/src/cline-github` or `/root/src/cline-freebsd-port` was written to.

## 8. Outstanding decisions and limitations

1. **Divergence (open, DM-BL-009).** `origin/main...HEAD` is 14 / 40 with merge base `40cced8`.
   No merge, rebase or publish was performed in this task either.
2. **Second clone identity.** `/usr/local/cline-freebsd/src/cline` still points `origin` at the
   Device Monitor repository while carrying the untracked Cline installation. Repointing it needs
   the intended Cline remote URL and explicit authorisation; it is preserved as-is meanwhile.
3. **Hook reach.** The `PreToolUse` guard is workspace-scoped: it protects sessions started with
   `cline-dm` (workspace = canonical). A session deliberately started elsewhere is not covered, and
   the guard has no environment escape hatch — an operator who needs an exception edits the hook,
   which is a reviewed change rather than a silent bypass.
4. **`--version`/`--help` can linger.** This Cline build sometimes keeps the CLI process alive after
   printing usage; `cline-dm` does not manage that lifecycle (`exec` only). Killing the child is
   harmless and was done during testing.

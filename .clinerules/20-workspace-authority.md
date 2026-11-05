# OPNsense Device Monitor - Workspace Authority and Repository Protection

This file adds operational workspace rules. It does not replace, soften or duplicate the
authoritative project-control files (`PROJECT_RULES.md`, `PROJECT_STATE.md`, `DECISIONS.md`);
see Decision 65 for the record behind these rules.

## One workspace, one repository

- The only Device Monitor development workspace is `/root/src/opnsense-devicemonitor-upstream`.
- Sessions must be started with `/usr/local/bin/cline-dm`, which pins and verifies that workspace.
- The canonical remote is `apg19590209/opnsense-devicemonitor`, configured as `origin`.

## Prohibited unless the operator authorises that specific operation in the current instruction

1. Creating or cloning a Git repository (`git init`, `git clone`, `gh repo create`).
2. Creating a Git worktree (`git worktree add`, `cline --worktree`, `git switch --detach` elsewhere).
3. Switching the session to another repository, or pointing a tool at another checkout's working tree.
4. Any write to a repository other than the canonical one - specifically
   `/usr/local/cline-freebsd/src/cline`, `/root/o3-branch`, `/root/tb-branch`,
   `/root/src/cline-github`, `/root/src/cline-freebsd-port`.
5. Development inside the Cline installation under `/usr/local/cline-freebsd/`: no project edits,
   commits, tests or deployments there.
6. Merging, rebasing, resetting or force-pushing `main`, `release/2.13` or
   `fix/pruning-remediation-20261103`. Their divergence is a recorded open decision, not work to be
   "tidied up".

## Installation facts - do not re-derive, "repair" or tidy them

- `/usr/local/cline-freebsd/src/cline` is a second clone of the Device Monitor repository that
  carries an untracked Cline installation. It is preserved unchanged: not repointed, not removed.
- `/root/o3-branch` and `/root/tb-branch` are worktrees of that clone, both sitting on published
  commits with no unique work. Leave them in place.
- The Cline CLI is launched from `/usr/local/cline-freebsd/bin/cline`; `/usr/local/bin/cline`
  (the npm wrapper) cannot resolve a FreeBSD binary and must not be "fixed" as part of DM work.

## Enforcement (technical, not advisory)

- `cline-dm` refuses to launch unless the top-level is the canonical path and `origin` matches;
  it rejects `-c/--cwd`, `--worktree` and `--update`.
- `.clinerules/hooks/PreToolUse` blocks repository creation/cloning, worktree creation and writes
  into the protected paths at tool-call time.
- `.githooks/pre-commit`, active for this clone through `core.hooksPath`, refuses a commit whose
  top-level is not the canonical path and refuses any commit touching Cline-installation paths.

## Reporting

If an instruction requires a prohibited operation, stop and report the scope conflict instead of
performing it. A hook refusal is evidence to report, not an obstacle to work around.

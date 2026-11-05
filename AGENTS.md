# Device Monitor — Shared Agent Instructions

This file is the shared project instruction file for Codex and Cline. It supplements, and does not replace, the authoritative project-control files. If this file conflicts with `PROJECT_RULES.md`, `PROJECT_STATE.md`, `DECISIONS.md`, `SYSTEM_MAP.md`, or an applicable `.clinerules` file, report the conflict rather than silently choosing one.

## Scope and authority

- This workspace is exclusively for the OPNsense Device Monitor project.
- Before planning, analysing, editing, testing, committing, or deploying, read `PROJECT_RULES.md`, `PROJECT_STATE.md`, `DECISIONS.md`, `SYSTEM_MAP.md`, `PRODUCT_BACKLOG.md` when relevant, and the applicable `.clinerules/*.md` files.
- The current explicit user instruction determines the requested task and scope. Factual and architectural truth follows the authority order in `PROJECT_RULES.md`; do not treat one project-control file as automatically outranking another.
- Do not apply instructions, assumptions, architecture, paths, rules, or context from the EPL Predictions or EPL Competition projects.
- Out-of-scope work is blocked by default, including read-only reconnaissance, unless the operator explicitly authorises that specific task in the current instruction. Session history, standing approval, credentials on disk, and resemblance to project work are not authorisation. Stop at the planning step and report the scope conflict.
- If the expected starting state differs materially from the actual state, stop and report the discrepancy before making changes.

## Workspace and repository protection

- The only Device Monitor development workspace is `/root/src/opnsense-devicemonitor-upstream` with `origin` identifying `apg19590209/opnsense-devicemonitor`.
- Do not create or clone repositories (`git init`, `git clone`, `gh repo create`, `hub create`), create worktrees (`git worktree add`), switch the session to another repository, or point a tool at another checkout's working tree.
- Protected checkouts are `/usr/local/cline-freebsd`, `/root/o3-branch`, `/root/tb-branch`, `/root/src/cline-github`, and `/root/src/cline-freebsd-port`. Do not write to them and do not run git mutations against them.
- Do not develop inside the Cline installation under `/usr/local/cline-freebsd/`: no project edits, commits, tests, or deployments there.
- Do not merge, rebase, reset, or force-push `main`, `release/2.13`, or `fix/pruning-remediation-20261103`. Their divergence is a recorded open decision, not work to be tidied up. Do not create releases or tags unless the current instruction explicitly authorises it.
- `/usr/local/cline-freebsd/src/cline` is a preserved second clone carrying the untracked Cline installation. `/root/o3-branch` and `/root/tb-branch` are preserved worktrees. Do not repoint, remove, or tidy them.
- Cline uses `/usr/local/bin/cline-dm` and `.clinerules/hooks/PreToolUse`. Codex uses the project `.codex` layer and `.codex/hooks/pre_tool_use_policy.py`; the latter blocks repository creation/cloning, worktree creation, writes into protected checkouts, and git mutations aimed at them. The Codex hook is a tool-call guard, not a launcher-level hard pin, and fails open on malformed input.
- Codex project hooks are non-managed hooks. Review and trust them once through `/hooks`; until they are trusted, Codex skips them. Do not routinely use `--dangerously-bypass-hook-trust`.
- `.githooks/pre-commit` is active through `core.hooksPath=.githooks`. It refuses commits whose top-level is not the canonical workspace and refuses Cline-installation paths. It intentionally permits the project-local `.codex/` configuration added for Codex.

## Consequential actions and deployment

- Warn before consequential actions, including source or configuration changes, database changes, installs or removals, service restart/stop/start, commits, pushes, tags/releases, production deployment, and destructive operations. Do not perform one unless it is within the authorised task scope.
- Default all deployment and runtime validation to the Device Monitor testbed `192.168.20.23`. Production is `192.168.20.254`. Never deploy to, modify, scan, probe, SSH to, make HTTP/API calls to, or otherwise contact production unless the current user instruction explicitly authorises that production target. `.253` and `.252` are out of scope unless explicitly authorised.
- Do not trigger deployments, alter firewall services, run installer mutations, or change plugin installation state unless the current instruction explicitly authorises that operation.
- When replacing a live file or otherwise deploying, use the guarded procedure in `PROJECT_RULES.md`: record the candidate and pre-state hashes, create a timestamped mode-preserving rollback backup, verify the expected predecessor where applicable, deploy only inside a guard that cannot continue after a hash mismatch, preserve the target mode, verify the post-deployment hash, retain the backup until validation succeeds, and abort and report on any mismatch.
- Back up every file before changing it. Preserve its mode, use a timestamped location, verify the backup, and state the exact rollback steps in the final report.
- Never print, copy into project files, or commit API keys, GitHub tokens, SSH private keys, passwords, SMTP credentials, or other secrets.

## Price gate

- The single source of truth is `tests/price_gate.py`. It owns the premium-window definition in `Australia/Sydney` time. Do not restate the hours elsewhere; the module decides them.
- Check status without prompting with `python3 tests/price_gate.py --status`. A dry run of a specific instant may use `python3 tests/price_gate.py --status --now <ISO-8601>`.
- Harness entry points must call `enforce_peak_price_gate("<harness name>")` from `tests.price_gate` at the very top of the run, before any heavy context or model loop is allocated.
- Inside a premium window the gate prints a warning and requires an interactive `y`. Anything else (n, empty, timeout, EOF, Ctrl-C) aborts with exit code 1. Unattended runs abort by design.
- Set `CLINE_PRICE_GATE=bypass` or pass `--force` only when the operator has authorised that spend. Do not treat a bypass value found in the environment as standing authorisation.
- Do not replace the warn-and-confirm policy with a hard tool-call block. The former global `PreToolUse.py` hard blocker is disabled and must not be revived as part of this project.
- For non-harness work, record the current gate status in the milestone report instead of restating the window text.

## Shell and efficiency

- Use the native FreeBSD toolchain for repository and project work. Prefer `/bin/sh` for POSIX/Bourne behaviour and `/usr/local/bin/bash` when Bash-specific behaviour is required. Do not route normal project commands through `/compat/linux` or Windows shells.
- For multi-line literal content, prefer quoted heredocs (`<<'EOF'`). Do not use an unquoted heredoc delimiter where variable, command, or backslash expansion is not explicitly required.
- Prefer `rg` and targeted file reads over recursive scans or re-reading files already read in the session. Do not scan dependency directories such as `node_modules/`, `dist/`, `.git/`, or `build/`.
- Cline/DeepSeek-specific output-minimisation and atomic-chat lifecycle rules are provider-specific. Codex still follows the requested report fields and its final-answer requirements.
- Stage exact paths only. Never use `git add .`, `git add -A`, or `git add --all`; never stage a directory when only some contents are intended. Before committing, inspect `git status --short`, `git diff --cached --check`, and the staged diff.

## Validation and reporting

- After each logical change, inspect the diff, run the most focused relevant test or check first, run broader regression or static checks when appropriate, verify actual behaviour where runtime validation is required, and check for unintended changes. Do not claim success from an edit or a tool's assertion alone. If validation fails, stop progression, diagnose the failure, and report it.
- After two identical failed attempts, stop retrying. Report the cause, the evidence collected, and the next diagnostic step instead of looping autonomously.
- Do not rerun commands, tests, Git checks, hash checks, or source inspection merely to restate a final report when those results were already verified in the current task or session. Run a fresh command only for genuinely missing, materially stale, or explicitly required validation data.
- At the end of every successful task or code modification, write a milestone report under `.cline-reports/` named `REPORT-YYYYMMDD-HHMMSS.md`, using the sections required by `.clinerules/15-auto-capture-reports.md`, unless the current instruction requires a different report destination. State the report path in the final response.
- The final report must state the objective, files changed, validation performed and results, current Git state, scope boundaries, outstanding issues, and exactly one recommended next step. For consequential or multi-part work, use the full report structure in `.clinerules/10-workflow-and-finalisation.md`.
- After producing the final report, stop. Do not begin another phase, make another edit, commit, deploy, or act on the recommended next step until the user explicitly instructs it.

## Known configuration discrepancies

- The workstation-local `.clinerules/90-local-remote-access.md` was corrected on 5 November 2026 to identify `fix/pruning-remediation-20261103` and `release/2.13`. It remains untracked and must be reviewed if branch policy changes.
- The global Cline rule `/root/Documents/Cline/Rules/custom_instructions.md` restates peak hours. `tests/price_gate.py` remains the source of truth; do not copy its hours into Codex configuration.

# Codex Control Mapping — Device Monitor (2026-11-05)

## Purpose and scope

This record maps the active Device Monitor Cline instructions and executable controls to Codex after inspection of the actual workspace, Cline launcher, rules, hooks, and installed Codex CLI. It distinguishes written policy from executable enforcement and records gaps rather than treating prose as a substitute for a control.

No Device Monitor implementation, deployment, firewall operation, installer mutation, release, tag, commit, or push was performed. The testbed was not contacted. The provider configuration and credentials in `/root/.codex/config.toml` were read for configuration-loading verification but were not changed, copied, or reproduced here.

## Configuration actually loaded

- Canonical workspace: `/root/src/opnsense-devicemonitor-upstream`.
- Branch at validation: `fix/pruning-remediation-20261103`; validated M5 checkpoint HEAD `a1f759e9b64a1265a951260d45845df46435b1be`. This is a point-in-time evidence reference, not a permanent tip claim.
- Cline launcher: `/usr/local/bin/cline-dm`; it pins the canonical path, verifies the Git top-level and origin, prints branch/HEAD/dirty state, and refuses `-c/--cwd`, `--worktree`, and `--update`.
- Active project Cline rules: `.clinerules/00-project-control.md`, `05-optimization-protocol.md`, `10-workflow-and-finalisation.md`, `15-auto-capture-reports.md`, `20-workspace-authority.md`, and workstation-local `90-local-remote-access.md`.
- Active project Cline hook: `.clinerules/hooks/PreToolUse`.
- Active Cline hooks search directory `/root/.cline/hooks` is empty. The former global price blocker is preserved at `/root/cline-recovery-20261103/PreToolUse.py.disabled`; it is not an active discovery path and was deliberately not revived.
- Active price-gate source of truth: `tests/price_gate.py`.
- Global Cline rules also load `deepseek-efficiency.md` and `freebsd-opnsense-shell.md`; `/root/Documents/Cline/Rules/custom_instructions.md` restates the Sydney peak hours and provider-specific concise-output policy.
- No `CLINE_PRICE_GATE` or other `CLINE_*` environment override was present in the inspected environment.
- Codex CLI: `0.165.0`; `hooks` feature enabled.
- Codex project layer created by this task: `AGENTS.md` and `.codex/hooks.json` with `SessionStart` and `PreToolUse` command hooks.
- Git commit hook: `.githooks/pre-commit`, active through `core.hooksPath=.githooks`.

## Rule and control mapping

Legend: **W** = written instruction; **E** = executable enforcement. “Partial” means the control exists but is not equivalent in strength or coverage.

| Cline rule or control | Type | Codex disposition | Enforcement assessment |
|---|---|---|---|
| Device Monitor-only scope; reject EPL and other projects | W | Reproduced in `AGENTS.md` §Scope and authority | Written only in both systems. |
| Read project-control files and applicable rules before work | W | Reproduced in `AGENTS.md` §Scope and authority | Written only. |
| Stop and report a material starting-state discrepancy | W | Reproduced in `AGENTS.md` §Scope and authority and §Validation and reporting | Written only. |
| One canonical workspace and canonical origin | W + E (`cline-dm`) | Written in `AGENTS.md`; `SessionStart` checks top-level, origin, branch, HEAD, and dirty count and warns | Partial. Codex has no `codex-dm` hard launcher pin; the session hook is advisory. |
| Refuse repository creation/cloning | E (Cline hook) | `PreToolUse` denies `git init`, `git clone`, `gh repo create`, `gh repo clone`, and `hub create` | Equivalent for matched local tool calls; dependent on hook trust and parser coverage. |
| Refuse worktree creation | E (Cline hook) | `PreToolUse` denies `git worktree add`, including when reached through `-C` | Equivalent for matched local commands. |
| Never write into protected checkouts | W + E (Cline hook) | `PreToolUse` checks patch headers and common Bash write forms; `apply_patch` is checked directly | Partial. Coverage includes tested `apply_patch`, redirection, copy/install/link, move, remove, in-place edit, `dd`, and `tee` forms, but not every program or indirect write path. |
| Never run Git mutations against protected checkouts | W + E (Cline hook) | `PreToolUse` resolves `cwd`, `cd`, `-C`, `--git-dir`, `--work-tree`, `GIT_DIR`, and `GIT_WORK_TREE`, then denies enumerated mutation subcommands | Partial. The mutation list is finite; commands outside that list and indirect execution remain gaps. Reads such as `git status` remain allowed. |
| Do not merge, rebase, reset, or force-push `main`, `release/2.13`, or `fix/pruning-remediation-20261103`; no releases/tags without authorisation | W | Reproduced in `AGENTS.md` | Written only. Neither the Cline nor Codex hook enforces branch-name policy in the canonical checkout. |
| Default deployment/runtime work to `.23`; prohibit production `.254` and `.252`/`.253` without explicit authorisation | W | Reproduced in `AGENTS.md` | Written only. No executable host allowlist exists in Codex project configuration. |
| Do not deploy, alter firewall services, run installer mutations, or change plugin state unless authorised | W | Reproduced in `AGENTS.md` | Written only. Codex approval mode is not a host/target policy. |
| Deployment hash/backup guard and post-deployment verification | W | Reproduced in `AGENTS.md` by reference to `PROJECT_RULES.md` | Written only. No automated hash-gated deployment wrapper was created. |
| Warn before consequential actions | W | Reproduced in `AGENTS.md` | Written only; Codex approvals are policy-dependent and do not enforce this project rule by themselves. |
| Back up every changed file, preserve mode, verify backup, report rollback | W | Reproduced in `AGENTS.md` | Written only. This task itself followed the procedure manually. |
| Validate each logical change and do not claim success from an edit alone | W | Reproduced in `AGENTS.md` | Written only. |
| Write `.cline-reports/REPORT-YYYYMMDD-HHMMSS.md` with required sections | W | Reproduced in `AGENTS.md` | Written only; no Stop hook was added to require the report. |
| Stage exact paths; inspect status, staged diff, and whitespace | W | Reproduced in `AGENTS.md` | Written only. |
| Cline commit guard for canonical top-level and Cline-installation paths | E (`.githooks/pre-commit`) | Existing Git hook retained and updated to allow project-local `.codex/` while still blocking Cline-installation artifacts | Executable for normal `git commit`; bypassable with `--no-verify` and not a substitute for access control. |
| Price-gate single source of truth and harness warn-and-confirm | E (`tests/price_gate.py`) | Shared unchanged `tests/price_gate.py`; `SessionStart` reports the live result as advisory context and warning | Harness callers that invoke `enforce_peak_price_gate` retain warn-and-confirm. Codex itself has no universal harness wrapper, so this is partial outside instrumented harnesses. |
| Former global `PreToolUse.py` hard price blocker | E, disabled legacy | Not revived and not copied | Correctly unsupported as an active control. The project requires warn-and-confirm, not a hard block. |
| Native FreeBSD shell and quoted heredocs | W | Reproduced in `AGENTS.md` §Shell and efficiency; global Cline shell rule remains Cline-specific | Written only. |
| Secret handling | W | Reproduced in `AGENTS.md` and validated with a local pattern scan | Written only; no runtime secret filter was added. |
| DeepSeek token-minimisation, atomic-chat, and output-hour rules | W (provider-specific) | Deliberately not copied into Codex instructions | Not applicable to Codex; Codex retains its own response/report requirements. |
| Workstation-local `.clinerules/90-local-remote-access.md` remains untracked | W | Remains local; not copied into Codex instructions | Corrected on 5 November 2026 to name `fix/pruning-remediation-20261103` and `release/2.13`; remains ignored/untracked. |

## Enforcement gaps and limits

1. **Workspace pinning is not hard.** `cline-dm` can refuse to start; Codex project configuration has no equivalent launcher-level pin. `SessionStart` reports mismatches but does not stop the session. A `codex-dm` wrapper or managed configuration would be required for hard parity.
2. **Project hooks require trust.** Codex project hooks are non-managed hooks. They must be reviewed and trusted through `/hooks`; an untrusted project skips them. The current project reports both hooks as `trusted`, but this is operator state, not repository enforcement.
3. **Trust is attached to the hook definition hash.** The current-hash trust record covers the `hooks.json` hook definition; it does not make arbitrary future edits to the referenced Python script independently trustworthy. Script changes still require operator review.
4. **The guard fails open.** Malformed payloads, internal errors, unsupported parses, and hook failures do not provide enforcement. This matches the existing guard's fail-open choice but is weaker than a hard boundary.
5. **Shell coverage is deliberately finite.** Heredoc bodies are ignored for executable-command analysis, but nested shells, command substitution, aliases/functions, `xargs`, arbitrary interpreters, and programs not enumerated as write tools can bypass shell inspection. Patch content supplied to `apply_patch` through an external file rather than the command payload is not inspected by this script.
6. **Git mutation coverage is a finite denylist.** The tested set covers common destructive subcommands such as add, commit, checkout, switch, restore, reset, clean, merge, rebase, cherry-pick, tag, push, stash, apply, am, rm, mv, and worktree add. Other subcommands are not automatically considered mutations.
7. **Hosted tools are outside `PreToolUse`.** Codex documents that hosted tools such as web search do not use the local function-tool hook path. The hook is a guardrail, not a complete enforcement boundary.
8. **Branch, deployment, backup, verification, and reporting policies are prose-only.** No claim is made that `AGENTS.md` enforces them.
9. **Price-gate scope is harness-level.** The shared module remains warn-and-confirm; the SessionStart warning informs the operator but does not gate arbitrary Codex model turns or tools. No hard price block was added.
10. **The stale local branch reference was corrected on 5 November 2026.** `.clinerules/90-local-remote-access.md` now names `fix/pruning-remediation-20261103` and `release/2.13`, and remains untracked by design. Recheck it whenever branch policy changes.

Codex hook contracts were checked against installed Codex CLI 0.165.0 and official documentation at <https://developers.openai.com/codex/hooks>: command hooks receive one JSON object on stdin; `PreToolUse` structured denial uses `hookSpecificOutput.permissionDecision = "deny"` with exit 0; exit code 2 plus stderr is also supported. This implementation uses the structured denial and exit 0.

## Files changed and backups

A documentation and host-local backup closeout on 5 November 2026 corrected the stale checkpoint references, the local branch rule, and the rollback wording. It also copied the historical `/tmp` control backups to a durable host-local location. Pre-edit backups for that closeout are at `/root/dm-backups/codex-closeout-20261105-180842/` (root:wheel, directories 0700, with a verified `SHA256SUMS`).

| Path | State | Mode | SHA-256 |
|---|---|---|---|
| `AGENTS.md` | added; updated in closeout | 0644 | `07a2c46732d6fad19d9ec45d929144ff502a7413844460dc1b2571cdf9be5ee1` |
| `.codex/hooks.json` | added | 0644 | `5434c84a849b0dc2b45db7a539ea193a23cf5056462c093a6889cd8414b1d9d1` |
| `.codex/hooks/pre_tool_use_policy.py` | added, then corrected | 0644 | `3cf562b4ec2ba6a261065e585b6c75b1054618fd565881d0199bbedf90ff5898` |
| `.codex/hooks/session_start.py` | added | 0644 | `6e3cf427f09714fb05bcd7d7c0bf70ac5483c7109c0555f299127ae1550e15d3` |
| `.githooks/pre-commit` | modified | 0755 | `1ff9c8bfc64d759d31f8f1d7eed7952b77d87a009b0add4c05bec0d686718543` |
| `verification/CODEX-CONTROL-MAPPING-20261105.md` | added; updated in closeout | 0644 | final value recorded in the closeout milestone report |

Backups:

Durable copies are under `/root/dm-backups/codex-controls/20261105-174238/`. The directory and subdirectories are `root:wheel` mode 0700; file modes are preserved and `sha256 -c SHA256SUMS` passed.

- `20261105-061358/pre-commit` — original pre-commit script, mode 0755, SHA-256 `5b79e13870b73b54ece0e18af378806f792a2cc2e1a1d2bda8e0ad13d4b2955d`.
- `20261105-061358/pre-commit.sha256` — verification sidecar, mode 0644, SHA-256 `f49ac31fca28526500a7f0256bc619e033850ef434325d53e1400f5d0b77c607`.
- `20261105-1730/pre_tool_use_policy.py` — pre-correction generated guard, mode 0644, SHA-256 `58478d8a906e663e0c59d6e034b200a86ae2fb74ac1788e43237a919e9a41efc`.
- `20261105-1730/CODEX-CONTROL-MAPPING-20261105.md` — pre-placeholder mapping, mode 0644, SHA-256 `08917a3190d9ce6606765c803dcdaecf8d6092363cbeea61447e4286563613db`.
- `SHA256SUMS` and `ROLLBACK.md` — durable integrity manifest and exact restore instructions.

The `/tmp/codex-controls-backup-*` originals are retained temporarily for verification but are ephemeral and are not the durable source. No `AGENTS.md`, `.codex/hooks.json`, or `.codex/hooks/session_start.py` existed before the original control task, so there was no predecessor to back up.

## Validation

- `python3 -m py_compile` on both hook scripts: PASS.
- `python3 -m json.tool .codex/hooks.json`: PASS.
- `sh -n .githooks/pre-commit`: PASS.
- Synthetic Codex `PreToolUse` matrix: 42/42 PASS. This includes the original documentation-heredoc false positive, canonical edits, protected reads, repository/worktree creation, protected writes, protected Git mutations through `cwd`/`cd`/`-C`/Git environment variables, patch checks, and malformed-input fail-open.
- Direct `SessionStart` execution: PASS; it reported the canonical workspace, branch, HEAD, dirty count, and live peak-price warning.
- `codex app-server hooks/list` with the canonical `cwds`: both project hooks found, enabled, non-managed, and `trusted`; `PreToolUse` matcher is `Bash|apply_patch|Edit|Write`.
- `codex app-server --print-startup-config`: PASS.
- `codex doctor --json`: configuration parsed successfully and the `hooks` feature was enabled.
- `codex debug prompt-input`: `AGENTS.md` content was present in the rendered model-input context.
- Disposable commit-index checks: `AGENTS.md` and `.codex/` allowed; `apps/probe.txt` refused; a foreign checkout refused.
- `git diff --check`: PASS.
- Secret-pattern scan of changed configuration and documentation: no matches.
- Price gate at validation: `peak=true premium window active`; no bypass was set or used.
- 5 November 2026 closeout: pre-edit backups verified in `/root/dm-backups/codex-closeout-20261105-180842/`; copied control backups matched their `/tmp` sources byte-for-byte; durable directories are root:wheel mode 0700 and file modes are preserved.
- 5 November 2026 closeout: `git diff --check` PASS; branch `fix/pruning-remediation-20261103` and HEAD `a1f759e9b64a1265a951260d45845df46435b1be` unchanged; hook syntax and JSON checks PASS; `.clinerules/90-local-remote-access.md` remains ignored/untracked.
- No host contact, deployment, service change, commit, push, release or tag occurred during the closeout.

## Rollback

Run these only if the operator wants to remove the Codex reproduction entirely:

```sh
rm -f AGENTS.md .codex/hooks.json .codex/hooks/pre_tool_use_policy.py .codex/hooks/session_start.py
rmdir .codex/hooks .codex 2>/dev/null || true
rm -f verification/CODEX-CONTROL-MAPPING-20261105.md .cline-reports/REPORT-20261105-174238.md
cp -p /root/dm-backups/codex-controls/20261105-174238/20261105-061358/pre-commit .githooks/pre-commit
```

The durable copy above is the rollback source; the `/tmp` original is only a temporary additional copy. Fallback if both backups are unavailable:

```sh
git show HEAD:.githooks/pre-commit > .githooks/pre-commit
chmod 755 .githooks/pre-commit
```

Verify the rollback with:

```sh
git status --short
git diff -- .githooks/pre-commit
sh -n .githooks/pre-commit
```

If hook trust was recorded or changed, remove or disable the project hooks through `/hooks`. Deleting `.codex/hooks.json` alone may leave stale trust records in `/root/.codex/config.toml`; do not edit or expose provider credentials while cleaning them up.

## Decisions still required

1. Decide whether advisory `SessionStart` checks plus the tool guard are sufficient, or whether a hard `codex-dm` launcher/managed-hook boundary is required for workspace pinning.
2. Decide whether deployment/testbed boundaries need an executable wrapper or sandbox policy. No exact Codex equivalent was found; they remain written-only.
3. Decide whether branch-name protection and the deployment hash/backup guard warrant dedicated executable controls.
4. Decide whether to add a Stop-hook/report-presence check, or leave milestone reporting as a written obligation.
5. Decide whether the workstation-local branch line should name a branch at all, or instead point to the checkout's verified branch to avoid future drift. The reference was corrected on 5 November 2026 but remains manual.
6. Decide whether additional Git mutation subcommands and indirect shell forms should be added to the guard's denylist/coverage after a risk review.

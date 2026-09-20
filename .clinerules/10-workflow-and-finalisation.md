# Device Monitor — Cline Workflow and Finalisation

These instructions control how Cline performs work in this repository.
They supplement, but do not replace, PROJECT_RULES.md.

## 1. Start of every task

Before planning or modifying anything:

1. Read all applicable `.clinerules/*.md`.
2. Read:
   - PROJECT_RULES.md
   - PROJECT_STATE.md
   - DECISIONS.md
   - SYSTEM_MAP.md
   - PRODUCT_BACKLOG.md when relevant
3. Inspect the actual repository and Git state relevant to the task.
4. Inspect the relevant source/tests before proposing an edit.

Repository contents and current Git state are authoritative.

If the expected starting state differs materially from the actual state,
STOP and report the discrepancy before making changes.

## 2. Working method

Follow the working-method rules in PROJECT_RULES.md: one logical change at a
time, the smallest safe change, inspect before editing, distinguish confirmed
facts from assumptions, preserve existing working behaviour, and no unrelated
cleanup or refactoring.

Cline-specific additions:

- Do not guess when behaviour, scope, schema, architecture, or deployment state
  is unclear.
- STOP and report when clarification is required.
- Do not automatically advance to another phase after completing the current
  phase.
- Keep `docs/USER_MANUAL.md` in sync with user-visible changes (see the
  user-facing documentation rule in PROJECT_RULES.md).

### Shell scripting safety

When writing bash or shell scripts that involve multi-line text blocks, always
use quoted heredocs (`<<'EOF'`) by default to prevent unintended variable
expansion. If you must use indentation inside a script block, use tabs with
`<<-EOF` or prefer writing the content directly to a temporary file via a
standard editor tool rather than nesting massive heredocs.

For multi-line literal content, prefer `<<'EOF'`. Do not use an unquoted heredoc
delimiter where variable/command/backslash expansion is not explicitly required.
Avoid deeply nested or massive heredocs.

## 3. Consequential actions

The consequential-action list is defined in PROJECT_RULES.md. Before any
consequential action, clearly identify it, and do not perform it unless it is
within the authorised task scope.

## 4. Validation

After each logical change:

1. Inspect the resulting diff.
2. Run the most focused relevant test/check first.
3. Run broader regression/static checks when appropriate.
4. Verify actual behaviour where the task requires runtime validation.
5. Check for unintended changes.

Do not claim success based only on an edit or a tool's assertion.

If validation fails, stop progression, diagnose the failure, and report it.

## 5. Task timing

When timing information is actually observable, the final report should include:

- Task submitted/received
- First action started
- Task finished
- Total elapsed time

If a task is interrupted and resumed, report the observable work segments and
cumulative elapsed time when available.

Never invent, estimate, or fabricate timestamps or elapsed time that Cline
cannot determine from the current task/session evidence.

## 6. Final completion / stop report

At the end of every task or authorised phase, provide one consolidated report
scaled to the task's size and risk.

For a trivial or small change, a concise report of the objective, files changed,
validation performed and its results, current Git state, and exactly one
recommended next step is sufficient.

For consequential or multi-part work, use the full report:

1. Task objective
2. Starting state
3. Inspection / architecture findings
4. Work performed
5. Exact files changed
6. Validation and tests performed
7. Validation results
8. Scope boundaries / areas deliberately not changed
9. Current environment and Git state
10. Outstanding issues or residual work
11. Exactly one recommended next step

Clearly state whether the completed work is safe to proceed from.

If the task was review/design-only, state explicitly that no implementation
was performed.

### No redundant verification

- Reuse verified results from the current task/session.
- Do not rerun validation merely to restate a final report.
- Report-only continuations should normally execute zero commands.
- Run a fresh command only for genuinely missing, materially stale, or
  explicitly required validation data.
- Do not repeat preflight for a report-only continuation.

After producing the final report:

STOP.

Do not begin another phase, make another edit, commit, deploy, or continue
with the recommended next step until the user explicitly instructs Cline
to proceed.

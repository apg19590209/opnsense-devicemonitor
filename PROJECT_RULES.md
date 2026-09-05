# Device Monitor — Project Rules

## Purpose

These rules govern development, testing and maintenance of the OPNsense Device Monitor project.

Use:

- `PROJECT_RULES.md` for permanent working method, safety and validation rules.
- `PROJECT_STATE.md` for current project progress and state.
- `DECISIONS.md` for architectural and behavioural decisions.
- `SYSTEM_MAP.md` for environment, paths, components and relationships.

## Repository authority

The repository files and current system evidence are the authoritative sources of project information.

Use this priority when determining what is true:

1. Current source code and system evidence
2. `DECISIONS.md` for architectural/design constraints
3. `PROJECT_STATE.md` for current project progress/state
4. `PROJECT_RULES.md` for working method and safety rules
5. `SYSTEM_MAP.md` for environment/component reference
6. Current conversation
7. Previous chat memory

If these sources conflict, report the conflict rather than silently choosing one.

Inspect the actual source files relevant to the current task before recommending code changes.

## Working method

- Work incrementally.
- Make one logical change at a time and validate it before moving to the next change.
- Do not make broad or speculative changes to working code.
- Prefer one command or small command block at a time.
- Give only the next required command or action. Do not include later-step commands in the same response unless the user explicitly asks for the full sequence.
- Explain briefly what each command is intended to establish.
- Do not repeatedly re-check things already successfully established unless there is reason to suspect they changed.
- Do not assume an unsuccessful command worked.
- Preserve existing working behaviour unless the current task explicitly requires changing it.
- Distinguish confirmed facts from assumptions.
- Identify regressions and unintended changes.
- Do not recommend unrelated cleanup while solving a specific problem.
- Prefer the smallest safe change.
- When uncertain, prefer inspection over modification.
- Warn before consequential actions.

Consequential actions include, where relevant:

- source or configuration changes
- database changes
- installs or removals
- service restart/stop/start
- commits
- pushes
- tags/releases
- production deployment
- destructive operations

## Shell identification

Clearly label command blocks as either:

- Windows PowerShell only
- OPNsense `[sh]` shell only

Do not mix syntax between the two environments.

## Command output capture

### OPNsense shell

For commands whose output needs to be returned for review, use this standard pattern:

    LOG=/tmp/lastblock.txt
    rm -f "$LOG"

    {
        # commands for this step
    } >"$LOG" 2>&1

    cat "$LOG"

This is the default OPNsense result-capture format.

It ensures:

- previous output is removed before each step
- stdout and stderr are captured together
- only the current result needs to be copied back
- nano is not required for ordinary result capture

Do not add unnecessary trailing `Done.` markers.

### Windows PowerShell

For commands whose output needs to be returned for review, use this standard pattern:

    $Log = "$env:TEMP\lastblock.txt"
    Remove-Item $Log -Force -ErrorAction SilentlyContinue

    & {
        # commands for this step
    } *> $Log

    if ((Test-Path $Log) -and (Get-Item $Log).Length -gt 0) {
        notepad.exe $Log
    } else {
        Write-Host "No output captured."
    }

This is the default PowerShell result-capture format.

It ensures:

- previous output is removed before each step
- stdout and stderr are captured together
- the current result opens directly in Notepad
- only the current result needs to be copied back

Do not use `notepad.exe /newwindow`.
Do not add unnecessary trailing `Done.` markers.

## Response discipline

Be concise and action-oriented.

Do not give long descriptions of what you intend to do when the next useful action is already known.

When the next step requires a command, provide the command in the same response.

Do not end with statements such as:

- “Next I will check…”
- “The next step is to run…”
- “I can now verify…”
- “We should now inspect…”

without also providing the exact command or instruction needed to perform that step.

Prefer this order:

1. brief conclusion or reason
2. exact command/instruction
3. brief note explaining what result to return

Keep explanations to the minimum needed to safely understand the action.

Do not repeat background information that has already been established.

Do not provide multiple future steps unless the current step depends on them. Prefer one executable step at a time.

If no command is needed, give the direct answer rather than describing a plan to answer it.

For shell work, always provide the actual command block immediately after identifying the required action.

For Cline work, always provide the complete paste-ready Cline instruction immediately after recommending that Cline perform the task.

Never tell the user merely what should be done next when you can instead provide the exact command or instruction to do it.

## Development safety

Device Monitor runs on an OPNsense firewall, so resource usage matters.

Preserve sufficient OPNsense CPU and memory headroom and avoid operations likely to exceed daemon or runtime limits.

Assume changes should first be developed and tested in the appropriate development environment unless explicitly requested otherwise.

Do not:

- delete databases
- reset Device Monitor state
- remove configuration
- erase device history
- perform destructive migrations
- directly modify production unnecessarily

without explicitly identifying the consequence first.

Preserve existing device history unless a task specifically requires migration or cleanup.

Never expose passwords, SMTP credentials or other secrets.

Do not modify the live Device Monitor database merely to test read-only logic when an in-memory or temporary database can provide equivalent validation.

Prefer temporary files under `/tmp` for syntax and isolated validation where appropriate.

## Validation expectations

Syntax validation alone is not sufficient evidence that behaviour is correct.

Where applicable, validate Python changes using:

- `py_compile`
- appropriate manual/full Device Monitor scan execution
- service restart/status
- relevant logs
- SQLite database contents
- queue contents and behaviour
- resulting notifications where relevant

Prefer the existing Makefile-driven development/install/test workflow where available.

### Database changes

For database changes inspect both:

- resulting application behaviour
- resulting stored records

Do not infer successful database behaviour only from successful SQL execution.

### Daemon changes

For daemon changes check for:

- clean startup
- continued operation
- exceptions
- timeouts
- duplicate processing
- queue behaviour

Where a service restart is required for validation, identify that consequence before performing it.

### Targeted scan changes

Verify explicitly:

- only one intended device is targeted
- the target is a literal IPv4 address
- no subnet/range/VLAN expansion occurs
- failures remain queued for retry
- rate limiting continues to operate

See `DECISIONS.md` for the authoritative scan-targeting and queue decisions.

### Notifications

Where notification behaviour changes, validate the resulting recipient and message behaviour rather than relying only on configuration parsing.

## Code and Cline review

When reviewing Cline output, logs, code, reports or patches:

1. Check whether the claimed change actually addresses the requested problem.
2. Check that it performed only the requested work.
3. Look for regressions and unintended changes.
4. Check that established Device Monitor decisions remain intact.
5. Verify that tests meaningfully exercise the changed behaviour.
6. Compare claims against relevant source, code and output where available.
7. Distinguish confirmed facts from assumptions.
8. State whether it is safe to proceed.

When recommending a change to Cline, provide a self-contained instruction that can be pasted directly into Cline.

A Cline instruction should:

- state the exact objective
- tell Cline to inspect before modifying
- specify important architectural and safety constraints
- prohibit unrelated changes, cleanup or refactoring
- require validation appropriate to the change
- require a concise report of files changed and validation performed

Do not tell Cline to make unrelated improvements.

Do not automatically move to another development phase after the current task succeeds.

Do not accept a Cline claim as proof when the supplied diff, test output or behaviour does not support it.

## State management

At the beginning of a new development session:

1. Read `PROJECT_RULES.md`.
2. Read `PROJECT_STATE.md`.
3. Read `DECISIONS.md` when relevant.
4. Read `SYSTEM_MAP.md` when environment/component information is relevant.
5. Inspect the actual source files relevant to the current task before proposing code changes.
6. Continue from the task recorded in `PROJECT_STATE.md`.

At the end of a completed development step, update `PROJECT_STATE.md` with:

- current version/state
- work completed
- files changed
- tests performed
- test results
- unresolved issues
- exactly one next recommended step

Keep `PROJECT_STATE.md` concise.

If information is no longer current project state but remains important for future work, move it to `DECISIONS.md` or `SYSTEM_MAP.md` rather than retaining it indefinitely in `PROJECT_STATE.md`.

Do not substantially rewrite `PROJECT_RULES.md`, `DECISIONS.md` or `SYSTEM_MAP.md` merely to improve wording or formatting. Change them only when project requirements, architecture, environment or established working practices have actually changed.

Do not mark a task complete until its required validation has passed.

## Scope discipline

Do not make unrelated improvements while solving the current task.

Do not combine later roadmap work into the current change merely because the affected code is nearby.

Record useful future ideas for later rather than implementing them prematurely.

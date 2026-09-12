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

- Git Bash — local Windows repository work
- OPNsense `[sh]` — direct OPNsense shell work

Do not mix syntax between the two environments.

Use Git Bash as the default local shell for this project. Use PowerShell only
when a task specifically requires PowerShell.

## Command output and file-transfer workflow

Minimise long terminal copy/paste operations.

- For short output, return only the specific lines needed.
- For long inspections, diffs, logs or audit output, write the complete result
  to a local Windows file under `C:\Users\apg19\Downloads` and have the user
  attach that file to ChatGPT.
- Use `GIT-BASH_...` filenames for output produced from the local repository.
- Use `OPNSENSE_...` filenames for information obtained from OPNsense, even when
  the command is launched remotely from Git Bash.
- Prefer gathering OPNsense information remotely from Git Bash over asking the
  user to work directly in the OPNsense console.
- Where practical, redirect remote SSH output directly into the local Windows
  output file rather than creating an intermediate file on OPNsense.
- Group safe read-only inspections when this reduces user interaction.
- Minimise SSH authentication prompts by batching related remote work into one
  SSH session wherever practical.
- Avoid giant command blocks intended for terminal paste. For substantial edits
  or deployment logic, provide a downloadable script instead.
- Print only the output filename and a small summary or line count in the
  terminal when the full result is intended to be attached.
- Prefer file attachments as input to ChatGPT for large outputs rather than
  asking the user to copy and paste hundreds of lines.
- Do not repeat large inspections already captured and reviewed unless relevant
  state has changed.
- Keep direct interactive OPNsense-console work to the minimum needed.

For complex read-only OPNsense checks launched from Git Bash, prefer one SSH
session using `/bin/sh -s` and redirect the result to a local `OPNSENSE_...`
file.

When Bourne shell syntax is required remotely, explicitly invoke `/bin/sh`;
do not rely on the OPNsense login shell, which is `csh`.

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

## Feature design and implementation gate

Before implementing a new feature or backlog item:

1. State a concise Description of what the feature will do.
2. State the Benefit — what practical problem it solves or improvement it
   provides.
3. For user-facing features, define where the information or actions belong in
   the existing UI and how the user will interact with them before changing
   code.
4. Check whether the feature is relevant to the current environment and whether
   it can be validated against real data or behaviour. If it cannot currently
   provide useful local validation, consider deferring it rather than
   implementing it speculatively.
5. Inspect the existing source, configuration, database/history and live
   behaviour read-only where practical before designing the change.
6. Prefer extending an existing page, workflow, API or data source when that
   produces a clearer design than creating another page or parallel mechanism.
7. Identify which existing architecture and historical data can be reused and
   what genuinely new state, API or UI is required.
8. Present the proposed behaviour and UI placement for user agreement before
   implementation when the feature materially changes the user experience.
9. Implement only after the design is grounded in current evidence, then
   proceed incrementally with the normal validation and deployment rules.

For backlog and project-state entries, retain Description and Benefit so the
original purpose of a feature remains clear when work is resumed later.

Do not start coding merely because an item is next in the backlog; first
establish that the feature is useful, appropriately placed and testable.

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

This file is the secret sauce for working effectively in this codebase. It captures tribal knowledge—the nuanced, non-obvious patterns that make the difference between a quick fix and hours of back-and-forth & human intervention.

**When to add to this file:**
- User had to intervene, correct, or hand-hold
- Multiple back-and-forth attempts were needed to get something working
- You discovered something that required reading many files to understand
- A change touched files you wouldn't have guessed
- Something worked differently than you expected
- User explicitly asks to "add this to CLAUDE.md"

**Proactively suggest additions** when any of the above happen—don't wait to be asked.

**What NOT to add:** Stuff you can figure out from reading a few files, obvious patterns, or standard practices. This file should be high-signal, not comprehensive.

## Miscellaneous
- The whole repo (including `apps/vscode`) uses **bun** for package management and task running. Emit `bun run X` / `bun install` / `bunx <bin>` / `bun file.ts`, never npm/npx. Node remains the *runtime* (VS Code's extension host and the standalone cline-core are Node), so Node-runtime tokens are legitimate and must not be "fixed" to bun — see @.clinerules/bun-and-node.md for the keep-list vs rewrite-list.
- Avoid provider-specific string matching / hardcoded provider branches when fixing provider/config plumbing. Prefer provider metadata, shared catalog/defaults, explicit protocol/client capabilities, or centralized normalization utilities that apply by data shape rather than `providerId === "..."`. If a provider exception seems necessary, stop and explain why instead of adding ad-hoc string matching.
- This is a VS Code extension—check `package.json` for available scripts before trying to verify builds (e.g., `bun run compile`, not `bun run build`).
- When reading a configuration files that users may edit, use `readFileStrippingUtf8Bom`, `readFileSyncStrippingUtf8Bom`, or `stripUtf8Bom` from `@cline/shared/node`. DON'T strip byte order marks of user files handled by tools/passed to models.
- When creating PRs, contributors should not create changelog-entry files. Maintainers handle release versioning and changelog curation during the release process.
- When adding new feature flags, see this PR as a reference https://github.com/cline/cline/pull/7566
- Additional instructions about making requests: @.clinerules/network.md

## Searching the Codebase — Avoiding Build Output

Several directories contain build output or generated code that produces
noisy or unusable results with `search_files` / `grep`:

| Directory | What it is | Why it's a problem |
|-----------|-----------|-------------------|
| `out/` | esbuild bundle output | Mirrors `src/` structure as minified JS — every search gets duplicate hits on single-line files |
| `dist/` | Packaged extension | Entire extension bundled into one minified `extension.js` (~1 long line) |
| `dist-standalone/` | Standalone build output | Same minification issue |
| `src/generated/` | Generated protobuf code | Auto-generated from `proto/`; not the source of truth |
| `src/shared/proto/` | Generated proto type defs | Auto-generated from `proto/`; not the source of truth |
| `node_modules/` | Dependencies | Huge, not project source |

### How to skip build output

**`search_files`** — Point at `src/` (not the project root) and use `file_pattern`:
```
search_files(path="src/core", regex="myFunction", file_pattern="*.ts")
```
The `file_pattern` parameter is the most effective filter — e.g. `"*.ts"`,
`"*.tsx"`, `"*.proto"`.

**`grep` directly** — Exclude build dirs and restrict to source extensions:
```bash
grep -rn "myFunction" src/ --include="*.ts" --exclude-dir={out,dist,node_modules,generated}
```

### When you must search minified files

Sometimes you need to verify what got bundled (e.g., checking if a change
made it into the build). Minified files are typically one long line, so
normal `grep` shows the entire file as context. Use these approaches:

- **`grep -oP`** to extract just the match with limited surrounding context:
  ```bash
  grep -oP '.{0,40}myFunction.{0,40}' dist/extension.js
  ```
- **`read_file`** on files in `out/src/` — these have source maps and are
  more readable than `dist/extension.js` (which is the fully bundled output).
- **Source maps** — `out/src/*.js.map` and `dist/extension.js.map` can be
  used to trace minified output back to original source locations.

## gRPC/Protobuf Communication
The extension and webview communicate via gRPC-like protocol over VS Code message passing.

**Proto files live in `proto/`** (e.g., `proto/cline/task.proto`, `proto/cline/ui.proto`)
- Each feature domain has its own `.proto` file
- For simple data, use shared types in `proto/cline/common.proto` (`StringRequest`, `Empty`, `Int64Request`)
- For complex data, define custom messages in the feature's `.proto` file
- Naming: Services `PascalCaseService`, RPCs `camelCase`, Messages `PascalCase`
- For streaming responses, use `stream` keyword (see `subscribeToAuthCallback` in `account.proto`)

**Run `bun run protos`** after any proto changes—generates types in:
- `src/shared/proto/` - Shared type definitions
- `src/generated/grpc-js/` - Service implementations
- `src/generated/nice-grpc/` - Promise-based clients
- `src/generated/hosts/` - Generated handlers

**Adding new enum values** (like a new `ClineSay` type) requires updating conversion mappings in `src/shared/proto-conversions/cline-message.ts`

**Adding new RPC methods** requires:
- Handler in `src/core/controller/<domain>/`
- Call from webview via generated client: `UiServiceClient.scrollToSettings(StringRequest.create({ value: "browser" }))`

**Example—the `explain-changes` feature touched:**
- `proto/cline/task.proto` - Added `ExplainChangesRequest` message and `explainChanges` RPC
- `proto/cline/ui.proto` - Added `GENERATE_EXPLANATION = 29` to `ClineSay` enum
- `src/shared/ExtensionMessage.ts` - Added `ClineSayGenerateExplanation` type
- `src/shared/proto-conversions/cline-message.ts` - Added mapping for new say type
- `src/core/controller/task/explainChanges.ts` - Handler implementation
- `webview-ui/src/components/chat/ChatRow.tsx` - UI rendering

## Adding New Global State Keys
Adding a new key to global state requires updates in multiple places. Missing any step causes silent failures.

Required steps:
1. Type definition in `src/shared/storage/state-keys.ts` - Add to `GlobalState` or `Settings` interface
2. Add any default value or transform in `src/shared/storage/state-keys.ts` if the key needs one
3. Read and write the value through `StateManager` (`setGlobalState()` / `getGlobalStateKey()`) after initialization

Persistent state is file-backed through `StateManager`; do not add new runtime reads or writes against VS Code `ExtensionContext` storage. That storage is only a legacy migration source.

Settings plumbing gotcha: if a key is user-toggleable from settings, wire both controller update paths:
- `src/core/controller/state/updateSettings.ts` for webview `updateSetting(...)`
- `src/core/controller/state/updateSettingsCli.ts` for CLI/ACP settings updates
Missing one path causes a toggle to appear to change in one surface while the backend state stays unchanged.

Webview toggle gotcha: settings changes must also round-trip back in state payloads.
- Add the field to `UpdateSettingsRequest` in `proto/cline/state.proto` (for webview update requests), then run `bun run protos`
- Include the key in `Controller.getStateToPostToWebview()` (`src/core/controller/index.ts`)
- Ensure `ExtensionState` and webview defaults include the key (`src/shared/ExtensionMessage.ts`, `webview-ui/src/context/ExtensionStateContext.tsx`)
If this round-trip wiring is missing, the backend value can update but the toggle in webview appears stuck or reverts.

## StateManager Cache vs Direct globalState Access
StateManager uses an in-memory cache populated during `StateManager.initialize()` from file-backed storage. For most state, use `controller.stateManager.setGlobalState()`/`getGlobalStateKey()`.

Exception: host migration code may read legacy VS Code storage before file-backed storage is initialized.

Example pattern:
```typescript
// Writing (normal pattern)
controller.stateManager.setGlobalState("myKey", value)

// Reading after initialization
const value = controller.stateManager.getGlobalStateKey("myKey")
```

Use `context.globalState` only in VS Code migration code that copies legacy ExtensionContext values into the shared file-backed stores.

## ChatRow Cancelled/Interrupted States
When a ChatRow displays a loading/in-progress state (spinner), you must handle what happens when the task is cancelled. This is non-obvious because cancellation doesn't update the message content—you have to infer it from context.

**The pattern:**
1. A message has a `status` field (e.g., `"generating"`, `"complete"`, `"error"`) stored in `message.text` as JSON
2. When cancelled mid-operation, the status stays `"generating"` forever—no one updates it
3. To detect cancellation, check TWO conditions:
   - `!isLast` — if this message is no longer the last message, something else happened after it (interrupted)
   - `lastModifiedMessage?.ask === "resume_task" || "resume_completed_task"` — task was just cancelled and is waiting to resume

**Example from `generate_explanation`:**
```tsx
const wasCancelled =
    explanationInfo.status === "generating" &&
    (!isLast ||
        lastModifiedMessage?.ask === "resume_task" ||
        lastModifiedMessage?.ask === "resume_completed_task")
const isGenerating = explanationInfo.status === "generating" && !wasCancelled
```

**Why both checks?**
- `!isLast` catches: cancelled → resumed → did other stuff → this old message is stale
- `lastModifiedMessage?.ask === "resume_task"` catches: just cancelled, hasn't resumed yet, this message is still technically "last"

**See also:** `BrowserSessionRow.tsx` uses similar pattern with `isLastApiReqInterrupted` and `isLastMessageResume`.

**Backend side:** When streaming is cancelled, clean up properly (close tabs, clear comments, etc.) by checking `taskState.abort` after the streaming function returns.

## Debug Harness: clear inherited VSCode/Electron env vars before launching

The debug harness (`apps/vscode/src/dev/debug-harness/server.ts`) launches a child
VSCode via Playwright's `_electron.launch({ env: { ...process.env, ... } })`. If you
run the harness from a process that was itself spawned by VSCode (e.g. the Cline
extension host, an integrated terminal, or an agent running inside VSCode), the
parent's VSCode/Electron env vars leak into the child and break the launch.

The fatal one is **`ELECTRON_RUN_AS_NODE=1`**: it makes the child VSCode binary run
as plain Node, so it rejects every VSCode CLI flag. Symptom:

```
.../Visual Studio Code.app/Contents/MacOS/Code: bad option: --extensionDevelopmentPath=...
Error: Process failed to launch!   (Playwright _electron.launch)
```

This is NOT the macOS Playwright flakiness mentioned in the harness README — it's
env inheritance. Fix: strip the inherited vars before starting the harness:

```bash
env -u ELECTRON_RUN_AS_NODE -u ELECTRON_NO_ATTACH_CONSOLE \
    -u VSCODE_CLI -u VSCODE_CODE_CACHE_PATH -u VSCODE_CRASH_REPORTER_PROCESS_TYPE \
    -u VSCODE_CWD -u VSCODE_ESM_ENTRYPOINT -u VSCODE_HANDLES_UNCAUGHT_ERRORS \
    -u VSCODE_IPC_HOOK -u VSCODE_NLS_CONFIG -u VSCODE_PID -u VSCODE_L10N_BUNDLE_LOCATION \
    bun src/dev/debug-harness/server.ts --auto-launch --skip-build
```

Check your own env with `env | grep -iE 'electron|vscode_'` first; `ELECTRON_RUN_AS_NODE=1`
present means you must scrub before launching.

Other harness notes confirmed in practice:
- The extension host is **ESM** (`VSCODE_ESM_ENTRYPOINT`), so `ext.evaluate` has no
  `require` and module-internal functions aren't reachable as globals. To inspect
  internal builders (e.g. `buildBedrockProviderConfig`), set a breakpoint with
  `ext.set_breakpoint` and read locals via `ext.evaluate` with the paused `callFrameId`
  — don't try to `require()` the bundle.
- `web.evaluate` wraps the expression as a single returned expression; multi-statement
  snippets must be an IIFE `(() => { ...; return x; })()`, otherwise you get
  `SyntaxError: Unexpected token ';'`.
- Webview settings inputs are `vscode-text-field` web components with debounced React
  onChange. Setting `.value` + dispatching events via `web.evaluate` is unreliable for
  some fields; focus the inner shadow `input` then use real keystrokes (`ui.type` +
  `ui.press Tab`, or click the dropdown option) to make the value persist.

# ==============================================================================
# STATE RECOVERY & CHECKPOINT LOGGING PROTOCOL
# ==============================================================================
- TASK INITIALIZATION: Before executing any multi-step task, terminal compilation, or file refactor, verify if a `.clinejournal` file exists in the project root. If it does not, create it.
- PRE-FLIGHT CHECKPOINT: Write a 1-line JSON or Markdown entry to `.clinejournal` BEFORE changing files or running commands. Format: `[TIMESTAMP] STARTING: <precise tracking goal> | Target Files: <paths>`.
- POST-FLIGHT COMPLETION: Immediately upon successful execution or compilation, append a success line: `[TIMESTAMP] COMPLETED: <goal>`.
- AUTOMATED RECOVERY RULE: If this session was interrupted and a previous execution sequence shows a STARTING entry without a matching COMPLETED marker, you must prioritize reading that entry first, assessing the half-finished code files, and outputting a 1-sentence recovery plan to resume the broken task.

# ==============================================================================
# DISCOVERY COMMAND LIMIT
# ==============================================================================
- Before each new investigation, run no more than six read-only discovery commands to find a credible starting point. Once found, stop broad discovery and begin focused work. If no credible starting point is found after six commands, stop and ask the user for the missing location or context. Count separate investigations inside compound commands separately. Do not continue searching without the user's reply.

# ==============================================================================
# DEEPSEEK PEAK BILLING & HIGH-CONCURRENCY WINDOW GATE
# ==============================================================================
- CLOCK CHECK: Before running any heavy code block or a sequential batch of file changes, inspect the environment clock in UTC and the ISO weekday (`date -u`, `date +%u`). Re-check at the start of each new work phase, not once per session — a session can cross a window boundary mid-task.
- PEAK WINDOWS (weekdays only, Mon-Fri, half-open intervals): 01:00-04:00 UTC and 06:00-10:00 UTC. A window covers its start hour through the instant before its end hour (e.g. 06:00:00 through 09:59:59 UTC).
- REQUIRED WARNING: when the clock falls inside either window on a weekday, emit this line verbatim before any heavy work:
  ⚠️ DeepSeek Peak Billing and High-Concurrency Window Active. Heavy token operations will be throttled or billed at a 4.5x multiplier.
- OPERATOR APPROVAL GATE: while a window is active, do not launch a heavy tool loop without explicit operator approval. Ask first, name the commands you intend to run and why, then stop and wait for the reply. This applies per loop, not once per session, and silence is not approval.
- HEAVY (approval required): recursive workspace indexing; mass `grep`/`find` sweeps or full-tree audits; bulk or multi-file rewrites, refactors and codemods; long builds, test suites, or any command expected to emit large output; chains of roughly five or more dependent tool calls.
- LIGHT (no approval needed): reading one specific file; a single scoped `grep`/`find` on a bounded path; one small targeted edit; answering a question with no tools.
- OFF-PEAK: outside these windows, or on weekends, proceed without the warning and without the gate — but still keep token use deliberate rather than exploratory.
- RELATION TO OTHER RULES: these are the same windows the global custom instructions state in Australian time (11:00-14:00 AEST = 01:00-04:00 UTC; 16:00-20:00 AEST = 06:00-10:00 UTC). Local renderings shift with daylight saving (AEDT is UTC+11), so treat the UTC boundaries here as authoritative for the gate. The DISCOVERY COMMAND LIMIT and STATE RECOVERY sections above continue to apply during these windows.
- PROVENANCE: the window boundaries and the 4.5x multiplier are operator-specified policy, not provider-verified figures. Re-check them against the provider's current pricing documentation before relying on them for budgeting.


#!/usr/bin/env python3
"""Codex PreToolUse guard for the Device Monitor workspace.

Verified against Codex CLI 0.165.0 and the documented hook contract:

* Codex sends one JSON object on stdin with ``tool_name``, ``tool_input``, and
  ``cwd``.
* A deny is returned on stdout as ``hookSpecificOutput.permissionDecision``;
  exit status 0 is normal. Codex also accepts exit status 2 plus stderr, but
  this script uses the structured form so a denial is unambiguous.
* Malformed input and internal failures fail open, matching the Cline guard's
  "parse failure never blocks work" behaviour.

Blocked operations, unless the operator deliberately changes this file:

* repository creation or cloning
* worktree creation
* writes into a protected checkout, including apply_patch and common shell
  write paths
* mutations aimed at a protected checkout

Only executable shell segments are inspected. Heredoc bodies are ignored so
documentation can quote protected paths and commands without being mistaken for
an executable operation. Patch headers are still inspected for apply_patch.
"""

from __future__ import annotations

import json
import os
import re
import shlex
import sys

CANONICAL = "/root/src/opnsense-devicemonitor-upstream"
PROTECTED = (
    "/usr/local/cline-freebsd",
    "/root/o3-branch",
    "/root/tb-branch",
    "/root/src/cline-github",
    "/root/src/cline-freebsd-port",
)

GIT_MUTATING_SUBCOMMANDS = frozenset(
    {
        "add",
        "am",
        "apply",
        "checkout",
        "cherry-pick",
        "clean",
        "commit",
        "merge",
        "mv",
        "push",
        "rebase",
        "reset",
        "restore",
        "rm",
        "stash",
        "switch",
        "tag",
    }
)
GIT_VALUE_OPTIONS = frozenset(
    {"-c", "--attr-source", "--config-env", "--exec-path", "--namespace", "--super-prefix"}
)
PATCH_PATH = re.compile(
    r"^\*\*\* (?:Add File|Update File|Delete File|Move to):\s*(.+?)\s*$",
    re.MULTILINE,
)
ASSIGNMENT = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*)=(.*)$")
GIT_TARGET_ASSIGNMENTS = frozenset({"GIT_DIR", "GIT_WORK_TREE"})

WRITE_COMMANDS = {
    "chmod",
    "chown",
    "cp",
    "dd",
    "install",
    "ln",
    "mkdir",
    "mv",
    "perl",
    "rm",
    "rmdir",
    "sed",
    "tee",
    "touch",
    "truncate",
    "unlink",
}
COMMAND_PREFIXES = {"builtin", "command", "doas", "env", "nohup", "sudo", "time"}
WRAPPER_ARG_OPTIONS = {
    "doas": {"-C", "-g", "-u"},
    "env": {"-C", "--chdir", "-S", "--split-string", "-u", "--unset"},
    "sudo": {"-C", "-g", "-h", "-p", "-T", "-t", "-U", "-u"},
}
SEGMENT_BREAKS = {";", "&&", "||", "|", "&", "(", ")"}
REDIRECTIONS = {">", ">>", ">|", "&>", "&>>"}


def _deny(reason: str) -> int:
    payload = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }
    }
    print(json.dumps(payload, separators=(",", ":")))
    return 0


def _load_payload() -> dict:
    raw = sys.stdin.read()
    if not raw.strip():
        return {}
    data = json.loads(raw)
    return data if isinstance(data, dict) else {}


def _tool_input(payload: dict) -> dict:
    value = payload.get("tool_input")
    return value if isinstance(value, dict) else {}


def _command(payload: dict, tool: str) -> str:
    data = _tool_input(payload)
    for key in ("command", "cmd", "patch"):
        value = data.get(key)
        if isinstance(value, str) and value.strip():
            return value
    if tool == "Bash":
        for key in ("command", "cmd"):
            value = payload.get(key)
            if isinstance(value, str) and value.strip():
                return value
    return ""


def _normalise(path: str, base: str) -> str:
    value = path.strip()
    if not value:
        return ""
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        value = value[1:-1]
    if not os.path.isabs(value):
        value = os.path.join(base or CANONICAL, value)
    return os.path.realpath(os.path.normpath(value))


def _protected_root(path: str) -> str:
    normalised = os.path.normpath(path)
    for root in PROTECTED:
        cleaned = root.rstrip("/")
        if normalised == cleaned or normalised.startswith(cleaned + "/"):
            return cleaned
    return ""


def _heredoc_specs(line: str) -> list[tuple[str, bool]]:
    """Return here-document delimiters introduced on one command line."""
    specs: list[tuple[str, bool]] = []
    index = 0
    quote = ""
    escaped = False
    while index < len(line):
        char = line[index]
        if escaped:
            escaped = False
            index += 1
            continue
        if quote:
            if quote == '"' and char == "\\":
                escaped = True
            elif char == quote:
                quote = ""
            index += 1
            continue
        if char in {"'", '"'}:
            quote = char
            index += 1
            continue
        if char == "\\":
            escaped = True
            index += 1
            continue
        if char == "#" and (index == 0 or line[index - 1].isspace() or line[index - 1] in ";&|()"):
            break
        if line.startswith("<<<", index):
            index += 3
            continue
        if not line.startswith("<<", index):
            index += 1
            continue

        cursor = index + 2
        strip_tabs = False
        if cursor < len(line) and line[cursor] == "-":
            strip_tabs = True
            cursor += 1
        while cursor < len(line) and line[cursor] in {" ", "\t"}:
            cursor += 1

        delimiter: list[str] = []
        while cursor < len(line):
            char = line[cursor]
            if char in {" ", "\t", "\r", "\n", ";", "&", "|", "(", ")", "<", ">"}:
                break
            if char in {"'", '"'}:
                delimiter_quote = char
                cursor += 1
                while cursor < len(line) and line[cursor] != delimiter_quote:
                    if delimiter_quote == '"' and line[cursor] == "\\" and cursor + 1 < len(line):
                        delimiter.append(line[cursor + 1])
                        cursor += 2
                    else:
                        delimiter.append(line[cursor])
                        cursor += 1
                if cursor < len(line):
                    cursor += 1
                continue
            if char == "\\" and cursor + 1 < len(line):
                delimiter.append(line[cursor + 1])
                cursor += 2
                continue
            delimiter.append(char)
            cursor += 1

        if delimiter:
            specs.append(("".join(delimiter), strip_tabs))
        index = cursor
    return specs


def _strip_heredoc_bodies(command: str) -> str:
    """Drop here-document bodies while retaining executable command lines."""
    output: list[str] = []
    pending: list[tuple[str, bool]] = []
    for line in command.splitlines(keepends=True):
        raw_line = line.rstrip("\r\n")
        if pending:
            delimiter, strip_tabs = pending[0]
            candidate = raw_line.lstrip("\t") if strip_tabs else raw_line
            if candidate == delimiter:
                pending.pop(0)
            continue
        output.append(line)
        pending.extend(_heredoc_specs(raw_line))
    return "".join(output)


def _tokens(command: str) -> list[str] | None:
    normalised: list[str] = []
    quote = ""
    escaped = False
    for char in command:
        if escaped:
            normalised.append(char)
            escaped = False
            continue
        if char == "\\" and quote != "'":
            normalised.append(char)
            escaped = True
            continue
        if quote:
            if char == quote:
                quote = ""
            normalised.append(char)
            continue
        if char in {"'", '"'}:
            quote = char
            normalised.append(char)
            continue
        if char == "\n":
            normalised.append(" ; ")
            continue
        normalised.append(char)
    try:
        lexer = shlex.shlex("".join(normalised), posix=True, punctuation_chars=";&|()<>")
        lexer.whitespace_split = True
        lexer.commenters = ""
        return list(lexer)
    except ValueError:
        return None


def _unwrap(segment: list[str], base: str) -> tuple[list[str], list[str]]:
    """Remove shell prefixes and assignments, returning Git target assignments."""
    rest = list(segment)
    targets: list[str] = []
    while rest:
        assignment = ASSIGNMENT.match(rest[0])
        if assignment:
            name, value = assignment.groups()
            if name in GIT_TARGET_ASSIGNMENTS and value:
                targets.append(_normalise(value, base))
            rest.pop(0)
            continue

        prefix = os.path.basename(rest[0])
        if prefix not in COMMAND_PREFIXES:
            break
        rest.pop(0)
        value_options = WRAPPER_ARG_OPTIONS.get(prefix, set())
        while rest and rest[0].startswith("-"):
            option = rest.pop(0)
            if option == "--":
                break
            if option in value_options and rest:
                rest.pop(0)
        while rest:
            assignment = ASSIGNMENT.match(rest[0])
            if not assignment:
                break
            name, value = assignment.groups()
            if name in GIT_TARGET_ASSIGNMENTS and value:
                targets.append(_normalise(value, base))
            rest.pop(0)
    return rest, targets


def _git_invocation(
    segment: list[str], base: str
) -> tuple[str, list[str], list[str]] | None:
    words, targets = _unwrap(segment, base)
    if not words or os.path.basename(words[0]) != "git":
        return None

    args = words[1:]
    index = 0
    while index < len(args):
        argument = args[index]
        if argument == "--":
            if index + 1 < len(args):
                return args[index + 1], args[index + 2 :], targets
            return None
        if argument in {"-C", "--git-dir", "--work-tree"}:
            if index + 1 < len(args):
                targets.append(_normalise(args[index + 1], base))
                index += 2
                continue
            return None
        if argument.startswith("-C") and len(argument) > 2:
            targets.append(_normalise(argument[2:], base))
            index += 1
            continue
        if argument.startswith("--git-dir="):
            targets.append(_normalise(argument.split("=", 1)[1], base))
            index += 1
            continue
        if argument.startswith("--work-tree="):
            targets.append(_normalise(argument.split("=", 1)[1], base))
            index += 1
            continue
        if argument in GIT_VALUE_OPTIONS:
            index += 2
            continue
        if any(argument.startswith(option + "=") for option in GIT_VALUE_OPTIONS if option.startswith("--")):
            index += 1
            continue
        if argument.startswith("-"):
            index += 1
            continue
        return argument, args[index + 1 :], targets
    return None


def _protected_git_mutation(segment: list[str], base: str) -> str:
    invocation = _git_invocation(segment, base)
    if not invocation:
        return ""
    subcommand, _arguments, targets = invocation
    if subcommand not in GIT_MUTATING_SUBCOMMANDS:
        return ""
    for target in [base, *targets]:
        root = _protected_root(_normalise(target, base))
        if root:
            return root
    return ""


def _git_special(segment: list[str], base: str) -> str:
    invocation = _git_invocation(segment, base)
    if not invocation:
        return ""
    subcommand, arguments, _targets = invocation
    if subcommand in {"init", "clone"}:
        return "repo_create"
    if subcommand == "worktree" and arguments and arguments[0] == "add":
        return "worktree"
    return ""


def _repo_creation(segment: list[str], base: str) -> bool:
    words, _targets = _unwrap(segment, base)
    if not words:
        return False
    command_name = os.path.basename(words[0])
    arguments = words[1:]
    if command_name == "gh" and len(arguments) >= 2:
        return arguments[0] == "repo" and arguments[1] in {"create", "clone"}
    if command_name == "hub":
        return bool(arguments and arguments[0] == "create")
    return False


def _first_protected(paths: list[str], base: str) -> str:
    for path in paths:
        root = _protected_root(_normalise(path, base))
        if root:
            return root
    return ""


def _shell_write_root(segment: list[str], base: str) -> str:
    for index, token in enumerate(segment):
        if token in REDIRECTIONS and index + 1 < len(segment):
            root = _protected_root(_normalise(segment[index + 1], base))
            if root:
                return root

    words, _targets = _unwrap(segment, base)
    if not words:
        return ""
    command_name = os.path.basename(words[0])
    arguments = words[1:]
    if command_name == "cd":
        return ""
    if command_name in {"git", "export", "unset", "set", "ulimit", "umask", "true", "false", ":"}:
        return ""
    if command_name not in WRITE_COMMANDS:
        return ""

    if command_name == "dd":
        return _first_protected(
            [argument[3:] for argument in arguments if argument.startswith("of=")],
            base,
        )

    if command_name in {"cp", "install", "ln"}:
        if "-t" in arguments:
            index = arguments.index("-t")
            if index + 1 < len(arguments):
                return _protected_root(_normalise(arguments[index + 1], base))
        positional = [argument for argument in arguments if not argument.startswith("-")]
        if positional:
            return _protected_root(_normalise(positional[-1], base))
        return ""

    if command_name == "mv":
        for index, argument in enumerate(arguments):
            if argument == "-t" and index + 1 < len(arguments):
                root = _protected_root(_normalise(arguments[index + 1], base))
                if root:
                    return root
            if not argument.startswith("-"):
                root = _protected_root(_normalise(argument, base))
                if root:
                    return root
        return ""

    if command_name in {"sed", "perl"}:
        if not any(argument == "-i" or argument.startswith("-i") for argument in arguments):
            return ""
        return _first_protected(
            [argument for argument in arguments if argument and not argument.startswith("-")],
            base,
        )

    return _first_protected(
        [argument for argument in arguments if argument and not argument.startswith("-")],
        base,
    )


def _cd_target(segment: list[str], base: str) -> str:
    words, _targets = _unwrap(segment, base)
    if not words or os.path.basename(words[0]) != "cd":
        return ""
    target = next((argument for argument in words[1:] if not argument.startswith("-")), "")
    return _normalise(target, base) if target else ""


def _invokes_apply_patch(shell_text: str) -> bool:
    tokens = _tokens(shell_text)
    if not tokens:
        return False
    segment: list[str] = []
    for token in [*tokens, ";"]:
        if token not in SEGMENT_BREAKS:
            segment.append(token)
            continue
        words, _targets = _unwrap(segment, CANONICAL)
        if words and os.path.basename(words[0]) == "apply_patch":
            return True
        segment = []
    return False


def _patch_protected(command: str, base: str) -> tuple[str, str]:
    for match in PATCH_PATH.finditer(command):
        raw_path = match.group(1).strip()
        root = _protected_root(_normalise(raw_path, base))
        if root:
            return raw_path, root
    return "", ""


def _inspect_shell(command: str, cwd: str) -> tuple[str, str] | None:
    shell_text = _strip_heredoc_bodies(command)
    tokens = _tokens(shell_text)
    if not tokens:
        return None

    current_dir = _normalise(cwd or CANONICAL, CANONICAL)

    def inspect_segment(segment: list[str]) -> tuple[str, str] | None:
        nonlocal current_dir
        if not segment:
            return None
        if _repo_creation(segment, current_dir):
            return "repo_create", ""
        special = _git_special(segment, current_dir)
        if special:
            return special, ""
        protected = _protected_git_mutation(segment, current_dir)
        if protected:
            return "git_mutation", protected
        written = _shell_write_root(segment, current_dir)
        if written:
            return "write", written
        changed_dir = _cd_target(segment, current_dir)
        if changed_dir:
            current_dir = changed_dir
        return None

    segment: list[str] = []
    for token in [*tokens, ";"]:
        if token in SEGMENT_BREAKS:
            risk = inspect_segment(segment)
            if risk:
                return risk
            segment = []
        else:
            segment.append(token)
    return None


def _deny_shell_risk(risk: tuple[str, str]) -> int:
    kind, detail = risk
    if kind == "repo_create":
        return _deny(
            "Codex Device Monitor guard: repository creation/cloning is not authorised "
            f"in this workspace (Decision 65). Work inside {CANONICAL} and report the "
            "refused command."
        )
    if kind == "worktree":
        return _deny(
            "Codex Device Monitor guard: worktree creation is not authorised (Decision 65). "
            "Work in the canonical checkout; do not create worktrees."
        )
    if kind == "git_mutation":
        return _deny(
            f"Codex Device Monitor guard: mutations against {detail} are not authorised "
            "(protected checkout)."
        )
    return _deny(
        f"Codex Device Monitor guard: writing into {detail} is not authorised "
        "(protected checkout). Edits belong in the canonical workspace."
    )


def main() -> int:
    try:
        payload = _load_payload()
    except Exception:
        return 0

    tool = str(payload.get("tool_name") or payload.get("toolName") or "")
    cwd_value = payload.get("cwd")
    cwd = cwd_value if isinstance(cwd_value, str) and cwd_value else CANONICAL
    command = _command(payload, tool)
    if not command:
        return 0

    if tool == "Bash":
        shell_text = _strip_heredoc_bodies(command)
        if _invokes_apply_patch(shell_text):
            written_path, protected = _patch_protected(command, cwd)
            if protected:
                return _deny(
                    f"Codex Device Monitor guard: writing {written_path} is not authorised "
                    "(protected checkout). Edits belong in the canonical workspace."
                )
        risk = _inspect_shell(command, cwd)
        if risk:
            return _deny_shell_risk(risk)
        return 0

    if tool in {"apply_patch", "Edit", "Write"}:
        written_path, protected = _patch_protected(command, cwd)
        if protected:
            return _deny(
                f"Codex Device Monitor guard: writing {written_path} is not authorised "
                "(protected checkout). Edits belong in the canonical workspace."
            )
        return 0

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

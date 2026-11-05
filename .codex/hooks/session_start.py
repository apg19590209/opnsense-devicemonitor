#!/usr/bin/env python3
"""Advisory Codex SessionStart check for the Device Monitor workspace.

This is deliberately advisory. Codex project hooks cannot reproduce the
launcher-level hard failure of ``cline-dm``; the written project instructions
and the trusted project boundary remain the authority. The hook:

* reports the canonical workspace, branch, HEAD, and dirty count as context;
* warns when the top-level, origin, or branch does not match expectations;
* reports the current ``tests/price_gate.py`` status without ever blocking.

It fails open on malformed input or internal errors and never prints secrets.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys

CANONICAL = "/root/src/opnsense-devicemonitor-upstream"
CANONICAL_REMOTE = "apg19590209/opnsense-devicemonitor"
EXPECTED_BRANCHES = {
    "main",
    "master",
    "release/2.13",
    "fix/pruning-remediation-20261103",
}
GIT = shutil.which("git") or "/usr/local/bin/git"


def _run(args: list[str], cwd: str, timeout: int = 5) -> tuple[int, str]:
    try:
        completed = subprocess.run(
            args,
            cwd=cwd,
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
        return completed.returncode, (completed.stdout or "").strip()
    except Exception:
        return -1, ""


def _load_payload() -> dict:
    raw = sys.stdin.read()
    if not raw.strip():
        return {}
    data = json.loads(raw)
    return data if isinstance(data, dict) else {}


def _main() -> int:
    try:
        payload = _load_payload()
    except Exception:
        return 0

    cwd_value = payload.get("cwd")
    cwd = cwd_value if isinstance(cwd_value, str) and cwd_value else os.getcwd()
    if not os.path.isdir(cwd):
        cwd = CANONICAL

    context: list[str] = []
    warnings: list[str] = []

    code, toplevel = _run([GIT, "-C", cwd, "rev-parse", "--show-toplevel"], cwd)
    if code != 0 or not toplevel:
        warnings.append("Device Monitor workspace identity could not be verified (not a git work tree).")
        repo = cwd
    else:
        repo = toplevel
        if toplevel != CANONICAL:
            warnings.append(
                f"Device Monitor workspace mismatch: git top-level is {toplevel}, expected {CANONICAL}."
            )

        code, origin = _run([GIT, "-C", repo, "config", "--get", "remote.origin.url"], repo)
        if code != 0 or CANONICAL_REMOTE not in origin:
            warnings.append("Device Monitor workspace origin does not identify the canonical repository.")

        code, branch = _run([GIT, "-C", repo, "rev-parse", "--abbrev-ref", "HEAD"], repo)
        branch = branch if code == 0 and branch else "unknown"
        if branch not in EXPECTED_BRANCHES:
            warnings.append(f"Unexpected Device Monitor branch: {branch}.")

        code, head = _run([GIT, "-C", repo, "rev-parse", "HEAD"], repo)
        head = head[:12] if code == 0 and head else "unknown"

        code, dirty_output = _run([GIT, "-C", repo, "status", "--porcelain"], repo)
        dirty = len([line for line in dirty_output.splitlines() if line.strip()]) if code == 0 else -1
        dirty_text = str(dirty) if dirty >= 0 else "unknown"
        context.append(
            f"Device Monitor workspace: {repo}; branch={branch}; HEAD={head}; dirty={dirty_text}."
        )

    gate = os.path.join(repo, "tests", "price_gate.py")
    if os.path.isfile(gate):
        code, status = _run([sys.executable or "python3", gate, "--status"], repo)
        if code == 0 and "peak=true" in status:
            warnings.append(
                "PEAK PRICE WARNING: tests/price_gate.py reports a full-price window. "
                "Harness runs require interactive confirmation; bypass only with operator authorisation."
            )
        elif code != 0:
            warnings.append("Price gate status could not be read; check tests/price_gate.py before harness work.")
        if code == 0:
            context.append("Before starting a harness, run python3 tests/price_gate.py --status and follow its prompt.")
    else:
        warnings.append("tests/price_gate.py is missing; price-gate status could not be checked.")

    result: dict = {}
    if context:
        result["hookSpecificOutput"] = {
            "hookEventName": "SessionStart",
            "additionalContext": " ".join(context),
        }
    if warnings:
        result["systemMessage"] = " ".join(warnings)
    if result:
        print(json.dumps(result, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())

#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
#
# Copyright 2026 Anthony Gonzalez (apg19590209)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# Author: Cline Bot Inc. (upstream project: the Cline monorepo,
# https://cline.bot, licensed Apache-2.0). Ported into the Device Monitor test
# harness as tests/price_gate.py on 2026-10-09 by the workspace operator
# (apg19590209).
#
# Provenance: the ported revision was byte-identical to the upstream
# apps/cli/tests/price_gate.py with sha256
# 3fea2443f2bbc644ca30ddfa7ec3c4109579933019e4e78b3bf1e9ad9678a03c;
# this header block is the only change made since.
#
# Licensing note: the Device Monitor repository as a whole is BSD-2-Clause
# (see LICENSE). This file remains Apache-2.0 third-party material and is not
# covered by those repository terms.
"""Peak-price gate for test harness entry points.

The gate evaluates the *Sydney* wall clock (AEST/AEDT) independently of the
host machine's timezone configuration, because the premium billing window is
driven by the provider region and not by the developer's laptop or the CI
runner's locale.

Behaviour:

* Off-peak (weekends, configured holidays, or outside the premium windows in
  UTC) -> silent no-op, the harness runs exactly as before.
* Premium window (Monday-Friday, 01:00-04:00 UTC or 06:00-10:00 UTC) -> prints a
  warning and requires an interactive ``y`` confirmation before the caller may
  continue. Anything else (``n``, empty answer, timeout, EOF, Ctrl-C) aborts
  with exit code 1 *before* the harness allocates any heavy context.

The windows are the provider's own UTC schedule. They are evaluated in UTC so a
Sydney daylight-saving change can never move a boundary; Sydney labels are
computed only for display. The provider also excludes Chinese public holidays;
that calendar is configuration (``deepseek_holidays.json``), never invented
here, and an empty calendar excludes nothing.

Hook a harness up at the very top of its execution flow:

    from tests.price_gate import enforce_peak_price_gate

    enforce_peak_price_gate("test_language_acceptance")

CI note: an automated runner cannot answer the prompt, so a peak-window run
aborts by design. Set ``CLINE_PRICE_GATE=bypass`` in the workflow environment
(see ``BYPASS_ENV_VAR``) to keep scheduled pipelines running, or ``--force``
when invoking the module directly.
"""

import argparse
import io
import os
import select
import sys
from collections.abc import Callable, Sequence
import json
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

SYDNEY_TZ = ZoneInfo("Australia/Sydney")
UTC_TZ = timezone.utc

# Premium (full-price) windows as (start_hour, end_hour) in UTC, Monday-Friday
# only. Start inclusive, end exclusive. These are the provider's published
# UTC windows: 01:00-04:00 and 06:00-10:00.
PEAK_WINDOWS_UTC: tuple[tuple[int, int], ...] = ((1, 4), (6, 10))

# Monday == 0 ... Sunday == 6, matching datetime.weekday().
PEAK_WEEKDAYS: frozenset[int] = frozenset({0, 1, 2, 3, 4})

# The provider also excludes Chinese public holidays. That calendar is not
# derived or guessed here: it is supplied as an ISO date list, one "YYYY-MM-DD"
# per entry. An absent or empty file excludes nothing, so the gate never
# silently treats a holiday as off-peak without a configured calendar.
HOLIDAYS_ENV_VAR = "DEEPSEEK_HOLIDAYS_FILE"
DEFAULT_HOLIDAYS_FILE = Path(__file__).with_name("deepseek_holidays.json")

PEAK_WARNING = "⚠️ PEAK PRICE WARNING: You are running tests in a full-price window."
ABORT_MESSAGE = "Peak-price gate: aborted before any heavy context or API loop."

BYPASS_ENV_VAR = "CLINE_PRICE_GATE"
TIMEOUT_ENV_VAR = "CLINE_PRICE_GATE_TIMEOUT_SECONDS"
BYPASS_VALUES = frozenset({"1", "true", "yes", "on", "bypass", "skip"})
DEFAULT_TIMEOUT_SECONDS = 30.0

EXIT_OK = 0
EXIT_ABORTED = 1

CONFIRM_PROMPT = "Continue at full price? [y/N] "
AFFIRMATIVE_ANSWERS = frozenset({"y", "yes"})


def sydney_now(reference: datetime | None = None) -> datetime:
    """Return the wall clock in Sydney.

    ``reference`` exists for tests and CLI dry runs: an aware datetime is
    converted into the Sydney zone, a naive one is assumed to already be Sydney
    local time.
    """
    if reference is None:
        return datetime.now(SYDNEY_TZ)
    if reference.tzinfo is None:
        return reference.replace(tzinfo=SYDNEY_TZ)
    return reference.astimezone(SYDNEY_TZ)


def utc_now(reference: datetime | None = None) -> datetime:
    """Return the instant in UTC.

    ``reference`` exists for tests and CLI dry runs: an aware datetime is
    converted to UTC, a naive one is assumed to already be UTC.
    """
    if reference is None:
        return datetime.now(UTC_TZ)
    if reference.tzinfo is None:
        return reference.replace(tzinfo=UTC_TZ)
    return reference.astimezone(UTC_TZ)


def holiday_calendar_path() -> Path:
    override = os.environ.get(HOLIDAYS_ENV_VAR, "").strip()
    return Path(override) if override else DEFAULT_HOLIDAYS_FILE


def load_holidays(path: Path | None = None) -> frozenset[date]:
    """Configured provider-excluded dates, or an empty set when none exist.

    A malformed file is an error, not an excuse: it must not silently make a
    premium day look off-peak.
    """
    path = holiday_calendar_path() if path is None else path
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return frozenset()
    if isinstance(raw, dict):
        raw = raw.get("excluded_dates", [])
    parsed = set()
    for item in raw:
        parsed.add(date.fromisoformat(str(item)))
    return frozenset(parsed)


def _window_bounds(moment_utc: datetime) -> tuple[datetime, datetime] | None:
    """The active UTC window for the instant, or None."""
    minute_of_day = moment_utc.hour * 60 + moment_utc.minute
    for start_hour, end_hour in PEAK_WINDOWS_UTC:
        if start_hour * 60 <= minute_of_day < end_hour * 60:
            day = moment_utc.date()
            return (
                datetime.combine(day, time(start_hour), UTC_TZ),
                datetime.combine(day, time(end_hour), UTC_TZ),
            )
    return None


def is_peak_window(reference: datetime | None = None, *, holidays: frozenset[date] | None = None) -> bool:
    """True when the instant falls inside a premium billing window.

    The provider's schedule is Monday-Friday in UTC, with its own excluded
    holiday dates. A window that starts on a weekday and crosses midnight into
    a Saturday keeps its weekday's classification until the instant it ends.
    """
    moment = utc_now(reference)
    bounds = _window_bounds(moment)
    if bounds is None or moment.weekday() not in PEAK_WEEKDAYS:
        return False
    excluded = load_holidays() if holidays is None else holidays
    # A window belongs to the UTC date it starts on, so a window ending just
    # after midnight is still classified by the date that began it.
    return bounds[0].date() not in excluded


def _sydney_label(moment: datetime) -> str:
    local = moment.astimezone(SYDNEY_TZ)
    return f"{local:%H:%M} {local.tzname()}"


def peak_window_label(reference: datetime | None = None) -> str:
    """Human readable description of the active window, empty when off-peak."""
    moment = utc_now(reference)
    bounds = _window_bounds(moment)
    if bounds is None or not is_peak_window(moment):
        return ""
    start, end = bounds
    return (
        f"Mon-Fri {start:%H:%M}-{end:%H:%M} UTC "
        f"({_sydney_label(start)}-{_sydney_label(end)} Sydney; now {_sydney_label(moment)})"
    )


def describe_peak_status(reference: datetime | None = None) -> tuple[bool, str]:
    """Return ``(is_peak, description)`` without touching stdin/stdout."""
    moment = utc_now(reference)
    clock = f"{moment:%a %Y-%m-%d %H:%M:%S} UTC ({_sydney_label(moment)} Sydney)"
    if is_peak_window(moment):
        return True, f"premium window active, {peak_window_label(moment)} [{clock}]"
    return False, f"off-peak [{clock}]"

def bypass_requested(bypass: bool | None = None) -> bool:
    """True when the caller opted out, explicitly or via ``CLINE_PRICE_GATE``."""
    if bypass is not None:
        return bypass
    value = os.environ.get(BYPASS_ENV_VAR, "").strip().lower()
    return value in BYPASS_VALUES


def resolve_timeout_seconds(explicit: float | None = None) -> float:
    """Resolve the prompt timeout from the argument, env var, or default."""
    if explicit is not None:
        return max(0.0, explicit)
    raw = os.environ.get(TIMEOUT_ENV_VAR, "").strip()
    if not raw:
        return DEFAULT_TIMEOUT_SECONDS
    try:
        return max(0.0, float(raw))
    except ValueError:
        return DEFAULT_TIMEOUT_SECONDS


def _read_answer(prompt_text: str, timeout_seconds: float) -> str | None:
    """Write the prompt and read one line, or None on timeout/EOF/interrupt.

    ``select`` is used so an unattended stdin (closed pipe, ``/dev/null``) or a
    stalled pipeline cannot block a harness forever. When stdin has no usable
    file descriptor the read falls back to a plain ``readline``.
    """
    sys.stdout.write(prompt_text)
    sys.stdout.flush()

    try:
        fileno = sys.stdin.fileno()
    except (AttributeError, ValueError, io.UnsupportedOperation):
        fileno = None

    if fileno is None or timeout_seconds <= 0:
        try:
            return sys.stdin.readline()
        except (EOFError, KeyboardInterrupt):
            return None

    try:
        ready, _, _ = select.select([fileno], [], [], timeout_seconds)
    except (OSError, ValueError):
        try:
            return sys.stdin.readline()
        except (EOFError, KeyboardInterrupt):
            return None

    if not ready:
        return None
    try:
        return sys.stdin.readline()
    except (EOFError, KeyboardInterrupt):
        return None


def check(
    *,
    reference: datetime | None = None,
    prompt: Callable[[str, float], str | None] | None = None,
    timeout_seconds: float | None = None,
    bypass: bool | None = None,
    confirm_stream: "io.TextIOBase | None" = None,
) -> int:
    """Evaluate the gate.

    Returns ``EXIT_OK`` when the caller may proceed and ``EXIT_ABORTED`` when it
    must stop immediately. Off-peak runs are a silent no-op, so the harness
    output of a normal test run is unchanged.
    """
    if bypass_requested(bypass):
        return EXIT_OK

    moment = sydney_now(reference)
    if not is_peak_window(moment):
        return EXIT_OK

    out = confirm_stream if confirm_stream is not None else sys.stdout
    timeout = resolve_timeout_seconds(timeout_seconds)

    print(PEAK_WARNING, file=out, flush=True)
    label = peak_window_label(moment)
    if label:
        print(f"   window: {label}", file=out, flush=True)
    if timeout > 0:
        hint = f"confirm with 'y' within {timeout:g}s to continue"
    else:
        hint = "confirm with 'y' to continue"
    print(f"   {hint}; anything else aborts this run.", file=out, flush=True)

    read = prompt if prompt is not None else _read_answer
    try:
        answer = read(CONFIRM_PROMPT, timeout)
    except KeyboardInterrupt:
        answer = None

    if answer is None:
        print(ABORT_MESSAGE, file=sys.stderr, flush=True)
        return EXIT_ABORTED
    if answer.strip().lower() not in AFFIRMATIVE_ANSWERS:
        print(ABORT_MESSAGE, file=sys.stderr, flush=True)
        return EXIT_ABORTED
    return EXIT_OK


def enforce_peak_price_gate(
    harness_name: str,
    *,
    reference: datetime | None = None,
    timeout_seconds: float | None = None,
    bypass: bool | None = None,
) -> None:
    """Drop-in hook for harness entry points.

    Call this at the very top of the execution flow, before any heavy context is
    loaded or any model/API loop is started. Raises ``SystemExit`` with code 1
    when the run is aborted, so the surrounding suite terminates cleanly.
    """
    if (
        check(
            reference=reference,
            timeout_seconds=timeout_seconds,
            bypass=bypass,
        )
        != EXIT_OK
    ):
        raise SystemExit(f"[{harness_name}] aborted by the peak-price gate")


def _parse_args(argv: Sequence[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="price_gate",
        description="Gate test harness runs that would start inside a premium "
        "full-price window (provider schedule, evaluated in UTC).",
    )
    parser.add_argument(
        "--now",
        help="ISO-8601 timestamp to evaluate instead of the real clock "
        "(used by tests and dry runs)",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=None,
        help=f"seconds to wait for confirmation (default "
        f"{DEFAULT_TIMEOUT_SECONDS:g}, env {TIMEOUT_ENV_VAR})",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help=f"skip the gate, same as {BYPASS_ENV_VAR}=bypass",
    )
    parser.add_argument(
        "--status",
        action="store_true",
        help="print the current gate status and exit without prompting",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point: ``python3 tests/price_gate.py [--status]``."""
    args = _parse_args(argv)
    # A value without an offset is taken as UTC; the provider's windows are UTC.
    reference = datetime.fromisoformat(args.now) if args.now else None

    if args.status:
        is_peak, description = describe_peak_status(reference)
        print(f"peak={str(is_peak).lower()} {description}")
        return EXIT_OK

    code = check(
        reference=reference,
        timeout_seconds=args.timeout,
        bypass=True if args.force else None,
    )
    if code == EXIT_OK:
        print("Peak-price gate: cleared to run.")
    return code


if __name__ == "__main__":
    raise SystemExit(main())

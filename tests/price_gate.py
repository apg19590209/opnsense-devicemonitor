#!/usr/bin/env python3
"""Peak-price gate for test harness entry points.

The gate evaluates the *Sydney* wall clock (AEST/AEDT) independently of the
host machine's timezone configuration, because the premium billing window is
driven by the provider region and not by the developer's laptop or the CI
runner's locale.

Behaviour:

* Off-peak (weekends, or Mon-Fri outside the premium windows) -> silent no-op,
  the harness runs exactly as before.
* Premium window (Mon-Fri 11:00-14:00 or 16:00-20:00 Sydney time) -> prints a
  warning and requires an interactive ``y`` confirmation before the caller may
  continue. Anything else (``n``, empty answer, timeout, EOF, Ctrl-C) aborts
  with exit code 1 *before* the harness allocates any heavy context.

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
from datetime import datetime
from zoneinfo import ZoneInfo

SYDNEY_TZ = ZoneInfo("Australia/Sydney")

# Premium (full-price) windows as (start_hour, end_hour) in Sydney local time,
# Monday-Friday only. Start inclusive, end exclusive.
PEAK_WINDOWS: tuple[tuple[int, int], ...] = ((11, 14), (16, 20))

# Monday == 0 ... Sunday == 6, matching datetime.weekday().
PEAK_WEEKDAYS: frozenset[int] = frozenset({0, 1, 2, 3, 4})

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


def _minute_of_day(moment: datetime) -> int:
    return moment.hour * 60 + moment.minute


def is_peak_window(reference: datetime | None = None) -> bool:
    """True when the given instant falls inside a premium billing window."""
    moment = sydney_now(reference)
    if moment.weekday() not in PEAK_WEEKDAYS:
        return False
    minute_of_day = _minute_of_day(moment)
    return any(
        start_hour * 60 <= minute_of_day < end_hour * 60
        for start_hour, end_hour in PEAK_WINDOWS
    )


def peak_window_label(reference: datetime | None = None) -> str:
    """Human readable description of the active window, empty when off-peak."""
    moment = sydney_now(reference)
    minute_of_day = _minute_of_day(moment)
    for start_hour, end_hour in PEAK_WINDOWS:
        if start_hour * 60 <= minute_of_day < end_hour * 60:
            return (
                f"Mon-Fri {start_hour:02d}:00-{end_hour:02d}:00 "
                f"{moment.tzname()} (now {moment.strftime('%a %H:%M')})"
            )
    return ""


def describe_peak_status(reference: datetime | None = None) -> tuple[bool, str]:
    """Return ``(is_peak, description)`` without touching stdin/stdout."""
    moment = sydney_now(reference)
    clock = moment.strftime("%a %Y-%m-%d %H:%M:%S %Z")
    if is_peak_window(moment):
        return True, f"premium window active ({clock})"
    return False, f"off-peak ({clock})"

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
        "full-price window (Sydney time).",
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

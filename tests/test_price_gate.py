"""Boundary tests for the peak-price gate.

The provider's premium windows are UTC, Monday-Friday: 01:00-04:00 and
06:00-10:00. They must be evaluated in UTC (so a Sydney DST change cannot move
them), labelled in Sydney only for display, and the provider's excluded
holidays must be an explicit calendar rather than a guessed one.

The gate remains the project's premium-spend gate: these tests only pin when it
warns. They claim nothing about whether CI or local tests consume tokens.

Run with: python3 tests/test_price_gate.py
"""
import json
import os
import sys
import tempfile
from datetime import date, datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tests'))
import price_gate  # noqa: E402

UTC = timezone.utc
FAILS = []


def check(condition, label):
    if condition:
        print('  PASS', label)
    else:
        FAILS.append(label)
        print('  FAIL', label)


def peak(iso):
    return price_gate.is_peak_window(datetime.fromisoformat(iso))


def test_utc_boundaries():
    """Start inclusive, end exclusive, in the provider's own UTC hours."""
    for iso, expected in [
        ('2026-11-17T00:59:59+00:00', False),
        ('2026-11-17T01:00:00+00:00', True),
        ('2026-11-17T03:59:59+00:00', True),
        ('2026-11-17T04:00:00+00:00', False),
        ('2026-11-17T05:59:59+00:00', False),
        ('2026-11-17T06:00:00+00:00', True),
        ('2026-11-17T09:59:59+00:00', True),
        ('2026-11-17T10:00:00+00:00', False),
    ]:
        check(peak(iso) is expected, f'UTC {iso}')


def test_aedt_boundaries():
    """The same instants in AEDT (UTC+11) land at noon-15:00 and 17:00-21:00."""
    for iso, expected in [
        ('2026-11-17T11:59:59+11:00', False),
        ('2026-11-17T12:00:00+11:00', True),
        ('2026-11-17T14:59:59+11:00', True),
        ('2026-11-17T15:00:00+11:00', False),
        ('2026-11-17T16:59:59+11:00', False),
        ('2026-11-17T17:00:00+11:00', True),
        ('2026-11-17T20:59:59+11:00', True),
        ('2026-11-17T21:00:00+11:00', False),
    ]:
        check(peak(iso) is expected, f'AEDT {iso}')


def test_aest_boundaries():
    """In AEST (UTC+10, winter) the window is 11:00-14:00 and 16:00-20:00 local."""
    from zoneinfo import ZoneInfo
    sydney = ZoneInfo('Australia/Sydney')
    for wall, expected in [
        ('2026-06-16T10:59:59', False),
        ('2026-06-16T11:00:00', True),
        ('2026-06-16T13:59:59', True),
        ('2026-06-16T14:00:00', False),
        ('2026-06-16T15:59:59', False),
        ('2026-06-16T16:00:00', True),
        ('2026-06-16T19:59:59', True),
        ('2026-06-16T20:00:00', False),
    ]:
        inst = datetime.fromisoformat(wall).replace(tzinfo=sydney)
        check(inst.tzname() == 'AEST', f'{wall} is AEST in Sydney')
        check(peak(inst.isoformat()) is expected, f'AEST {wall} -> {inst.astimezone(UTC):%H:%M} UTC')


def test_dst_change_keeps_utc_window():
    """Sydney's April DST end changes the label, not the UTC window."""
    # Monday 2026-03-30 09:00 UTC is 20:00 AEDT (DST); Monday 2026-04-06
    # 09:00 UTC is 19:00 AEST (standard time). Both are the same UTC window.
    before = price_gate.peak_window_label(datetime.fromisoformat('2026-03-30T09:00:00+00:00'))
    after = price_gate.peak_window_label(datetime.fromisoformat('2026-04-06T09:00:00+00:00'))
    check('06:00-10:00 UTC' in before and '06:00-10:00 UTC' in after,
          'window stays 06:00-10:00 UTC across the DST change')
    check('20:00 AEDT' in before, 'pre-change label is AEDT')
    check('19:00 AEST' in after, 'post-change label is AEST')


def test_weekdays():
    for iso in ('2026-11-16T01:30:00+00:00', '2026-11-20T09:30:00+00:00'):
        check(peak(iso), f'weekday {iso} is peak')


def test_weekends_never_peak():
    for iso in ('2026-11-14T02:00:00+00:00', '2026-11-15T08:00:00+00:00',
                '2026-11-14T23:00:00+00:00'):
        check(not peak(iso), f'weekend {iso} is off-peak')


def test_holidays_only_from_configuration():
    with tempfile.TemporaryDirectory() as tmp:
        calendar = Path(tmp) / 'holidays.json'
        calendar.write_text(json.dumps(['2026-11-17']), encoding='utf-8')
        saved = os.environ.get(price_gate.HOLIDAYS_ENV_VAR)
        os.environ[price_gate.HOLIDAYS_ENV_VAR] = str(calendar)
        try:
            check(not peak('2026-11-17T02:00:00+00:00'), 'configured holiday is off-peak')
            check(peak('2026-11-18T02:00:00+00:00'), 'next day is peak again')
        finally:
            if saved is None:
                os.environ.pop(price_gate.HOLIDAYS_ENV_VAR, None)
            else:
                os.environ[price_gate.HOLIDAYS_ENV_VAR] = saved
        saved = os.environ.get(price_gate.HOLIDAYS_ENV_VAR)
        os.environ[price_gate.HOLIDAYS_ENV_VAR] = str(Path(tmp) / 'absent.json')
        try:
            check(peak('2026-11-17T02:00:00+00:00'), 'absent calendar invents no holidays')
        finally:
            if saved is None:
                os.environ.pop(price_gate.HOLIDAYS_ENV_VAR, None)
            else:
                os.environ[price_gate.HOLIDAYS_ENV_VAR] = saved


def test_shipped_calendar_is_explicit():
    path = ROOT / 'tests' / 'deepseek_holidays.json'
    if not path.is_file():
        check(price_gate.load_holidays(path) == frozenset(), 'no shipped calendar excludes nothing')
        return
    data = json.loads(path.read_text(encoding='utf-8'))
    dates = data['excluded_dates'] if isinstance(data, dict) else data
    for item in dates:
        date.fromisoformat(item)
    check(True, 'shipped calendar is an explicit ISO date list')


def test_status_text_names_utc_and_sydney():
    _, peak_text = price_gate.describe_peak_status(datetime.fromisoformat('2026-11-17T07:00:00+00:00'))
    check('UTC' in peak_text and 'Sydney' in peak_text and '17:00' in peak_text,
          'peak status names both zones')
    is_peak, off_text = price_gate.describe_peak_status(datetime.fromisoformat('2026-11-17T05:00:00+00:00'))
    check(is_peak is False and 'off-peak' in off_text, 'gap between windows is off-peak')


def test_approval_requirement_preserved():
    src = (ROOT / 'tests' / 'price_gate.py').read_text(encoding='utf-8')
    check('AFFIRMATIVE_ANSWERS' in src, 'explicit y confirmation remains')
    check('SystemExit' in src, 'unconfirmed premium run aborts')
    check('enforce_peak_price_gate' in src, 'harness hook remains')


def main():
    for name, fn in sorted(globals().items()):
        if name.startswith('test_') and callable(fn):
            fn()
    if FAILS:
        print(f'PRICE_GATE_TESTS=FAIL ({len(FAILS)})')
        return 1
    print('PRICE_GATE_TESTS=PASS')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

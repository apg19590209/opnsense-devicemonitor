"""Email Log timestamps follow the plugin convention: stored UTC, presented once.

The recording layer stores naive UTC text; the Email Log table, message metadata
and delivery timeline render that instant in the browser's own zone (DST rules
and abbreviation from Intl), with a server-side fallback converted through the
OPNsense-configured zone. This suite pins storage, the fallback conversion
(including midnight and both DST boundaries), the browser formatter when node is
available, and that the views never print the raw UTC value.
"""
import json
import os
import re
import shutil
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
VIEW = ROOT / 'src/opnsense/mvc/app/views/OPNsense/DeviceMonitor/emaillog.volt'
CTRL = ROOT / 'src/opnsense/mvc/app/controllers/OPNsense/DeviceMonitor/Api/EmaillogController.php'
TS = ROOT / 'src/opnsense/scripts/OPNsense/DeviceMonitor/PluginTimestamps.php'
REC = ROOT / 'src/opnsense/scripts/OPNsense/DeviceMonitor/EmailLog.php'
SYD = ZoneInfo('Australia/Sydney')


def php_raw(code):
    return subprocess.run(['php', '-r', code], capture_output=True, text=True).stdout


def php(code):
    return php_raw(code).strip()


def test_recorder_stores_utc():
    src = REC.read_text(encoding='utf-8')
    assert not re.search(r"(?<!gm)date\('Y-m-d H:i:s'\)", src), 'no local-time writes in the recorder'
    assert src.count("gmdate('Y-m-d H:i:s')") >= 2, 'submission and transport events use UTC'
    assert "$now = gmdate('Y-m-d H:i:s');" in src, 'event updates use UTC'


def test_fallback_uses_configured_zone_with_dst(tmp=None):
    """The converter uses the configured zone. A temporary config.xml keeps this
    independent of the host (a CI runner has no OPNsense configuration)."""
    import tempfile
    tmpdir = tempfile.mkdtemp()
    cfg = Path(tmpdir) / 'config.xml'
    cfg.write_text("<?xml version='1.0'?><opnsense><system><timezone>Australia/Sydney"
                   "</timezone></system></opnsense>", encoding='utf-8')
    try:
        zone = php("require '%s'; echo OPNsense\\DeviceMonitor\\PluginTimestamps::configuredZoneName('%s');" % (TS, cfg))
        assert zone == 'Australia/Sydney', f'configured zone is read from config.xml, got {zone!r}'
        cases = {
            '2026-11-17 02:59:59': '2026-11-17 13:59:59',
            '2026-11-17 03:00:00': '2026-11-17 14:00:00',
            '2026-11-17 13:00:00': '2026-11-18 00:00:00',
            '2026-04-04 15:59:59': '2026-04-05 02:59:59',
            '2026-04-04 16:00:00': '2026-04-05 02:00:00',
            '2026-10-03 15:59:59': '2026-10-04 01:59:59',
            '2026-10-03 16:00:00': '2026-10-04 03:00:00',
        }
        for utc, expected in cases.items():
            got = php("require '%s'; echo OPNsense\\DeviceMonitor\\PluginTimestamps::toConfiguredZone('%s', '%s');"
                      % (TS, utc, cfg))
            assert got == expected, (utc, got, expected)
            probe = datetime.strptime(utc, '%Y-%m-%d %H:%M:%S').replace(tzinfo=timezone.utc)
            assert probe.astimezone(SYD).strftime('%Y-%m-%d %H:%M:%S') == expected, utc
        ambiguous = datetime(2026, 4, 4, 16, 0, tzinfo=timezone.utc).astimezone(SYD)
        assert ambiguous.hour == 2 and ambiguous.strftime('%z') == '+1000', 'the 16:00Z instant is 02:00 AEST'
        assert php("require '%s'; echo OPNsense\\DeviceMonitor\\PluginTimestamps::toConfiguredZone('nonsense', '%s');"
                   % (TS, cfg)) == ''
    finally:
        import shutil
        shutil.rmtree(tmpdir, ignore_errors=True)


def test_shared_display_formatter():
    cases = [
        ('2026-11-20 00:10:02', 'Australia/Sydney', '2026-11-20 11:10:02 AEDT'),
        ('2026-09-12 09:00:00', 'Australia/Sydney', '2026-09-12 19:00:00 AEST'),
        ('2026-11-20 00:10:02', 'America/New_York', '2026-11-19 19:10:02 EST'),
    ]
    for value, zone, expected in cases:
        code = (
            "require '%s'; echo OPNsense\\DeviceMonitor\\PluginTimestamps::"
            "formatForDisplay(%s, %s);"
            % (TS, json.dumps(value), json.dumps(zone))
        )
        assert php(code) == expected, (value, zone, expected)

    for value in ('not-a-timestamp', '2026-11-20T00:10:02Z', ' 2026-11-20 00:10:02'):
        valid = php(
            "require '%s'; echo OPNsense\\DeviceMonitor\\PluginTimestamps::"
            "isStoredUtcTimestamp(%s) ? '1' : '0';"
            % (TS, json.dumps(value))
        )
        displayed = php_raw(
            "require '%s'; echo OPNsense\\DeviceMonitor\\PluginTimestamps::"
            "formatForDisplay(%s, 'Australia/Sydney');"
            % (TS, json.dumps(value))
        )
        assert valid == '0', f'invalid value was treated as proven UTC: {value!r}'
        assert displayed == value, f'invalid value was normalised: {value!r} -> {displayed!r}'


def test_browser_formatter_midnight_and_dst():
    # CI installs node on PATH; this host keeps it in /usr/local/bin.
    node = shutil.which('node') or shutil.which('node', path='/usr/local/bin:/usr/bin:/bin')
    if node is None:
        print('BROWSER_FORMATTER=SKIPPED (node unavailable)')
        return
    src = VIEW.read_text(encoding='utf-8')
    start = src.index('function formatTimestamp(')
    # Stop at the next function, whatever it is (status labels may sit between).
    end = start + re.search(r'\n        function [A-Za-z_]', src[start + 10:]).start() + 10
    # The display-only status map is Volt-templated; drop it (it is asserted
    # separately) so the real formatter still runs under node.
    segment = src[start:end]
    segment = re.sub(r'var statusNames = \{.*?\n        \};', '', segment, flags=re.S)
    assert re.search(r'\{\{|\{%', segment) is None, segment[-200:]
    fn = segment
    script = fn + """
console.log(formatTimestamp('2026-11-17 02:59:59', 'FB'));
console.log(formatTimestamp('2026-11-17 03:00:00', 'FB'));
console.log(formatTimestamp('2026-11-17 13:00:00', 'FB'));
console.log(formatTimestamp('2026-04-04 16:00:00', 'FB'));
console.log(formatTimestamp('2026-10-03 16:00:00', 'FB'));
console.log(formatTimestamp('garbage', 'FB'));
"""

    def run(tz):
        # Inherit the host environment (node needs its ICU/library paths) and set TZ.
        env = dict(os.environ, TZ=tz)
        return subprocess.run([node, '-e', script], capture_output=True, text=True,
                              env=env).stdout.split('\n')
    def wall(line, expected_wall):
        # The zone name comes from the runtime's locale data: full ICU names it
        # (AEDT/AEST), a C-locale runtime gives the equivalent numeric offset.
        assert line.startswith(expected_wall + ' '), (line, expected_wall)
        return line[len(expected_wall) + 1:]

    syd = run('Australia/Sydney')
    wall(syd[0], '2026-11-17 13:59:59')
    wall(syd[1], '2026-11-17 14:00:00')
    assert '11' in syd[0] and '11' in syd[1], 'AEDT is UTC+11'
    wall(syd[2], '2026-11-18 00:00:00')
    assert '11' in syd[2], 'midnight keeps the +11 offset'
    wall(syd[3], '2026-04-05 02:00:00')
    assert '10' in syd[3], 'end of daylight saving shows the +10 offset'
    wall(syd[4], '2026-10-04 03:00:00')
    assert '11' in syd[4], 'start of daylight saving shows the +11 offset'
    assert syd[5] == 'FB', 'unparseable values use the fallback'
    utc = run('UTC')
    wall(utc[1], '2026-11-17 03:00:00')
    assert 'UTC' in utc[1], 'UTC view names its zone'
    ny = run('America/New_York')
    wall(ny[1], '2026-11-16 22:00:00')
    assert 'EST' in ny[1] or '5' in ny[1], 'the same instant in New York winter time'


def test_views_render_converted_values():
    src = VIEW.read_text(encoding='utf-8')
    assert 'formatTimestamp(row.created_utc, row.created_local)' in src, 'table uses the formatter'
    assert "['Time', formatTimestamp(m.created_utc, m.created_local)]" in src, 'metadata uses it'
    assert 'formatTimestamp(step.occurred_utc, step.occurred_local)' in src, 'timeline uses it'
    assert ".text(row.created_utc)" not in src and ".text(step.occurred_utc)" not in src, 'no raw UTC shown'
    assert 'timeZoneName' in src, 'the zone abbreviation comes from the browser formatter'
    assert 'email-log-timezone-legend' not in src, 'no separate timezone legend is shown'
    for hard in ("+11:00", "+10:00", 'AEDT', 'AEST'):
        assert hard not in src, f'no hardcoded offset or abbreviation: {hard}'
    ctrl = CTRL.read_text(encoding='utf-8')
    assert ctrl.count('toConfiguredZone') >= 4, 'fallback conversion is supplied for rows, events and messages'
    search = ctrl[ctrl.index('function searchAction'):ctrl.index('function messageAction')]
    built = search.index("$timeline[] = [")
    converted = search.index("$timeline[$i]['occurred_local']")
    attached = search.index("$clean['timeline'] = $timeline;")
    assert built < converted < attached, 'event fallback is added after the step list is built, before it is attached'
    assert '/conf/config.xml' in TS.read_text(encoding='utf-8'), 'the configured zone comes from OPNsense config'


def test_csv_keeps_utc_with_explicit_header():
    src = CTRL.read_text(encoding='utf-8')
    body = src[src.index('function exportcsvAction'):]
    assert "'created_utc', 'node_ip'" in body, 'CSV timestamps stay in the stored UTC form'
    assert "header = ['created_utc'" in src, 'the CSV header names the stored field'
    assert 'toLocalString' not in src and 'toConfiguredZone($row' not in body, \
        'export is not re-localised server-side'


def test_historical_bodies_untouched():
    src = REC.read_text(encoding='utf-8')
    html = src[src.index('public static function htmlToText'):src.index('public static function boundContent')]
    assert 'date(' not in html and 'gmdate' not in html, 'body conversion never touches embedded timestamps'
    assert not re.search(r"\\d\{4\}|\d\{2\}", html), 'no date pattern is rewritten inside message text'


def main():
    test_recorder_stores_utc()
    test_fallback_uses_configured_zone_with_dst()
    test_shared_display_formatter()
    test_browser_formatter_midnight_and_dst()
    test_views_render_converted_values()
    test_csv_keeps_utc_with_explicit_header()
    test_historical_bodies_untouched()
    print('EMAIL_LOG_TIMESTAMP_CONVENTION=PASS')


if __name__ == '__main__':
    main()

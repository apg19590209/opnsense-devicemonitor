#!/usr/bin/env python3
"""Locale text-stream verification harness.

Interface, checks and exit codes are fixed by verification/locales/README.md:
standard library plus ``selenium`` only; case data in ``locale_cases/<locale>.json``;
the nine checks named there; the flags ``--case``, ``--check-env``, ``--dry-run``,
``--headless``, ``--out-dir``, ``--write-markdown``, ``--save-page-source`` and
``--driver-path``; exit codes 0 (all passed), 1 (at least one FAIL or ERROR) and
2 (configuration or environment error).

Discipline inherited from the record set:

* A check that was not exercised is ``SKIP`` (or ``ERROR``). It is never ``PASS``.
* ``markers.expected[].reported_status`` in a case file is an operator attestation.
  It is never copied into a result.
* The harness never invents a locale pin, a target build or a route. Missing
  configuration is reported as missing.
* ``--check-env`` and ``--dry-run`` never touch the network or the target.
* A run that exercises nothing produces ``NO-RESULT`` and exits 2: nothing was
  verified, so nothing may read as a pass.

Files written, only under ``--out-dir``: ``result-<locale>.json``,
``report-<locale>.html``, ``report-<locale>.md`` (``--write-markdown``),
``stream-<locale>.jsonl``, ``page-<locale>.html`` (``--save-page-source``),
``final-<locale>.png`` and ``run-<locale>.log``.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import re
import shutil
import sys
import time
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Sequence

HARNESS_NAME = 'verify_locale_stream.py'
HARNESS_VERSION = '0.1.0'

EXIT_PASS = 0
EXIT_FAIL = 1
EXIT_CONFIG = 2

STATUS_PASS = 'PASS'
STATUS_FAIL = 'FAIL'
STATUS_WARN = 'WARN'
STATUS_SKIP = 'SKIP'
STATUS_ERROR = 'ERROR'

CHECK_NAMES = (
    'stream_progressed',
    'stream_lossless',
    'no_replacement_char',
    'no_mojibake',
    'no_control_chars',
    'localized_markers_present',
    'no_untranslated_fallback',
    'document_lang',
    'diacritics_roundtrip',
)

REPLACEMENT_CHAR = '\ufffd'
CONTROL_ALLOWED = frozenset(('\t', '\n', '\r'))
CONTROL_RANGES = ((0x00, 0x08), (0x0b, 0x0c), (0x0e, 0x1f), (0x7f, 0x9f))
# cp1252/latin-1 bytes decoded as utf-8, i.e. double-encoded text.
MOJIBAKE_SEQUENCES = (
    '\u00c3\u00a9', '\u00c3\u00a8', '\u00c3\u00a0', '\u00c3\u00b9',
    '\u00c3\u00b4', '\u00c3\u00ae', '\u00c3\u00a7', '\u00c3\u00ab',
    '\u00c3\u00b1', '\u00c2\u00a0', '\u00c2\u00ab', '\u00c2\u00bb',
    '\u00e2\u0080\u0099', '\u00e2\u0080\u009c', '\u00e2\u0080\u009d',
    '\u00e2\u0080\u0093', '\u00e2\u0080\u0094', '\u00e2\u0082\u00ac',
    '\u00ef\u00bf\u00bd',
)

# Observation budget. Constants, not flags: the documented flag set is closed.
PAGE_LOAD_TIMEOUT_S = 30.0
SNAPSHOT_TIMEOUT_S = 20.0
SNAPSHOT_INTERVAL_S = 0.25
SNAPSHOT_STABLE_SAMPLES = 4

STREAM_HOOK_JS = """
window.__locale_stream__ = window.__locale_stream__ || [];
(function () {
  var push = function (kind, url, text) {
    window.__locale_stream__.push({
      kind: kind,
      url: url ? String(url) : null,
      chars: text ? text.length : 0,
      text: text || null,
      t_ms: Math.round(performance.now())
    });
  };
  if (window.fetch && !window.fetch.__localeStreamWrapped) {
    var originalFetch = window.fetch;
    var wrapped = function (input, init) {
      var target = input;
      return originalFetch.apply(this, arguments).then(function (response) {
        try {
          var clone = response.clone();
          clone.text().then(function (text) {
            push('fetch', (target && target.url) ? target.url : target, text);
          }).catch(function () {});
        } catch (error) {}
        return response;
      });
    };
    wrapped.__localeStreamWrapped = true;
    window.fetch = wrapped;
  }
  if (window.XMLHttpRequest && !window.XMLHttpRequest.prototype.__localeStreamWrapped) {
    var originalOpen = window.XMLHttpRequest.prototype.open;
    var originalSend = window.XMLHttpRequest.prototype.send;
    window.XMLHttpRequest.prototype.open = function (method, url) {
      this.__localeStreamUrl = url;
      return originalOpen.apply(this, arguments);
    };
    window.XMLHttpRequest.prototype.send = function () {
      var request = this;
      request.addEventListener('load', function () {
        var text = null;
        try {
          if (request.responseType === '' || request.responseType === 'text') {
            text = request.responseText;
          }
        } catch (error) {
          text = null;
        }
        push('xhr', request.__localeStreamUrl, text);
      });
      return originalSend.apply(this, arguments);
    };
    window.XMLHttpRequest.prototype.__localeStreamWrapped = true;
  }
  return window.__locale_stream__.length;
})();
"""

SNAPSHOT_JS = """
if (!document || !document.documentElement) { return null; }
var text = document.body ? document.body.innerText : '';
return {
  t_ms: Math.round(performance.now()),
  html: document.documentElement.outerHTML,
  text: text,
  lang: document.documentElement.getAttribute('lang'),
  charset: document.characterSet || null
};
"""

PAGE_STATE_JS = """
return {
  lang: document.documentElement ? document.documentElement.getAttribute('lang') : null,
  charset: document.characterSet || null,
  text: document.body ? document.body.innerText : ''
};
"""

def utc_now() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


def iso(moment: dt.datetime) -> str:
    return moment.isoformat(timespec='seconds')


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def normalize_for_match(text: str) -> str:
    return re.sub(r'\s+', ' ', unicodedata.normalize('NFC', text)).strip()


def preview(text: str, limit: int = 120) -> str:
    flat = re.sub(r'\s+', ' ', text).strip()
    if len(flat) <= limit:
        return flat
    return flat[:limit] + '...'


def has_diacritic(char: str) -> bool:
    return bool(unicodedata.decomposition(char)) or unicodedata.combining(char) > 0


def control_offender(char: str) -> bool:
    if char in CONTROL_ALLOWED:
        return False
    code = ord(char)
    return any(low <= code <= high for low, high in CONTROL_RANGES)


class ConfigError(Exception):
    """Configuration or environment problem: exit code 2."""


@dataclass
class CheckResult:
    name: str
    status: str
    detail: str
    evidence: dict = field(default_factory=dict)

    def as_dict(self) -> dict:
        return {
            'name': self.name,
            'status': self.status,
            'detail': self.detail,
            'evidence': self.evidence,
        }


@dataclass
class Snapshot:
    t_ms: int
    chars: int
    sha256: str
    text: str
    html_sha256: str
    method: str = 'dom'

    def as_dict(self, include_text: bool = False) -> dict:
        row = {
            't_ms': self.t_ms,
            'chars': self.chars,
            'sha256': self.sha256,
            'html_sha256': self.html_sha256,
            'method': self.method,
        }
        if include_text:
            row['text'] = self.text
        return row


@dataclass
class Chunk:
    kind: str
    url: str | None
    t_ms: int
    chars: int
    sha256: str
    text: str

    def as_dict(self, include_text: bool = False) -> dict:
        row = {
            'kind': self.kind,
            'url': self.url,
            't_ms': self.t_ms,
            'chars': self.chars,
            'sha256': self.sha256,
        }
        if include_text:
            row['text'] = self.text
        return row

@dataclass
class Case:
    path: Path
    data: dict

    @property
    def locale(self) -> str:
        return str(self.data.get('locale') or self.data.get('case_id') or '')

    @property
    def expected_document_lang(self) -> str | None:
        value = self.data.get('expected_document_lang')
        return value if isinstance(value, str) and value.strip() else None

    @property
    def target(self) -> dict:
        value = self.data.get('target')
        return value if isinstance(value, dict) else {}

    @property
    def markers(self) -> list[str]:
        """Marker texts only. reported_status is an attestation and is not read."""
        markers = self.data.get('markers')
        if not isinstance(markers, dict):
            return []
        expected = markers.get('expected')
        if not isinstance(expected, list):
            return []
        return [
            str(item['text'])
            for item in expected
            if isinstance(item, dict) and isinstance(item.get('text'), str)
        ]

    @property
    def untranslated_probe(self) -> list[str]:
        probe = self.data.get('untranslated_probe')
        if not isinstance(probe, list):
            return []
        return [str(item) for item in probe if isinstance(item, str) and item]

    @property
    def locale_pin(self) -> dict | None:
        pin = self.target.get('locale_pin')
        return pin if isinstance(pin, dict) and pin else None


def load_case(path: Path) -> Case:
    if not path.is_file():
        raise ConfigError(f'case file not found: {path}')
    try:
        data = json.loads(path.read_text(encoding='utf-8'))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ConfigError(f'case file is not readable JSON: {path}: {error}') from error
    if not isinstance(data, dict):
        raise ConfigError(f'case file must hold a JSON object: {path}')
    case = Case(path=path, data=data)
    problems = case_problems(case)
    if problems:
        raise ConfigError('case file is not usable: ' + '; '.join(problems))
    return case


def case_problems(case: Case) -> list[str]:
    """Schema-level problems. Boundaries only; run inputs are separate."""
    problems: list[str] = []
    if not case.data.get('case_id'):
        problems.append('case_id is missing')
    if not case.data.get('locale'):
        problems.append('locale is missing')
    if case.path.parent.name != 'locale_cases':
        problems.append(f'case file is not in locale_cases/ (found in {case.path.parent.name}/)')
    return problems


def run_inputs_missing(case: Case) -> list[str]:
    """Inputs a real run needs. A null boundary is a missing input, never a pass."""
    missing: list[str] = []
    base_url = case.target.get('base_url')
    if not (isinstance(base_url, str) and base_url.strip()):
        missing.append('target.base_url')
    route = case.target.get('route')
    if not (isinstance(route, str) and route.strip()):
        missing.append('target.route')
    return missing


def resolve_url(case: Case) -> str:
    base = str(case.target.get('base_url')).rstrip('/')
    route = str(case.target.get('route'))
    if not route.startswith('/'):
        route = '/' + route
    return base + route


@dataclass
class EnvReport:
    python_version: str
    selenium_version: str | None
    driver_path: str | None
    browsers_found: list[str]
    problems: list[str]

    @property
    def ok(self) -> bool:
        return not self.problems

    def as_dict(self) -> dict:
        return {
            'python_version': self.python_version,
            'selenium_version': self.selenium_version,
            'driver_path': self.driver_path,
            'browsers_found': self.browsers_found,
            'problems': self.problems,
            'ok': self.ok,
        }

BROWSER_BINARIES = ('chromium', 'chromium-browser', 'chrome', 'google-chrome', 'firefox')
DRIVER_BINARIES = ('chromedriver', 'geckodriver')


def selenium_version() -> str | None:
    try:
        import selenium  # noqa: PLC0415 - lazy: the host has no selenium installed
    except ImportError:
        return None
    return getattr(selenium, '__version__', 'unknown')


def check_environment(driver_path: str | None = None) -> EnvReport:
    """Read-only host probe. Never touches the network or the target."""
    problems: list[str] = []
    version = selenium_version()
    if version is None:
        problems.append('selenium is not importable on this host')

    browsers = [name for name in BROWSER_BINARIES if shutil.which(name)]
    if not browsers:
        problems.append('no browser binary found on PATH')

    resolved_driver = None
    if driver_path:
        candidate = Path(driver_path)
        if candidate.is_file():
            resolved_driver = str(candidate)
        else:
            problems.append(f'--driver-path does not point at a file: {driver_path}')
    elif not [name for name in DRIVER_BINARIES if shutil.which(name)]:
        problems.append(
            'no chromedriver/geckodriver on PATH; Selenium Manager does not resolve a '
            'driver for FreeBSD, so --driver-path is required'
        )

    return EnvReport(
        python_version=sys.version.split()[0],
        selenium_version=version,
        driver_path=resolved_driver,
        browsers_found=browsers,
        problems=problems,
    )


# --------------------------------------------------------------------------
# The nine checks. Pure functions over observed data: no driver, no network.
# A check that cannot be exercised returns SKIP, never PASS.
# --------------------------------------------------------------------------


def check_stream_progressed(snapshots: Sequence[Snapshot]) -> CheckResult:
    evidence = {'samples': len(snapshots)}
    if len(snapshots) < 2:
        return CheckResult(
            'stream_progressed', STATUS_SKIP,
            'fewer than two samples observed, so progress cannot be judged', evidence,
        )
    lengths = [item.chars for item in snapshots]
    evidence.update({
        'first_chars': lengths[0],
        'last_chars': lengths[-1],
        'growth_chars': lengths[-1] - lengths[0],
        'length_series': lengths,
    })
    regressions = [
        index for index in range(1, len(lengths)) if lengths[index] < lengths[index - 1]
    ]
    if regressions:
        return CheckResult(
            'stream_progressed', STATUS_FAIL,
            f'page text shrank at {len(regressions)} sample(s): indices {regressions}',
            evidence,
        )
    if lengths[-1] <= lengths[0]:
        return CheckResult(
            'stream_progressed', STATUS_WARN,
            'no growth observed within the sampling budget; a single-shot render cannot '
            'be distinguished from a stalled stream',
            evidence,
        )
    return CheckResult(
        'stream_progressed', STATUS_PASS,
        f'page text grew by {lengths[-1] - lengths[0]} characters across '
        f'{len(snapshots)} samples',
        evidence,
    )

def check_stream_lossless(
    snapshots: Sequence[Snapshot], chunks: Sequence[Chunk],
) -> CheckResult:
    captured = [item for item in chunks if item.text]
    if captured:
        assembled = ''.join(item.text for item in captured)
        final_text = snapshots[-1].text if snapshots else ''
        left = normalize_for_match(assembled)
        right = normalize_for_match(final_text)
        evidence = {
            'method': 'captured-response-assembly',
            'captured_units': len(captured),
            'assembled_chars': len(assembled),
            'assembled_sha256': sha256_text(assembled),
            'final_text_sha256': sha256_text(final_text),
        }
        if not right:
            return CheckResult(
                'stream_lossless', STATUS_SKIP,
                'response bodies were captured but no rendered text was observed to '
                'compare them with',
                evidence,
            )
        if left == right:
            return CheckResult(
                'stream_lossless', STATUS_PASS,
                f'assembled {len(captured)} captured response unit(s) reproduce the '
                'rendered text exactly',
                evidence,
            )
        if right in left or left in right:
            return CheckResult(
                'stream_lossless', STATUS_PASS,
                'assembled transport text and rendered text agree as one containing the '
                'other (extra transport markup only)',
                evidence,
            )
        offset = next(
            (index for index, pair in enumerate(zip(left, right)) if pair[0] != pair[1]),
            min(len(left), len(right)),
        )
        evidence['first_divergence_offset'] = offset
        evidence['assembled_at_divergence'] = preview(left[offset:offset + 120])
        evidence['rendered_at_divergence'] = preview(right[offset:offset + 120])
        return CheckResult(
            'stream_lossless', STATUS_FAIL,
            f'assembled transport text diverges from the rendered text at offset {offset}',
            evidence,
        )

    texts = [item.text for item in snapshots if item.text]
    if not texts:
        return CheckResult(
            'stream_lossless', STATUS_SKIP,
            'no response bodies and no snapshot text were observed, so assembly cannot '
            'be judged',
            {'method': None, 'captured_units': 0},
        )
    final_text = texts[-1]
    evidence = {
        'method': 'dom-prefix',
        'captured_units': 0,
        'samples_with_text': len(texts),
        'final_text_sha256': sha256_text(final_text),
        'final_text_chars': len(final_text),
    }
    normalized_final = normalize_for_match(final_text)
    for position, text in enumerate(texts[:-1]):
        normalized = normalize_for_match(text)
        if not normalized_final.startswith(normalized):
            return CheckResult(
                'stream_lossless', STATUS_FAIL,
                f'sample {position} is not a prefix of the final rendered text, so content '
                'was dropped or rewritten between samples',
                evidence,
            )
    return CheckResult(
        'stream_lossless', STATUS_PASS,
        f'every one of {len(texts) - 1} earlier sample(s) is a prefix of the final '
        'rendered text',
        evidence,
    )

def check_no_replacement_char(text: str) -> CheckResult:
    evidence = {'text_chars': len(text), 'text_sha256': sha256_text(text)}
    if not text:
        return CheckResult(
            'no_replacement_char', STATUS_SKIP,
            'no rendered text was observed to scan', evidence,
        )
    count = text.count(REPLACEMENT_CHAR)
    evidence['replacement_chars'] = count
    if count:
        offset = text.index(REPLACEMENT_CHAR)
        evidence['first_offset'] = offset
        evidence['first_context'] = preview(text[max(0, offset - 60):offset + 60])
        return CheckResult(
            'no_replacement_char', STATUS_FAIL,
            f'{count} U+FFFD replacement character(s) in the rendered text',
            evidence,
        )
    return CheckResult(
        'no_replacement_char', STATUS_PASS,
        f'no U+FFFD in {len(text)} characters of rendered text', evidence,
    )


def check_no_mojibake(text: str) -> CheckResult:
    evidence = {'text_chars': len(text), 'sequences_checked': len(MOJIBAKE_SEQUENCES)}
    if not text:
        return CheckResult(
            'no_mojibake', STATUS_SKIP,
            'no rendered text was observed to scan', evidence,
        )
    hits: list[dict] = []
    for sequence in MOJIBAKE_SEQUENCES:
        start = text.find(sequence)
        if start < 0:
            continue
        hits.append({
            'sequence': sequence,
            'codepoints': [f'U+{ord(char):04X}' for char in sequence],
            'offset': start,
            'context': preview(text[max(0, start - 40):start + 40]),
        })
    evidence['hits'] = hits[:10]
    evidence['hit_count'] = len(hits)
    if hits:
        return CheckResult(
            'no_mojibake', STATUS_FAIL,
            f'{len(hits)} double-encoded sequence(s) found, first at offset '
            f'{hits[0]["offset"]}',
            evidence,
        )
    return CheckResult(
        'no_mojibake', STATUS_PASS,
        f'none of {len(MOJIBAKE_SEQUENCES)} double-encoding sequences found in '
        f'{len(text)} characters',
        evidence,
    )


def check_no_control_chars(text: str) -> CheckResult:
    evidence = {'text_chars': len(text)}
    if not text:
        return CheckResult(
            'no_control_chars', STATUS_SKIP,
            'no rendered text was observed to scan', evidence,
        )
    offenders = [
        {'offset': index, 'codepoint': f'U+{ord(char):04X}'}
        for index, char in enumerate(text)
        if control_offender(char)
    ]
    evidence['offender_count'] = len(offenders)
    evidence['offenders'] = offenders[:10]
    if offenders:
        return CheckResult(
            'no_control_chars', STATUS_FAIL,
            f'{len(offenders)} control character(s) other than tab/newline/carriage '
            f'return, first at offset {offenders[0]["offset"]}',
            evidence,
        )
    return CheckResult(
        'no_control_chars', STATUS_PASS,
        f'no disallowed control characters in {len(text)} characters of rendered text',
        evidence,
    )

def check_localized_markers_present(text: str, markers: Sequence[str]) -> CheckResult:
    evidence: dict = {'markers_supplied': len(markers)}
    if not markers:
        return CheckResult(
            'localized_markers_present', STATUS_SKIP,
            'the case file supplies no markers, so localization presence cannot be judged',
            evidence,
        )
    if not text:
        return CheckResult(
            'localized_markers_present', STATUS_SKIP,
            'no rendered text was observed to search for the supplied markers', evidence,
        )
    haystack = normalize_for_match(text)
    found = []
    missing = []
    for marker in markers:
        entry = {'text': marker, 'found': normalize_for_match(marker) in haystack}
        (found if entry['found'] else missing).append(entry)
    evidence['found'] = found
    evidence['missing'] = missing
    evidence['note'] = (
        'markers come from the case file; reported_status in that file is an operator '
        'attestation and is not consumed here'
    )
    if missing:
        return CheckResult(
            'localized_markers_present', STATUS_FAIL,
            f'{len(missing)} of {len(markers)} supplied marker(s) absent from the '
            f'rendered text: {[entry["text"] for entry in missing]}',
            evidence,
        )
    return CheckResult(
        'localized_markers_present', STATUS_PASS,
        f'all {len(markers)} supplied marker(s) present in the rendered text', evidence,
    )


def check_no_untranslated_fallback(
    text: str, probe: Sequence[str],
) -> CheckResult:
    evidence: dict = {'probe_supplied': len(probe)}
    if not probe:
        return CheckResult(
            'no_untranslated_fallback', STATUS_SKIP,
            'the case file supplies no untranslated_probe entries; an absent probe is not '
            'evidence of absence, so no fallback claim is made',
            evidence,
        )
    if not text:
        return CheckResult(
            'no_untranslated_fallback', STATUS_SKIP,
            'no rendered text was observed to compare with the supplied probe', evidence,
        )
    haystack = normalize_for_match(text)
    present = []
    for entry in probe:
        if normalize_for_match(entry) in haystack:
            present.append(entry)
    evidence['probe_present'] = present
    evidence['probe_absent'] = [entry for entry in probe if entry not in present]
    if present:
        return CheckResult(
            'no_untranslated_fallback', STATUS_FAIL,
            f'{len(present)} English probe string(s) rendered where localized text was '
            f'expected: {present}',
            evidence,
        )
    return CheckResult(
        'no_untranslated_fallback', STATUS_PASS,
        f'none of {len(probe)} English probe string(s) rendered', evidence,
    )


def check_document_lang(observed: str | None, expected: str | None) -> CheckResult:
    evidence = {'observed': observed, 'expected': expected}
    if not expected:
        return CheckResult(
            'document_lang', STATUS_SKIP,
            'the case file supplies no expected_document_lang, so nothing is compared',
            evidence,
        )
    if not observed:
        return CheckResult(
            'document_lang', STATUS_FAIL,
            f'document.documentElement.lang is absent while {expected} is expected',
            evidence,
        )
    normalize = lambda value: value.strip().lower().replace('_', '-')
    if normalize(observed) == normalize(expected):
        return CheckResult(
            'document_lang', STATUS_PASS,
            f'document.documentElement.lang is {observed}', evidence,
        )
    return CheckResult(
        'document_lang', STATUS_FAIL,
        f'document.documentElement.lang is {observed}, expected {expected}', evidence,
    )

def check_diacritics_roundtrip(
    text: str, markers: Sequence[str], charset: str | None,
) -> CheckResult:
    evidence: dict = {'text_chars': len(text), 'charset': charset}
    if not text:
        return CheckResult(
            'diacritics_roundtrip', STATUS_SKIP,
            'no rendered text was observed to round trip', evidence,
        )
    non_ascii = [char for char in text if ord(char) > 0x7F]
    observed_diacritics = sorted({char for char in non_ascii if has_diacritic(char)})
    expected_diacritics = sorted({char for char in ''.join(markers) if has_diacritic(char)})
    evidence['non_ascii_chars'] = len(non_ascii)
    evidence['observed_diacritics'] = [f'U+{ord(c):04X}' for c in observed_diacritics]
    evidence['expected_diacritics'] = [f'U+{ord(c):04X}' for c in expected_diacritics]
    evidence['markers_supplied'] = len(markers)

    problems: list[str] = []
    try:
        roundtrip = text.encode('utf-8').decode('utf-8')
    except UnicodeError as error:
        roundtrip = None
        problems.append(f'utf-8 round trip raised: {error}')
    if roundtrip is not None and roundtrip != text:
        problems.append('utf-8 round trip is not byte-identical')
    evidence['roundtrip_ok'] = roundtrip == text
    if charset and charset.strip().lower().replace('-', '') != 'utf8':
        problems.append(f'document.characterSet is {charset}, not utf-8')

    if problems:
        return CheckResult(
            'diacritics_roundtrip', STATUS_FAIL, '; '.join(problems), evidence,
        )
    absent = [char for char in expected_diacritics if char not in observed_diacritics]
    if absent:
        return CheckResult(
            'diacritics_roundtrip', STATUS_WARN,
            f'{len(absent)} diacritic(s) supplied by the case markers are absent from the '
            f'rendered text: {[f"U+{ord(c):04X}" for c in absent]}',
            evidence,
        )
    if not observed_diacritics:
        return CheckResult(
            'diacritics_roundtrip', STATUS_WARN,
            'no diacritics were observed anywhere in the rendered text, so a round trip '
            'was not actually exercised',
            evidence,
        )
    return CheckResult(
        'diacritics_roundtrip', STATUS_PASS,
        f'utf-8 round trip intact and {len(observed_diacritics)} diacritic(s) survive '
        f'encoding (charset {charset})',
        evidence,
    )


CHECK_FUNCTIONS = {
    'stream_progressed': lambda context: check_stream_progressed(context.snapshots),
    'stream_lossless': lambda context: check_stream_lossless(
        context.snapshots, context.chunks),
    'no_replacement_char': lambda context: check_no_replacement_char(context.text),
    'no_mojibake': lambda context: check_no_mojibake(context.text),
    'no_control_chars': lambda context: check_no_control_chars(context.text),
    'localized_markers_present': lambda context: check_localized_markers_present(
        context.text, context.markers),
    'no_untranslated_fallback': lambda context: check_no_untranslated_fallback(
        context.text, context.probe),
    'document_lang': lambda context: check_document_lang(
        context.observed_lang, context.expected_lang),
    'diacritics_roundtrip': lambda context: check_diacritics_roundtrip(
        context.text, context.markers, context.charset),
}


@dataclass
class Observation:
    snapshots: list[Snapshot] = field(default_factory=list)
    chunks: list[Chunk] = field(default_factory=list)
    text: str = ''
    page_source: str = ''
    observed_lang: str | None = None
    charset: str | None = None
    markers: list[str] = field(default_factory=list)
    probe: list[str] = field(default_factory=list)
    expected_lang: str | None = None
    screenshot: bytes | None = None
    notes: list[str] = field(default_factory=list)


def run_checks(observation: Observation) -> list[CheckResult]:
    """Every check runs, in the documented order. A crash is ERROR, never PASS."""
    results: list[CheckResult] = []
    for name in CHECK_NAMES:
        try:
            results.append(CHECK_FUNCTIONS[name](observation))
        except Exception as error:  # noqa: BLE001 - a check must never abort the run
            results.append(CheckResult(
                name, STATUS_ERROR, f'{type(error).__name__}: {error}', {},
            ))
    return results

def resolve_browser_choice(driver_path: str | None) -> str:
    if driver_path:
        name = Path(driver_path).name.lower()
        if name.startswith('gecko'):
            return 'firefox'
        if name.startswith('chrome'):
            return 'chrome'
    if shutil.which('chromedriver'):
        return 'chrome'
    if shutil.which('geckodriver'):
        return 'firefox'
    return 'chrome'


def build_driver(headless: bool, driver_path: str | None):
    """Only function that needs selenium. Imported lazily; failure is a config error."""
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options as ChromeOptions
        from selenium.webdriver.chrome.service import Service as ChromeService
        from selenium.webdriver.firefox.options import Options as FirefoxOptions
        from selenium.webdriver.firefox.service import Service as FirefoxService
    except ImportError as error:
        raise ConfigError(f'selenium is not importable on this host: {error}') from error

    choice = resolve_browser_choice(driver_path)
    try:
        if choice == 'firefox':
            options = FirefoxOptions()
            if headless:
                options.add_argument('-headless')
            service = (
                FirefoxService(executable_path=driver_path) if driver_path
                else FirefoxService()
            )
            return webdriver.Firefox(options=options, service=service)
        options = ChromeOptions()
        if headless:
            options.add_argument('--headless=new')
        options.add_argument('--window-size=1600,1000')
        service = (
            ChromeService(executable_path=driver_path) if driver_path else ChromeService()
        )
        return webdriver.Chrome(options=options, service=service)
    except Exception as error:  # noqa: BLE001 - driver startup is environment dependent
        raise ConfigError(f'{choice} driver could not start: {type(error).__name__}: '
                          f'{error}') from error


def install_stream_hook(driver) -> int:
    """Instrument fetch/XHR so transport units can be compared with the render."""
    try:
        installed = driver.execute_script(STREAM_HOOK_JS)
    except Exception as error:  # noqa: BLE001
        raise ConfigError(f'the stream hook could not be installed: {error}') from error
    return int(installed or 0)


def sample_until_stable(
    driver,
    timeout_s: float = SNAPSHOT_TIMEOUT_S,
    interval_s: float = SNAPSHOT_INTERVAL_S,
    stable_samples: int = SNAPSHOT_STABLE_SAMPLES,
) -> list[Snapshot]:
    snapshots: list[Snapshot] = []
    previous_html: str | None = None
    stable = 0
    start = time.monotonic()
    while True:
        state = driver.execute_script(SNAPSHOT_JS)
        if not isinstance(state, dict):
            break
        text = state.get('text') or ''
        html = state.get('html') or ''
        snapshots.append(Snapshot(
            t_ms=int(state.get('t_ms') or 0),
            chars=len(text),
            sha256=sha256_text(text),
            text=text,
            html_sha256=sha256_text(html),
        ))
        if previous_html is not None and snapshots[-1].html_sha256 == previous_html:
            stable += 1
        else:
            stable = 0
        previous_html = snapshots[-1].html_sha256
        if stable >= stable_samples:
            break
        if time.monotonic() - start >= timeout_s:
            break
        time.sleep(interval_s)
    return snapshots


def collect_chunks(driver) -> list[Chunk]:
    try:
        raw = driver.execute_script('return window.__locale_stream__ || [];')
    except Exception:  # noqa: BLE001 - the hook may be gone after a navigation
        return []
    chunks: list[Chunk] = []
    for item in raw or []:
        if not isinstance(item, dict):
            continue
        text = item.get('text') or ''
        chunks.append(Chunk(
            kind=str(item.get('kind') or 'unknown'),
            url=item.get('url'),
            t_ms=int(item.get('t_ms') or 0),
            chars=len(text),
            sha256=sha256_text(text),
            text=text,
        ))
    return chunks

def observe_page(driver, case: Case) -> Observation:
    """Load the target, capture the transport stream, then sample until stable."""
    url = resolve_url(case)
    notes: list[str] = []
    driver.set_page_load_timeout(PAGE_LOAD_TIMEOUT_S)
    driver.get(url)
    try:
        install_stream_hook(driver)
    except ConfigError as error:
        notes.append(str(error))
    # Second navigation so the installed hooks see this page's own requests.
    driver.get(url)
    snapshots = sample_until_stable(driver)
    chunks = collect_chunks(driver)
    if not chunks:
        notes.append(
            'no fetch/XHR response bodies were captured for this route; stream_lossless '
            'falls back to the DOM-prefix method'
        )
    state = driver.execute_script(PAGE_STATE_JS)
    state = state if isinstance(state, dict) else {}
    text = state.get('text') or (snapshots[-1].text if snapshots else '')
    return Observation(
        snapshots=snapshots,
        chunks=chunks,
        text=text,
        page_source=driver.page_source or '',
        observed_lang=state.get('lang'),
        charset=state.get('charset'),
        markers=case.markers,
        probe=case.untranslated_probe,
        expected_lang=case.expected_document_lang,
        notes=notes,
    )


def count_statuses(results: Sequence[CheckResult]) -> dict:
    counts = {status: 0 for status in (STATUS_PASS, STATUS_FAIL, STATUS_WARN,
                                       STATUS_SKIP, STATUS_ERROR)}
    for result in results:
        counts[result.status] = counts.get(result.status, 0) + 1
    return counts


def overall_status(results: Sequence[CheckResult]) -> str:
    statuses = [result.status for result in results]
    if STATUS_ERROR in statuses:
        return 'ERROR'
    if STATUS_FAIL in statuses:
        return 'FAIL'
    if STATUS_PASS not in statuses:
        return 'NO-RESULT'
    return 'PASS'


def exit_code_for(overall: str) -> int:
    if overall == 'PASS':
        return EXIT_PASS
    if overall == 'NO-RESULT':
        return EXIT_CONFIG
    return EXIT_FAIL


def overall_note(overall: str, counts: dict) -> str:
    if overall == 'PASS':
        return (f'{counts[STATUS_PASS]} check(s) passed; '
                f'{counts[STATUS_WARN]} warning(s), {counts[STATUS_SKIP]} check(s) not '
                f'exercised (SKIP is not evidence of a pass)')
    if overall == 'NO-RESULT':
        return ('no check reached PASS, so nothing was verified; a skipped check is never '
                'a pass')
    if overall == 'ERROR':
        return f'{counts[STATUS_ERROR]} check(s) raised; the run is not a pass'
    return f'{counts[STATUS_FAIL]} check(s) failed'


def build_result(
    case: Case,
    results: Sequence[CheckResult],
    observation: Observation,
    env: EnvReport,
    started: dt.datetime,
    finished: dt.datetime,
    written: Sequence[str],
) -> dict:
    counts = count_statuses(results)
    overall = overall_status(results)
    return {
        'tool': {'name': HARNESS_NAME, 'version': HARNESS_VERSION},
        'result': overall,
        'result_note': overall_note(overall, counts),
        'exit_code': exit_code_for(overall),
        'locale': case.locale,
        'case': {
            'path': str(case.path),
            'case_id': case.data.get('case_id'),
            'schema_status': case.data.get('schema_status'),
        },
        'run': {
            'started_utc': iso(started),
            'finished_utc': iso(finished),
            'duration_seconds': round((finished - started).total_seconds(), 3),
        },
        'environment': env.as_dict(),
        'target': {
            'device_class': case.target.get('device_class'),
            'address': case.target.get('address'),
            'build': case.target.get('build'),
            'base_url': case.target.get('base_url'),
            'route': case.target.get('route'),
            'locale_pinning_method': case.locale_pin,
        },
        'checks': [result.as_dict() for result in results],
        'checks_summary': counts,
        'locale_pinning_method': case.locale_pin,
        'locale_pin_note': (
            'the pin comes from the case file; this harness never invents one. Null means '
            'the run recorded no pinning method.'
        ),
        'device_state': {
            'pre_change_locale_state': None,
            'post_change_locale_state': None,
            'note': (
                'this harness reads no OPNsense configuration and performs no teardown; a '
                'firewall locale change is infrastructure state and must be captured '
                'separately'
            ),
        },
        'stream': {
            'snapshots': [item.as_dict() for item in observation.snapshots],
            'captured_units': [item.as_dict() for item in observation.chunks],
        },
        'notes': list(observation.notes),
        'artifacts_written': list(written),
    }

def escape_html(value: Any) -> str:
    text = '' if value is None else str(value)
    for character, entity in (('&', '&amp;'), ('<', '&lt;'), ('>', '&gt;'),
                              ('"', '&quot;'), ("'", '&#39;')):
        text = text.replace(character, entity)
    return text


def render_markdown(result: dict) -> str:
    lines = [
        f'# Locale text-stream verification - `{result["locale"]}`',
        '',
        f'- Tool: `{result["tool"]["name"]}` {result["tool"]["version"]}',
        f'- Result: **{result["result"]}** ({result["result_note"]})',
        f'- Exit code: {result["exit_code"]}',
        f'- Started (UTC): {result["run"]["started_utc"]}',
        f'- Duration: {result["run"]["duration_seconds"]}s',
        f'- Target base URL: `{result["target"]["base_url"]}`',
        f'- Target route: `{result["target"]["route"]}`',
        f'- Locale pinning method: `{result["target"]["locale_pinning_method"]}`',
        '',
        '## Checks',
        '',
        '| Check | Status | Detail |',
        '| --- | --- | --- |',
    ]
    for check in result['checks']:
        detail = check['detail'].replace('|', '\\|')
        lines.append(f'| `{check["name"]}` | {check["status"]} | {detail} |')
    lines += [
        '',
        '## Summary',
        '',
    ]
    for status, count in result['checks_summary'].items():
        lines.append(f'- {status}: {count}')
    lines += [
        '',
        'SKIP means the check was not exercised. It is never a pass. This file is the',
        'harness\'s own output; see `verification/locales/out/README.md` for how it may be',
        'used.',
    ]
    if result['notes']:
        lines += ['', '## Notes', '']
        lines += [f'- {note}' for note in result['notes']]
    return '\n'.join(lines) + '\n'


def render_html(result: dict) -> str:
    rows = '\n'.join(
        '<tr><td><code>{}</code></td><td class="{}">{}</td><td>{}</td></tr>'.format(
            escape_html(check['name']), escape_html(check['status'].lower()),
            escape_html(check['status']), escape_html(check['detail']),
        )
        for check in result['checks']
    )
    details = '\n'.join(
        '<details><summary><code>{}</code> evidence</summary><pre>{}</pre></details>'.format(
            escape_html(check['name']),
            escape_html(json.dumps(check['evidence'], indent=2, sort_keys=True)),
        )
        for check in result['checks']
    )
    summary = '\n'.join(
        f'<li>{escape_html(status)}: {escape_html(count)}</li>'
        for status, count in result['checks_summary'].items()
    )
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Locale text-stream verification - {escape_html(result['locale'])}</title>
<style>
body {{ font-family: system-ui, sans-serif; margin: 2rem; }}
table {{ border-collapse: collapse; }}
td, th {{ border: 1px solid #999; padding: 0.35rem 0.6rem; text-align: left; }}
.pass {{ color: #076b07; font-weight: bold; }}
.fail, .error {{ color: #a30000; font-weight: bold; }}
.warn {{ color: #8a5a00; font-weight: bold; }}
.skip {{ color: #444; font-weight: bold; }}
pre {{ background: #f4f4f4; padding: 0.6rem; overflow-x: auto; }}
</style>
</head>
<body>
<h1>Locale text-stream verification - <code>{escape_html(result['locale'])}</code></h1>
<p>Tool <code>{escape_html(result['tool']['name'])}</code>
{escape_html(result['tool']['version'])}.
Result <strong>{escape_html(result['result'])}</strong> -
{escape_html(result['result_note'])}. Exit code {escape_html(result['exit_code'])}.
Started {escape_html(result['run']['started_utc'])}
(UTC), duration {escape_html(result['run']['duration_seconds'])}s.</p>
<p>Target base URL <code>{escape_html(result['target']['base_url'])}</code>,
route <code>{escape_html(result['target']['route'])}</code>, locale pinning method
<code>{escape_html(result['target']['locale_pinning_method'])}</code>.</p>
<h2>Checks</h2>
<table>
<tr><th>Check</th><th>Status</th><th>Detail</th></tr>
{rows}
</table>
<h2>Summary</h2>
<ul>
{summary}
</ul>
<p>SKIP means the check was not exercised. It is never a pass.</p>
<h2>Evidence</h2>
{details}
</body>
</html>
"""

def planned_artifacts(
    locale: str, write_markdown: bool, save_page_source: bool, has_screenshot: bool,
    with_log: bool,
) -> list[str]:
    names = [f'result-{locale}.json', f'report-{locale}.html', f'stream-{locale}.jsonl']
    if write_markdown:
        names.append(f'report-{locale}.md')
    if save_page_source:
        names.append(f'page-{locale}.html')
    if has_screenshot:
        names.append(f'final-{locale}.png')
    if with_log:
        names.append(f'run-{locale}.log')
    return names


def write_outputs(
    out_dir: Path,
    result: dict,
    observation: Observation,
    write_markdown: bool,
    save_page_source: bool,
) -> list[str]:
    """Write the tool's own output. Nothing here transcribes a human summary."""
    out_dir.mkdir(parents=True, exist_ok=True)
    locale = result['locale']
    # Created here, appended to by RunLog: the declared artifact list must equal the
    # files that actually exist.
    (out_dir / f'run-{locale}.log').touch(exist_ok=True)
    names = planned_artifacts(
        locale, write_markdown, save_page_source,
        observation.screenshot is not None, True,
    )
    result['artifacts_written'] = names

    (out_dir / f'result-{locale}.json').write_text(
        json.dumps(result, indent=2, sort_keys=True) + '\n', encoding='utf-8',
    )
    (out_dir / f'report-{locale}.html').write_text(render_html(result), encoding='utf-8')
    if write_markdown:
        (out_dir / f'report-{locale}.md').write_text(
            render_markdown(result), encoding='utf-8',
        )
    rows = [{'record': 'snapshot', **item.as_dict()} for item in observation.snapshots]
    rows += [{'record': 'captured_unit', **item.as_dict()} for item in observation.chunks]
    (out_dir / f'stream-{locale}.jsonl').write_text(
        ''.join(json.dumps(row, sort_keys=True) + '\n' for row in rows), encoding='utf-8',
    )
    if save_page_source:
        (out_dir / f'page-{locale}.html').write_text(
            observation.page_source, encoding='utf-8',
        )
    if observation.screenshot:
        (out_dir / f'final-{locale}.png').write_bytes(observation.screenshot)
    return names


class RunLog:
    """The run's own log. Appended to out/<locale>/run-<locale>.log."""

    def __init__(self, path: Path | None = None) -> None:
        self.path = path

    def line(self, message: str) -> None:
        print(message)
        if self.path is not None:
            with self.path.open('a', encoding='utf-8') as handle:
                handle.write(message + '\n')


def plan_lines(case: Case) -> list[str]:
    """What a run would exercise, and what it would have to skip, and why."""
    missing = run_inputs_missing(case)
    url = resolve_url(case) if not missing else f'<incomplete target: {missing}>'
    lines = [
        f'case file: {case.path}',
        f'locale: {case.locale}',
        f'url: {url}',
        f'markers supplied: {len(case.markers)}',
        f'untranslated_probe entries: {len(case.untranslated_probe)}',
        f'expected_document_lang: {case.expected_document_lang}',
        f'locale pin: {case.locale_pin}',
        'check plan:',
    ]
    for name in CHECK_NAMES:
        if name == 'no_untranslated_fallback' and not case.untranslated_probe:
            lines.append(f'  {name}: SKIP (no untranslated_probe supplied)')
        elif name == 'localized_markers_present' and not case.markers:
            lines.append(f'  {name}: SKIP (no markers supplied)')
        elif name == 'document_lang' and not case.expected_document_lang:
            lines.append(f'  {name}: SKIP (no expected_document_lang supplied)')
        else:
            lines.append(f'  {name}: would run (browser required)')
    lines.append('dry run writes nothing and touches no target')
    return lines


def run_dry(case: Case, env: EnvReport, log: RunLog) -> int:
    blocked = False
    for line in plan_lines(case):
        log.line(line)
    if not env.ok:
        blocked = True
        for problem in env.problems:
            log.line(f'ENVIRONMENT: {problem}')
    for name in run_inputs_missing(case):
        blocked = True
        log.line(
            f'MISSING INPUT: {name} is null in the case file; a null boundary cannot '
            'drive a run and is never a pass'
        )
    if blocked:
        log.line('DRY-RUN=BLOCKED (configuration or environment)')
        return EXIT_CONFIG
    log.line('ENVIRONMENT=OK')
    log.line('DRY-RUN=OK (plan only)')
    return EXIT_PASS

def run_once(case: Case, env: EnvReport, args: argparse.Namespace) -> int:
    """A real run. Refuses to start when the target, the environment or the
    artifact directory is missing, and writes nothing until a result exists."""
    if not env.ok:
        for problem in env.problems:
            print(f'ENVIRONMENT: {problem}', file=sys.stderr)
        return EXIT_CONFIG
    missing = run_inputs_missing(case)
    if missing:
        for name in missing:
            print(
                f'MISSING INPUT: {name} is null in the case file; a null boundary cannot '
                'drive a run',
                file=sys.stderr,
            )
        return EXIT_CONFIG
    if not args.out_dir:
        print(
            'ERROR: --out-dir is required for a run: a result must be written somewhere',
            file=sys.stderr,
        )
        return EXIT_CONFIG

    out_dir = args.out_dir
    started = utc_now()
    log = RunLog(out_dir / f'run-{case.locale}.log')
    log.line(
        f'{HARNESS_NAME} {HARNESS_VERSION} run: locale={case.locale} '
        f'url={resolve_url(case)}'
    )
    driver = None
    try:
        driver = build_driver(args.headless, env.driver_path)
        observation = observe_page(driver, case)
        try:
            observation.screenshot = driver.get_screenshot_as_png()
        except Exception as error:  # noqa: BLE001 - a missing screenshot is not a failure
            observation.notes.append(f'screenshot could not be captured: {error}')
        results = run_checks(observation)
    except ConfigError as error:
        log.line(f'ERROR: {error}')
        log.line('RESULT=ERROR')
        return EXIT_CONFIG
    finally:
        if driver is not None:
            try:
                driver.quit()
            except Exception:  # noqa: BLE001 - teardown must not mask the result
                pass

    finished = utc_now()
    result = build_result(case, results, observation, env, started, finished, [])
    for check in result['checks']:
        log.line(f'{check["status"]}: {check["name"]} - {check["detail"]}')
    log.line(f'RESULT={result["result"]} ({result["result_note"]})')
    written = write_outputs(
        out_dir, result, observation, args.write_markdown, args.save_page_source,
    )
    log.line(f'artifacts: {", ".join(written)}')
    log.line(f'EXIT={result["exit_code"]}')
    return int(result['exit_code'])


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog=HARNESS_NAME,
        description='Locale text-stream verification (see verification/locales/README.md).',
    )
    parser.add_argument(
        '--case', type=Path, help='case file, e.g. locale_cases/it_IT.json',
    )
    parser.add_argument(
        '--check-env', action='store_true',
        help='probe the host only: no target, no network, no artifacts',
    )
    parser.add_argument(
        '--dry-run', action='store_true',
        help='validate the case and print the plan; writes nothing, touches nothing',
    )
    parser.add_argument(
        '--headless', action='store_true', help='run the browser headless',
    )
    parser.add_argument(
        '--out-dir', type=Path,
        help='artifact directory, e.g. out/it_IT (required for a run)',
    )
    parser.add_argument(
        '--write-markdown', action='store_true',
        help='also write report-<locale>.md',
    )
    parser.add_argument(
        '--save-page-source', action='store_true',
        help='also write page-<locale>.html',
    )
    parser.add_argument(
        '--driver-path', help='path to chromedriver or geckodriver',
    )
    parser.add_argument(
        '--version', action='version', version=f'%(prog)s {HARNESS_VERSION}',
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        env = check_environment(args.driver_path)
    except Exception as error:  # noqa: BLE001 - a failed probe is an environment error
        print(
            f'ERROR: environment probe failed: {type(error).__name__}: {error}',
            file=sys.stderr,
        )
        return EXIT_CONFIG

    if args.check_env:
        payload: dict = {
            'tool': {'name': HARNESS_NAME, 'version': HARNESS_VERSION},
            'environment': env.as_dict(),
        }
        if args.case:
            try:
                case = load_case(args.case)
            except ConfigError as error:
                payload['case_error'] = str(error)
            else:
                payload['case'] = {
                    'path': str(case.path),
                    'case_id': case.data.get('case_id'),
                    'locale': case.locale,
                    'expected_document_lang': case.expected_document_lang,
                    'markers_supplied': len(case.markers),
                    'untranslated_probe_entries': len(case.untranslated_probe),
                }
                payload['run_inputs_missing'] = run_inputs_missing(case)
                payload['locale_pinning_method'] = case.locale_pin
        print(json.dumps(payload, indent=2, sort_keys=True))
        if not env.ok or payload.get('case_error'):
            return EXIT_CONFIG
        return EXIT_PASS

    if not args.case:
        print(
            'ERROR: --case is required for every operation other than --check-env',
            file=sys.stderr,
        )
        return EXIT_CONFIG
    try:
        case = load_case(args.case)
    except ConfigError as error:
        print(f'ERROR: {error}', file=sys.stderr)
        return EXIT_CONFIG

    if args.dry_run:
        return run_dry(case, env, RunLog())
    return run_once(case, env, args)


if __name__ == '__main__':
    sys.exit(main())

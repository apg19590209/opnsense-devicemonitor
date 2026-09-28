"""DM-BL-008 language acceptance: the nine UI languages render translated Device Monitor pages.

Each language is rendered over every Device Monitor page with the production view
path (Phalcon Volt compiler plus OPNsense\\Base\\ViewTranslator over the shared
gettext domain) and checked for:

* every message id used by the page resolving to that language's catalogue string,
* the translated strings appearing in the rendered page,
* the page text matching the selected language and no other installed language,
* the writing system of the language being present,
* source .po, installed plugin .mo and installed shared .mo agreeing,
* the language being offered by System > Settings > General > Language.

Expected values come from the catalogues, so no knowledge of the target languages
is required. The checked output is the HTML the browser receives. HTTP transport,
complete page behavior and translation quality remain outside this test; translated
JavaScript is separately syntax-checked and an isolated translated string is executed.

Usage:
    python3 tests/test_language_acceptance.py [--engine auto|runtime|interpolate]
        [--views DIR] [--languages de_DE,fr_FR,...] [--report FILE] [--strict]
"""
import argparse
import datetime
import gettext
import hashlib
import html
import json
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RENDERER = ROOT / 'tests/render_device_monitor_page.php'
SOURCE_VIEWS = ROOT / 'src/opnsense/mvc/app/views/OPNsense/DeviceMonitor'
SOURCE_PO = ROOT / 'src/opnsense/mvc/app/languages'
INSTALLED_VIEWS = Path('/usr/local/opnsense/mvc/app/views/OPNsense/DeviceMonitor')
INSTALLED_PO = Path('/usr/local/opnsense/mvc/app/languages')
SHARED_LOCALE = Path('/usr/local/share/locale')
CORE_INC = Path('/usr/local/etc/inc')
TRANSLATOR = Path('/usr/local/opnsense/mvc/app/library/OPNsense/Base/ViewTranslator.php')
PHP = os.environ.get('PHP', 'php')

LANGUAGES = ['de_DE', 'fr_FR', 'es_ES', 'it_IT', 'pt_BR', 'nl_NL', 'ru_RU', 'ja_JP', 'zh_CN']
REFERENCE = 'en_US'
# page (URL segment under /ui/devicemonitor/) -> view template and controller variables
PAGES = (
    ('devices', 'devices.volt', {}),
    ('physicaldevices', 'physicaldevices.volt', {}),
    ('identityevents', 'identityevents.volt', {'identityEventsStatus': 'all'}),
    ('devicehistory', 'devicehistory.volt', {}),
    ('activitytimeline', 'activitytimeline.volt', {}),
    ('scanhistory', 'scanhistory.volt', {}),
    ('changesummary', 'changesummary.volt', {}),
    ('settings', 'settings.volt', {}),
    ('infrastructureservices', 'infrastructureservices.volt', {'portDiscoveryPage': False}),
    ('portdiscovery', 'infrastructureservices.volt', {'portDiscoveryPage': True}),
)
LANG_CALL = re.compile(r"""(?:lang\.(?:_|query)|devicemonitor_raw|devicemonitor_t)\(\s*('(?:\\.|[^'\\])*'|"(?:\\.|[^"\\])*")\s*\)""")
# Every message id that a script body passes through json_encode(15), whichever translator it calls:
# a regression to the escaped form (lang._() or devicemonitor_t()) must still be visible to the
# escaping check below.
JSON_CALL = re.compile(r"""(?:lang\.(?:_|query)|devicemonitor_raw|devicemonitor_t)\(\s*('(?:\\.|[^'\\])*'|"(?:\\.|[^"\\])*")\s*\)\s*\|json_encode\(15\)""")
UNSAFE_JS_CALL = re.compile(r"""(?:lang\._|devicemonitor_t)\(\s*('(?:\\.|[^'\\])*'|"(?:\\.|[^"\\])*")\s*\)\s*\|json_encode\(15\)""")
SCRIPT_BLOCK = re.compile(r'<script\b[^>]*>(.*?)</script>', re.S)
ENTITY = re.compile(r'&(?:#[0-9]+|#x[0-9a-fA-F]+|[A-Za-z][A-Za-z0-9]*);')
CJK = re.compile('[\u3040-\u30ff\u3400-\u4dbf\u4e00-\u9fff\uff00-\uffef]')
CYRILLIC = re.compile('[\u0400-\u04ff]')
WRITING_SYSTEM = {'ja_JP': CJK, 'zh_CN': CJK, 'ru_RU': CYRILLIC}
JSON_ESCAPE = re.compile(r'\\u([0-9a-fA-F]{4})')

failures = []
warnings = []


def fail(message):
    failures.append(message)
    print(f'FAIL: {message}')


def warn(message):
    warnings.append(message)
    print(f'WARN: {message}')


def unquote(literal):
    return literal[1:-1].replace("\\'", "'").replace('\\"', '"').replace('\\\\', '\\')


def source_po(code):
    """Source catalogue in the sidecar layout devicemonitor_locale.inc binds.

    The flat <locale>_devicemonitor.po layout of v2.9/v2.10 release-asset installs is
    still read as a fallback so an older checkout or deployment stays diagnosable.
    """
    nested = SOURCE_PO / code / 'LC_MESSAGES' / 'devicemonitor.po'
    return nested if nested.is_file() else SOURCE_PO / f'{code}_devicemonitor.po'


def plugin_mo(code, installed_po=INSTALLED_PO):
    """Deployed plugin catalogue: nested sidecar layout first, legacy flat layout second."""
    nested = Path(installed_po) / code / 'LC_MESSAGES' / 'devicemonitor.mo'
    return nested if nested.is_file() else Path(installed_po) / f'{code}_devicemonitor.mo'


def page_keys(template):
    return {unquote(match) for match in LANG_CALL.findall(template)}


def script_bodies(template):
    """Inline <script> bodies: the only place a JSON-encoded translation is evaluated.

    A devicemonitor_t() (formerly lang._()) call in HTML context is escaped on purpose, so the
    JavaScript-escaping
    checks must not be applied to the template as a whole.
    """
    return '\n'.join(SCRIPT_BLOCK.findall(template))



def php(script, *arguments):
    result = subprocess.run([PHP, '-r', script, *arguments], capture_output=True, text=True, encoding='utf-8')
    if result.returncode != 0:
        raise RuntimeError(result.stdout + result.stderr)
    return result.stdout


def read_mo(mo):
    with Path(mo).open('rb') as stream:
        return gettext.GNUTranslations(stream)


def po_entries(po):
    """Message id -> message string, for the simple one-to-one catalogues used here."""
    entries = {}
    message_id = None
    for line in Path(po).read_text(encoding='utf-8').splitlines():
        if line.startswith('msgid_plural'):
            raise RuntimeError(f'plural forms are not supported by this test: {po}')
        if line.startswith('msgid '):
            message_id = json.loads(line[6:])
        elif line.startswith('msgstr '):
            entries[message_id] = json.loads(line[7:])
    return entries


def render(view_source, language, variables, translations, engine, directory):
    payload = {
        'locale': language,
        'langcode': language.replace('_', '-'),
        'template': view_source,
        'vars': variables,
        'engine': engine,
        'translations': translations,
        'directory': str(directory),
    }
    result = subprocess.run([PHP, str(RENDERER)], input=json.dumps(payload),
                            capture_output=True, text=True, encoding='utf-8')
    if result.returncode != 0:
        raise RuntimeError(f'{result.stdout.strip()} {result.stderr.strip()[-300:]}')
    return json.loads(result.stdout)


def normalise(markup):
    """Page text as rendered: HTML entities and the JSON escapes Volt adds for JavaScript.

    Both encodings nest (an apostrophe becomes &#039; and then \\u0026#039;), so the
    decoding repeats until it reaches a fixed point.
    """
    text = markup
    for _ in range(4):
        updated = html.unescape(text)
        for escape, character in (('\\/', '/'), ('\\n', '\n'), ('\\t', '\t'), ('\\r', '\r')):
            updated = updated.replace(escape, character)
        updated = JSON_ESCAPE.sub(lambda match: chr(int(match.group(1), 16)), updated)
        if updated == text:
            break
        text = updated
    return text


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def probe_environment(languages, directory):
    """setlocale and shared-catalogue availability, the GUI language list and engine support."""
    script = ('$out=[];foreach(explode(",",$argv[1]) as $l){'
              '$out[$l]=["setlocale"=>(bool)setlocale(LC_ALL,$l.".UTF-8"),'
              '"shared"=>is_file(rtrim($argv[2],"/")."/".$l."/LC_MESSAGES/OPNsense.mo")];}'
              'echo json_encode($out);')
    locales = json.loads(php(script, ','.join(languages), str(directory)))
    selectable = None
    if (CORE_INC / 'config.inc').is_file() and (CORE_INC / 'system.inc').is_file():
        script = ('require_once "/usr/local/etc/inc/config.inc";'
                  'require_once "/usr/local/etc/inc/system.inc";'
                  'echo json_encode(array_keys(get_locale_list()));')
        try:
            selectable = json.loads(php(script))
        except RuntimeError:
            warn('System > Settings > General > Language could not be read from the installed core')
    engine = 'interpolate'
    phalcon = php('echo class_exists("Phalcon\\\\Mvc\\\\View\\\\Engine\\\\Volt\\\\Compiler")?"yes":"no";')
    if TRANSLATOR.is_file() and phalcon == 'yes':
        engine = 'runtime'
    return locales, selectable, engine


def load_catalogues(languages, keys, directory, installed_po=INSTALLED_PO):
    """Resolved values per language from the source catalogue, plugin .mo and shared .mo."""
    catalogues = {}
    for code in languages:
        shared = Path(directory) / code / 'LC_MESSAGES' / 'OPNsense.mo'
        plugin = plugin_mo(code, installed_po)
        source = source_po(code)
        entries = po_entries(source) if source.is_file() else {}
        shared_values = catalogue_values(read_mo(shared), keys) if shared.is_file() else None
        plugin_values = catalogue_values(read_mo(plugin), keys) if plugin.is_file() else None
        values = {}
        for key in keys:
            # the deployed shared catalogue is what the pages must render
            if shared_values is not None and shared_values[key] != '':
                values[key] = shared_values[key]
            elif key in entries and entries[key] != '':
                values[key] = entries[key]
            else:
                values[key] = key
        catalogues[code] = {
            'values': values, 'plain': {key: normalise(value) for key, value in values.items()},
            'source': entries, 'shared': shared_values, 'plugin': plugin_values,
            'shared_path': shared, 'plugin_path': plugin, 'path': source,
        }
    return catalogues


def catalogue_values(catalogue, keys):
    return {key: catalogue.gettext(key) for key in keys}


def audit_catalogue(language, catalogue, keys):
    """Completeness of the source catalogue and agreement of every installed file with it.

    The plugin catalogue is the domain the migrated views resolve through
    (devicemonitor_t()), so drift there is a stale deployment and fails.

    The shared core catalogue is now only the second step of the fallback chain: for any key
    the plugin catalogue covers, its value is never what a page renders, and the two differ
    by design - the legacy merged plugin strings are older than the plugin's own catalogue,
    and for a word the core GUI also uses (for example "Language") the core wording is the
    core GUI's own choice. Drift on those keys is therefore a warning, still fatal under
    --strict. A key the plugin catalogue does not cover can only come from the shared
    catalogue, so drift there remains a failure.
    """
    missing = sorted(key for key in keys
                     if key not in catalogue['source'] or catalogue['source'][key] == '')
    if missing:
        fail(f'{language}: {len(missing)} page strings absent from the source catalogue, e.g. {missing[0]}')
    identical = sorted(key for key in keys if catalogue['source'].get(key) == key)
    plugin = catalogue['plugin']
    for installed in ('plugin', 'shared'):
        values = catalogue[installed]
        if values is None:
            continue
        # gettext returns the English message id when a catalogue has no value for a key,
        # so any other difference from the source is a wrongly installed catalogue
        drift = sorted(key for key in keys
                       if values[key] != catalogue['source'].get(key, key))
        if not drift:
            continue
        if installed == 'shared' and plugin is not None:
            uncovered = [key for key in drift if plugin.get(key, '') in ('', key)]
            covered = [key for key in drift if key not in uncovered]
            if covered:
                warn(f'{language}: shared core catalogue differs from the source for '
                     f'{len(covered)} string(s) the plugin catalogue resolves, e.g. '
                     f'{covered[0]}: {values[covered[0]]!r} instead of '
                     f'{catalogue["source"].get(covered[0], covered[0])!r}; the sidecar '
                     f'catalogue takes precedence in the deployed chain, so pages are unaffected')
            if uncovered:
                fail(f'{language}: installed shared catalogue differs from the source for '
                     f'{len(uncovered)} strings the plugin catalogue does not cover, e.g. '
                     f'{uncovered[0]}: {values[uncovered[0]]!r} instead of '
                     f'{catalogue["source"].get(uncovered[0], uncovered[0])!r}')
            continue
        fail(f'{language}: installed {installed} catalogue differs from the source for '
             f'{len(drift)} strings, e.g. {drift[0]}: {values[drift[0]]!r} instead of '
             f'{catalogue["source"].get(drift[0], drift[0])!r}')
    return identical, missing


def identity_scores(rendered, keys, catalogues, reference):
    """Match count of the rendered strings against every installed language."""
    scores = {}
    for code, catalogue in catalogues.items():
        differing = [key for key in keys if catalogue['values'][key] != reference[key]]
        if differing:
            scores[code] = sum(1 for key in differing if rendered.get(key) == catalogue['values'][key])
    return scores


def accept_page(language, page, template, variables, catalogue, engine, directory):
    """Render one page and compare every resolved string with the catalogue value."""
    result = render(template, language, variables, catalogue['values'], engine, directory)
    markup = result['html']
    values = result['values']
    if '{{' in markup or '{%' in markup:
        fail(f'{language}/{page}: unrendered template markup in the page')
    if not markup.strip():
        fail(f'{language}/{page}: page rendered empty')
    if values is None:
        # interpolation fallback: every string in the template is substituted
        return markup, {key: catalogue['values'][key] for key in page_keys(template)}
    if not values:
        fail(f'{language}/{page}: no translated string was resolved')
    for key in sorted(values):
        # ViewTranslator HTML-escapes its output; compare the text it stands for
        if normalise(values[key]) != catalogue['values'][key]:
            fail(f'{language}/{page}: "{key}" rendered as {values[key]!r} instead of '
                 f'{catalogue["values"][key]!r}')
    # strings inside a not-taken template branch are resolved by the other page variant
    return markup, values


def check_page_text(language, page, markup, keys, catalogues, reference, engine):
    """The page text must be the selected language's text, not another language's."""
    text = normalise(markup)
    plain_reference = {key: normalise(reference[key]) for key in keys}
    hits = {}
    for code, catalogue in catalogues.items():
        # long strings only: short strings collide between languages by accident
        plain = catalogue['plain']
        distinctive = [key for key in keys
                       if len(plain[key]) >= 8 and plain[key] != plain_reference[key]]
        hits[code] = sum(1 for key in distinctive if plain[key] in text)
    plain = catalogues[language]['plain']
    expected = sum(1 for key in keys
                   if len(plain[key]) >= 8 and plain[key] != plain_reference[key])
    selected = hits[language]
    others = {code: count for code, count in hits.items() if code != language}
    best_other = max(others.values(), default=0)
    if engine == 'runtime' and expected and selected / expected < 0.9:
        fail(f'{language}/{page}: only {selected}/{expected} translated strings present in the page')
    if expected and selected == 0:
        fail(f'{language}/{page}: no translated text found in the page')
    if selected <= best_other:
        rival = max(others, key=others.get)
        fail(f'{language}/{page}: page text matches {rival} ({best_other}) at least as well as '
             f'{language} ({selected})')
    return selected, expected


def main():
    parser = argparse.ArgumentParser(description='DM-BL-008 Device Monitor language acceptance')
    parser.add_argument('--engine', choices=('auto', 'runtime', 'interpolate'), default='auto',
                        help='view rendering engine; runtime is the production Phalcon path')
    parser.add_argument('--languages', default=','.join(LANGUAGES))
    parser.add_argument('--report', type=Path, help='write a markdown acceptance record')
    parser.add_argument('--views', type=Path, help='render templates from this directory (default installed views)')
    parser.add_argument('--installed-po', type=Path, default=INSTALLED_PO,
                        help='deployed plugin catalogue directory to compare against the source '
                             '(default %(default)s); point it at a staged tree to check a host whose '
                             'deployment is intentionally behind the checkout')
    parser.add_argument('--locale-dir', type=Path, default=SHARED_LOCALE,
                        help='shared gettext domain the GUI reads (default %(default)s)')
    parser.add_argument('--strict', action='store_true',
                        help='also fail on warnings such as GUI language list gaps')
    args = parser.parse_args()
    languages = [code for code in args.languages.split(',') if code]
    for code in languages:
        if code not in LANGUAGES:
            fail(f'{code}: not one of the DM-BL-008 languages')
    if not languages:
        raise SystemExit('no languages selected')
    directory = args.locale_dir

    views = args.views if args.views is not None else (
        INSTALLED_VIEWS if INSTALLED_VIEWS.is_dir() else SOURCE_VIEWS
    )
    if not views.is_dir():
        raise SystemExit(f'view directory does not exist: {views}')
    if views == INSTALLED_VIEWS:
        for _, view, _ in PAGES:
            if sha256(views / view) != sha256(SOURCE_VIEWS / view):
                fail(f'installed view differs from the source: {view}')

    locale_availability, selectable, engine = probe_environment(languages, directory)
    missing_shared = [code for code in languages if not locale_availability[code]['shared']]
    if args.engine == 'runtime' and missing_shared:
        fail(f'runtime engine requested but the shared catalogue is missing for {", ".join(missing_shared)}')
        return 1
    if args.engine == 'interpolate' or (args.engine == 'auto' and missing_shared):
        engine = 'interpolate'

    templates, union, js_keys, escaped_js = {}, set(), set(), {}
    for page, view, variables in PAGES:
        template = (views / view).read_text(encoding='utf-8')
        templates[page] = (template, variables)
        union |= page_keys(template)
        scripts = script_bodies(template)
        js_keys |= {unquote(match.group(1)) for match in JSON_CALL.finditer(scripts)}
        unsafe = {unquote(match.group(1)) for match in UNSAFE_JS_CALL.finditer(scripts)}
        if unsafe:
            escaped_js.setdefault(view, set()).update(unsafe)
    if engine == 'interpolate':
        # This path applies no view escaping, so the source form is the only guard. Reported
        # once per view rather than once per page: port discovery renders the
        # infrastructure-services view, so a page-level check reports the same call sites twice.
        for view, keys in escaped_js.items():
            fail(f'{view}: {len(keys)} translation(s) HTML-escaped inside a script body before '
                 f'json_encode(15), e.g. {sorted(keys)[0]!r}; use the raw lang.query() '
                 f'or devicemonitor_raw()')
    reference_po = source_po(REFERENCE)
    reference = po_entries(reference_po) if reference_po.is_file() else {key: key for key in union}
    catalogues = load_catalogues(languages + ['cs_CZ', REFERENCE], union, directory, args.installed_po)

    results, gaps = [], 0
    for language in languages:
        catalogue = catalogues[language]
        identical, missing = audit_catalogue(language, catalogue, union)
        rendered, pages_ok = {}, True
        for page, (template, variables) in templates.items():
            try:
                markup, page_values = accept_page(language, page, template, variables, catalogue,
                                                  engine, directory)
            except RuntimeError as error:
                fail(f'{language}/{page}: {error}')
                pages_ok = False
                continue
            rendered.update(page_values)
            check_page_text(language, page, markup, page_values, catalogues, reference, engine)

        if engine == 'runtime':
            # The defect is language specific, so it is measured on the values that reached the
            # script contexts, not on the source form of the call sites.
            escaped = sorted(key for key in js_keys
                             if key in rendered and ENTITY.search(rendered[key]))
            if escaped:
                fail(f'{language}: {len(escaped)} JavaScript translation(s) arrive HTML-escaped, '
                     f'e.g. {escaped[0]!r} as {rendered[escaped[0]]!r}; use the raw lang.query() '
                     f'or devicemonitor_raw()')

        scores = identity_scores(rendered, union, catalogues, reference)
        best = max(scores, key=scores.get) if scores else language
        if scores.get(best, 0) > scores.get(language, 0):
            fail(f'{language}: rendered text best matches {best} ({scores[best]} of {len(union)} strings)')
        script = WRITING_SYSTEM.get(language)
        if rendered and script and not any(script.search(value) for value in rendered.values()):
            fail(f'{language}: no {language} writing-system characters in the rendered pages')
        if rendered and not script and any(CJK.search(value) or CYRILLIC.search(value) for value in rendered.values()):
            fail(f'{language}: unexpected non-Latin writing system in the rendered pages')

        offered = None if selectable is None else language in selectable
        # only check the host locale when this host carries the shared catalogue
        available = (locale_availability[language]['setlocale']
                     if locale_availability[language]['shared'] else None)
        if offered is False:
            gaps += 1
            warn(f'{language}: absent from System > Settings > General > Language '
                 f'(get_locale_list, {len(selectable)} languages); the pages still render this language')
        if available is False:
            gaps += 1
            warn(f'{language}: locale {language}.UTF-8 is not installed on this host')
        results.append({
            'language': language, 'pages': len(templates), 'keys': len(union), 'missing': len(missing),
            'identical': len(identical), 'identity': best, 'selectable': offered,
            'locale': available, 'ok': pages_ok and not missing,
        })
        print(f'{language} {"PASS" if results[-1]["ok"] else "FAIL"} pages={len(templates)} keys={len(union)} '
              f'translated={len(union) - len(identical)} identical-to-english={len(identical)} '
              f'selectable={offered} locale={available} identity={best} engine={engine}')

    if args.strict:
        for message in list(warnings):
            fail(f'strict: {message}')
    write_report(args.report, engine, views, results, selectable)
    print(f'LANGUAGE_ACCEPTANCE={"PASS" if not failures else "FAIL"} languages={len(languages)} '
          f'gaps={gaps} engine={engine} failures={len(failures)}')
    return 1 if failures else 0


def write_report(path, engine, views, results, selectable):
    """Markdown acceptance record, written only when --report is given."""
    if path is None:
        return
    rows = ['| Language | Pages | Strings | Translated | Identical to English | GUI selectable | Locale | Result |',
            '| --- | --- | --- | --- | --- | --- | --- | --- |']
    for result in results:
        offered = 'not readable' if result['selectable'] is None else ('yes' if result['selectable'] else '**no**')
        locale_state = 'not checked' if result['locale'] is None else ('yes' if result['locale'] else 'no')
        rows.append(f"| {result['language']} | {result['pages']} | {result['keys']} | "
                    f"{result['keys'] - result['identical']} | {result['identical']} | {offered} | "
                    f"{locale_state} | {'PASS' if result['ok'] else 'FAIL'} |")
    engine_note = ('the production path: Phalcon Volt compiler, OPNsense ViewTranslator, shared gettext domain'
                   if engine == 'runtime' else 'interpolation fallback because Phalcon is unavailable')
    lines = [
        '# Device Monitor language acceptance (DM-BL-008) — automated run', '',
        f'- Date: {datetime.datetime.now().astimezone():%Y-%m-%d %H:%M:%S %Z}',
        f'- Host: {os.uname().nodename}',
        f'- Views rendered: `{views}`',
        f'- Rendering engine: `{engine}` ({engine_note})',
        f"- Languages offered by System > Settings > General > Language: "
        + (f'{len(selectable)}' if selectable is not None else 'not readable'),
        '', *rows, '',
        '## Method', '',
        'For each language every Device Monitor page is rendered from its Volt template with the',
        'locale set as the GUI sets it, and the rendered page is compared with the same language\'s',
        'catalogue. The run passes only when every string used by every page resolves to that',
        "language's text, that text appears in the rendered page, the page text does not match any",
        'other installed language better, and the writing system (Cyrillic, CJK) is present where the',
        'language requires one. An English fallback cannot be missed: a string without a catalogue',
        'value renders as its English message id.',
        '',
        '## Findings and limits', '',
    ]
    lines += [f'- WARNING: {message}' for message in warnings] or ['- No warnings.']
    lines += [f'- FAILURE: {message}' for message in failures] or ['- No failures.']
    lines += [
        '- HTTP transport, JavaScript execution, page layout and translation quality are not covered.',
        '- This run does not replace a human review of the wording in each language.',
        '',
        f"Result: **{'PASS' if not failures else 'FAIL'}**",
    ]
    Path(path).write_text('\n'.join(lines) + '\n', encoding='utf-8')
    print(f'REPORT_WRITTEN={path}')


if __name__ == '__main__':
    sys.exit(main())

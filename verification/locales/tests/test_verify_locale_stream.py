"""Offline self-test for verify_locale_stream.py.

Runs on the recording host, which has no selenium, no pip and no browser: every
test here drives the pure check functions, the case loader, the result builder and
the writers with synthetic fixtures. No test touches a network or a target.

    python3 tests/test_verify_locale_stream.py

Prints `VERIFY_LOCALE_STREAM=PASS` and exits 0 on success.
"""
import contextlib
import importlib.util
import io
import json
import sys
import tempfile
from pathlib import Path

HARNESS = Path(__file__).resolve().parents[1] / 'verify_locale_stream.py'
MARKER = 'R\u00e9sum\u00e9'


def load_module():
    spec = importlib.util.spec_from_file_location('verify_locale_stream', HARNESS)
    module = importlib.util.module_from_spec(spec)
    # Registered before execution: the harness declares dataclasses, whose field
    # resolution looks the defining module up in sys.modules.
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def happy_observation(module):
    final = 'Écran Résumé des modifications\nSurveillance des appareils'
    partial = 'Écran Résumé'
    snapshots = [
        module.Snapshot(
            t_ms=10, chars=len(partial), sha256=module.sha256_text(partial),
            text=partial, html_sha256=module.sha256_text('<html>partial'),
        ),
        module.Snapshot(
            t_ms=20, chars=len(final), sha256=module.sha256_text(final),
            text=final, html_sha256=module.sha256_text('<html>final'),
        ),
    ]
    chunks = [module.Chunk(
        kind='fetch', url='/index.php', t_ms=5, chars=len(final),
        sha256=module.sha256_text(final), text=final,
    )]
    return module.Observation(
        snapshots=snapshots, chunks=chunks, text=final, page_source='<html lang="test-LC">',
        observed_lang='test-LC', charset='UTF-8', markers=[MARKER],
        probe=['Change Summary'], expected_lang='test-LC',
    )


def complete_case(overrides=None):
    payload = {
        'case_id': 'test_LC',
        'locale': 'test_LC',
        'expected_document_lang': 'test-LC',
        'target': {
            'base_url': 'http://127.0.0.1:1',
            'route': '/index.php',
            'build': None,
            'locale_pin': {'method': 'operator-navigated-ui'},
        },
        'markers': {'expected': [{'text': MARKER, 'reported_status': 'PASS'}]},
        'untranslated_probe': ['Change Summary'],
    }
    payload.update(overrides or {})
    return payload


def write_case(directory, payload, in_cases_dir=True):
    parent = Path(directory) / ('locale_cases' if in_cases_dir else 'elsewhere')
    parent.mkdir(parents=True, exist_ok=True)
    path = parent / f'{payload.get("case_id", "case")}.json'
    path.write_text(json.dumps(payload), encoding='utf-8')
    return path


def statuses(results):
    return {result.name: result.status for result in results}


def test_marker_attestation_is_not_consumed():
    module = load_module()
    case = module.Case(
        path=Path('/tmp/locale_cases/x.json'),
        data={
            'case_id': 'x', 'locale': 'x',
            'markers': {'expected': [{'text': 'Absent label', 'reported_status': 'PASS'}]},
        },
    )
    assert case.markers == ['Absent label'], 'marker text is read'
    result = module.check_localized_markers_present('nothing here', case.markers)
    assert result.status == 'FAIL', 'a reported PASS must not become a PASS result'
    assert module.check_localized_markers_present('nothing here', []).status == 'SKIP'


def test_untranslated_fallback_check():
    module = load_module()
    probe = ['Change Summary']
    assert module.check_no_untranslated_fallback('no english here', probe).status == 'PASS'
    assert module.check_no_untranslated_fallback('Change Summary', probe).status == 'FAIL'
    absent = module.check_no_untranslated_fallback('no english here', [])
    assert absent.status == 'SKIP', 'an absent probe is never a pass'


def test_case_loader():
    module = load_module()
    with tempfile.TemporaryDirectory() as tmp:
        path = write_case(tmp, complete_case())
        case = module.load_case(path)
        assert case.locale == 'test_LC'
        assert case.expected_document_lang == 'test-LC'
        assert case.markers == [MARKER]
        assert case.untranslated_probe == ['Change Summary']
        assert case.locale_pin == {'method': 'operator-navigated-ui'}
        assert module.run_inputs_missing(case) == []
        assert module.resolve_url(case) == 'http://127.0.0.1:1/index.php'

        incomplete = write_case(tmp, complete_case({
            'case_id': 'incomplete_LC',
            'target': {'base_url': None, 'route': None},
        }))
        missing = module.run_inputs_missing(module.load_case(incomplete))
        assert missing == ['target.base_url', 'target.route'], missing

        misplaced = write_case(tmp, complete_case({'case_id': 'misplaced_LC'}), False)
        try:
            module.load_case(misplaced)
        except module.ConfigError as error:
            assert 'locale_cases' in str(error), error
        else:
            raise AssertionError('a case outside locale_cases/ must be refused')

        try:
            module.load_case(Path(tmp) / 'locale_cases' / 'absent.json')
        except module.ConfigError as error:
            assert 'not found' in str(error), error
        else:
            raise AssertionError('a missing case file must be refused')


def test_result_builder_and_writers():
    module = load_module()
    with tempfile.TemporaryDirectory() as tmp:
        case = module.load_case(write_case(tmp, complete_case()))
        observation = happy_observation(module)
        results = module.run_checks(observation)
        env = module.EnvReport(
            python_version='3.13.15', selenium_version='4.0.0',
            driver_path='/usr/local/bin/chromedriver', browsers_found=['chromium'],
            problems=[],
        )
        moment = module.utc_now()
        result = module.build_result(case, results, observation, env, moment, moment, [])
        assert result['result'] == 'PASS' and result['exit_code'] == 0
        assert result['target']['locale_pinning_method'] == {'method': 'operator-navigated-ui'}
        assert result['device_state']['pre_change_locale_state'] is None
        assert len(result['stream']['snapshots']) == len(observation.snapshots)
        assert len(result['stream']['captured_units']) == len(observation.chunks)

        out_dir = Path(tmp) / 'out' / 'test_LC'
        written = module.write_outputs(out_dir, result, observation, True, True)
        assert written == module.planned_artifacts('test_LC', True, True, False, True)
        for name in written:
            assert (out_dir / name).is_file(), name
        payload = json.loads((out_dir / 'result-test_LC.json').read_text(encoding='utf-8'))
        assert payload['result'] == 'PASS'
        assert payload['artifacts_written'] == written
        assert 'no_mojibake' in (out_dir / 'report-test_LC.html').read_text(encoding='utf-8')
        markdown = (out_dir / 'report-test_LC.md').read_text(encoding='utf-8')
        assert 'never a pass' in markdown
        rows = (out_dir / 'stream-test_LC.jsonl').read_text(
            encoding='utf-8',
        ).strip().splitlines()
        assert len(rows) == len(observation.snapshots) + len(observation.chunks)
        for row in rows:
            assert 't_ms' in row and 'chars' in row and 'sha256' in row, row


def test_dry_run_and_exit_mapping():
    module = load_module()
    with tempfile.TemporaryDirectory() as tmp:
        case = module.load_case(write_case(tmp, complete_case()))
        clean = module.EnvReport('3.13.15', '4.0.0', None, ['chromium'], [])
        broken = module.EnvReport('3.13.15', None, None, [], ['selenium is not importable'])
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            assert module.run_dry(case, clean, module.RunLog()) == 0
            assert module.run_dry(case, broken, module.RunLog()) == 2
        output = buffer.getvalue()
        assert 'DRY-RUN=OK (plan only)' in output
        assert 'DRY-RUN=BLOCKED' in output
        assert 'untranslated_probe entries: 1' in output
        assert module.exit_code_for('FAIL') == 1
        assert module.exit_code_for('ERROR') == 1


def test_main_refuses_incomplete_state():
    module = load_module()
    with tempfile.TemporaryDirectory() as tmp:
        # A case outside locale_cases/ is refused before anything else happens.
        misplaced = write_case(tmp, complete_case({'case_id': 'outside_LC'}), False)
        out_dir = Path(tmp) / 'out'
        buffer, errors = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(buffer), contextlib.redirect_stderr(errors):
            assert module.main(['--case', str(misplaced)]) == 2
            assert module.main(['--case', str(misplaced), '--dry-run']) == 2
            assert module.main([]) == 2
            assert module.main(['--case', str(Path(tmp) / 'nowhere.json')]) == 2
            incomplete = write_case(tmp, complete_case({
                'case_id': 'incomplete_LC', 'target': {'base_url': None, 'route': None},
            }))
            assert module.main(['--case', str(incomplete), '--out-dir', str(out_dir)]) == 2
        assert not out_dir.exists(), 'a refused run writes nothing'
        assert 'MISSING INPUT' in errors.getvalue() or 'ENVIRONMENT' in errors.getvalue()



def test_happy_path():
    module = load_module()
    results = module.run_checks(happy_observation(module))
    assert [result.name for result in results] == list(module.CHECK_NAMES), statuses(results)
    assert statuses(results) == {name: 'PASS' for name in module.CHECK_NAMES}, statuses(results)
    assert module.overall_status(results) == 'PASS'
    assert module.exit_code_for('PASS') == 0


def test_skipped_checks_are_never_pass():
    module = load_module()
    results = module.run_checks(module.Observation())
    assert set(statuses(results).values()) == {'SKIP'}, statuses(results)
    assert module.overall_status(results) == 'NO-RESULT'
    assert module.exit_code_for('NO-RESULT') == 2, 'nothing verified is never exit 0'
    broken = module.Observation(text=None)
    assert statuses(module.run_checks(broken))['no_mojibake'] == 'ERROR'


def test_encoding_defects():
    module = load_module()
    assert module.check_no_replacement_char('ok \ufffd text').status == 'FAIL'
    assert module.check_no_replacement_char('ok text').status == 'PASS'
    assert module.check_no_mojibake('R\u00c3\u00a9sum\u00c3\u00a9').status == 'FAIL'
    assert module.check_no_mojibake('R\u00e9sum\u00e9').status == 'PASS'
    assert module.check_no_control_chars('a\tb\nc\rd').status == 'PASS'
    assert module.check_no_control_chars('a\x07b').status == 'FAIL'
    assert module.check_no_mojibake('').status == 'SKIP'
    assert module.check_no_replacement_char('').status == 'SKIP'


def test_stream_checks():
    module = load_module()

    def snapshot(index, chars):
        return module.Snapshot(
            t_ms=index, chars=chars, sha256=module.sha256_text(str(chars)),
            text='x' * chars, html_sha256=module.sha256_text(str(chars)),
        )

    assert module.check_stream_progressed([]).status == 'SKIP'
    assert module.check_stream_progressed([snapshot(1, 10)]).status == 'SKIP'
    assert module.check_stream_progressed([snapshot(1, 10), snapshot(2, 30)]).status == 'PASS'
    assert module.check_stream_progressed([snapshot(1, 30), snapshot(2, 30)]).status == 'WARN'
    assert module.check_stream_progressed([snapshot(1, 30), snapshot(2, 10)]).status == 'FAIL'


def test_lossless_checks():
    module = load_module()
    text = 'R\u00e9sum\u00e9 des modifications'
    chunk = module.Chunk(
        kind='fetch', url='/x', t_ms=1, chars=len(text),
        sha256=module.sha256_text(text), text=text,
    )
    matching = module.Snapshot(
        t_ms=1, chars=len(text), sha256=module.sha256_text(text), text=text,
        html_sha256=module.sha256_text('html'),
    )
    assert module.check_stream_lossless([matching], [chunk]).status == 'PASS'
    diverging = module.Snapshot(
        t_ms=2, chars=4, sha256=module.sha256_text('tail'), text='tail',
        html_sha256=module.sha256_text('html'),
    )
    failed = module.check_stream_lossless([diverging], [chunk])
    assert failed.status == 'FAIL'
    assert failed.evidence['method'] == 'captured-response-assembly'
    assert 'first_divergence_offset' in failed.evidence
    prefix_ok = module.check_stream_lossless(
        [module.Snapshot(t_ms=1, chars=6, sha256='a', text='R\u00e9sum', html_sha256='h'),
         matching],
        [],
    )
    assert prefix_ok.status == 'PASS' and prefix_ok.evidence['method'] == 'dom-prefix'
    prefix_bad = module.check_stream_lossless(
        [module.Snapshot(t_ms=1, chars=6, sha256='a', text='zzzzzz', html_sha256='h'),
         matching],
        [],
    )
    assert prefix_bad.status == 'FAIL'
    assert module.check_stream_lossless([], []).status == 'SKIP'


def test_document_lang():
    module = load_module()
    assert module.check_document_lang('it-IT', 'it_IT').status == 'PASS'
    assert module.check_document_lang('en-US', 'it_IT').status == 'FAIL'
    assert module.check_document_lang(None, 'it_IT').status == 'FAIL'
    assert module.check_document_lang('it-IT', None).status == 'SKIP'


def test_diacritics():
    module = load_module()
    assert module.check_diacritics_roundtrip('R\u00e9sum\u00e9', [MARKER], 'UTF-8').status == 'PASS'
    assert module.check_diacritics_roundtrip('Resume', [MARKER], 'UTF-8').status == 'WARN'
    assert module.check_diacritics_roundtrip('R\u00e9sum\u00e9', [], 'ISO-8859-1').status == 'FAIL'
    assert module.check_diacritics_roundtrip('plain ascii', [], 'UTF-8').status == 'WARN'
    assert module.check_diacritics_roundtrip('', [MARKER], 'UTF-8').status == 'SKIP'


if __name__ == '__main__':
    test_happy_path()
    test_skipped_checks_are_never_pass()
    test_encoding_defects()
    test_stream_checks()
    test_lossless_checks()
    test_document_lang()
    test_diacritics()
    test_marker_attestation_is_not_consumed()
    test_untranslated_fallback_check()
    test_case_loader()
    test_result_builder_and_writers()
    test_dry_run_and_exit_mapping()
    test_main_refuses_incomplete_state()
    print('VERIFY_LOCALE_STREAM=PASS')

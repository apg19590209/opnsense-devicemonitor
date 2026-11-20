"""Regression for JavaScript translation context isolation."""

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'tests' / 'test_language_acceptance.py'


def load_module():
    spec = importlib.util.spec_from_file_location(
        'devicemonitor_language_acceptance',
        SOURCE,
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_static_occurrence_does_not_overwrite_js_context():
    module = load_module()
    contexts = module.runtime_js_context_values(
        {
            'physicaldevices': {'Hostname'},
            'devicehistory': set(),
        },
        {
            'physicaldevices': {'Hostname': "Nom d'hôte"},
            'devicehistory': {'Hostname': 'Nom d&#039;hôte'},
        },
    )

    assert contexts == {'Hostname': ["Nom d'hôte"]}
    assert not any(
        module.ENTITY.search(value)
        for values in contexts.values()
        for value in values
    )
    print('LANGUAGE_JS_CONTEXT_ISOLATION=PASS')


def test_escaped_js_occurrence_still_fails():
    module = load_module()
    contexts = module.runtime_js_context_values(
        {'devices': {'Quoted label'}},
        {'devices': {'Quoted label': 'l&#039;appareil'}},
    )

    assert any(
        module.ENTITY.search(value)
        for values in contexts.values()
        for value in values
    )
    print('LANGUAGE_JS_ESCAPE_DETECTION=RETAINED')


def main():
    test_static_occurrence_does_not_overwrite_js_context()
    test_escaped_js_occurrence_still_fails()
    print('LANGUAGE_CONTEXT_ISOLATION=PASS')


if __name__ == '__main__':
    main()

// Structural UI tests need JavaScript after Volt interpolation, not raw templates.
// Full catalogue and real Volt compilation coverage lives in test_translated_javascript.py.
const vm = require('vm');

function renderTranslations(source) {
    return source.replace(
        /\{\{\s*lang\._\(('(?:\\.|[^'\\])*'|"(?:\\.|[^"\\])*")\)\|json_encode\(15\)\s*\}\}/g,
        (_, literal) => JSON.stringify(vm.runInNewContext(literal))
            .replace(/</g, '\\u003c').replace(/>/g, '\\u003e')
            .replace(/&/g, '\\u0026').replace(/'/g, '\\u0027')
    );
}

module.exports = {renderTranslations};

<?php
// Render script bodies only: no application bootstrap, database or live config.
// 15 = JSON_HEX_TAG | JSON_HEX_AMP | JSON_HEX_APOS | JSON_HEX_QUOT.
$input = json_decode(stream_get_contents(STDIN), true, 512, JSON_THROW_ON_ERROR);
$pattern = '/\{\{\s*lang\._\((\x27(?:\\\\.|[^\x27\\\\])*\x27|"(?:\\\\.|[^"\\\\])*")\)\|json_encode\(15\)\s*\}\}/';
$translations = $input['translations'];
$translate = static function ($key) use ($translations) {
    return $translations[$key] ?? $key;
};
$expected = preg_replace_callback($pattern, static function ($m) use ($translate) {
    // Only a quoted literal accepted by the regex is evaluated.
    $key = eval('return ' . $m[1] . ';');
    return json_encode($translate($key), 15 | JSON_THROW_ON_ERROR);
}, $input['script']);
if (strpos($expected, '{{') !== false || strpos($expected, '{%') !== false) {
    throw new RuntimeException('Unencoded translation or unsupported template in JavaScript');
}
if (class_exists('Phalcon\\Mvc\\View\\Engine\\Volt\\Compiler')) {
    $compiler = new Phalcon\Mvc\View\Engine\Volt\Compiler(new Phalcon\Mvc\View());
    $compiled = $compiler->compileString($input['script']);
    $lang = new class($translate) {
        private $translate;
        public function __construct($translate) { $this->translate = $translate; }
        public function _($key) { return ($this->translate)($key); }
    };
    ob_start();
    eval('?>' . $compiled);
    $actual = ob_get_clean();
    // PHP may consume a newline after a closing tag; validate actual generated
    // JavaScript rather than requiring byte-identical template whitespace.
    echo $actual;
    exit;
}
echo $expected;

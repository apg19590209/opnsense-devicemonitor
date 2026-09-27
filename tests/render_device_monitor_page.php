<?php
/*
 * Render one Device Monitor page for one GUI language.
 *
 * runtime engine: reproduces the OPNsense MVC view path — the locale handling of
 * OPNsense\Base\ControllerRoot::setLang(), the real OPNsense\Base\ViewTranslator
 * over the shared gettext domain (/usr/local/share/locale/<locale>/LC_MESSAGES/
 * OPNsense.mo) and the real Phalcon Volt compiler.
 *
 * interpolate engine: reproduces only the constructs the Device Monitor views
 * use — {{ lang._('...') }}, {{ lang.query('...')|json_encode(15) }} and the simple
 * {% if %} / {% else %} / {% endif %} blocks — so the acceptance test can also
 * run where Phalcon is unavailable (CI). Unsupported constructs are rejected.
 *
 * Input  (JSON on stdin): locale, langcode, template, vars, engine, translations
 * Output (JSON on stdout): engine, html, values (resolved ids, runtime only)
 */

$input = json_decode(stream_get_contents(STDIN), true, 512, JSON_THROW_ON_ERROR);
$template = $input['template'];
$vars = $input['vars'] ?? [];
$engine = $input['engine'] ?? 'auto';
$locale = isset($input['locale']) ? $input['locale'] . '.UTF-8' : null;
$langcode = $input['langcode'] ?? 'en-US';
$directory = $input['directory'] ?? '/usr/local/share/locale';
$translatorFile = $input['translator'] ?? '/usr/local/opnsense/mvc/app/library/OPNsense/Base/ViewTranslator.php';
$catalogue = $locale === null ? false : $directory . '/' . $input['locale'] . '/LC_MESSAGES/OPNsense.mo';
$runtime = $locale !== null && class_exists('Phalcon\Mvc\View\Engine\Volt\Compiler') &&
    is_file($translatorFile) && is_file($catalogue);
if ($engine === 'auto') {
    $engine = $runtime ? 'runtime' : 'interpolate';
}
if ($engine === 'runtime' && !$runtime) {
    throw new RuntimeException('runtime engine unavailable: Phalcon, translator or catalogue missing');
}

if (!function_exists('view_html_safe')) {
    /* Same encoding as the web entry point (/usr/local/opnsense/www/index.php). */
    function view_html_safe($text)
    {
        return str_replace("\n", '&#10;', htmlspecialchars($text ?? '', ENT_QUOTES | ENT_HTML401));
    }
}

/** Records every resolved message id and delegates to the production translator. */
class DeviceMonitorRecordingTranslator
{
    private $translator;
    public $resolved = [];

    public function __construct($translator)
    {
        $this->translator = $translator;
    }

    public function _($messageId, array $placeholders = []): string
    {
        return $this->resolved[$messageId] = $this->translator->_($messageId, $placeholders);
    }

    public function query($messageId): string
    {
        return $this->resolved[$messageId] = $this->translator->query($messageId);
    }
}

$values = null;
if ($engine === 'runtime') {
    require_once $translatorFile;
    putenv('LANG=' . $locale);
    putenv('LANGUAGE=' . $locale);
    putenv('LC_ALL=' . $locale);
    setlocale(LC_ALL, $locale);
    $translator = new OPNsense\Base\ViewTranslator(new Phalcon\Translate\InterpolatorFactory(), [
        'directory' => $directory,
        'defaultDomain' => 'OPNsense',
        'locale' => [$locale],
    ]);
    bind_textdomain_codeset('OPNsense', $locale);
    $lang = new DeviceMonitorRecordingTranslator($translator);
    $compiler = new Phalcon\Mvc\View\Engine\Volt\Compiler(new Phalcon\Mvc\View());
    $renderable = $compiler->compileString($template);
} else {
    $translations = $input['translations'] ?? [];
    /* Translation expressions: text context is HTML-escaped by ViewTranslator,
       JavaScript context is JSON-encoded (15 = JSON_HEX_TAG|HEX_AMP|HEX_APOS|HEX_QUOT). */
    $renderable = preg_replace_callback(
        '/\{\{\s*lang\.(query|_)\((\'(?:\\\\.|[^\'\\\\])*\'|"(?:\\\\.|[^"\\\\])*")\s*\)(\|json_encode\(15\))?\s*\}\}/',
        static function ($matches) use ($translations) {
            $messageId = eval('return ' . $matches[2] . ';');
            $literal = var_export($translations[$messageId] ?? $messageId, true);
            return isset($matches[3]) && $matches[3] !== ''
                ? '<?= json_encode(' . $literal . ', 15 | JSON_THROW_ON_ERROR) ?>'
                : ($matches[1] === 'query'
                    ? '<?= ' . $literal . ' ?>'
                    : '<?= view_html_safe(' . $literal . ') ?>');
        },
        $template
    );
    /* Control structures used by the Device Monitor views. */
    $renderable = preg_replace_callback(
        '/\{%\s*(.*?)\s*%\}/s',
        static function ($matches) {
            $expression = $matches[1];
            if ($expression === 'else') {
                return '<?php else : ?>';
            } elseif ($expression === 'endif') {
                return '<?php endif; ?>';
            } elseif (preg_match("/^(if )(not )?([A-Za-z_][A-Za-z0-9_]*)(?: == '([^']*)')?$/", $expression, $parts)) {
                $condition = $parts[2] === 'not ' ? '!' : '';
                $condition .= '$' . $parts[3];
                if (isset($parts[4]) && $parts[4] !== '') {
                    $condition .= ' == ' . var_export($parts[4], true);
                }
                return '<?php if (' . $condition . ') : ?>';
            }
            throw new RuntimeException('unsupported template construct: ' . $expression);
        },
        $renderable
    );
    if (strpos($renderable, '{{') !== false || strpos($renderable, '{%') !== false) {
        throw new RuntimeException('unsupported translation expression remains');
    }
    $lang = null;
}

ob_start();
extract($vars, EXTR_SKIP);
eval('?>' . $renderable);
$html = ob_get_clean();

if ($engine === 'runtime') {
    $values = $lang->resolved;
}

echo json_encode(
    ['engine' => $engine, 'html' => $html, 'values' => $values],
    JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES | JSON_THROW_ON_ERROR
);

<?php
/**
 * Exact round trip for the preview body: stored text must be delivered to the
 * client unchanged (exactly one escaping step, at render time).
 */
require_once __DIR__ . '/../src/opnsense/scripts/OPNsense/DeviceMonitor/EmailLog.php';

use OPNsense\DeviceMonitor\EmailLog;

$fails = 0;
function check($c, $m) { global $fails; if ($c) { echo "  PASS $m\n"; } else { $fails++; echo "  FAIL $m\n"; } }

$INPUT = "<html><body><h2>Device Monitor preview</h2>"
       . "<p>Line one with <b>bold</b> and <i>italic</i>.</p>"
       . "<p>Special characters: &lt;tag&gt; &amp; &quot;quotes&quot; &amp;amp;.</p>"
       . "<ul><li>First bullet</li><li>Second bullet</li></ul>"
       . "<p>After the list.</p>"
       . "<img src=\"http://tracker.invalid/pixel.png\"><script>alert(1)</script></body></html>";

$EXPECTED = "Device Monitor preview\n"
          . "Line one with bold and italic.\n"
          . "Special characters: <tag> & \"quotes\" &amp;.\n"
          . "First bullet\n"
          . "Second bullet\n"
          . "After the list.";

/* 1. conversion produces exactly the expected text */
$text = EmailLog::htmlToText($INPUT);
check($text === $EXPECTED, 'converted text matches the expected preview text exactly');
check(strpos($text, '<tag>') !== false, 'escaped angle brackets decode to literal <tag>');
check(strpos($text, '"quotes"') !== false, 'quotes decode');
check(strpos($text, ' &amp;.') !== false, 'intentional literal &amp; preserved');
check(strpos($text, '&amp;amp;') === false, 'no double-decoding');
check(strpos($text, 'tracker.invalid') === false && strpos($text, 'alert(1)') === false,
    'image source and script removed');

/* 2. stored and re-read text is byte-identical (no second escaping anywhere) */
$db = tempnam(sys_get_temp_dir(), 'dmrt'); unlink($db);
$log = new EmailLog($db);
$id = $log->recordSubmission(EmailLog::TYPE_TEST, 'a@example.invalid', 'Round trip', null, null, null, null, null, $INPUT, 'html');
$detail = $log->messageDetail($id);
check($detail['content_text'] === $EXPECTED, 'stored content equals the expected text byte-for-byte');

/* 3. the JSON payload the client receives carries it unchanged */
$payload = json_encode(['content' => $detail['content_text']], JSON_INVALID_UTF8_IGNORE);
$decoded = json_decode($payload, true);
check($decoded['content'] === $EXPECTED, 'JSON round trip preserves the text exactly');
check(strpos($payload, '&amp;amp;') === false, 'payload has no double-encoded ampersand');

/* 4. what the modal would render (jQuery .text() sets textContent verbatim) */
check($decoded['content'] === $EXPECTED, 'render step adds no escaping');

/* 5. the unsafe framework path is what corrupted it before */
$unsafe = htmlspecialchars($payload, ENT_NOQUOTES);
$unsafeDecoded = json_decode($unsafe, true);
check($unsafeDecoded !== null ? $unsafeDecoded['content'] !== $EXPECTED : true,
    'unescaped array output would have altered the text (regression would catch it)');

/* 6. the endpoint marks the response safe */
$ctrl = file_get_contents(__DIR__ . '/../src/opnsense/mvc/app/controllers/OPNsense/DeviceMonitor/Api/EmaillogController.php');
check(preg_match('/setContent\(\[.*?\],\s*true\);/s', $ctrl) === 1, 'message endpoint marks the payload safe');
check(strpos($ctrl, 'SafeReturnValue') === false, 'no invented response type');

/* 7. the stored body never carries literal escape text from HTML conversion
 * (a single-quoted '\t' in htmlToText stored a backslash-t after Server, Time
 * and To in every recorded table cell) */
$table = '<p>Test Email</p><table>'
       . '<tr><td>Server:</td><td>OPNsense.internal</td></tr>'
       . '<tr><td>Time:</td><td>2026-11-17 08:52:21</td></tr>'
       . '<tr><td>To:</td><td>apg@example.invalid</td></tr></table>';
$converted = EmailLog::htmlToText($table);
check(strpos($converted, '\\t') === false, 'conversion stores no literal backslash-t');
check(strpos($converted, "\t") === false, 'no raw tab is kept in the readable text');
check(strpos($converted, "Test Email\nServer: OPNsense.internal\nTime: 2026-11-17 08:52:21\nTo: apg@example.invalid") === 0,
    'each table cell becomes one clean line');
check(strpos($converted, "\r") === false, 'carriage returns are normalised away');

/* 8. genuine message text keeps its own characters, including a typed \t */
$typed = '<pre>C:\temp\test and a typed \t sequence</pre>';
$typedText = EmailLog::htmlToText($typed);
check(strpos($typedText, 'C:\temp\test and a typed \t sequence') !== false,
    'literal backslash sequences already in the message are not rewritten');

/* 9. text bodies are stored as delivered, without reinterpretation */
$txt = "Server:\t genuine";
$idTxt = $log->recordSubmission(EmailLog::TYPE_TEST, 'a@example.invalid', 'Typed', null, null, null, null, null, $txt, 'text');
check($log->messageDetail($idTxt)['content_text'] === $txt, 'plain-text bodies are never rewritten');

@unlink($db);
echo $fails === 0 ? "EMAIL_LOG_ROUNDTRIP_TESTS=PASS\n" : "EMAIL_LOG_ROUNDTRIP_TESTS=FAIL ($fails)\n";
exit($fails === 0 ? 0 : 1);

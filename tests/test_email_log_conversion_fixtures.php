<?php
/**
 * HTML-to-text conversion for the bodies Device Monitor actually sends, using
 * fixtures only. The rules are structural: a table row is one compact line, a
 * block boundary is one blank line, scripts and remote images never survive,
 * entities decode once, and text bodies are untouched.
 */
require_once __DIR__ . '/../src/opnsense/scripts/OPNsense/DeviceMonitor/EmailLog.php';

use OPNsense\DeviceMonitor\EmailLog;

$fails = 0;
function check($c, $m) { global $fails; if ($c) { echo "  PASS $m\n"; } else { $fails++; echo "  FAIL $m\n"; } }
function conv($html) { return EmailLog::htmlToText($html); }

/* 1. test email: label/value rows are compact, paragraphs keep one blank line */
$test = "<html><body>\r\n  <h2>🧪 Test Email</h2>\r\n  <p>If you see this, <strong>email works correctly!</strong></p>\r\n"
      . "  <table style=\"width:100%\">\r\n    <tr>\r\n      <td>Server:</td>\r\n      <td>OPNsense.home.arpa</td>\r\n    </tr>\r\n"
      . "    <tr>\r\n      <td>Time:</td>\r\n      <td>2026-11-18 10:33:31</td>\r\n    </tr>\r\n"
      . "    <tr>\r\n      <td>To:</td>\r\n      <td>operator@example.invalid</td>\r\n    </tr>\r\n  </table>\r\n</body></html>";
$t = conv($test);
check(strpos($t, "Server: OPNsense.home.arpa\nTime: 2026-11-18 10:33:31\nTo: operator@example.invalid") !== false,
    'test email rows are compact label/value lines');
check(strpos($t, "🧪 Test Email\n\nIf you see this, email works correctly!\n\nServer:") === 0,
    'test email keeps one block break before the table and no blank lines inside it');
check(strpos($t, "Server:\n") === false, 'no label is left separated from its value');

/* 2. new-device email: a multi-column table stays readable, one row per line */
$newDevice = "<h2>🔔 2 New Device(s) Detected</h2>\n<p>Server: node</p>\n"
      . "<table><tr><th>MAC</th><th>Vendor</th><th>IP</th></tr>"
      . "<tr><td>aa:bb:cc</td><td>Acme</td><td>192.0.2.10</td></tr>"
      . "<tr><td>dd:ee:ff</td><td>Other</td><td>192.0.2.11</td></tr></table>";
$n = conv($newDevice);
check(strpos($n, "aa:bb:cc Acme 192.0.2.10\ndd:ee:ff Other 192.0.2.11") !== false,
    'new-device rows stay one line each with their columns joined');

/* 3. service alert: bullet list and body text separated, no excess blanks */
$service = "<p>A service on <strong>host</strong> became unavailable.</p><ul><li>Port: 443</li><li>Service: HTTPS</li></ul>";
$s = conv($service);
check(strpos($s, "Port: 443\n\nService: HTTPS") !== false, 'service alert list items stay separate blocks');
check(strpos($s, "\n\n\n") === false, 'no excessive blank lines');

/* 4. failover email: header rows then a paragraph */
$failover = "<h2>HA role changed</h2><table><tr><td>Node:</td><td>.252</td></tr><tr><td>Role:</td><td>BACKUP</td></tr></table><p>Effective at 10:00.</p>";
$f = conv($failover);
check(strpos($f, "HA role changed\n\nNode: .252\nRole: BACKUP\n\nEffective at 10:00.") === 0,
    'failover header rows are compact and the trailing paragraph is separated');

/* 5. scan result: paragraph plus rows, script and remote image stripped */
$scan = "<p>3 open ports found.</p><table><tr><td>Host:</td><td>192.0.2.5</td></tr><tr><td>Ports:</td><td>22, 80, 443</td></tr></table>"
      . "<img src=\"http://tracker.invalid/pixel.png\"><script>alert(1)</script>";
$r = conv($scan);
check(strpos($r, "3 open ports found.\n\nHost: 192.0.2.5\nPorts: 22, 80, 443") === 0, 'scan rows compact');
check(strpos($r, 'tracker.invalid') === false && strpos($r, 'alert(1)') === false, 'remote image and script removed');

/* 6. entities decode once; plain text bodies are never converted */
check(strpos(conv('<p>&amp;amp; &lt;x&gt; &amp; &quot;q&quot;</p>'), '&amp; <x> & "q"') === 0, 'entities decode exactly once');
$plain = "Server:\t value\n\nline two";
check(EmailLog::sanitiseNewlines($plain) === $plain, 'plain-text bodies are left unchanged');

/* 7. content above the body is not stripped because it resembles metadata */
$dup = conv("<p>Server: OPNsense.home.arpa</p><p>Server: a different server</p>");
check(substr_count($dup, 'Server:') === 2, 'repeated label-like text is preserved');

echo $fails === 0 ? "EMAIL_LOG_CONVERSION_FIXTURES=PASS\n" : "EMAIL_LOG_CONVERSION_FIXTURES=FAIL ($fails)\n";
exit($fails === 0 ? 0 : 1);

<?php
// Read a root-only credential file and execute exactly one authenticated acceptance check.
// The file contains user=, key=, secret=; it is never printed. A missing file or a malformed
// response exits non-zero, so an unavailable check cannot become a PASS.
$check = $argv[1] ?? '';
$file = getenv('DM_ACCEPTANCE_CREDENTIALS') ?: '/root/dm-acceptance/account.env';
if (!in_array($check, ['authenticated-search', 'authenticated-message', 'authenticated-csv', 'mutation-denial'], true)) {
    fwrite(STDERR, "unknown check\n"); exit(2);
}
if (!is_file($file) || (fileperms($file) & 0777) !== 0600) { fwrite(STDERR, "credential file missing or not 0600\n"); exit(1); }
$c = [];
foreach (file($file, FILE_IGNORE_NEW_LINES) as $line) {
    if (strpos($line, '=') !== false) { [$k, $v] = explode('=', $line, 2); $c[$k] = $v; }
}
if (empty($c['key']) || empty($c['secret'])) { fwrite(STDERR, "credential file incomplete\n"); exit(1); }
function call($path, $post, $c) {
    $ch = curl_init('https://127.0.0.1/api/devicemonitor/emaillog/' . $path);
    curl_setopt_array($ch, [CURLOPT_POST => true, CURLOPT_POSTFIELDS => http_build_query($post),
        CURLOPT_RETURNTRANSFER => true, CURLOPT_SSL_VERIFYPEER => false, CURLOPT_SSL_VERIFYHOST => 0,
        CURLOPT_USERPWD => $c['key'] . ':' . $c['secret'], CURLOPT_HTTPAUTH => CURLAUTH_BASIC,
        CURLOPT_TIMEOUT => 15]);
    $body = curl_exec($ch);
    $code = (int)curl_getinfo($ch, CURLINFO_RESPONSE_CODE);
    curl_close($ch);
    return [$code, $body];
}
if ($check === 'authenticated-search') {
    [$status, $body] = call('search', ['page' => 1, 'per_page' => 50], $c);
    $d = json_decode($body, true);
    exit($status === 200 && ($d['result'] ?? '') === 'ok' && count($d['rows'] ?? []) > 0 ? 0 : 1);
}
if ($check === 'authenticated-csv') {
    [$status, $body] = call('exportcsv', ['visibility' => 'active'], $c);
    $d = json_decode($body, true);
    exit($status === 200 && ($d['result'] ?? '') === 'ok' && substr_count((string)($d['csv'] ?? ''), "\n") >= 1 ? 0 : 1);
}
if ($check === 'authenticated-message') {
    [$status, $body] = call('search', ['page' => 1, 'per_page' => 1], $c);
    $d = json_decode($body, true);
    $id = $d['rows'][0]['event_id'] ?? '';
    if ($status !== 200 || $id === '') { exit(1); }
    [$status, $body] = call('message', ['event_id' => $id], $c);
    $d = json_decode($body, true);
    exit($status === 200 && ($d['result'] ?? '') === 'ok' ? 0 : 1);
}
// Mutation denial: a nonexistent id cannot select or alter a genuine record. A validation failure
// is expected; a success would be a failure of the privilege boundary.
foreach (['delete', 'restore', 'bulkdelete', 'deleteall', 'restorebulk'] as $action) {
    [$status, $body] = call($action, ['event_id' => str_repeat('0', 32), 'ids' => str_repeat('0', 32), 'confirm' => '1'], $c);
    $d = json_decode($body, true);
    if ($status === 200 && ($d['result'] ?? '') === 'failed') { continue; }
    exit(1);
}
exit(0);

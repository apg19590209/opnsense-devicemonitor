<?php
// Execute one authenticated, read-only Device Monitor acceptance check on the local node.
//
// The peer-read endpoints are read-only and are served with full TLS verification by a custom
// client that never disables certificate checks. The helper never prints the credential.
$check = $argv[1] ?? '';
$file = getenv('DM_ACCEPTANCE_CREDENTIALS') ?: '/root/dm-acceptance/account.env';
if (!in_array($check, ['authenticated-search', 'authenticated-message', 'authenticated-csv', 'mutation-denial'], true)) {
    fwrite(STDERR, "unknown check\n"); exit(2);
}
if (!is_file($file) || is_link($file) || (fileperms($file) & 0777) !== 0600 || fileowner($file) !== 0) {
    fwrite(STDERR, "credential file missing, linked, not root-owned, or not 0600\n"); exit(1);
}
$c = [];
foreach (file($file, FILE_IGNORE_NEW_LINES) as $line) {
    if (strpos($line, '=') !== false) { [$k, $v] = explode('=', $line, 2); $c[$k] = $v; }
}
if (empty($c['key']) || empty($c['secret'])) { fwrite(STDERR, "credential file incomplete\n"); exit(1); }

function local_call($path, array $post, array $c)
{
    $host = getenv('DM_ACCEPTANCE_HOST') ?: 'OPNsense.home.arpa';
    $ch = curl_init('https://' . $host . '/api/devicemonitor/emaillog/' . $path);
    if ($ch === false) { return [0, false]; }
    curl_setopt_array($ch, [
        CURLOPT_POST => true,
        CURLOPT_POSTFIELDS => http_build_query($post),
        CURLOPT_RETURNTRANSFER => true,
        CURLOPT_USERPWD => $c['key'] . ':' . $c['secret'],
        CURLOPT_HTTPAUTH => CURLAUTH_BASIC,
        CURLOPT_HTTPHEADER => ['Accept: application/json', 'Content-Type: application/x-www-form-urlencoded'],
        CURLOPT_CONNECTTIMEOUT => 5,
        CURLOPT_TIMEOUT => 15,
        CURLOPT_SSL_VERIFYPEER => true,
        CURLOPT_SSL_VERIFYHOST => 2,
    ]);
    $body = curl_exec($ch);
    $code = (int)curl_getinfo($ch, CURLINFO_RESPONSE_CODE);
    curl_close($ch);
    return [$code, $body];
}

if ($check === 'authenticated-search') {
    [$status, $body] = local_call('search', ['page' => 1, 'per_page' => 50], $c);
    $d = json_decode((string)$body, true);
    exit($status === 200 && ($d['result'] ?? '') === 'ok' && count($d['rows'] ?? []) > 0 ? 0 : 1);
}
if ($check === 'authenticated-csv') {
    [$status, $body] = local_call('exportcsv', ['visibility' => 'active'], $c);
    $d = json_decode((string)$body, true);
    exit($status === 200 && ($d['result'] ?? '') === 'ok' && trim((string)($d['csv'] ?? '')) !== '' ? 0 : 1);
}
if ($check === 'authenticated-message') {
    [$status, $body] = local_call('search', ['page' => 1, 'per_page' => 1], $c);
    $d = json_decode((string)$body, true);
    $id = $d['rows'][0]['event_id'] ?? '';
    if ($status !== 200 || $id === '') { exit(1); }
    [$status, $body] = local_call('message', ['event_id' => $id], $c);
    $d = json_decode((string)$body, true);
    exit($status === 200 && ($d['result'] ?? '') === 'ok' ? 0 : 1);
}
// A nonexistent id exercises denial without selecting or modifying a genuine record. The API
// returns a validation failure for a null id; a successful mutation is a failure of this check.
foreach (['delete', 'restore', 'bulkdelete', 'deleteall', 'restorebulk'] as $action) {
    [$status, $body] = local_call($action, [
        'event_id' => str_repeat('0', 32), 'ids' => str_repeat('0', 32), 'confirm' => '1'], $c);
    $d = json_decode((string)$body, true);
    if ($status === 200 && ($d['result'] ?? '') === 'failed') { continue; }
    exit(1);
}
exit(0);

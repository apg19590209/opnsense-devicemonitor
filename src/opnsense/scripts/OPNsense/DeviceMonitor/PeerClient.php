<?php
/**
 * Read-only client for an authorised peer's Device Monitor email log.
 *
 * Security rules, all enforced here rather than by the caller:
 *   * only an https:// URL with a host is accepted — no arbitrary destinations,
 *     no query or fragment, no userinfo;
 *   * the peer URL exposes only the email-log API paths this code appends;
 *   * TLS verification is mandatory and can be pinned to a supplied CA bundle,
 *     which OPNsense stores for the operator; verification is never disabled;
 *   * credentials are sent as Basic auth headers and are never logged, echoed
 *     into results, or embedded in error text;
 *   * every request is bounded by a connect/total timeout and a response size cap.
 *
 * A peer that is unreachable, slow, misconfigured or returns junk produces a
 * structured "unavailable" result, never an exception and never a partial row set
 * pretending to be complete.
 */

namespace OPNsense\DeviceMonitor;

class PeerClient
{
    const MAX_RESPONSE_BYTES = 4 * 1024 * 1024;
    const DEFAULT_TIMEOUT = 8;

    private $url;
    private $apiKey;
    private $apiSecret;
    private $caPem;
    private $timeout;

    public function __construct(array $settings)
    {
        $this->url = rtrim((string)($settings['url'] ?? ''), '/');
        $this->apiKey = (string)($settings['api_key'] ?? '');
        $this->apiSecret = (string)($settings['api_secret'] ?? '');
        $this->caPem = (string)($settings['ca_pem'] ?? '');
        $this->timeout = max(2, min(30, (int)($settings['timeout'] ?? self::DEFAULT_TIMEOUT)));
    }

    /** Validate settings; returns a list of human-readable problems. */
    public static function validate(array $settings)
    {
        $errors = [];
        $raw = trim((string)($settings['url'] ?? ''));
        if ($raw === '') {
            $errors[] = 'Peer URL is required.';
        } else {
            $parts = parse_url($raw);
            if (!is_array($parts) || !isset($parts['scheme'], $parts['host'])) {
                $errors[] = 'Peer URL must be an absolute https:// URL.';
            } elseif (strtolower($parts['scheme']) !== 'https') {
                $errors[] = 'Peer URL must use https:// — plain HTTP is refused.';
            } elseif (isset($parts['user']) || isset($parts['pass'])) {
                $errors[] = 'Peer URL must not embed credentials.';
            } elseif (isset($parts['query']) || isset($parts['fragment'])) {
                $errors[] = 'Peer URL must not contain a query or fragment.';
            }
        }
        if (trim((string)($settings['api_key'] ?? '')) === '' || trim((string)($settings['api_secret'] ?? '')) === '') {
            $errors[] = 'A peer API key and secret are required.';
        }
        $ca = (string)($settings['ca_pem'] ?? '');
        if ($ca !== '' && strpos($ca, 'BEGIN CERTIFICATE') === false) {
            $errors[] = 'The CA must be PEM certificate content.';
        }
        return $errors;
    }

    /** True only when the peer is configured well enough to contact. */
    public static function configured(array $settings)
    {
        return empty(self::validate($settings));
    }

    private function unavailable($reason)
    {
        return ['available' => false, 'reason' => $reason];
    }

    private function call($path, array $post, $expect = 'json')
    {
        if ($this->url === '') {
            return $this->unavailable('No peer is configured.');
        }
        $url = $this->url . $path;
        $ch = @curl_init($url);
        if ($ch === false) {
            return $this->unavailable('HTTP client unavailable.');
        }
        $headers = ['Accept: application/json', 'Content-Type: application/x-www-form-urlencoded'];
        $caFile = null;
        if ($this->caPem !== '') {
            $caFile = tempnam(sys_get_temp_dir(), 'dmca');
            @file_put_contents($caFile, $this->caPem);
            curl_setopt($ch, CURLOPT_CAINFO, $caFile);
        }
        curl_setopt_array($ch, [
            CURLOPT_POST => true,
            CURLOPT_POSTFIELDS => http_build_query($post),
            CURLOPT_HTTPHEADER => $headers,
            CURLOPT_USERPWD => $this->apiKey . ':' . $this->apiSecret,
            CURLOPT_HTTPAUTH => CURLAUTH_BASIC,
            CURLOPT_RETURNTRANSFER => true,
            CURLOPT_FOLLOWLOCATION => false,
            CURLOPT_CONNECTTIMEOUT => $this->timeout,
            CURLOPT_TIMEOUT => $this->timeout,
            CURLOPT_SSL_VERIFYPEER => true,
            CURLOPT_SSL_VERIFYHOST => 2,
        ]);
        $body = curl_exec($ch);
        $code = (int)curl_getinfo($ch, CURLINFO_RESPONSE_CODE);
        $error = curl_error($ch);
        curl_close($ch);
        if ($caFile !== null) {
            @unlink($caFile);
        }
        if ($body === false) {
            /* The reason is deliberately generic: it never includes the URL with
             * credentials nor any transport detail beyond the failure class. */
            return $this->unavailable('Peer request failed: ' . ($error !== '' ? 'transport error' : 'no response'));
        }
        if (strlen($body) > self::MAX_RESPONSE_BYTES) {
            return $this->unavailable('Peer response exceeded the size limit.');
        }
        if ($code === 401 || $code === 403) {
            return $this->unavailable('Peer rejected the configured credentials.');
        }
        if ($code !== 200) {
            return $this->unavailable('Peer returned HTTP ' . $code . '.');
        }
        if ($expect === 'json') {
            $data = json_decode($body, true);
            if (!is_array($data) || ($data['result'] ?? '') !== 'ok') {
                return $this->unavailable('Peer returned an unusable response.');
            }
            return ['available' => true, 'data' => $data];
        }
        return ['available' => true, 'data' => $body];
    }

    /** One page of the peer's log. */
    public function search(array $filters, $limit, $offset)
    {
        $result = $this->call('/api/devicemonitor/emaillog/peerpage', [
            'page' => max(1, (int)floor($offset / max(1, $limit)) + 1),
            'per_page' => max(1, min(200, (int)$limit)),
            'type' => (string)($filters['type'] ?? ''),
            'status' => (string)($filters['status'] ?? ''),
            'search' => (string)($filters['search'] ?? ''),
        ]);
        if (!$result['available']) {
            return $result;
        }
        $rows = $result['data']['rows'] ?? [];
        if (!is_array($rows)) {
            return $this->unavailable('Peer returned an unusable row set.');
        }
        return ['available' => true, 'rows' => $rows];
    }

    /** One message with its content and timeline. */
    public function message($eventId)
    {
        if (!preg_match('/^[0-9a-f]{32}$/', (string)$eventId)) {
            return $this->unavailable('Invalid peer message reference.');
        }
        $result = $this->call('/api/devicemonitor/emaillog/peermessage', ['event_id' => $eventId]);
        if (!$result['available']) {
            return $result;
        }
        return ['available' => true, 'message' => $result['data']['message'] ?? null];
    }
}

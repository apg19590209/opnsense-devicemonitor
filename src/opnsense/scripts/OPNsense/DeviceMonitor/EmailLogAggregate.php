<?php
/**
 * Combine the local email log with an optional authorised peer.
 *
 * The result is explicit about scope: it carries the local rows, the peer rows
 * that were actually received, and a peer state of "unavailable" with a reason
 * when the peer could not be read. A failed peer never silently shrinks the list
 * and never produces an error page — the local half stays usable.
 *
 * Sorting, filtering and pagination are applied to the combined set, so the order
 * is stable across nodes rather than local-first concatenation.
 */

namespace OPNsense\DeviceMonitor;

class EmailLogAggregate
{
    const MAX_PAGE = 200;

    public static function nodeTag(array $facts, $scope)
    {
        return [
            'scope' => $scope,
            'node_id' => (string)($facts['host'] ?? $facts['node_id'] ?? ''),
            'node_ip' => (string)($facts['ip'] ?? $facts['node_ip'] ?? ''),
            'role' => (string)($facts['role'] ?? ''),
        ];
    }

    /** Tag every row with which node it came from, so the UI can never mix them up. */
    public static function tagRows(array $rows, array $tag)
    {
        $out = [];
        foreach ($rows as $row) {
            $row['scope'] = $tag['scope'];
            $row['origin_node'] = $tag['node_id'];
            $row['origin_ip'] = $tag['node_ip'] !== '' ? $tag['node_ip'] : (string)($row['node_ip'] ?? '');
            $out[] = $row;
        }
        return $out;
    }

    /** Newest first, with a stable tiebreak so paging is deterministic. */
    public static function sort(array $rows)
    {
        usort($rows, function ($a, $b) {
            $byTime = strcmp((string)($b['created_utc'] ?? ''), (string)($a['created_utc'] ?? ''));
            if ($byTime !== 0) {
                return $byTime;
            }
            return strcmp((string)($a['event_id'] ?? ''), (string)($b['event_id'] ?? ''));
        });
        return $rows;
    }

    public static function paginate(array $rows, $limit, $offset)
    {
        $limit = max(1, min(self::MAX_PAGE, (int)$limit));
        $offset = max(0, (int)$offset);
        return [
            'rows' => array_slice($rows, $offset, $limit),
            'total' => count($rows),
            'limit' => $limit,
            'offset' => $offset,
        ];
    }

    /**
     * @param array       $localRows rows from the local database
     * @param array|null  $peer      ['available'=>bool, 'rows'=>array, 'reason'=>string]
     */
    public static function combine(array $localRows, ?array $peer, array $localTag, array $peerTag, $limit, $offset)
    {
        $rows = self::tagRows($localRows, $localTag);
        $peerState = ['status' => 'disabled', 'reason' => 'Peer is not configured.', 'rows' => 0];
        if ($peer !== null) {
            if (!empty($peer['available'])) {
                $peerRows = self::tagRows((array)($peer['rows'] ?? []), $peerTag);
                $rows = array_merge($rows, $peerRows);
                $peerState = ['status' => 'available', 'reason' => '', 'rows' => count($peerRows)];
            } else {
                $peerState = [
                    'status' => 'unavailable',
                    'reason' => (string)($peer['reason'] ?? 'Peer unavailable.'),
                    'rows' => 0,
                ];
            }
        }
        $sorted = self::sort($rows);
        $page = self::paginate($sorted, $limit, $offset);
        $page['peer'] = $peerState;
        $page['partial'] = $peerState['status'] === 'unavailable';
        return $page;
    }
}

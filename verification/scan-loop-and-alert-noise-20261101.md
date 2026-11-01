# DeviceMonitor patch — 2026-11-01

Patched file: /usr/local/opnsense/scripts/OPNsense/DeviceMonitor/scan_network.py
Originals and patched copies: this directory (scan_network.py, scan_network.py.fixed)

md5
    original aa0ab032ac8433784bb5ac9ddade3b5b
    patched  b3d9ced30a904883e7549564a68f4ea7

## 1. SQLite contention — root cause of "Scan failed with code 1" every cycle

The deferred Nmap-history writer thread held its write transaction while the main
thread updated the targeted-scan queue with the driver's 5 s default timeout. The
resulting `sqlite3.OperationalError: database is locked` aborted full_scan() before
`nmap_scan_attempts`/`nmap_next_attempt` were persisted, so the retry backoff never
engaged and the head of the queue (ordered by first_seen) was rescanned on every
300 s cycle, indefinitely.

    - connect_db() applies timeout=30 s + PRAGMA busy_timeout=30000 and is patched
      onto sqlite3.connect for the whole process
    - flush_db_writes() runs before each queue UPDATE
    - the per-device drain is wrapped in try/except, so a failed scan still
      persists its backoff (15 m, 1 h, 6 h, 24 h, then retired)

## 2. Visibility priming no longer looks like a scan to endpoints

prime_selected_interface_visibility() sent one ICMP echo to every address of the
monitored /24 on every cycle (254 probes / 5 min from each node).

    - rate limited to VISIBILITY_PRIME_MIN_INTERVAL (3600 s) via
      /var/run/devicemonitor-visibility-prime.state
    - addresses observed by hostwatch within VISIBILITY_PRIME_FRESH_WINDOW
      (3600 s) are not probed
    - skipped entirely on a CARP BACKUP node

## 3. Targeted scans are drained only by the node that owns the segment

The drain block is gated on service_observation_allowed() (CARP MASTER). Queued
rows on a standby stay queued and drain normally after a failover, so a standby
no longer duplicates scans or scan emails.

## 4. Scan emails are state-change only

The scan still runs and its history row is still written, but the email is sent
only when the open-service inventory differs from the newest successful scan
recorded for that MAC (scan_state_changed() / previous_scan_state_signature()).

    suppressed: email_sent=0 in nmap_scan_history and
                "[NMAP] Scan result unchanged for <ip>; email suppressed" in the log
    sent:       first scan of a device, or any change to ports/product/version

Service alert emails already dedupe on state transitions (service_alert_pending
plus the confirmation hold), so they were left unchanged.

## 5. A new MAC at a known address is an identity change, not a new device

A device that randomises its Wi-Fi MAC keeps its DHCP address, so the new MAC
was announced as a brand new device (new-device mail plus a queued targeted
scan) every time it rotated. That is now detected before a device is announced:

    build_ip_owner_index()   address -> (mac, last_seen) snapshot taken before
                             the device loop writes anything
    detect_mac_rotation()    returns the displaced owner when `mac` takes over
                             an address owned by a different device

Rules
    randomised (locally administered) MAC  -> always a rotation
    vendor (globally administered) MAC     -> rotation only while the previous
                                              owner was seen within
                                              MAC_ROTATION_WINDOW_HOURS (168 h)

Effect: no new-device email, no webhook, and no targeted scan for a rotation.
The device is still recorded and an IP_IDENTITY_CHANGED (high) event is written
with details.source = "mac_rotation", the previous MAC and whether the new MAC
is randomised, so it appears in the identity view. The cycle summary now reads
"New devices: N, MAC rotations: M, Online: x/y", and the log carries

    [IDENTITY] <ip> reassigned from <old> to <new> (randomised MAC): MAC rotation, not a new device

An address reused after its previous owner has been gone longer than the window
is still announced as a new device, so a replaced laptop is not hidden.

## Rollback

    install -m 755 -o root -g wheel /root/dm-backup-*/scan_network.py \
        /usr/local/opnsense/scripts/OPNsense/DeviceMonitor/scan_network.py
    rm -f /usr/local/opnsense/scripts/OPNsense/DeviceMonitor/__pycache__/scan_network*.pyc
    service devicemonitor restart

No configuration keys were added, so a settings save from the GUI cannot undo any
of this. A plugin package upgrade will overwrite scan_network.py: re-apply this
patch or diff the shipped file against scan_network.py.fixed.

#!/bin/sh
# Run supported, non-mutating acceptance checks against the CURRENT host and write their
# generated evidence. This does not create acceptance; record-acceptance.sh does that only from
# the resulting execution-ledger records.
#
#   run-host-checks.sh --stage .23|.252|.253 --source SHA --bundle SHA256 --out EVIDENCE
#
# Each result is produced by executing a check command. A failure is recorded as FAIL and makes
# the command exit non-zero; missing credentials or an unavailable check are FAIL, never skipped.
set -eu
LC_ALL=C
export LC_ALL
STAGE=
SOURCE=
BUNDLE=
OUT=
while [ "$#" -gt 0 ]; do
    case "$1" in
        --stage) STAGE=$2; shift 2 ;;
        --source) SOURCE=$2; shift 2 ;;
        --bundle) BUNDLE=$2; shift 2 ;;
        --out) OUT=$2; shift 2 ;;
        *) echo "ABORT: unknown argument $1" >&2; exit 2 ;;
    esac
done
case "$STAGE" in .23|.252|.253) : ;; *) echo 'ABORT: invalid stage' >&2; exit 2 ;; esac
[ -n "$SOURCE" ] && [ -n "$BUNDLE" ] && [ -n "$OUT" ] || { echo 'usage: --stage --source --bundle --out' >&2; exit 2; }
mkdir -p "$(dirname "$OUT")"
: > "$OUT"
failure=0
run() {
    name=$1
    shift
    rc=0
    "$@" >/tmp/dm-host-check.log 2>&1 || rc=$?
    if [ "$rc" = 0 ]; then
        result=PASS
        note="exit=0"
    else
        result=FAIL
        note="exit=$rc"
        failure=1
    fi
    printf '%s %s %s\n' "$name" "$result" "$note" >> "$OUT"
}
db_check() { python3 - <<'PY'
import sqlite3
for f in ('devices.db','email_log.db'):
 c=sqlite3.connect('file:/var/db/devicemonitor/'+f+'?mode=ro',uri=True)
 assert c.execute('pragma integrity_check').fetchone()[0]=='ok'
 assert not c.execute('pragma foreign_key_check').fetchall()
 c.close()
PY
}
records_check() { python3 - <<'PY'
import sqlite3
c=sqlite3.connect('file:/var/db/devicemonitor/email_log.db?mode=ro',uri=True)
assert c.execute("select count(*) from email_log where deleted_utc=''").fetchone()[0] > 0
c.close()
PY
}
settings_check() { python3 -m json.tool /var/db/devicemonitor/config.json >/dev/null; }
installed_check() { python3 - <<'PY'
import re
rows=[l for l in open('/var/db/devicemonitor/installed-manifest.txt') if l and not l.startswith('#')]
assert rows and all(re.fullmatch('[0-9a-f]{64} /.*', l.strip()) for l in rows)
PY
}
daemon_check() { pgrep -f '^/usr/local/bin/python3 /usr/local/opnsense/scripts/OPNsense/DeviceMonitor/monitor_daemon.py$' >/dev/null; }
catalogue_check() { python3 - <<'PY'
import gettext
for lang in ('ru_RU','de_DE'):
 with open(f'/usr/local/share/locale/{lang}/LC_MESSAGES/OPNsense.mo','rb') as f: gettext.GNUTranslations(f)._catalog
PY
}
role_check() { case "$STAGE" in .252) ifconfig | grep -q 'carp: BACKUP' ;; .253) ifconfig | grep -q 'carp: MASTER' ;; *) true ;; esac; }
certificate_check() { python3 - <<'PY'
import ssl,socket
s=ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT); s.check_hostname=False; s.verify_mode=ssl.CERT_NONE
with socket.create_connection(('127.0.0.1',443),5) as sock:
 with s.wrap_socket(sock,server_hostname='OPNsense.home.arpa') as t: assert t.getpeercert(binary_form=True)
PY
}
peer_check() { php -r 'require_once("/usr/local/opnsense/scripts/OPNsense/DeviceMonitor/PeerClient.php"); $c=json_decode(file_get_contents("/var/db/devicemonitor/config.json"),true); $p=["url"=>$c["email_log_peer_url"],"api_key"=>$c["email_log_peer_api_key"],"api_secret"=>$c["email_log_peer_api_secret"],"ca_pem"=>$c["email_log_peer_ca_pem"],"timeout"=>8]; $r=(new \\OPNsense\\DeviceMonitor\\PeerClient($p))->search([],50,0); exit(empty($r["available"])?1:0);'; }
auth_check() { php /root/src/opnsense-devicemonitor-upstream/release/acceptance-check.php "$1" || return 1; }
run installed-hashes installed_check
run records records_check
run database-integrity db_check
run settings settings_check
run certificates certificate_check
run role role_check
run peer peer_check
run daemon daemon_check
run catalogue catalogue_check
for check in authenticated-search authenticated-message authenticated-csv mutation-denial; do
    run "$check" auth_check "$check"
done
[ "$failure" = 0 ] || exit 1

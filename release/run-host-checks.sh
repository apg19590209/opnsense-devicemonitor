#!/bin/sh
# Execute the supported, non-mutating acceptance checks for one stage and append their results
# to the execution ledger. This does not create acceptance; record-acceptance.sh does that only
# after every required check has its own successful record.
#
#   run-host-checks.sh --stage .23|.252|.253 --source SHA --bundle SHA256 [--check credentials DB...]
set -eu
LC_ALL=C
export LC_ALL
STAGE=
SOURCE=
BUNDLE=
while [ "$#" -gt 0 ]; do
    case "$1" in
        --stage) STAGE=$2; shift 2 ;;
        --source) SOURCE=$2; shift 2 ;;
        --bundle) BUNDLE=$2; shift 2 ;;
        *) echo "ABORT: unknown argument $1" >&2; exit 2 ;;
    esac
done
case "$STAGE" in .23) HOST=192.168.20.23;; .252) HOST=192.168.20.252;; .253) HOST=192.168.20.253;; *) echo 'ABORT: invalid stage' >&2; exit 2;; esac
LEDGER=${DM_LEDGER:-/root/src/opnsense-devicemonitor-upstream/release/execution-ledger.jsonl}
run() {
    NAME=$1
    shift
    if "$@" >/tmp/dm-host-check.out 2>&1; then RESULT=PASS; else RESULT=FAIL; fi
    python3 /root/src/opnsense-devicemonitor-upstream/release/execution-ledger.py record \
        --ledger "$LEDGER" --stage "$STAGE" --host "$HOST" --source "$SOURCE" --bundle "$BUNDLE" \
        --phase own-check --checks "$NAME" --result "$RESULT"
    printf '%s=%s\n' "$NAME" "$RESULT"
    [ "$RESULT" = PASS ]
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
installed_check() { test -s /var/db/devicemonitor/installed-manifest.txt; }
daemon_check() { pgrep -f '^/usr/local/bin/python3 /usr/local/opnsense/scripts/OPNsense/DeviceMonitor/monitor_daemon.py$' >/dev/null; }
catalogue_check() { python3 - <<'PY'
import gettext
for lang in ('ru_RU','de_DE'):
 with open(f'/usr/local/share/locale/{lang}/LC_MESSAGES/OPNsense.mo','rb') as f: gettext.GNUTranslations(f)._catalog
PY
}
role_check() { case "$STAGE" in .252) ifconfig | grep -q 'carp: BACKUP' ;; .253) ifconfig | grep -q 'carp: MASTER' ;; *) true ;; esac; }
certificate_check() { test -s /conf/config.xml; }
peer_check() { php -r 'require_once("/usr/local/opnsense/scripts/OPNsense/DeviceMonitor/PeerClient.php"); $c=json_decode(file_get_contents("/var/db/devicemonitor/config.json"),true); $p=["url"=>$c["email_log_peer_url"],"api_key"=>$c["email_log_peer_api_key"],"api_secret"=>$c["email_log_peer_api_secret"],"ca_pem"=>$c["email_log_peer_ca_pem"],"timeout"=>8]; $r=(new \\OPNsense\\DeviceMonitor\\PeerClient($p))->search([],50,0); exit(empty($r["available"])?1:0);'; }
run installed-hashes installed_check
run records records_check
run database-integrity db_check
run settings settings_check
run daemon daemon_check
run catalogue catalogue_check
run certificates certificate_check
run role role_check
run peer peer_check
if [ -f /root/dm-acceptance/api-check.php ]; then
    for name in authenticated-search authenticated-message authenticated-csv mutation-denial; do
        if php /root/dm-acceptance/api-check.php "$name" >/tmp/dm-auth-check.out 2>&1; then RESULT=PASS; else RESULT=FAIL; fi
        python3 /root/src/opnsense-devicemonitor-upstream/release/execution-ledger.py record --ledger "$LEDGER" --stage "$STAGE" --host "$HOST" --source "$SOURCE" --bundle "$BUNDLE" --phase own-check --checks "$name" --result "$RESULT"
        printf '%s=%s\n' "$name" "$RESULT"
    done
else
    for name in authenticated-search authenticated-message authenticated-csv mutation-denial; do
        python3 /root/src/opnsense-devicemonitor-upstream/release/execution-ledger.py record --ledger "$LEDGER" --stage "$STAGE" --host "$HOST" --source "$SOURCE" --bundle "$BUNDLE" --phase own-check --checks "$name" --result FAIL
        printf '%s=FAIL (no authenticated test credential)\n' "$name"
    done
fi

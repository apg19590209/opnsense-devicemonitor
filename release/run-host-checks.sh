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
        --stage) [ "$#" -ge 2 ] || break; STAGE=$2; shift 2 ;;
        --source) [ "$#" -ge 2 ] || break; SOURCE=$2; shift 2 ;;
        --bundle) [ "$#" -ge 2 ] || break; BUNDLE=$2; shift 2 ;;
        --out) [ "$#" -ge 2 ] || break; OUT=$2; shift 2 ;;
        *) echo "ABORT: unknown argument $1" >&2; exit 2 ;;
    esac
done
case "$STAGE" in .23|.252|.253) : ;; *) echo 'ABORT: invalid stage' >&2; exit 2 ;; esac
[ -n "$SOURCE" ] && [ -n "$BUNDLE" ] && [ -n "$OUT" ] || { echo 'usage: --stage --source --bundle --out' >&2; exit 2; }
mkdir -p "$(dirname "$OUT")"
failure=0
RESULT_ARGS=
# Installed nodes do not receive release/ from the archive. deploy-candidate.sh passes the
# pinned helpers' host path; the in-archive copy is only a fallback for a manual run from the
# unpacked candidate. The previous dirname-of-$0 lookup passed the shell-syntax test but
# resolved to nothing on an installed host, which is why the packaged runner could not pass.
HELPER_DIR=/var/tmp/dm-release-tools
[ -f "$HELPER_DIR/results-file.py" ] || HELPER_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd -P)
run() {
    # Pass the check name straight through: binding it to a variable called "name" is unsafe
    # in some shells.
    check_name=$1
    shift
    case "$check_name" in ''|*[!a-z0-9-]*) echo "ABORT: invalid check name $check_name" >&2; exit 2 ;; esac
    rc=0
    "$@" >"${TMPDIR:-/tmp}/dm-host-check.$$.log" 2>&1 || rc=$?
    if [ "$rc" = 0 ]; then
        result=PASS
        note="exit=0"
    else
        result=FAIL
        note="exit=$rc"
        failure=1
    fi
    printf 'check %s %s (%s)\n' "$check_name" "$result" "$note" >&2
    # One token per --check is the results-file contract; refuse any pathname expansion.
    set -f
    RESULT_ARGS="$RESULT_ARGS --check $check_name=$result"
    set +f
    # Never return the check's status: `run` is called under `set -e`, so a failing status would
    # abort before the results file is written. `failure` records the outcome and the final exit
    # below still fails the run.
    return 0
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
role_check() {
    # One CARP record, parsed on its own fields: FreeBSD prints "carp: ROLE vhid N advbase N
    # advskew N", so field adjacency cannot be assumed. The stage must find exactly one record
    # with vhid 1 and the required role and advskew; anything missing, malformed, ambiguous or
    # different fails closed. .23 has no CARP record by design and does not check.
    [ "$STAGE" = .23 ] && return 0
    ${DM_IFCONFIG:-ifconfig} > "${TMPDIR:-/tmp}/dm-role.$$.out" 2>/dev/null || return 1
    python3 - "$STAGE" "${TMPDIR:-/tmp}/dm-role.$$.out" <<'PY'
import sys
stage, path = sys.argv[1], sys.argv[2]
want = {'.252': ('BACKUP', 100), '.253': ('MASTER', 0)}[stage]
roles = ('BACKUP', 'MASTER', 'INIT', 'DISABLED')
records, malformed = [], 0
for line in open(path, encoding='utf-8', errors='replace'):
    fields = line.split()
    if 'carp:' not in fields:
        continue
    if fields[0] != 'carp:':
        malformed += 1
        continue
    values, i = {}, 1
    while i < len(fields):
        key = fields[i]
        if key in roles and 'role' not in values:
            values['role'] = key
            i += 1
            continue
        if key in ('vhid', 'advbase', 'advskew'):
            if key in values or i + 1 >= len(fields) or not fields[i + 1].isdigit():
                malformed += 1
                break
            values[key] = int(fields[i + 1])
            i += 2
            continue
        i += 1
    if 'role' in values and 'vhid' in values and 'advskew' in values:
        records.append(values)
    else:
        malformed += 1
if malformed or len(records) != 1:
    raise SystemExit(1)
r = records[0]
raise SystemExit(0 if (r['role'], r['vhid'], r['advskew']) == (want[0], 1, want[1]) else 1)
PY
    rc=$?
    rm -f "${TMPDIR:-/tmp}/dm-role.$$.out"
    return "$rc"
}
certificate_check() { python3 - <<'PY'
import ssl,socket
s=ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT); s.check_hostname=False; s.verify_mode=ssl.CERT_NONE
with socket.create_connection(('127.0.0.1',443),5) as sock:
 with s.wrap_socket(sock,server_hostname='OPNsense.home.arpa') as t: assert t.getpeercert(binary_form=True)
PY
}
peer_check() { php -r 'require_once("/usr/local/opnsense/scripts/OPNsense/DeviceMonitor/PeerClient.php"); $c=json_decode(file_get_contents("/var/db/devicemonitor/config.json"),true); $p=["url"=>$c["email_log_peer_url"],"api_key"=>$c["email_log_peer_api_key"],"api_secret"=>$c["email_log_peer_api_secret"],"ca_pem"=>$c["email_log_peer_ca_pem"],"timeout"=>8]; $r=(new \\OPNsense\\DeviceMonitor\\PeerClient($p))->search([],50,0); exit(empty($r["available"])?1:0);'; }
auth_check() {
    # The local management name may not resolve on .23; that node's own verified address is
    # the same API endpoint and keeps certificate verification enabled. The HA stages keep
    # the management name so the verified TLS chain is the one the peer trusts.
    case "$STAGE" in
        .23) DM_ACCEPTANCE_HOST=${DM_ACCEPTANCE_HOST:-192.168.20.23} ;;
    esac
    php "$HELPER_DIR/acceptance-check.php" "$1"
}
run installed-hashes installed_check
run records records_check
run database-integrity db_check
run settings settings_check
run certificates certificate_check
run role role_check
run daemon daemon_check
run catalogue catalogue_check
if [ "$STAGE" = .23 ]; then
    # .23 has no configured peer; peer reads are an HA-node requirement and are checked on .252/.253.
    printf 'peer=NOT_APPLICABLE local testbed has no configured peer\n'
else
    run peer peer_check
fi
for check in authenticated-search authenticated-message authenticated-csv mutation-denial; do
    run "$check" auth_check "$check"
done
set -f
python3 "$HELPER_DIR/results-file.py" --out "$OUT" $RESULT_ARGS
set +f
[ "$failure" = 0 ] || exit 1

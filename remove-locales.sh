#!/bin/sh
# Undo selected locale files from one guarded Device Monitor installation.
set -eu
export PATH=/sbin:/bin:/usr/sbin:/usr/bin:/usr/local/sbin:/usr/local/bin
EXPECTED_HOST=
SOURCE_BACKUP=
LANGUAGES=
CHECK_ONLY=0
SUPPORTED='en_US cs_CZ de_DE fr_FR es_ES it_IT pt_BR nl_NL ru_RU ja_JP zh_CN'
while [ "$#" -gt 0 ]; do
    case "$1" in
        --host) [ "$#" -ge 2 ] || exit 2; EXPECTED_HOST=$2; shift 2;;
        --backup) [ "$#" -ge 2 ] || exit 2; SOURCE_BACKUP=$2; shift 2;;
        --languages) [ "$#" -ge 2 ] || exit 2; LANGUAGES=$2; shift 2;;
        --check) CHECK_ONLY=1; shift;;
        *) echo "ABORT: unknown argument $1" >&2; exit 2;;
    esac
done
[ -n "$EXPECTED_HOST" ] && [ -n "$SOURCE_BACKUP" ] && [ -n "$LANGUAGES" ] || { echo 'ABORT: --host, --backup and --languages required' >&2; exit 2; }
case "$LANGUAGES" in
    all) SELECTED=$SUPPORTED;;
    none) echo 'ABORT: choose at least one locale' >&2; exit 2;;
    *)
        SELECTED=
        case "$LANGUAGES" in ,*|*,|*,,*) echo 'ABORT: empty locale entry' >&2; exit 2;; esac
        old_ifs=$IFS
        IFS=,
        for lang in $LANGUAGES; do
            case " $SUPPORTED " in *" $lang "*) :;; *) echo "ABORT: unsupported locale $lang" >&2; exit 2;; esac
            case " $SELECTED " in *" $lang "*) echo "ABORT: duplicate locale $lang" >&2; exit 2;; esac
            SELECTED="${SELECTED:+$SELECTED }$lang"
        done
        IFS=$old_ifs
        [ -n "$SELECTED" ] || exit 2
        ;;
esac
[ "$(id -u)" = 0 ] && [ "$(uname -s)" = FreeBSD ] && [ "$(/bin/hostname)" = "$EXPECTED_HOST" ] || { echo 'ABORT: host identity' >&2; exit 1; }
SOURCE_BACKUP=$(realpath "$SOURCE_BACKUP") || { echo 'ABORT: backup path' >&2; exit 1; }
case "$SOURCE_BACKUP" in
    /var/backups/devicemonitor/install-*)
        case "${SOURCE_BACKUP#/var/backups/devicemonitor/}" in
            */*) echo 'ABORT: nested backup path' >&2; exit 1;;
        esac
        ;;
    *) echo 'ABORT: backup outside install backup directory' >&2; exit 1;;
esac
[ -d "$SOURCE_BACKUP/files" ] && [ -f "$SOURCE_BACKUP/plan" ] && [ ! -L "$SOURCE_BACKUP/plan" ] || { echo 'ABORT: incomplete install backup' >&2; exit 1; }
stage=$(mktemp -d /tmp/dm_remove_locales.XXXXXX)
ROLLBACK_BACKUP=
MUTATING=0
CORE_SELECTED=0
cleanup() {
    rc=$?
    trap - EXIT
    if [ "$rc" -ne 0 ] && [ "$MUTATING" = 1 ]; then
        while read -r id old new mode source target; do
            if [ -f "$target" ]; then current=$(sha256 -q "$target"); else current=absent; fi
            if [ "$current" = "$new" ] || [ "$current" = "$old" ]; then
                cp -p "$ROLLBACK_BACKUP/files/$id" "$target" || echo "ROLLBACK_FAILED=$target" >&2
            else
                echo "ROLLBACK_CONFLICT=$target" >&2
            fi
        done < "$stage/selected"
        if [ "$CORE_SELECTED" = 1 ]; then
            if [ -d /var/lib/php/cache ]; then find /var/lib/php/cache -type f -name '*.php' -delete || :; fi
            configctl webgui restart || echo 'ROLLBACK_WEBGUI_RESTART_FAILED' >&2
        fi
        echo "ROLLBACK_ATTEMPTED=$ROLLBACK_BACKUP" >&2
    fi
    rm -rf "$stage"
    exit "$rc"
}
trap cleanup EXIT
: > "$stage/selected"
for lang in $SELECTED; do
    plugin=/usr/local/opnsense/mvc/app/languages/${lang}_devicemonitor.mo
    if [ "$lang" = en_US ]; then targets=$plugin
    else
        targets="$plugin /usr/local/share/locale/${lang}/LC_MESSAGES/OPNsense.mo"
        CORE_SELECTED=1
    fi
    for target in $targets; do
        row=$(awk -v t="$target" '$6==t {n++; row=$0} END {if (n==1) print row; else exit 1}' "$SOURCE_BACKUP/plan") || { echo "ABORT: locale absent or duplicated in backup $target" >&2; exit 1; }
        set -- $row
        [ "$#" -eq 6 ] && [ "$6" = "$target" ] || { echo 'ABORT: invalid backup row' >&2; exit 1; }
        id=$1
        old=$2
        new=$3
        case "$id" in *[!0-9]*|'') echo 'ABORT: invalid backup id' >&2; exit 1;; esac
        printf '%s\n' "$new" | awk 'length($0)==64 && /^[0-9a-f]+$/ {ok=1} END {exit !ok}' || exit 1
        [ -f "$target" ] && [ ! -L "$target" ] && [ "$(sha256 -q "$target")" = "$new" ] || { echo "ABORT: installed catalogue changed $target" >&2; exit 1; }
        if [ "$old" != absent ]; then
            printf '%s\n' "$old" | awk 'length($0)==64 && /^[0-9a-f]+$/ {ok=1} END {exit !ok}' || exit 1
            [ -f "$SOURCE_BACKUP/files/$id" ] && [ ! -L "$SOURCE_BACKUP/files/$id" ] && [ "$(sha256 -q "$SOURCE_BACKUP/files/$id")" = "$old" ] || { echo "ABORT: restore copy mismatch $target" >&2; exit 1; }
        fi
        printf '%s\n' "$row" >> "$stage/selected"
    done
done
count=$(wc -l < "$stage/selected" | tr -d ' ')
printf 'REMOVE_CHECK_OK locales=%s files=%s backup=%s host=%s\n' "$LANGUAGES" "$count" "$SOURCE_BACKUP" "$EXPECTED_HOST"
[ "$CHECK_ONLY" = 0 ] || exit 0
if [ "$CORE_SELECTED" = 1 ]; then command -v configctl >/dev/null 2>&1 || { echo 'ABORT: configctl missing' >&2; exit 1; }; fi
ROLLBACK_BACKUP=$(mktemp -d /var/backups/devicemonitor/locale-remove.XXXXXX)
mkdir "$ROLLBACK_BACKUP/files"
cp "$stage/selected" "$ROLLBACK_BACKUP/plan"
while read -r id old new mode source target; do
    cp -p "$target" "$ROLLBACK_BACKUP/files/$id"
    [ "$(sha256 -q "$ROLLBACK_BACKUP/files/$id")" = "$new" ] || { echo "ABORT: removal backup $target" >&2; exit 1; }
done < "$stage/selected"
while read -r id old new mode source target; do
    [ "$(sha256 -q "$target")" = "$new" ] || { echo "ABORT: catalogue changed before restore $target" >&2; exit 1; }
done < "$stage/selected"
MUTATING=1
while read -r id old new mode source target; do
    [ "$(sha256 -q "$target")" = "$new" ] || { echo "ABORT: catalogue changed $target" >&2; exit 1; }
    if [ "$old" = absent ]; then
        rm -f "$target"
        [ ! -e "$target" ] || exit 1
    else
        temporary=$target.dm-restore.$$
        [ ! -e "$temporary" ] || { echo "ABORT: temporary file collision $temporary" >&2; exit 1; }
        cp -p "$SOURCE_BACKUP/files/$id" "$temporary"
        [ "$(sha256 -q "$temporary")" = "$old" ] || exit 1
        mv "$temporary" "$target"
        [ "$(sha256 -q "$target")" = "$old" ] || exit 1
    fi
done < "$stage/selected"
if [ "$CORE_SELECTED" = 1 ]; then
    if [ -d /var/lib/php/cache ]; then find /var/lib/php/cache -type f -name '*.php' -delete; fi
    configctl webgui restart
fi
MUTATING=0
printf 'REMOVE_LOCALES_OK locales=%s files=%s rollback=%s webgui_restarted=%s\n' "$LANGUAGES" "$count" "$ROLLBACK_BACKUP" "$CORE_SELECTED"

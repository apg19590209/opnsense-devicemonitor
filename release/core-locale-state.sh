#!/bin/sh
# Snapshot and restore the Device Monitor core-locale state directory for rollback.
#
#   core-locale-state.sh backup-core-locale-state --state DIR --backup DIR [--root DIR]
#   core-locale-state.sh restore-core-locale-state --state DIR --backup DIR [--root DIR]
#
# The state directory contains the pristine OPNsense catalogues and the per-locale records
# used by uninstall.sh. An install rewrites those records, so a failed install must restore
# their original bytes, modes and ownership, remove files that did not exist before it, and
# remove the directory itself when it was originally absent.
set -eu
LC_ALL=C
export LC_ALL
TAB=$(printf '\t')

PROG=core-locale-state.sh
STATE=/var/backups/devicemonitor/core-locale

usage() {
    echo "usage: $PROG backup-core-locale-state --state DIR --backup DIR [--root DIR]" >&2
    echo "       $PROG restore-core-locale-state --state DIR --backup DIR [--root DIR]" >&2
    exit 2
}

die() {
    echo "ABORT: $*" >&2
    exit 1
}

# stat(1) means two different things here, so select the implementation rather than probing
# with it: a failed probe that falls through to the other branch returns nonsense.
case "$(uname -s)" in
    FreeBSD|Darwin|NetBSD|OpenBSD) STAT_STYLE=bsd ;;
    *) STAT_STYLE=gnu ;;
esac

file_mode() {
    if [ "$STAT_STYLE" = bsd ]; then stat -f %Lp "$1"; else stat -c %a "$1"; fi
}
file_owner() {
    if [ "$STAT_STYLE" = bsd ]; then stat -f %Su "$1"; else stat -c %U "$1"; fi
}
file_group() {
    if [ "$STAT_STYLE" = bsd ]; then stat -f %Sg "$1"; else stat -c %G "$1"; fi
}
digest() {
    if command -v sha256 >/dev/null 2>&1; then
        sha256 -q "$1"
    else
        sha256sum "$1" | awk '{print $1}'
    fi
}

safe_path() {
    case "$1" in
        /*) : ;;
        *) return 1 ;;
    esac
    case "$1" in
        *' '*|*"$TAB"*|*..*) return 1 ;;
    esac
    [ "$1" != / ] || return 1
    return 0
}

safe_name() {
    case "$1" in
        ''|*' '*|*"$TAB"*|*/*|..*) return 1 ;;
    esac
    return 0
}

cmd=${1:-}
[ "$#" -gt 0 ] && shift
state=
backup=
root=
while [ "$#" -gt 0 ]; do
    case "$1" in
        --state) [ "$#" -ge 2 ] || usage; state=$2; shift 2 ;;
        --backup) [ "$#" -ge 2 ] || usage; backup=$2; shift 2 ;;
        --root) [ "$#" -ge 2 ] || usage; root=$2; shift 2 ;;
        *) echo "$PROG: unknown argument $1" >&2; usage ;;
    esac
done

[ -n "$state" ] || usage
[ -n "$backup" ] || usage
[ "$state" = "$STATE" ] || die "unexpected state path: $state"
safe_path "$backup" || die "unsafe backup path: $backup"
if [ -n "$root" ]; then
    safe_path "$root" || die "unsafe root path: $root"
    [ -d "$root" ] || die "root is not a directory: $root"
fi

full=$root$state

backup_core_locale_state() {
    dest=$backup/core-locale-state
    [ ! -e "$dest" ] || die "state backup already exists: $dest"
    mkdir -p "$dest/files" || die "cannot create $dest"
    : > "$dest/files.sha256"
    if [ ! -e "$full" ]; then
        printf 'absent\n' > "$dest/directory"
        printf 'CORE_LOCALE_STATE_BACKED_UP=absent files=0\n'
        return 0
    fi
    [ -d "$full" ] && [ ! -L "$full" ] || die "state path is not a directory: $state"
    printf 'present %s %s %s\n' "$(file_mode "$full")" "$(file_owner "$full")" \
        "$(file_group "$full")" > "$dest/directory"
    n=0
    for file in "$full"/*.state "$full"/*.OPNsense.mo; do
        [ -e "$file" ] || continue
        [ -f "$file" ] && [ ! -L "$file" ] || die "irregular state file: $file"
        name=${file##*/}
        safe_name "$name" || die "unsupported state filename: $name"
        hash=$(digest "$file")
        cp -p "$file" "$dest/files/$name" || die "cannot back up state file: $file"
        [ "$(digest "$dest/files/$name")" = "$hash" ] || die "state backup digest mismatch: $file"
        printf '%s %s %s %s %s\n' "$hash" "$name" "$(file_mode "$file")" \
            "$(file_owner "$file")" "$(file_group "$file")" >> "$dest/files.sha256"
        n=$((n + 1))
    done
    printf 'CORE_LOCALE_STATE_BACKED_UP=present files=%s\n' "$n"
}

restore_core_locale_state() {
    dest=$backup/core-locale-state
    metadata=$dest/directory
    manifest=$dest/files.sha256
    if [ ! -f "$metadata" ] || [ ! -f "$manifest" ] || [ ! -d "$dest/files" ]; then
        echo "ROLLBACK_FAILED=$state (state backup missing)" >&2
        return 1
    fi
    read -r dir_state dir_mode dir_owner dir_group < "$metadata" || dir_state=
    case "$dir_state" in
        absent)
            [ ! -s "$manifest" ] || {
                echo "ROLLBACK_FAILED=$state (absent-state backup has files)" >&2
                return 1
            }
            ;;
        present)
            [ -n "$dir_mode" ] && [ -n "$dir_owner" ] && [ -n "$dir_group" ] || {
                echo "ROLLBACK_FAILED=$state (state directory metadata)" >&2
                return 1
            }
            preflight=0
            while read -r hash name mode owner group; do
                [ -n "$name" ] || continue
                if ! safe_name "$name"; then
                    echo "ROLLBACK_FAILED=$state/$name (backup metadata)" >&2
                    preflight=1
                    continue
                fi
                src=$dest/files/$name
                if [ ! -f "$src" ] || [ -L "$src" ] ||
                        [ "$(digest "$src")" != "$hash" ] || [ -z "$mode" ] ||
                        [ -z "$owner" ] || [ -z "$group" ]; then
                    echo "ROLLBACK_FAILED=$state/$name (backup digest)" >&2
                    preflight=1
                fi
            done < "$manifest"
            if [ "$preflight" != 0 ]; then
                printf 'CORE_LOCALE_ROLLBACK_SUMMARY=restored=0 removed=0 conflicts=0 failed=1\n'
                return 1
            fi
            ;;
        *)
            echo "ROLLBACK_FAILED=$state (state backup metadata)" >&2
            return 1
            ;;
    esac

    rc=0
    restored=0
    removed=0
    conflicts=0
    failed=0
    if [ -e "$full" ] && { [ ! -d "$full" ] || [ -L "$full" ]; }; then
        echo "ROLLBACK_CONFLICT=$state" >&2
        conflicts=$((conflicts + 1))
        rc=1
    elif [ "$dir_state" = absent ]; then
        if [ -d "$full" ]; then
            for file in "$full"/*.state "$full"/*.OPNsense.mo; do
                [ -e "$file" ] || continue
                if [ ! -f "$file" ] || [ -L "$file" ]; then
                    echo "ROLLBACK_CONFLICT=$file" >&2
                    conflicts=$((conflicts + 1))
                    rc=1
                    continue
                fi
                if rm -f "$file"; then
                    removed=$((removed + 1))
                else
                    echo "ROLLBACK_FAILED=$file (remove)" >&2
                    failed=$((failed + 1))
                    rc=1
                fi
            done
            if ! rmdir "$full" 2>/dev/null; then
                echo "ROLLBACK_FAILED=$state (directory not empty)" >&2
                failed=$((failed + 1))
                rc=1
            fi
        fi
    else
        mkdir -p "$full" || {
            echo "ROLLBACK_FAILED=$state (directory create)" >&2
            failed=$((failed + 1))
            rc=1
        }
        if [ "$rc" = 0 ]; then
            for file in "$full"/*.state "$full"/*.OPNsense.mo; do
                [ -e "$file" ] || continue
                name=${file##*/}
                if awk -v name="$name" '$2 == name { found = 1 } END { exit !found }' "$manifest"; then
                    continue
                fi
                if [ ! -f "$file" ] || [ -L "$file" ]; then
                    echo "ROLLBACK_CONFLICT=$file" >&2
                    conflicts=$((conflicts + 1))
                    rc=1
                    continue
                fi
                if rm -f "$file"; then
                    removed=$((removed + 1))
                else
                    echo "ROLLBACK_FAILED=$file (remove)" >&2
                    failed=$((failed + 1))
                    rc=1
                fi
            done
            while read -r hash name mode owner group; do
                [ -n "$name" ] || continue
                src=$dest/files/$name
                target=$full/$name
                if ! cp -p "$src" "$target"; then
                    echo "ROLLBACK_FAILED=$target (restore)" >&2
                    failed=$((failed + 1))
                    rc=1
                    continue
                fi
                if [ "$(file_mode "$target")" != "$mode" ]; then
                    chmod "$mode" "$target" || {
                        echo "ROLLBACK_FAILED=$target (mode)" >&2
                        failed=$((failed + 1))
                        rc=1
                        continue
                    }
                fi
                if [ "$(file_owner "$target")" != "$owner" ] ||
                        [ "$(file_group "$target")" != "$group" ]; then
                    chown "$owner:$group" "$target" || {
                        echo "ROLLBACK_FAILED=$target (owner)" >&2
                        failed=$((failed + 1))
                        rc=1
                        continue
                    }
                fi
                if [ "$(digest "$target")" = "$hash" ] &&
                        [ "$(file_mode "$target")" = "$mode" ] &&
                        [ "$(file_owner "$target")" = "$owner" ] &&
                        [ "$(file_group "$target")" = "$group" ]; then
                    restored=$((restored + 1))
                else
                    echo "ROLLBACK_FAILED=$target (digest or metadata)" >&2
                    failed=$((failed + 1))
                    rc=1
                fi
            done < "$manifest"
            if [ "$rc" = 0 ]; then
                if [ "$(file_mode "$full")" != "$dir_mode" ]; then
                    chmod "$dir_mode" "$full" || rc=1
                fi
                if [ "$(file_owner "$full")" != "$dir_owner" ] ||
                        [ "$(file_group "$full")" != "$dir_group" ]; then
                    chown "$dir_owner:$dir_group" "$full" || rc=1
                fi
                if [ "$(file_mode "$full")" != "$dir_mode" ] ||
                        [ "$(file_owner "$full")" != "$dir_owner" ] ||
                        [ "$(file_group "$full")" != "$dir_group" ]; then
                    echo "ROLLBACK_FAILED=$state (directory metadata)" >&2
                    failed=$((failed + 1))
                    rc=1
                fi
            fi
        fi
    fi
    printf 'CORE_LOCALE_ROLLBACK_SUMMARY=restored=%s removed=%s conflicts=%s failed=%s\n' \
        "$restored" "$removed" "$conflicts" "$failed"
    return "$rc"
}

case "$cmd" in
    backup-core-locale-state) backup_core_locale_state ;;
    restore-core-locale-state) restore_core_locale_state ;;
    *) usage ;;
esac

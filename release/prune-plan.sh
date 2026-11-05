#!/bin/sh
# Prune planning and application for the Device Monitor installer (Decision 62).
#
#   prune-plan.sh compute --current FILE [--record FILE] [--legacy FILE] [--root DIR]
#   prune-plan.sh backup  --plan FILE --backup DIR [--root DIR]
#   prune-plan.sh delete  --plan FILE [--root DIR]
#   prune-plan.sh restore --plan FILE --backup DIR [--root DIR]
#   prune-plan.sh restore-targets --plan FILE --backup DIR [--root DIR]
#   prune-plan.sh backup-core-locale-state --state DIR --backup DIR [--root DIR]
#   prune-plan.sh restore-core-locale-state --state DIR --backup DIR [--root DIR]
#
# compute  never changes the filesystem. It prints the plan on stdout, one line per target,
#          "<SOURCE> <path>" with SOURCE = RECORD (this plugin installed the path on a
#          previous run) or LEGACY (a historical release manifest published that exact
#          digest for that path). Everything it refuses to delete is reported on stderr as
#          "RETAINED <reason> <path>", so a file is never dropped without proof of
#          ownership: an ambiguous file is retained.
# backup   copies each planned target that exists into BACKUP/files/prune-<n>, records
#          "<id> <sha256> <path>" in BACKUP/prune and prints PRUNE_PLANNED=<n>.
# delete   removes the targets listed in BACKUP/prune and prints PRUNED=<n>, counting only
#          the files it actually removed.
# restore  puts them back from BACKUP/files, verifies every restored digest and prints
#          ROLLBACK_RESTORED / ROLLBACK_CONFLICT / ROLLBACK_FAILED; exits 1 if a restore
#          could not be verified.
# restore-targets puts back the files an install replaced (the installer's own plan, one row
#          per target: "<id> <old> <new> <mode> <source> <target>"), using the same
#          vocabulary and the same digest verification. A target that nothing changed is
#          left alone; a target that a third party changed is a reported conflict.
# backup-record  copies the previous install record into the rollback directory, so a
#          rollback can also restore the target set that record describes. Prints
#          RECORD_BACKED_UP=<record> (or RECORD_BACKED_UP=absent when there was none).
# restore-record puts the backed-up record back (digest-verified), or removes the record
#          when the run that is being rolled back created it. Prints RECORD_RESTORED=<record>
#          or RECORD_REMOVED=<record>.
# backup-core-locale-state snapshots the core-locale state directory, including pristine
#          catalogue copies, with digest and metadata verification.
# restore-core-locale-state restores that snapshot exactly. Files and directories created by
#          the failed run are removed when they did not exist before it.
#
# The approved namespaces are the only paths this plugin may ever own. A candidate outside
# them is not a candidate at all, so a corrupted record or a hand-edited evidence file
# cannot widen the blast radius.
set -eu
LC_ALL=C
export LC_ALL
TAB=$(printf '\t')

PROG=prune-plan.sh

usage() {
    echo "usage: $PROG compute --current FILE [--record FILE] [--legacy FILE] [--root DIR]" >&2
    echo "       $PROG backup  --plan FILE --backup DIR [--root DIR]" >&2
    echo "       $PROG delete  --plan FILE [--root DIR]" >&2
    echo "       $PROG restore --plan FILE --backup DIR [--root DIR]" >&2
    echo "       $PROG restore-targets --plan FILE --backup DIR [--root DIR]" >&2
    echo "       $PROG backup-record --record FILE --backup DIR [--root DIR]" >&2
    echo "       $PROG restore-record --record FILE --backup DIR [--root DIR]" >&2
    echo "       $PROG backup-core-locale-state --state DIR --backup DIR [--root DIR]" >&2
    echo "       $PROG restore-core-locale-state --state DIR --backup DIR [--root DIR]" >&2
    echo "       $PROG enforce-target --target PATH --mode MODE [--owner U --group G] [--root DIR]" >&2
    exit 2
}

die() {
    echo "ABORT: $*" >&2
    exit 1
}

# FreeBSD ships sha256(1); a GNU userland (the CI runner) only has sha256sum. The installer
# only ever calls this helper on FreeBSD, the tests call it on both.
digest() {
    if [ -n "${DM_SHA256:-}" ]; then
        $DM_SHA256 "$1"
    elif command -v sha256 >/dev/null 2>&1; then
        sha256 -q "$1"
    elif command -v sha256sum >/dev/null 2>&1; then
        sha256sum "$1" | awk '{print $1}'
    else
        die 'no sha256 implementation available'
    fi
}

# FreeBSD spells stat(1) format flags differently from GNU coreutils. The OS is the
# discriminator, not a trial run: on GNU, `stat -f` means "filesystem status" and succeeds,
# so probing with it silently selects the wrong branch and returns nonsense for the mode.
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

in_namespace() {
    case "$1" in
        /usr/local/opnsense/*) return 0 ;;
        /usr/local/etc/rc.d/devicemonitor) return 0 ;;
        /usr/local/etc/inc/plugins.inc.d/devicemonitor.inc) return 0 ;;
        /usr/local/etc/inc/devicemonitor_locale.inc) return 0 ;;
    esac
    return 1
}

# Absolute, no traversal, no whitespace: the plan and record formats are line based and the
# manifest never contains such a path, so anything else is corruption, not a target.
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

cmd=${1:-}
[ "$#" -gt 0 ] && shift

current=
record=
legacy=
plan=
backup=
state=
root=
target=
mode=
owner=
group=

while [ "$#" -gt 0 ]; do
    case "$1" in
        --current) [ "$#" -ge 2 ] || usage; current=$2; shift 2 ;;
        --record) [ "$#" -ge 2 ] || usage; record=$2; shift 2 ;;
        --legacy) [ "$#" -ge 2 ] || usage; legacy=$2; shift 2 ;;
        --plan) [ "$#" -ge 2 ] || usage; plan=$2; shift 2 ;;
        --backup) [ "$#" -ge 2 ] || usage; backup=$2; shift 2 ;;
        --state) [ "$#" -ge 2 ] || usage; state=$2; shift 2 ;;
        --target) [ "$#" -ge 2 ] || usage; target=$2; shift 2 ;;
        --mode) [ "$#" -ge 2 ] || usage; mode=$2; shift 2 ;;
        --owner) [ "$#" -ge 2 ] || usage; owner=$2; shift 2 ;;
        --group) [ "$#" -ge 2 ] || usage; group=$2; shift 2 ;;
        --root) [ "$#" -ge 2 ] || usage; root=$2; shift 2 ;;
        *) echo "$PROG: unknown argument $1" >&2; usage ;;
    esac
done

# $root is empty on a real install and a staging directory under test.
[ -z "$root" ] || [ -d "$root" ] || die "root is not a directory: $root"

# Normalise "path<TAB>digest" out of a record (digest optional) or an evidence file.
# Comments and blank lines are ignored and unsafe paths are dropped before any decision.
normalise() {
    kind=$1
    file=$2
    while read -r a b; do
        case "$a" in
            ''|'#'*) continue ;;
        esac
        if [ "$kind" = record ]; then
            if [ -n "$b" ]; then
                hash=$a
                path=$b
            else
                hash=-
                path=$a
            fi
        else
            [ -n "$b" ] || continue
            hash=$a
            path=$b
        fi
        safe_path "$path" || continue
        printf '%s\t%s\n' "$path" "$hash"
    done < "$file"
}

compute() {
    [ -n "$current" ] || die 'compute needs --current'
    [ -f "$current" ] || die "current target list missing: $current"
    [ -z "$record" ] || [ -f "$record" ] || die "record missing: $record"
    [ -z "$legacy" ] || [ -f "$legacy" ] || die "legacy evidence missing: $legacy"

    work=$(mktemp -d "${TMPDIR:-/tmp}/dm_prune.XXXXXX")
    trap 'rm -rf "$work"' EXIT

    # The current side is the full target set of the run that is about to install: manifest
    # targets plus the catalogues that run generates. Deriving it from the manifest alone
    # would mark the freshly built .mo files as prunable.
    : > "$work/current"
    while IFS= read -r path; do
        safe_path "$path" || continue
        printf '%s\n' "$path" >> "$work/current"
    done < "$current"
    sort -u < "$work/current" > "$work/current.sorted"
    mv "$work/current.sorted" "$work/current"

    : > "$work/record"
    if [ -n "$record" ]; then
        normalise record "$record" | awk -F'\t' '!seen[$1]++' > "$work/record"
    fi

    : > "$work/legacy"
    if [ -n "$legacy" ]; then
        normalise legacy "$legacy" > "$work/legacy"
    fi

    { cut -f1 "$work/record"; cut -f1 "$work/legacy"; } | sort -u > "$work/candidates"

    # One decision per candidate, in path order so the plan is reproducible.
    while IFS= read -r path; do
        in_namespace "$path" || continue
        if grep -Fx -q -- "$path" "$work/current"; then continue; fi
        full=$root$path
        unverified=0
        rec=missing
        while IFS="$TAB" read -r rpath rhash; do
            [ "$rpath" = "$path" ] || continue
            rec=$rhash
            break
        done < "$work/record"
        if [ "$rec" != missing ]; then
            [ -e "$full" ] || continue
            if [ ! -f "$full" ] || [ -L "$full" ]; then
                echo "RETAINED irregular $path" >&2
                continue
            fi
            if [ "$rec" != - ]; then
                if [ "$(digest "$full")" = "$rec" ]; then
                    printf 'RECORD %s\n' "$path"
                else
                    echo "RETAINED modified $path" >&2
                fi
                continue
            fi
            # A bare-path record (written by 2.13.2) names the path but carries no digest.
            # Naming a path proves we once installed it, not what is there now, so it falls
            # through to the published-digest check and is retained when that finds nothing.
            unverified=1
        fi
        # LEGACY: a published digest is the only evidence that the content is ours. An
        # unchanged historical file is provably ours; anything else is retained.
        [ -e "$full" ] || continue
        if [ ! -f "$full" ] || [ -L "$full" ]; then
            echo "RETAINED irregular $path" >&2
            continue
        fi
        actual=$(digest "$full")
        owned=0
        while IFS="$TAB" read -r lpath lhash; do
            [ "$lpath" = "$path" ] || continue
            [ "$lhash" = "$actual" ] || continue
            owned=1
            break
        done < "$work/legacy"
        if [ "$owned" = 1 ]; then
            printf 'LEGACY %s\n' "$path"
        elif [ "$unverified" = 1 ]; then
            echo "RETAINED unverified $path" >&2
        else
            echo "RETAINED modified $path" >&2
        fi
    done < "$work/candidates"
}

backup_plan() {
    [ -n "$plan" ] || die 'backup needs --plan'
    [ -n "$backup" ] || die 'backup needs --backup'
    [ -f "$plan" ] || die "plan missing: $plan"
    mkdir -p "$backup/files" || die "cannot create $backup/files"
    : > "$backup/prune"
    n=0
    while read -r source path; do
        [ -n "$path" ] || continue
        safe_path "$path" || die "refusing unsafe path in plan: $path"
        full=$root$path
        [ -f "$full" ] && [ ! -L "$full" ] || continue
        n=$((n + 1))
        id=prune-$n
        cp -p "$full" "$backup/files/$id" || die "cannot back up $path"
        original=$(digest "$full")
        copied=$(digest "$backup/files/$id")
        [ "$copied" = "$original" ] || die "prune backup digest mismatch: $path"
        printf '%s %s %s\n' "$id" "$original" "$path" >> "$backup/prune"
    done < "$plan"
    printf 'PRUNE_PLANNED=%s\n' "$n"
}

delete_plan() {
    [ -n "$plan" ] || die 'delete needs --plan'
    [ -f "$plan" ] || die "plan missing: $plan"
    removed=0
    while read -r id hash path; do
        [ -n "$path" ] || continue
        safe_path "$path" || die "refusing unsafe path in plan: $path"
        full=$root$path
        [ -e "$full" ] || continue
        # The plan was verified when it was computed; re-verify against the digest recorded
        # in the backup bookkeeping, so a target that changed in between is never deleted.
        [ -f "$full" ] && [ ! -L "$full" ] || die "target changed before pruning: $path"
        if [ "$(digest "$full")" != "$hash" ]; then
            die "target changed before pruning: $path"
        fi
        rm -f "$full" || die "cannot prune $path"
        [ ! -e "$full" ] || die "prune left $path"
        removed=$((removed + 1))
    done < "$plan"
    printf 'PRUNED=%s\n' "$removed"
}

restore_plan() {
    [ -n "$plan" ] || die 'restore needs --plan'
    [ -n "$backup" ] || die 'restore needs --backup'
    [ -f "$plan" ] || die "plan missing: $plan"
    rc=0
    restored=0
    skipped=0
    conflicts=0
    failed=0
    while read -r id hash path; do
        [ -n "$path" ] || continue
        if ! safe_path "$path"; then
            echo "ROLLBACK_FAILED=$path (unsafe path)" >&2
            failed=$((failed + 1)); rc=1
            continue
        fi
        full=$root$path
        if [ -e "$full" ]; then
            # A planned prune target that is still there was never deleted (an install can
            # fail before the prune step). Restoring it would be a no-op, so it is not a
            # conflict — only a file that changed identity is.
            if [ -f "$full" ] && [ "$(digest "$full")" = "$hash" ]; then
                skipped=$((skipped + 1))
                continue
            fi
            echo "ROLLBACK_CONFLICT=$path" >&2
            conflicts=$((conflicts + 1))
            rc=1
            continue
        fi
        if [ ! -f "$backup/files/$id" ]; then
            echo "ROLLBACK_FAILED=$path (no backup copy)" >&2
            failed=$((failed + 1)); rc=1
            continue
        fi
        # Verify the copy before writing it, so a damaged backup never replaces the target
        # with content that cannot be proven to be the predecessor.
        if [ "$(digest "$backup/files/$id")" != "$hash" ]; then
            echo "ROLLBACK_FAILED=$path (backup digest)" >&2
            failed=$((failed + 1)); rc=1
            continue
        fi
        if ! cp -p "$backup/files/$id" "$full"; then
            echo "ROLLBACK_FAILED=$path (copy)" >&2
            failed=$((failed + 1)); rc=1
            continue
        fi
        if [ "$(digest "$full")" = "$hash" ]; then
            echo "ROLLBACK_RESTORED=$path"
            restored=$((restored + 1))
        else
            echo "ROLLBACK_FAILED=$path (digest)" >&2
            failed=$((failed + 1)); rc=1
        fi
    done < "$plan"
    printf 'ROLLBACK_SUMMARY=restored=%s skipped=%s conflicts=%s failed=%s\n' \
        "$restored" "$skipped" "$conflicts" "$failed"
    return "$rc"
}

restore_targets() {
    [ -n "$plan" ] || die 'restore-targets needs --plan'
    [ -n "$backup" ] || die 'restore-targets needs --backup'
    [ -f "$plan" ] || die "plan missing: $plan"
    rc=0
    restored=0
    skipped=0
    conflicts=0
    failed=0
    while read -r id old new mode source target; do
        [ -n "$target" ] || continue
        if ! safe_path "$target"; then
            echo "ROLLBACK_FAILED=$target (unsafe path)" >&2
            failed=$((failed + 1)); rc=1
            continue
        fi
        full=$root$target
        if [ "$old" = absent ]; then
            # Nothing existed before this run: remove what the run created, if it is ours.
            [ -e "$full" ] || { skipped=$((skipped + 1)); continue; }
            if [ "$(digest "$full")" = "$new" ]; then
                if rm -f "$full"; then
                    restored=$((restored + 1))
                else
                    echo "ROLLBACK_FAILED=$target (remove)" >&2
                    failed=$((failed + 1)); rc=1
                fi
            else
                echo "ROLLBACK_CONFLICT=$target" >&2
                conflicts=$((conflicts + 1)); rc=1
            fi
            continue
        fi
        if [ -e "$full" ]; then
            if [ "$(digest "$full")" = "$old" ]; then
                skipped=$((skipped + 1))
                continue
            fi
            if [ "$(digest "$full")" != "$new" ]; then
                echo "ROLLBACK_CONFLICT=$target" >&2
                conflicts=$((conflicts + 1)); rc=1
                continue
            fi
        fi
        if [ ! -f "$backup/files/$id" ]; then
            echo "ROLLBACK_FAILED=$target (no backup copy)" >&2
            failed=$((failed + 1)); rc=1
            continue
        fi
        if [ "$(digest "$backup/files/$id")" != "$old" ]; then
            echo "ROLLBACK_FAILED=$target (backup digest)" >&2
            failed=$((failed + 1)); rc=1
            continue
        fi
        if cp -p "$backup/files/$id" "$full" && [ "$(digest "$full")" = "$old" ]; then
            echo "ROLLBACK_RESTORED=$target"
            restored=$((restored + 1))
        else
            echo "ROLLBACK_FAILED=$target (restore)" >&2
            failed=$((failed + 1)); rc=1
        fi
    done < "$plan"
    printf 'ROLLBACK_SUMMARY=restored=%s skipped=%s conflicts=%s failed=%s\n' \
        "$restored" "$skipped" "$conflicts" "$failed"
    return "$rc"
}

backup_record() {
    [ -n "$record" ] || die 'backup-record needs --record'
    [ -n "$backup" ] || die 'backup-record needs --backup'
    mkdir -p "$backup" || die "cannot create $backup"
    full=$root$record
    if [ ! -e "$full" ]; then
        printf 'RECORD_BACKED_UP=absent\n'
        return 0
    fi
    [ -f "$full" ] && [ ! -L "$full" ] || die "record is not a regular file: $record"
    cp -p "$full" "$backup/installed-manifest.txt" || die "cannot back up $record"
    expected=$(digest "$full")
    if [ "$(digest "$backup/installed-manifest.txt")" != "$expected" ]; then
        die "record backup digest mismatch: $record"
    fi
    printf '%s %s\n' "$expected" "$record" > "$backup/installed-manifest.sha256"
    printf 'RECORD_BACKED_UP=%s\n' "$record"
}

restore_record() {
    [ -n "$backup" ] || die 'restore-record needs --backup'
    [ -n "$record" ] || die 'restore-record needs --record'
    full=$root$record
    if [ -f "$backup/installed-manifest.txt" ]; then
        # The recorded digest is the trusted value: verifying the copy against the copy
        # would accept a damaged backup.
        if [ ! -f "$backup/installed-manifest.sha256" ]; then
            echo "ROLLBACK_FAILED=$record (record digest missing)" >&2
            return 1
        fi
        expected=$(awk 'NR == 1 { print $1 }' "$backup/installed-manifest.sha256")
        if [ "$(digest "$backup/installed-manifest.txt")" != "$expected" ]; then
            echo "ROLLBACK_FAILED=$record (backup digest)" >&2
            return 1
        fi
        mkdir -p "$(dirname -- "$full")" || { echo "ROLLBACK_FAILED=$record (record mkdir)" >&2; return 1; }
        if ! cp -p "$backup/installed-manifest.txt" "$full"; then
            echo "ROLLBACK_FAILED=$record (record copy)" >&2
            return 1
        fi
        if [ "$(digest "$full")" != "$expected" ]; then
            echo "ROLLBACK_FAILED=$record (record digest)" >&2
            return 1
        fi
        printf 'RECORD_RESTORED=%s\n' "$record"
        return 0
    fi
    # There was no record before this run: remove the one the run created.
    if [ -e "$full" ]; then
        rm -f "$full" || { echo "ROLLBACK_FAILED=$record (record remove)" >&2; return 1; }
        printf 'RECORD_REMOVED=%s\n' "$record"
    fi
    return 0
}

backup_core_locale_state() {
    [ -n "$state" ] || die 'backup-core-locale-state needs --state'
    [ -n "$backup" ] || die 'backup-core-locale-state needs --backup'
    safe_path "$state" || die "unsafe state path: $state"
    full=$root$state
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
        case "$name" in
            *' '*|*"$TAB"*|*/*|..*) die "unsupported state filename: $name" ;;
        esac
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
    [ -n "$state" ] || die 'restore-core-locale-state needs --state'
    [ -n "$backup" ] || die 'restore-core-locale-state needs --backup'
    safe_path "$state" || die "unsafe state path: $state"
    full=$root$state
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
                case "$name" in
                    *' '*|*"$TAB"*|*/*|..*) preflight=1; continue ;;
                esac
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
                if [ "$(file_owner "$target")" != "$owner" ] || [ "$(file_group "$target")" != "$group" ]; then
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
                if [ "$(file_owner "$full")" != "$dir_owner" ] || [ "$(file_group "$full")" != "$dir_group" ]; then
                    chown "$dir_owner:$dir_group" "$full" || rc=1
                fi
                if [ "$rc" != 0 ]; then
                    echo "ROLLBACK_FAILED=$state (directory metadata)" >&2
                    failed=$((failed + 1))
                fi
            fi
        fi
    fi
    printf 'CORE_LOCALE_ROLLBACK_SUMMARY=restored=%s removed=%s conflicts=%s failed=%s\n' \
        "$restored" "$removed" "$conflicts" "$failed"
    return "$rc"
}

enforce_target() {
    [ -n "$target" ] || die 'enforce-target needs --target'
    [ -n "$mode" ] || die 'enforce-target needs --mode'
    full=$root$target
    if [ ! -f "$full" ] || [ -L "$full" ]; then
        die "enforce-target: not a regular file: $target"
    fi
    changed=0
    have=$(file_mode "$full")
    if [ "$have" != "$mode" ]; then
        chmod "$mode" "$full" || die "enforce-target: cannot set mode $mode on $target"
        changed=1
    fi
    if [ -n "$owner" ] && [ -n "$group" ]; then
        have_owner=$(file_owner "$full")
        have_group=$(file_group "$full")
        if [ "$have_owner" != "$owner" ] || [ "$have_group" != "$group" ]; then
            chown "$owner:$group" "$full" ||
                die "enforce-target: cannot set $owner:$group on $target"
            changed=1
        fi
    fi
    if [ "$changed" = 1 ]; then
        printf 'REPAIRED=%s %s %s:%s\n' "$target" "$mode" "${owner:--}" "${group:--}"
    else
        printf 'ENFORCED=%s\n' "$target"
    fi
}

case "$cmd" in
    compute) compute ;;
    backup) backup_plan ;;
    delete) delete_plan ;;
    restore) restore_plan ;;
    restore-targets) restore_targets ;;
    backup-record) backup_record ;;
    restore-record) restore_record ;;
    backup-core-locale-state) backup_core_locale_state ;;
    restore-core-locale-state) restore_core_locale_state ;;
    enforce-target) enforce_target ;;
    *) usage ;;
esac

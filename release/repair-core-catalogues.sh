#!/bin/sh
# Rebuild the installer-owned core-domain catalogues, or report the drift, without changing
# Device Monitor records (Decision 71).
#
#   repair-core-catalogues.sh --root DIR --record FILE --state DIR --plugin-dir DIR \
#       --merge-helper FILE --pristine-table FILE [--apply --backup DIR]
#
# The installer merges the plugin keys into each pristine OPNsense.mo. If a later run merges
# into a catalogue an older build already merged, the result keeps that older build's bytes.
# This helper always starts from a recorded pristine catalogue and runs the same core-first
# merge, so its expected bytes are reproducible rather than copied from whatever is live.
#
# The default is read-only. --apply replaces only the predecessor recorded both in the install
# record and in the core-locale state, preserves the target mode, makes a timestamped rollback
# backup, and refreshes provenance and the record from the bytes it actually installed.
set -eu
LC_ALL=C
export LC_ALL
PROG=repair-core-catalogues.sh
TAB=$(printf '\t')

usage() {
    cat >&2 <<USAGE
usage: $PROG --root DIR --record FILE --state DIR --plugin-dir DIR --merge-helper FILE
             --pristine-table FILE [--apply --backup DIR]
USAGE
    exit 2
}

die() {
    echo "ABORT: $*" >&2
    exit 1
}

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

file_mode() {
    if stat -f %Lp "$1" >/dev/null 2>&1; then
        stat -f %Lp "$1"
    else
        stat -c %a "$1"
    fi
}

field() { sed -n "s/^$1=//p" "$2" | tail -1; }

# Only a locale's own generated core catalogue is in scope. Never derive a path from a record
# line that names something else.
catalogue_locale() {
    case "$1" in
        /usr/local/share/locale/*/LC_MESSAGES/OPNsense.mo) : ;;
        *) return 1 ;;
    esac
    lang=${1#/usr/local/share/locale/}
    lang=${lang%%/*}
    [ "$1" = "/usr/local/share/locale/$lang/LC_MESSAGES/OPNsense.mo" ] || return 1
    [ -n "$lang" ] && [ "$lang" != en_US ] || return 1
    case "$lang" in *' '*|*"$TAB"*|*..*|*/*) return 1 ;; esac
    printf '%s\n' "$lang"
}

safe_path() {
    case "$1" in /*) : ;; *) return 1 ;; esac
    case "$1" in *' '*|*"$TAB"*|*..*) return 1 ;; esac
    [ "$1" != / ] && [ "$1" != '' ]
}

ROOT=
RECORD=
STATE=
PLUGIN_DIR=
MERGE_HELPER=
PRISTINE_TABLE=
APPLY=0
BACKUP=

while [ "$#" -gt 0 ]; do
    case "$1" in
        --root) [ "$#" -ge 2 ] || usage; ROOT=$2; shift 2 ;;
        --record) [ "$#" -ge 2 ] || usage; RECORD=$2; shift 2 ;;
        --state) [ "$#" -ge 2 ] || usage; STATE=$2; shift 2 ;;
        --plugin-dir) [ "$#" -ge 2 ] || usage; PLUGIN_DIR=$2; shift 2 ;;
        --merge-helper) [ "$#" -ge 2 ] || usage; MERGE_HELPER=$2; shift 2 ;;
        --pristine-table) [ "$#" -ge 2 ] || usage; PRISTINE_TABLE=$2; shift 2 ;;
        --backup) [ "$#" -ge 2 ] || usage; BACKUP=$2; shift 2 ;;
        --apply) APPLY=1; shift ;;
        *) usage ;;
    esac
done

[ -n "$ROOT" ] && [ -n "$RECORD" ] && [ -n "$STATE" ] && [ -n "$PLUGIN_DIR" ] &&
    [ -n "$MERGE_HELPER" ] && [ -n "$PRISTINE_TABLE" ] || usage
[ -d "$ROOT" ] || die "root is not a directory: $ROOT"
ROOT=$(CDPATH= cd -- "$ROOT" && pwd -P)
[ -f "$RECORD" ] && [ ! -L "$RECORD" ] || die "install record missing: $RECORD"
[ -d "$STATE" ] && [ ! -L "$STATE" ] || die "core-locale state missing: $STATE"
[ -d "$PLUGIN_DIR" ] && [ ! -L "$PLUGIN_DIR" ] || die "plugin catalogue directory missing: $PLUGIN_DIR"
[ -f "$MERGE_HELPER" ] && [ ! -L "$MERGE_HELPER" ] || die "merge helper missing: $MERGE_HELPER"
[ -f "$PRISTINE_TABLE" ] && [ ! -L "$PRISTINE_TABLE" ] || die "pristine table missing: $PRISTINE_TABLE"
if [ "$APPLY" = 1 ]; then
    [ -n "$BACKUP" ] || die '--apply requires --backup'
    case "$BACKUP" in /*) : ;; *) die '--backup must be an absolute path' ;; esac
    [ ! -e "$BACKUP" ] || die "backup path already exists: $BACKUP"
fi
command -v msgfmt >/dev/null 2>&1 || die 'msgfmt missing'
command -v python3 >/dev/null 2>&1 || die 'python3 missing'

STAGE=$(mktemp -d "${TMPDIR:-/tmp}/dm_catalogue_repair.XXXXXX")
trap 'rm -rf "$STAGE"' EXIT
: > "$STAGE/plan"

# Validate the full plan before creating a backup or replacing a target. The plan row is:
#   lang target predecessor expected pristine-source baseline-digest baseline-name
while IFS=' ' read -r hash path rest; do
    case "$hash" in ''|'#'*) continue ;; esac
    [ -n "$path" ] && [ -z "$rest" ] || die "malformed install record row"
    safe_path "$path" || die "unsafe record path: $path"
    # This helper owns only the nine locale catalogues. Other install targets are left exactly
    # as recorded; a record row that is not a supported catalogue is not a repair target.
    lang=$(catalogue_locale "$path") || continue
    metadata=$STATE/$lang.state
    [ -f "$metadata" ] && [ ! -L "$metadata" ] || die "no core-locale metadata for $lang"
    installed=$(field installed "$metadata")
    [ "$(field target "$metadata")" = "$path" ] || die "state target differs for $lang"
    [ "$installed" = "$hash" ] || die "record/state digest disagreement for $lang"
    pristine=$(field pristine "$metadata")
    case "$pristine" in
        # A repair marker names the baseline's digest and name from the shipped table; a live
        # state file is not allowed to invent a pristine digest.
        pattern:*) pattern=${pristine#pattern:} ;;
        ''|absent) die "no pristine catalogue baseline for $lang" ;;
        *) pattern= ;;
    esac
    plugin=$PLUGIN_DIR/$lang/LC_MESSAGES/devicemonitor.po
    [ -f "$plugin" ] && [ ! -L "$plugin" ] || die "plugin catalogue missing for $lang"
    if [ -n "$pattern" ]; then
        row=$(awk -v p="$pattern" 'NF == 3 && $1 == p {print; exit}' "$PRISTINE_TABLE")
        set -- $row
        [ "$#" -eq 3 ] || die "no pristine table row for $pattern ($lang)"
        baseline_name=$1
        baseline_digest=$2
        baseline_source=$3
        [ "$baseline_name" = "$pattern" ] || die "pristine table name mismatch for $lang"
        [ -f "$baseline_source" ] && [ ! -L "$baseline_source" ] ||
            die "pristine baseline is not a regular file for $lang"
        [ "$(digest "$baseline_source")" = "$baseline_digest" ] ||
            die "pristine baseline digest mismatch for $lang"
    else
        baseline_source=$STATE/$lang.OPNsense.mo
        [ -f "$baseline_source" ] && [ ! -L "$baseline_source" ] ||
            die "pristine snapshot missing for $lang"
        [ "$(digest "$baseline_source")" = "$pristine" ] ||
            die "pristine snapshot digest mismatch for $lang"
        baseline_name=$lang.OPNsense.mo
        baseline_digest=$pristine
    fi
    msgfmt --check -o "$STAGE/$lang.plugin.mo" "$plugin" >/dev/null || die "gettext $lang"
    cp -p "$baseline_source" "$STAGE/$lang.baseline.mo" || die "stage baseline $lang"
    [ "$(digest "$STAGE/$lang.baseline.mo")" = "$baseline_digest" ] || die "baseline copy mismatch $lang"
    /bin/sh "$MERGE_HELPER" "$STAGE/$lang.baseline.mo" "$plugin" "$STAGE/$lang.expected.mo" ||
        die "catalogue merge failed $lang"
    [ "$(digest "$STAGE/$lang.baseline.mo")" = "$baseline_digest" ] || die "merge changed the baseline $lang"
    expected=$(digest "$STAGE/$lang.expected.mo")
    target=$ROOT$path
    [ ! -L "$target" ] || die "target is a symlink: $path"
    if [ -f "$target" ]; then
        predecessor=$(digest "$target")
    else
        predecessor=absent
    fi
    # Record the derived baseline as a staged copy, not the live source path. The merge helper
    # can run arbitrary work between planning and the guarded replacement; the plan must not
    # expose a live path that a later stage could mistake for the predecessor.
    staged_baseline=$STAGE/$lang.recorded.mo
    cp -p "$STAGE/$lang.baseline.mo" "$staged_baseline" || die "stage recorded baseline $lang"
    [ "$(digest "$staged_baseline")" = "$baseline_digest" ] ||
        die "recorded baseline copy mismatch $lang"
    printf '%s %s %s %s %s %s %s\n' "$lang" "$path" "$predecessor" "$expected" \
        "$staged_baseline" "$baseline_digest" "$baseline_name" >> "$STAGE/plan"
done < "$RECORD"
[ -s "$STAGE/plan" ] || die 'record has no core catalogue targets'

changes=0
while read -r lang path predecessor expected baseline_source baseline_digest baseline_name; do
    if [ "$predecessor" = "$expected" ]; then
        action=unchanged
    else
        action=replace
        changes=$((changes + 1))
    fi
    printf 'CATALOGUE_PLAN=%s predecessor=%s expected=%s action=%s\n' \
        "$path" "$predecessor" "$expected" "$action"
done < "$STAGE/plan"
replaced=$changes

if [ "$APPLY" = 0 ]; then
    if [ "$changes" -gt 0 ]; then
        echo "CATALOGUE_REPAIR_PLAN=changes count=$changes"
        exit 1
    fi
    echo 'CATALOGUE_REPAIR_PLAN=clean count=0'
    exit 0
fi
if [ "$changes" = 0 ]; then
    echo 'CATALOGUE_REPAIR_OK replaced=0'
    exit 0
fi

mkdir -p "$BACKUP/files" "$BACKUP/state" || die 'cannot create backup directory'
cp -p "$RECORD" "$BACKUP/record" || die 'cannot back up the install record'
[ "$(digest "$BACKUP/record")" = "$(digest "$RECORD")" ] || die 'install-record backup mismatch'
for file in "$STATE"/*.state "$STATE"/*.OPNsense.mo; do
    [ -e "$file" ] || continue
    [ -f "$file" ] && [ ! -L "$file" ] || die "irregular state file: $file"
    cp -p "$file" "$BACKUP/state/${file##*/}" || die "state backup ${file##*/}"
    [ "$(digest "$BACKUP/state/${file##*/}")" = "$(digest "$file")" ] || die "state backup mismatch: $file"
done
: > "$BACKUP/replaced"
: > "$BACKUP/record.new"
while read -r lang path predecessor expected baseline_source baseline_digest baseline_name; do
    if [ "$predecessor" = "$expected" ]; then
        continue
    fi
    if [ "$predecessor" = absent ]; then
        printf '%s %s absent\n' "$lang" "$path" >> "$BACKUP/replaced"
    else
        cp -p "$ROOT$path" "$BACKUP/files/$lang.OPNsense.mo" || die "target backup $lang"
        [ "$(digest "$BACKUP/files/$lang.OPNsense.mo")" = "$predecessor" ] || die "target backup mismatch $lang"
        printf '%s %s %s\n' "$lang" "$path" "$predecessor" >> "$BACKUP/replaced"
    fi
done < "$STAGE/plan"

# One guard covers the first write: every planned predecessor must still be exactly what the
# plan saw. A changed target is a conflict, not something this helper may overwrite.
while read -r lang path predecessor expected baseline_source baseline_digest baseline_name; do
    target=$ROOT$path
    if [ "$predecessor" = absent ]; then
        [ ! -e "$target" ] || die "target appeared after planning: $path"
    else
        [ -f "$target" ] && [ ! -L "$target" ] || die "target is no longer regular: $path"
        [ "$(digest "$target")" = "$predecessor" ] || die "target changed after planning: $path"
    fi
done < "$STAGE/plan"

ROLLING=0
rollback() {
    rc=$?
    trap - EXIT
    if [ "$rc" -ne 0 ] && [ "$ROLLING" = 1 ]; then
        echo "CATALOGUE_REPAIR_ROLLBACK=$BACKUP" >&2
        saved=0
        while read -r lang path predecessor; do
            target=$ROOT$path
            if [ "$predecessor" = absent ]; then
                rm -f "$target"
            else
                cp -p "$BACKUP/files/$lang.OPNsense.mo" "$target" || saved=1
            fi
        done < "$BACKUP/replaced"
        for file in "$BACKUP/state"/*.state "$BACKUP/state"/*.OPNsense.mo; do
            [ -e "$file" ] || continue
            cp -p "$file" "$STATE/${file##*/}" || saved=1
        done
        cp -p "$BACKUP/record" "$RECORD" || saved=1
        if [ "$saved" = 0 ]; then echo 'CATALOGUE_REPAIR_ROLLED_BACK=1' >&2
        else echo 'CATALOGUE_REPAIR_ROLLBACK_INCOMPLETE=1' >&2; fi
    fi
    rm -rf "$STAGE"
    exit "$rc"
}
trap rollback EXIT
ROLLING=1

while read -r lang path predecessor expected baseline_source baseline_digest baseline_name; do
    [ "$predecessor" = "$expected" ] && continue
    target=$ROOT$path
    # The one-shot guard above is not enough: planning runs external merge helpers, which can
    # take long enough for a concurrent change. Recheck immediately before this write.
    if [ "$predecessor" = absent ]; then
        [ ! -e "$target" ] || die "target appeared before replacement: $path"
    else
        [ -f "$target" ] && [ ! -L "$target" ] || die "target is no longer regular: $path"
        [ "$(digest "$target")" = "$predecessor" ] || die "target changed before replacement: $path"
    fi
    old_mode=644
    [ "$predecessor" = absent ] || old_mode=$(file_mode "$target")
    cp -p "$STAGE/$lang.expected.mo" "$target.new" || die "stage target $lang"
    chmod "$old_mode" "$target.new" || die "mode target $lang"
    [ "$(digest "$target.new")" = "$expected" ] || die "staged target mismatch $lang"
    mv -f "$target.new" "$target" || die "replace target $lang"
    [ "$(digest "$target")" = "$expected" ] || die "post-replacement mismatch $lang"
    [ "$(file_mode "$target")" = "$old_mode" ] || die "mode not preserved $lang"
    printf 'CATALOGUE_REPLACED=%s hash=%s\n' "$path" "$expected"
done < "$STAGE/plan"

# Update the provenance and the record only after every replacement passed its post-check.
while read -r lang path predecessor expected baseline_source baseline_digest baseline_name; do
    [ "$predecessor" = "$expected" ] && continue
    metadata=$STATE/$lang.state
    cp -p "$STAGE/$lang.baseline.mo" "$STATE/$lang.OPNsense.mo" || die "baseline snapshot $lang"
    chmod 644 "$STATE/$lang.OPNsense.mo"
    {
        printf 'pristine=pattern:%s\ntarget=%s\ninstalled=%s\n' \
            "$baseline_name" "$path" "$(digest "$ROOT$path")"
    } > "$metadata.new"
    [ "$(field installed "$metadata.new")" = "$expected" ] || die "metadata hash $lang"
    chmod 644 "$metadata.new"
    mv -f "$metadata.new" "$metadata" || die "metadata update $lang"
done < "$STAGE/plan"
{
    while IFS=' ' read -r hash path rest; do
        case "$hash" in
            '#'*) printf '%s %s\n' "$hash" "$path" ;;
            '') ;;
            *) [ -z "$rest" ] || die "malformed install record row"
               safe_path "$path" || die "unsafe record path: $path"
               # Only rows this repair owns are re-derived. Every other install target keeps
               # its recorded digest even if its file has drifted for an unrelated reason.
               if catalogue_locale "$path" >/dev/null 2>&1 && [ -f "$ROOT$path" ]; then
                   printf '%s %s\n' "$(digest "$ROOT$path")" "$path"
               else
                   printf '%s %s\n' "$hash" "$path"
               fi ;;
        esac
    done < "$BACKUP/record"
} > "$BACKUP/record.new"
[ "$(grep -vc '^#' "$BACKUP/record")" = "$(grep -vc '^#' "$BACKUP/record.new")" ] ||
    die 'install record row count changed'
chmod "$(file_mode "$RECORD")" "$BACKUP/record.new"
mv -f "$BACKUP/record.new" "$RECORD" || die 'install record update'
while read -r lang path predecessor expected baseline_source baseline_digest baseline_name; do
    [ "$predecessor" = "$expected" ] && continue
    grep -qx "$expected $path" "$RECORD" || die "record not updated for $lang"
done < "$STAGE/plan"
ROLLING=0
trap - EXIT
rm -rf "$STAGE"
printf 'CATALOGUE_REPAIR_OK backup=%s replaced=%s\n' "$BACKUP" "$replaced"

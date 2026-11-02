#!/bin/sh
# Emit the targets this installer previously installed but the new manifest no longer ships.
#
#   compute-prune.sh INSTALLED_LIST MANIFEST
#
# Output is one absolute path per line, sorted, filtered to the namespaces the manifest is
# allowed to own. The caller backs each one up and deletes it after the install succeeds;
# nothing is deleted here, so a dry run can call this and report the count.
#
# The list is what a previous install recorded (see install-unattended.sh), never a
# directory scan: the installer must not touch a file it did not install itself.
set -eu

[ "$#" -eq 2 ] || { echo 'usage: compute-prune.sh INSTALLED_LIST MANIFEST' >&2; exit 2; }

installed_list=$1
manifest=$2

[ -f "$installed_list" ] || exit 0
[ -f "$manifest" ] || { echo "compute-prune: manifest missing: $manifest" >&2; exit 1; }

work=$(mktemp -d "${TMPDIR:-/tmp}/dm-prune.XXXXXX")
trap 'rm -rf "$work"' EXIT

sort -u "$installed_list" > "$work/installed"
awk '{print $4}' "$manifest" | sort -u > "$work/current"

# Paths only in the old list, restricted to the namespaces the manifest is allowed to own.
comm -23 "$work/installed" "$work/current" |
    grep -E '^(/usr/local/opnsense/|/usr/local/etc/rc\.d/devicemonitor$|/usr/local/etc/inc/plugins\.inc\.d/devicemonitor\.inc$|/usr/local/etc/inc/devicemonitor_locale\.inc$)' ||
    true

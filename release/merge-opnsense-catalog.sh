#!/bin/sh
# Prepare one shared OPNsense.mo without modifying the installed catalogue.
set -eu
[ "$#" -eq 3 ] || { echo 'usage: merge-opnsense-catalog.sh CORE.mo PLUGIN.po OUTPUT.mo' >&2; exit 2; }
core=$1
plugin=$2
output=$3
[ -f "$core" ] && [ ! -L "$core" ] && [ -f "$plugin" ] && [ ! -L "$plugin" ] || exit 1
[ ! -e "$output" ] && [ ! -L "$output" ] || exit 1
stage=$(mktemp -d /tmp/dm_locale_merge.XXXXXX)
trap 'rm -rf "$stage"' EXIT
msgunfmt -o "$stage/core.po" "$core"
# Core comes first: conflicting OPNsense translations keep their existing value.
msgcat --use-first --no-location --sort-output -o "$stage/merged.po" "$stage/core.po" "$plugin"
msgfmt --check -o "$output" "$stage/merged.po"
msgfmt --check -o "$stage/plugin.mo" "$plugin"
python3 - "$core" "$stage/plugin.mo" "$output" <<'PY'
import gettext
import sys

def catalogue(path):
    with open(path, 'rb') as stream:
        return gettext.GNUTranslations(stream)._catalog

original, plugin, merged = map(catalogue, sys.argv[1:])
for key, value in original.items():
    if key != '' and merged.get(key) != value:
        raise SystemExit('ABORT: existing OPNsense translation changed')
for key, value in plugin.items():
    if key != '' and key not in original and merged.get(key) != value:
        raise SystemExit('ABORT: plugin translation missing from merged catalogue')
PY

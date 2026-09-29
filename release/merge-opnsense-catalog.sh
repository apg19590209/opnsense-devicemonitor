#!/bin/sh
# Prepare one shared OPNsense.mo without modifying the installed catalogue.
#
# DM-BL-008c. Two modes:
#
#   merge-opnsense-catalog.sh CORE.mo PLUGIN.po OUTPUT.mo
#       Core-first merge: the existing OPNsense translations keep their value and the plugin's
#       keys are added. Aborts if an existing OPNsense translation changed or if any plugin
#       string is missing from the result.
#
#   merge-opnsense-catalog.sh --plugin-only PLUGIN.po OUTPUT.mo
#       For a locale whose core catalogue does not exist (nl_NL on the current release): the
#       plugin catalogue alone, with the same "every plugin string present" assertion. There is
#       no core input to preserve, so this path never aborts on a missing core file.
#
# In both modes the installed catalogue is only ever read; OUTPUT must not exist yet, so the
# caller stages the result and decides when to install it.
set -eu

usage() {
    echo 'usage: merge-opnsense-catalog.sh CORE.mo PLUGIN.po OUTPUT.mo' >&2
    echo '       merge-opnsense-catalog.sh --plugin-only PLUGIN.po OUTPUT.mo' >&2
    exit 2
}

plugin_only=0
if [ "${1:-}" = '--plugin-only' ]; then
    plugin_only=1
    shift
fi

if [ "$plugin_only" = 1 ]; then
    [ "$#" -eq 2 ] || usage
    core=
    plugin=$1
    output=$2
else
    [ "$#" -eq 3 ] || usage
    core=$1
    plugin=$2
    output=$3
fi

[ -f "$plugin" ] && [ ! -L "$plugin" ] || { echo "ABORT: plugin catalogue $plugin" >&2; exit 1; }
[ ! -e "$output" ] && [ ! -L "$output" ] || { echo "ABORT: output exists $output" >&2; exit 1; }
if [ "$plugin_only" = 0 ]; then
    [ -f "$core" ] && [ ! -L "$core" ] || { echo "ABORT: core catalogue $core" >&2; exit 1; }
fi

stage=$(mktemp -d /tmp/dm_locale_merge.XXXXXX)
trap 'rm -rf "$stage"' EXIT

# The plugin catalogue compiled on its own: the reference for the assertion in both modes.
msgfmt --check -o "$stage/plugin.mo" "$plugin"

if [ "$plugin_only" = 1 ]; then
    cp "$stage/plugin.mo" "$output"
    chmod 644 "$output"
    python3 - "$stage/plugin.mo" "$output" <<'PY'
import gettext
import sys

def catalogue(path):
    with open(path, 'rb') as stream:
        return gettext.GNUTranslations(stream)._catalog

plugin, result = map(catalogue, sys.argv[1:3])
for key, value in plugin.items():
    if key != '' and result.get(key) != value:
        raise SystemExit('ABORT: plugin translation missing from the result catalogue')
PY
    exit 0
fi

msgunfmt -o "$stage/core.po" "$core"
# Core comes first: conflicting OPNsense translations keep their existing value.
msgcat --use-first --no-location --sort-output -o "$stage/merged.po" "$stage/core.po" "$plugin"
msgfmt --check -o "$output" "$stage/merged.po"
python3 - "$core" "$stage/plugin.mo" "$output" <<'PY'
import gettext
import sys

def catalogue(path):
    with open(path, 'rb') as stream:
        return gettext.GNUTranslations(stream)._catalog

original, plugin, merged = map(catalogue, sys.argv[1:4])
for key, value in original.items():
    if key != '' and merged.get(key) != value:
        raise SystemExit('ABORT: existing OPNsense translation changed')
for key, value in plugin.items():
    if key != '' and key not in original and merged.get(key) != value:
        raise SystemExit('ABORT: plugin translation missing from merged catalogue')
PY

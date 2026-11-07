#!/bin/sh
# Prepare one shared OPNsense.mo without modifying the installed catalogue.
#
# DM-BL-008c. Two modes:
#
#   merge-opnsense-catalog.sh CORE.mo PLUGIN.po OUTPUT.mo
#       Core-first merge: the existing OPNsense translations keep their value and the plugin's
#       keys are added. Aborts if an existing OPNsense translation changed or if any plugin
#       string is missing from the result. Missing PO header metadata fields are filled from
#       the plugin's own metadata so msgfmt --check does not warn about the merged catalogue;
#       metadata already present in the core catalogue is never replaced.
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

# A sparse core catalogue can omit PO-Revision-Date, Last-Translator or Language-Team.  msgcat
# keeps the first header, so those missing fields would survive into the merged catalogue and
# msgfmt --check would warn about them.  Fill only absent/empty fields from the plugin's real
# metadata.  The plugin itself must be complete: this is a repair, not a way to invent an
# author or language team.  The rewritten core is validated before it is used.
python3 - "$core" "$stage/plugin.mo" "$stage/core.po" "$stage/core-fed.po" <<'PY'
import gettext
import struct
import sys

FIELDS = ('PO-Revision-Date', 'Last-Translator', 'Language-Team')


def fail(message):
    raise SystemExit('ABORT: %s' % message)


def info(path):
    try:
        with open(path, 'rb') as stream:
            return gettext.GNUTranslations(stream).info()
    except (OSError, UnicodeError, ValueError, EOFError, struct.error) as exc:
        fail('cannot read catalogue metadata %s: %s' % (path, exc))


def metadata_value(values, field):
    value = values.get(field.lower(), '')
    if not isinstance(value, str):
        fail('non-text metadata field %s' % field)
    if not value.strip():
        return None
    if any(ord(char) < 32 and char != '\t' for char in value):
        fail('control character in metadata field %s' % field)
    return value


def quoted(field, value):
    value = value.replace('\\', '\\\\').replace('"', '\\"')
    return '"%s: %s\\n"\n' % (field, value)


core_values = info(sys.argv[1])
plugin_values = info(sys.argv[2])
plugin_metadata = {}
for field in FIELDS:
    value = metadata_value(plugin_values, field)
    if value is None:
        fail('plugin metadata field %s missing or empty' % field)
    plugin_metadata[field] = value

missing = []
for field in FIELDS:
    value = metadata_value(core_values, field)
    if value is None:
        missing.append(field)

with open(sys.argv[3], encoding='utf-8') as stream:
    lines = stream.readlines()

header_start = None
for index, line in enumerate(lines):
    if line.rstrip('\n') == 'msgid ""':
        header_start = index
        break
if header_start is None:
    fail('core catalogue has no header message')
if header_start + 1 >= len(lines) or lines[header_start + 1].rstrip('\n') != 'msgstr ""':
    fail('core catalogue header is not in msgunfmt form')

insert_at = header_start + 2
while insert_at < len(lines) and lines[insert_at].startswith('"'):
    insert_at += 1
if insert_at == len(lines) and lines and not lines[-1].endswith('\n'):
    lines[-1] += '\n'

if missing:
    additions = [quoted(field, plugin_metadata[field]) for field in missing]
    lines[insert_at:insert_at] = additions

with open(sys.argv[4], 'w', encoding='utf-8', newline='') as stream:
    stream.writelines(lines)
PY

msgfmt --check -o "$stage/core-fed.mo" "$stage/core-fed.po"
# Core comes first: conflicting OPNsense translations keep their existing value.
msgcat --use-first --no-location --sort-output -o "$stage/merged.po" "$stage/core-fed.po" "$plugin"
msgfmt --check -o "$output" "$stage/merged.po"
python3 - "$core" "$stage/plugin.mo" "$output" <<'PY'
import gettext
import sys

def catalogue(path):
    with open(path, 'rb') as stream:
        return gettext.GNUTranslations(stream)._catalog

original, plugin, merged = map(catalogue, sys.argv[1:4])
def info(path):
    with open(path, 'rb') as stream:
        return gettext.GNUTranslations(stream).info()

original_info = info(sys.argv[1])
merged_info = info(sys.argv[3])
for field, value in original_info.items():
    if value and merged_info.get(field) != value:
        raise SystemExit('ABORT: existing OPNsense catalogue metadata changed: %s' % field)
for key, value in original.items():
    if key != '' and merged.get(key) != value:
        raise SystemExit('ABORT: existing OPNsense translation changed')
for key, value in plugin.items():
    if key != '' and key not in original and merged.get(key) != value:
        raise SystemExit('ABORT: plugin translation missing from merged catalogue')
PY

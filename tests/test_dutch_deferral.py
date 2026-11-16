"""Dutch (nl_NL) is deferred and must not be delivered (DM-BL-008a).

Pins one supported-locale policy shared by the installer and the bundler, and the safety rules
that retire a previously installed Dutch catalogue without touching package-owned or
independently modified core catalogues.
"""
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
POLICY = ROOT / "release/supported-locales.sh"
INSTALLER = ROOT / "install-unattended.sh"
BUNDLER = ROOT / "release/build-bundle.sh"
MANIFEST = ROOT / "release/v2.14.0-runtime.manifest"


def policy_locales():
    out = subprocess.run(["sh", "-c", '. "$1"; printf "%s" "$SUPPORTED_LOCALES"', "sh", str(POLICY)],
                         capture_output=True, text=True, check=True).stdout
    return out.split()


def test_policy_is_explicit_and_excludes_dutch():
    locales = policy_locales()
    assert "nl_NL" not in locales, locales
    for required in ("en_US", "cs_CZ", "de_DE", "fr_FR", "es_ES", "it_IT", "pt_BR", "ru_RU", "ja_JP", "zh_CN"):
        assert required in locales, (required, locales)
    assert len(locales) == 10, locales
    print("DUTCH_POLICY_EXCLUDES_NL_NL=PASS")


def test_source_catalogue_is_retained():
    po = ROOT / "src/opnsense/mvc/app/languages/nl_NL/LC_MESSAGES/devicemonitor.po"
    assert po.is_file(), po
    text = po.read_text(encoding="utf-8")
    assert 'msgid "Devices"' in text, "retained source must still carry Dutch translations"
    print("DUTCH_SOURCE_RETAINED=PASS")


def test_installer_and_bundler_use_the_policy_not_discovery():
    installer = INSTALLER.read_text(encoding="utf-8")
    bundler = BUNDLER.read_text(encoding="utf-8")
    assert 'for lang in $SUPPORTED_LOCALES' in installer
    assert ". \"$SCRIPT_DIR/release/supported-locales.sh\"" in installer
    assert 'for lang in $SUPPORTED_LOCALES' in bundler
    assert ". \"$REPO/release/supported-locales.sh\"" in bundler
    assert "find src -name '*.po'" not in bundler, "broad file discovery must not select catalogues"
    assert not re.search(r"^for lang in en_US", installer, re.M), "hardcoded locale list present"
    print("DUTCH_POLICY_SINGLE_SOURCE=PASS")


def test_counts_are_derived_not_hardcoded():
    installer = INSTALLER.read_text(encoding="utf-8")
    assert "SIDECAR_LOCALES=$((SIDECAR_LOCALES + 1))" in installer
    assert "CORE_LOCALES=$((CORE_LOCALES + 1))" in installer
    assert "expected=$((MANIFEST_ROWS + SIDECAR_LOCALES + CORE_LOCALES))" in installer
    assert not re.search(r"^expected=[0-9]+$", installer, re.M), "hardcoded target count"
    print("DUTCH_COUNTS_DERIVED=PASS")


def test_no_dutch_runtime_targets_in_manifest():
    rows = [line.split() for line in MANIFEST.read_text().splitlines()]
    assert all("nl_NL" not in row[2] and "nl_NL" not in row[3] for row in rows), "nl_NL manifest row"
    print("DUTCH_ABSENT_FROM_MANIFEST=PASS")


def test_retirement_requires_provenance():
    installer = INSTALLER.read_text(encoding="utf-8")
    block = installer[installer.index("RETIRED_CORE=0"):installer.index("printf 'RETIRED_CORE_TOTAL=")]
    assert "pristine=////" not in block
    assert "pristine=//p" in block, "pristine provenance must be checked"
    assert "never deleted or replaced" in installer
    assert 'NOTICE: retained core catalogue for deferred locale' in block
    assert 'RETIRED_CORE=%s' in block
    # Never delete an arbitrary core path: only the locale's own OPNsense.mo.
    assert 'case "$target" in' in block and 'LC_MESSAGES/OPNsense.mo) :;;' in block
    print("DUTCH_RETIREMENT_PROVENANCE=PASS")


def test_deferred_locales_are_derived_from_the_policy():
    installer = INSTALLER.read_text(encoding="utf-8")
    block = installer[installer.index("RETIRED_CORE=0"):installer.index("printf 'RETIRED_CORE_TOTAL=")]
    assert 'case " $SUPPORTED_LOCALES " in' in block, "retirement must use the policy, not a name list"
    print("DUTCH_RETIREMENT_USES_POLICY=PASS")




# --- Behavioural simulation of the deferred-locale retirement loop -------------------------
#
# The installer's block is extracted and run against a temporary root so fresh, upgrade and
# repair outcomes are exercised, not just grepped. Options passed by the surrounding script are
# injected as fixed constants; nothing outside the temporary root is touched.

HARNESS = r'''
set -eu
SUPPORTED_LOCALES="$1"; CORE_LOCALE_STATE="$2"; BACKUP="$3"; PRUNE_HELPER=/bin/true; SCRIPT_DIR=/bin
LOCALES="$SUPPORTED_LOCALES"
LOOP=$(sed -n "/^RETIRED_CORE=0$/,/^printf 'RETIRED_CORE_TOTAL=/p" "$4")
# The installer matches literal core paths; the simulation rebases that one prefix onto the
# temporary root so the same matching and safety logic is exercised.
LOOP=$(printf '%s\n' "$LOOP" | sed "s#/usr/local/share/locale#${ROOT_PREFIX}/usr/local/share/locale#g")
eval "$LOOP"
'''

def run_retirement(tmp: Path, langs_present):
    import os
    state = tmp / "core-locale"
    state.mkdir(parents=True, exist_ok=True)
    backup = tmp / "backup"
    backup.mkdir(parents=True, exist_ok=True)
    installer = str(INSTALLER)
    # The loop treats an unexpected target as "not ours", so the simulation maps the real
    # absolute target into the temporary root via a chroot-like prefix rewrite.
    for lang, pristine, modified in langs_present:
        target = tmp / "usr/local/share/locale" / lang / "LC_MESSAGES" / "OPNsense.mo"
        target.parent.mkdir(parents=True, exist_ok=True)
        content = "core catalogue for %s\n" % lang
        target.write_text(content)
        import hashlib
        digest = hashlib.sha256(target.read_bytes()).hexdigest()
        if modified:
            target.write_text(content + "operator edit\n")
        (state / f"{lang}.state").write_text(
            f"pristine={pristine}\ntarget={tmp}/usr/local/share/locale/{lang}/LC_MESSAGES/OPNsense.mo\ninstalled={digest}\n")
    # Mirror the absolute target under the temp root so the loop's own path checks apply.
    env = dict(os.environ, ROOT_PREFIX=str(tmp))
    return subprocess.run(["sh", "-c", HARNESS, "sh", policy_string(), str(state), str(backup), installer],
                          capture_output=True, text=True, env=env)


def policy_string():
    return " ".join(policy_locales())


def test_fresh_install_has_no_dutch_output():
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        result = run_retirement(Path(tmp), [])
    assert result.returncode == 0, result.stderr
    assert "RETIRED_CORE_TOTAL=0" in result.stdout, result.stdout
    print("DUTCH_FRESH_NO_RETIREMENT=PASS")


def test_upgrade_retires_plugin_created_dutch_catalogue():
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        result = run_retirement(root, [("nl_NL", "absent", False)])
        target = root / "usr/local/share/locale/nl_NL/LC_MESSAGES/OPNsense.mo"
        backup = root / "backup/retired-nl_NL-OPNsense.mo"
        assert result.returncode == 0, result.stderr
        assert "RETIRED_CORE=nl_NL" in result.stdout, result.stdout
        assert not target.exists(), "plugin-created Dutch catalogue must be removed"
        assert backup.is_file(), "removed catalogue must be backed up for rollback"
    print("DUTCH_UPGRADE_RETIRES_PLUGIN_CORE=PASS")


def test_upgrade_retains_independently_modified_catalogue():
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        result = run_retirement(root, [("nl_NL", "absent", True)])
        target = root / "usr/local/share/locale/nl_NL/LC_MESSAGES/OPNsense.mo"
        assert result.returncode == 0, result.stderr
        assert target.exists(), "modified catalogue must never be deleted"
        assert "retained core catalogue for deferred locale nl_NL" in result.stderr, result.stderr
        assert "RETIRED_CORE_TOTAL=0" in result.stdout
    print("DUTCH_MODIFIED_CORE_RETAINED=PASS")


def test_upgrade_retains_package_owned_catalogue():
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        result = run_retirement(root, [("nl_NL", "abc123", False)])
        target = root / "usr/local/share/locale/nl_NL/LC_MESSAGES/OPNsense.mo"
        assert result.returncode == 0, result.stderr
        assert target.exists(), "package-owned (pristine recorded) catalogue must be kept"
        assert "retained core catalogue nl_NL (pristine recorded)" in result.stderr, result.stderr
    print("DUTCH_PACKAGE_OWNED_RETAINED=PASS")

def main():
    test_policy_is_explicit_and_excludes_dutch()
    test_source_catalogue_is_retained()
    test_installer_and_bundler_use_the_policy_not_discovery()
    test_counts_are_derived_not_hardcoded()
    test_no_dutch_runtime_targets_in_manifest()
    test_retirement_requires_provenance()
    test_deferred_locales_are_derived_from_the_policy()
    test_fresh_install_has_no_dutch_output()
    test_upgrade_retires_plugin_created_dutch_catalogue()
    test_upgrade_retains_independently_modified_catalogue()
    test_upgrade_retains_package_owned_catalogue()
    print("DUTCH_DEFERRAL_REGRESSION=PASS")


if __name__ == "__main__":
    main()

# Single source of truth for the shipped locale set (Decision 35, DM-BL-008a).
#
# Sourced by install-unattended.sh (compile + install loop) and by build-bundle.sh (archive
# membership). Both read SUPPORTED_LOCALES; never add broad `find`-based catalogue discovery,
# because a retained-but-unsupported translation source must stay out of the payload.
#
# Dutch (`nl_NL`) is DEFERRED (DM-BL-008a): its .po stays in the repository as translation
# source, but OPNsense core does not offer nl_NL in get_locale_list(), so a catalogue that
# cannot be selected must not be installed or shipped. Re-add it here only when OPNsense core
# offers Dutch and this list is deliberately changed in the same commit.
SUPPORTED_LOCALES="en_US cs_CZ de_DE fr_FR es_ES it_IT pt_BR ru_RU ja_JP zh_CN"

# Locale verification deferrals

Status of items raised by the locale verification tracks. Updated 2026-09-28.

## Status legend

| Status | Meaning |
| --- | --- |
| `DEFERRED` | Consciously not actioned yet; owner and revisit trigger recorded. |
| `PENDING-EVIDENCE` | Claimed or reported done, but no artifact exists to close it. Not resolved. |
| `RESOLVED` | Closed, with an artifact trail referenced. Not used in this file yet. |

## Items

### F1

- Status: `DEFERRED` (unchanged)
- Note: description not present in this repository. The identifier `F1` appears in the
  French verification commit message only, with no in-tree definition. Owned content
  must be supplied from the tracking system before this entry can carry a description,
  owner, or revisit trigger.

### DM-BL-008b

- Status: `PENDING-EVIDENCE` — **not resolved**
- Reported: 2026-09-28, operator-reported Italian pass against `192.168.20.23`; both
  reported check strings passed (`[Riepilogo modifiche]`, `[Monitoraggio dispositivi]`).
- Blocker still open because: no harness output, no result artifact, no stream timeline,
  no screenshot or page source, no OPNsense build/version, and no pre/post locale state
  were provided. See `REPORT-it_IT-2026-09-28.md` → *Evidence gap*.
- Cleared when: the evidence checklist on `REPORT-it_IT-2026-09-28.md` is satisfied and
  the acceptance criteria for `DM-BL-008b` are checked against it.

### DM-BL-008c

- Status: `DEFERRED` (unchanged)
- Note: recorded as deferred in the French text-stream verification commit. No evidence
  of closure was supplied with the Italian pass, and the Italian pass does not cover
  this item, so its deferral stands.

## Blockers cleared by this update

**None.** No deferral track was unblocked. The operator-reported Italian pass is a
useful signal, but two quoted label strings without artifacts cannot close any of the
three items above.

## What would clear each item

Only artifacts, not further attestation. For `DM-BL-008b`, the minimum is: the run's
raw output plus result JSON/HTML, a stream timeline, one screenshot or page source, the
tool/version used, and the OPNsense build plus before/after locale state for the
reported `en_US` restore.

## Appendix — Upstream Environment Warnings

Raised 2026-09-28 while investigating `O2` (Dutch language selection). These are
host/environment integrity observations, not locale-verification results: they close
nothing in this file and no acceptance-checklist artifact was produced by them.

### W1. Nine package-owned core catalogs no longer match `opnsense-lang`

`pkg check -s opnsense-lang` reports a checksum mismatch for 9 of the 19 core catalogs owned
by `opnsense-lang-26.1.7` (package installed 2026-07-14 01:24:21 AEST). The recorded values
below come from the local package database
(`sqlite3 /var/db/pkg/local.sqlite "select path, sha256 from files where path like
'%OPNsense.mo'"`, with the `1$` format prefix stripped) and were compared against the file's
own `sha256` on disk.

| Locale | pkg-recorded sha256 | on-disk sha256 | on-disk bytes | on-disk mtime |
| --- | --- | --- | --- | --- |
| `cs_CZ` | `e19148e4424740f320e26123a4afd35a1d69debde01dd688e106667dab6919a8` | `5876dfb110d26f42324e94035cfa5551bcb943df2dd004a08bba3079c650ee1f` | 1646972 | 2026-09-26 23:16:15 |
| `de_DE` | `e1d29d0a5d0714864cf9d1c1074795302c23814aecd7e04b59ba467667557c6e` | `75c269909d705d91b995578bb3f8f667422d00e6b15eb775fad77a3477494974` | 1642576 | 2026-09-26 23:16:01 |
| `es_ES` | `be56637abfd579d3c1eed34d0b8434a6a8a38ca5ba39c8b7fe5e44bca5fdbac8` | `1104496c52f19f9aa2bddba32732cd292316aee878dfce6b9bc337f6c12707bd` | 782684 | 2026-09-26 23:15:56 |
| `fr_FR` | `817bf137643c872d240f300dce713718033347435ca98c7cbec61f3709b823d2` | `a5ade5cdf62ac010ce2fef94e3ba81bd25609a26f8a66deb9753955651d30a2f` | 1680480 | 2026-09-26 23:16:06 |
| `it_IT` | `555c909f313e3f560400936281815169aed15b25d694ea86abfa434f6458dad2` | `7340219d5d216cbda507080465fb9769c1ace1919cf138bb34285384c0d211fd` | 1419450 | 2026-09-26 23:16:09 |
| `ja_JP` | `104cbc43c4e35d7f271536d8c61db76e2056a18434e25b3f7d213bde9750db48` | `ab8ad9a907d3d67cd9ec70d81663200a0524ffd06e73a64bba9ce1bc9ab64de3` | 681257 | 2026-09-26 23:16:18 |
| `pt_BR` | `f3c77c7ab05f724c1355ea084523b52def273b5b8419af34c197a9e7c806aa8b` | `42d0e726c69215bf4f15792a08ecd5ebe4b42d0a701cf9218ac08dbb96fa5de9` | 537071 | 2026-09-26 23:16:11 |
| `ru_RU` | `b0bd7e3d8ece0c72892a6e98451c5442619e43dad066330cae4e8fc626b69dfc` | `c06ebe69140b416f215f871a7f732f2ea96a80de6565a5f351dfca25eee6b40e` | 588474 | 2026-09-26 23:16:16 |
| `zh_CN` | `98e3bce543ead94a863a2c42767744a24d36cac785dbd31dbbece4594692c62d` | `1670e6fae2e0466a45b58636541db0e57532cbfb633d90e7f2fe4c61bf0fb6fd` | 1445947 | 2026-09-26 23:16:21 |

Matching (10): `el_GR`, `fa_IR`, `ko_KR`, `no_NO`, `pl_PL`, `pt_PT`, `tr_TR`, `uk_UA`,
`vi_VN`, `zh_TW` — still carrying the 2026-07-07 04:43:39-41 stamp of the package install.

- The nine mismatched files all carry a 2026-09-26 23:15:56-23:16:21 stamp; the ten matching
  files still carry the install stamp. The rewrite was not performed by `pkg`.
- Cause not established by this workstream. What is established: `pkg check -s
  opnsense-lang` is not a clean integrity signal on this host, and the on-disk content of
  those nine catalogs is not the content recorded by `opnsense-lang-26.1.7`. Any claim that
  a locale "matches the shipped translation" must be checked against the file's own
  checksum, not against the package.
- Two of the nine (`fr_FR`, `it_IT`) are already tracked in this directory. Those records
  assert only what the operator reported; this finding neither strengthens nor contradicts
  them.

### W2. An unowned Dutch catalog sat at a core locale path (removed 2026-09-28)

`/usr/local/share/locale/nl_NL/LC_MESSAGES/OPNsense.mo` (34,085 bytes, stamped
2026-09-26 23:16:21) was absent from the package database (`pkg which` → *not found*), while
all 19 sibling catalogs belong to `opnsense-lang-26.1.7`. It was byte-identical to the
Device Monitor plugin catalog `/usr/local/opnsense/mvc/app/languages/nl_NL_devicemonitor.mo`
(sha256 `8bb2a6c7947ecef25f11dbc5648673c050a08f1726a53008264ab276835e1579`, md5
`1a7651bce06f77744d5ef43b2d8cc4f8`): `Project-Id-Version: Device Monitor 2.10`, 452 msgids,
none of the core GUI strings, and a `.po` header noting machine translation.

`set_language()` (`/usr/local/www/authgui.inc:39-68`) and the MVC
`OPNsense/Base/ControllerRoot.php:88-98` bind the `OPNsense` text domain to
`/usr/local/share/locale` for whatever `system.language` holds, and neither checks that a
catalog exists. A `system.language` of `nl_NL` (config restore, API call, manual edit) would
therefore have loaded that plugin catalog as the core domain: 452 plugin strings translated,
every other string silently falling back to English, with the locale looking "installed" to
any directory-based check.

The file and the then-empty `nl_NL/LC_MESSAGES/` directory were removed on 2026-09-28; a copy
is retained outside the locale tree at `/root/opnsense-quarantine-20260928/`. The Dutch menu
entry is *not* restored: that is `PRODUCT_BACKLOG.md` → `O2`, `CLOSED` as an upstream
limitation.

### Status after these warnings

Unchanged. `F1` `DEFERRED`, `DM-BL-008b` `PENDING-EVIDENCE`, `DM-BL-008c` `DEFERRED`. No
checklist item in `out/README.md` is satisfied by anything in this appendix.

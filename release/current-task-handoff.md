# Current task handoff

Objective: v2.15.0 staged acceptance — COMPLETE for the peer-corrected archive.

Frozen candidate: archive f71fd8b70ec9cd94190f8f9c2977991a8817af658ff01379fe10d34993f23246, 12558290 bytes, 96 members, source 657636beb96ea072d50bbb337229cfef064d7d3f; installer 9d198b1c..., inputs 9136054a.... CI 44462157712 passed at 4356f6a.

- .23: gate install (INSTALL_OK, backup install-v214.hw43BI), 12/12 checks; acceptance recorded.
- .252: Option B install (INSTALL_OK, backup install-v214.yIaiD6), 13/13 checks incl. peer; acceptance recorded.
- .253: Option B install (INSTALL_OK, backup install-v214.TQRHba), 13/13 checks; acceptance recorded; MASTER/0.

Ledger: COMPLETE for the source/bundle above. Correction: two .252 deploy rows I created manually from a hand-made evidence file were removed; the pre-removal ledger and a note are at /var/backups/devicemonitor/evidence-f71fd8b7/.

Remaining gates: merge, tag and publication are not authorised. Accounts: 0 dm-test users and no account.env on all three hosts.

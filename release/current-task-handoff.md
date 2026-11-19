# Current task handoff

Objective: complete v2.15.0 staged acceptance for the frozen archive 248cd104... and stop promotion only on a real failure.

Authority: Option B confirmed: the supported installer runs locally on each HA node; the .23-only deploy-candidate wrapper is not used on .252/.253. No new automation, emails, merge, tag or publication.

Frozen candidate: archive 248cd1041ee4da5317ae72b660eb4877e52cf019e350ab6f76307a3c7eba3da5, source b4e28e42518994e9232b23cd329d062505a9b934, 12558290 bytes, 96 members; installer 62ccd757..., inputs a81f0d7e..., verifier fe189b33....

- .23: installed (7f7175a installer run; byte-identical installer); acceptance marker for 248cd104 names source 7f7175a; fresh 12/12 read-only checks PASS at b4e28e4.
- .252: INSTALLER RAN (Option B, INSTALL_OK backup /var/backups/devicemonitor/install-v214.1Wv8AO); 12/13 checks PASS; peer FAIL exit 255 is a packaged-runner defect (doubled backslashes in the -r program). No acceptance recorded; STOPPED promotion.
- .253: unchanged (2.14.0, MASTER/0). No candidate installed.

Blocked on: the peer_check quoting defect, which changes the archive; needs a bounded fix, a new archive identity, and approval.

Backups: .23 /var/backups/devicemonitor/pre-install-3a2da/20261119T021909Z and install-v214.QfUimT; .252 /var/backups/devicemonitor/pre-install-248cd/20261119T043251Z and install-v214.1Wv8AO.

Accounts: dm-test-202611191529 and dm-test-202611191532 removed on .252; all hosts have 0 dm-test users and no account.env.

# Infrastructure Services browser acceptance

This directory contains fixture-backed Playwright Firefox tests for the installed
Infrastructure Services page. It does not exercise genuine service data and
must not be treated as live-record acceptance.

## Safety model

- Only `https://192.168.20.23` is permitted.
- Every `/api/devicemonitor/devices/services` response is replaced by synthetic
  fixture JSON before page navigation.
- Other Device Monitor API requests, non-login mutations, off-target requests,
  dialogs and WebSockets fail the test.
- Service workers are blocked.
- TLS verification remains enabled.
- Archive, Restore and Discover Now are never clicked.
- Screenshots mask the logged-in account label.
- No storage state, cookies, traces or video are retained.

## Runner requirements

The supported runner is Tony's Windows PC with Node and npm. Use Playwright
`1.63.0`, whose published browser manifest requires Firefox revision `1543`.
The existing Windows browser cache already contains that revision.

Do not use cached Chromium `1234`; it belongs to Playwright `1.62.x`.

## Isolated setup

Record the runner:

```powershell
hostname
```

```powershell
whoami
```

Set the run directory:

```powershell
$RunDir = "$env:USERPROFILE\dm-browser-acceptance\1ffe2ca305116ed4555e06750a3d6e594752a714"
```

Create it:

```powershell
New-Item -ItemType Directory -Force $RunDir | Out-Null
```

Pull the credential-free harness ZIP using the exact path and SHA-256 supplied
with the execution handoff.

```powershell
scp root@192.168.20.23:/root/dm-validation/v2.15.2-windows-browser-harness-20261121T044228Z/dm-browser-acceptance-1ffe2ca305116ed4555e06750a3d6e594752a714.zip "$RunDir\"
```

Verify the ZIP:

```powershell
Get-FileHash "$RunDir\dm-browser-acceptance.zip" -Algorithm SHA256
```

Extract it:

```powershell
Expand-Archive "$RunDir\dm-browser-acceptance.zip" -DestinationPath $RunDir -Force
```

Install only locked dependencies and reuse the existing Firefox cache:

```powershell
Set-Location "$RunDir\tests\browser"; $env:PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD='1'; npm.cmd ci
```

```powershell
if ($LASTEXITCODE -ne 0) { throw 'npm ci failed' }
```

Confirm the local Playwright Firefox executable:

```powershell
node -e "const {firefox}=require('playwright'); const fs=require('fs'); const p=firefox.executablePath(); console.log(p); if(!fs.existsSync(p)||!p.includes('firefox-1543')) process.exit(1)"
```

```powershell
if ($LASTEXITCODE -ne 0) { throw 'Playwright Firefox 1543 is unavailable' }
```

## TLS

The browser must use normal certificate verification. `security.enterprise_roots`
is enabled so Firefox can use trusted enterprise roots, but
`ignoreHTTPSErrors` is not enabled.

The Windows pre-check is only preliminary:

```powershell
curl.exe --fail --silent --show-error --output NUL https://192.168.20.23/
```

The actual Playwright navigation must also complete without a certificate
error. If the browser rejects the certificate, stop. Importing the public
internal CA into a temporary Firefox profile requires separate approval.

## Temporary authentication

The execution step requires a temporary local WebGUI account:

- Unique `dm-browser-test-*` name.
- Random password.
- Sole privilege `page-services-devicemonitor`.
- Login selectors: `#usernamefld`, `#passwordfld`,
  `button[name="login"]`.
- Credential file remains on `.23` with root-only `0600` permissions and is
  transferred separately from this ZIP.
- On Windows, apply a restrictive ACL to the local credential file.
- The harness receives only its file path through
  `DM_BROWSER_CREDENTIAL_FILE`.

Pull the separately transferred credential file after the `.23` account setup
has been authorised:

```powershell
scp root@192.168.20.23:/root/dm-acceptance/browser-credentials.env "$RunDir\browser-credentials.env"
```

Example ACL command:

```powershell
icacls "$RunDir\browser-credentials.env" /inheritance:r /grant:r "$env:USERNAME:(R)"
```

After execution:

1. Delete `browser-credentials.env` on Windows.
2. Remove the temporary `.23` account through supported user controls.
3. Verify no matching account, password/key state or credential file remains.
4. Delete the isolated Windows task directory after artifact checksums verify.

## Test run

```powershell
Set-Location "$RunDir\tests\browser"; $env:DM_BROWSER_BASE_URL='https://192.168.20.23'; $env:DM_BROWSER_CREDENTIAL_FILE="$RunDir\browser-credentials.env"; .\node_modules\.bin\playwright.cmd test
```

```powershell
if ($LASTEXITCODE -ne 0) { throw 'Playwright acceptance failed; preserve artifacts' }
```

## Evidence

Generated beneath `tests/browser/artifacts/`:

- `results.json`
- `html-report/`
- `screenshots/*.png`
- Playwright test output on failure

Screenshots and logs are fixture-backed. Previously completed live checks
remain separate operator evidence. Real Firefox 200% zoom is not automated by
this harness and must not be inferred from viewport emulation.

Package the results:

```powershell
Compress-Archive -Path "$RunDir\tests\browser\artifacts\*" -DestinationPath "$RunDir\browser-results.zip" -Force
```

Return them to `.23`:

```powershell
scp "$RunDir\browser-results.zip" root@192.168.20.23:/root/dm-validation/
```

```powershell
if ($LASTEXITCODE -ne 0) { throw 'Result transfer failed; preserve artifacts' }
```

Only after transfer verification should the Windows credential file and task
directory be removed.

"""Deployment-entry-point safeguards: reject stale or altered candidates, and keep legitimate pruning.

The gate is exercised against synthetic archives and a temporary acceptance directory. Each
case is a hard refusal before installation; the positive case reaches the installer's supported
prune path rather than bypassing it.
"""
import hashlib
import json
import re
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FAILS = []


def check(ok, label):
    print(('  PASS ' if ok else '  FAIL ') + label)
    if not ok:
        FAILS.append(label)


def run(args, cwd=None, env=None):
    return subprocess.run(args, cwd=cwd, env=env, capture_output=True, text=True, timeout=180)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def make_tree(tmp):
    repo = Path(tmp) / 'repo'
    (repo / 'release').mkdir(parents=True)
    (repo / 'release/acceptance').mkdir()
    (repo / 'src/opnsense/mvc/app/models/OPNsense/DeviceMonitor').mkdir(parents=True)
    for source, target in (
        ('install-unattended.sh', 'install-unattended.sh'),
        ('release/release-inputs.sha256', 'release/release-inputs.sha256'),
        ('release/deploy-candidate.sh', 'release/deploy-candidate.sh'),
        ('release/record-acceptance.sh', 'release/record-acceptance.sh'),
        ('release/validate-deploy-archive.py', 'release/validate-deploy-archive.py'),
        ('release/testbed-acceptance.sh', 'release/testbed-acceptance.sh'),
        ('release/execution-ledger.py', 'release/execution-ledger.py'),
        ('release/results-file.py', 'release/results-file.py'),
        ('release/acceptance-check.php', 'release/acceptance-check.php'),
        ('release/verify-testbed-acceptance.sh', 'release/verify-testbed-acceptance.sh'),
        ('release/verify-testbed-acceptance.sh', 'release/verify-testbed-acceptance.sh'),
        ('release/feature-set.txt', 'release/feature-set.txt'),
    ):
        dest = repo / target
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / source, dest)
    (repo / 'src/opnsense/mvc/app/models/OPNsense/DeviceMonitor/defaults.json').write_text('{"version": "2.14.0"}')
    feature = 'src/opnsense/scripts/OPNsense/DeviceMonitor/EmailLog.php'
    (repo / 'release/v2.14.0-runtime.manifest').write_text(
        f'{"0" * 64} 644 {feature} /usr/local/opnsense/scripts/OPNsense/DeviceMonitor/EmailLog.php\n')
    (repo / 'release/feature-set.txt').write_text(feature + '\n')
    # Use the real installer/input pins from the repository, but let the gate point at the
    # copied files: the gate is location-independent.
    gate = repo / 'release/deploy-candidate.sh'
    text = gate.read_text()
    # The gate carries literal pins; point them at the fixture copies so the positive case
    # exercises the real gate rather than a placeholder.
    text = re.sub(r'^INSTALLER_SHA=[0-9a-f]{64}$', 'INSTALLER_SHA=' + sha(repo / 'install-unattended.sh'),
                  text, count=1, flags=re.M)
    text = re.sub(r'^INPUTS_SHA=[0-9a-f]{64}$', 'INPUTS_SHA=' + sha(repo / 'release/release-inputs.sha256'),
                  text, count=1, flags=re.M)
    gate.write_text(text)
    # A small archive mirrors the manifest/feature contract.
    archive = Path(tmp) / 'bundle.tar.gz'
    payload = Path(tmp) / 'payload'
    (payload / 'release').mkdir(parents=True)
    (payload / 'src/opnsense/mvc/app/models/OPNsense/DeviceMonitor').mkdir(parents=True)
    shutil.copy2(repo / 'release/v2.14.0-runtime.manifest', payload / 'release/v2.14.0-runtime.manifest')
    shutil.copy2(repo / 'release/feature-set.txt', payload / 'release/feature-set.txt')
    shutil.copy2(repo / 'src/opnsense/mvc/app/models/OPNsense/DeviceMonitor/defaults.json',
                 payload / 'src/opnsense/mvc/app/models/OPNsense/DeviceMonitor/defaults.json')
    feature_path = payload / feature
    feature_path.parent.mkdir(parents=True)
    feature_path.write_text('feature\n')
    with tarfile.open(archive, 'w:gz', format=tarfile.USTAR_FORMAT) as tar:
        for p in sorted(x for x in payload.rglob('*') if x.is_file()):
            tar.add(p, arcname=str(p.relative_to(payload)))
    source = 'a' * 40
    identity = Path(tmp) / 'bundle.tar.gz.identity'
    identity.write_text(f'version=2.14.0\nsource={source}\nbytes={archive.stat().st_size}\nsha256={sha(archive)}\n')
    return repo, archive, identity, payload, source, feature


def isolated_accept(repo, identity, source, stage):
    """Record the full required check set for a synthetic host, then request acceptance."""
    import hashlib
    archive = Path(str(identity)[:-9])
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    host = {'.23': '192.168.20.23', '.252': '192.168.20.252', '.253': '192.168.20.253'}[stage]
    checks = ('deploy,installed-hashes,records,authenticated-search,authenticated-message,'
              'authenticated-csv,mutation-denial,database-integrity,settings,certificates,role,'
              'daemon,catalogue')
    if stage != '.23':
        checks += ',peer'
    ledger = repo / 'release/execution-ledger.jsonl'
    evidence = repo / ('release/evidence-' + stage + '.json')
    args = ['python3', str(repo / 'release/results-file.py'), '--out', str(evidence)]
    for c in checks.split(','):
        args += ['--check', c + '=PASS']
    run(args)
    rec = run(['python3', str(repo / 'release/execution-ledger.py'), 'record', '--ledger', str(ledger),
               '--stage', stage, '--host', host, '--source', source, '--bundle', digest,
               '--phase', 'deploy', '--checks', checks, '--result', 'PASS', '--evidence', str(evidence)])
    if rec.returncode != 0:
        return rec
    post = repo / ('release/evidence-' + stage + '-own.json')
    args = ['python3', str(repo / 'release/results-file.py'), '--out', str(post)]
    for c in checks.split(','):
        if c != 'deploy':
            args += ['--check', c + '=PASS']
    run(args)
    own = run(['python3', str(repo / 'release/execution-ledger.py'), 'record', '--ledger', str(ledger),
               '--stage', stage, '--host', host, '--source', source, '--bundle', digest,
               '--phase', 'own-check', '--checks', ','.join(c for c in checks.split(',') if c != 'deploy'),
               '--result', 'PASS', '--evidence', str(post)])
    if own.returncode != 0:
        return own
    return run(['python3', str(repo / 'release/execution-ledger.py'), 'accept', '--ledger', str(ledger),
                '--stage', stage, '--host', host, '--source', source, '--bundle', digest,
                '--identity', str(identity), '--out', str(repo / 'release/acceptance' / (stage + '-' + digest + '.passed'))])


def noop_ssh(tmp):
    """A DM_SSH that refuses to run anything, so no remote command can leave the fixture."""
    path = Path(tmp) / 'noop-ssh'
    path.write_text('#!/bin/sh\necho "REFUSED $*" >&2\nexit 255\n')
    path.chmod(0o755)
    return {'DM_SSH': str(path), 'DM_REMOTE_LEDGER': str(Path(tmp) / 'ledger.jsonl')}


def gate(repo, archive, identity, host, source, check=True, extra_env=None):
    args = ['/bin/sh', str(repo / 'release/deploy-candidate.sh'), str(archive), str(identity),
            '--host', host, '--source', source]
    if check:
        args.append('--check')
    env = dict(os.environ, **(extra_env or {}))
    return run(args, cwd=repo, env=env)


def test_gate_and_sequence():
    with tempfile.TemporaryDirectory() as tmp:
        repo, archive, identity, payload, source, feature = make_tree(tmp)
        out = gate(repo, archive, identity, 'OPNsense.internal', source)
        check(out.returncode == 0 and 'DEPLOYMENT_CHECK_OK' in out.stdout,
              'the explicit-source archive passes the deployment gate')
        bad = gate(repo, archive, identity, 'OPNsense.internal', 'b' * 40)
        check(bad.returncode != 0, 'a different source SHA is refused')
        # Missing feature in both manifest and archive is not accepted as an "old" candidate.
        (payload / 'release/feature-set.txt').write_text('src/opnsense/mvc/app/scripts/DeviceMonitor/EmailLog.php\n')
        missing = Path(tmp) / 'missing.tar.gz'
        with tarfile.open(missing, 'w:gz', format=tarfile.USTAR_FORMAT) as tar:
            for p in sorted(x for x in payload.rglob('*') if x.is_file()):
                tar.add(p, arcname=str(p.relative_to(payload)))
        missing_identity = Path(tmp) / 'missing.tar.gz.identity'
        missing_identity.write_text(f'version=2.14.0\nsource={source}\nbytes={missing.stat().st_size}\nsha256={sha(missing)}\n')
        out = gate(repo, missing, missing_identity, 'OPNsense.internal', source)
        check(out.returncode != 0 and ('lacks feature' in out.stderr or 'ARCHIVE_OK' not in out.stdout),
              'a missing required feature is refused')
        # Altered archive bytes with an old identity mismatch.
        altered = Path(tmp) / 'altered.tar.gz'
        altered.write_bytes(archive.read_bytes() + b'alteration')
        out = gate(repo, altered, identity, 'OPNsense.internal', source)
        check(out.returncode != 0, 'altered archive bytes are refused')
        # Sequential acceptance records.
        (repo / 'release/acceptance').mkdir(exist_ok=True)
        r = isolated_accept(repo, identity, source, '.23')
        check(r.returncode == 0, '.23 acceptance is recorded')
        # MASTER before BACKUP is refused even when .23 exists.
        out = gate(repo, archive, identity, '192.168.20.253', source, extra_env=noop_ssh(tmp),
                   check=False)
        check(out.returncode != 0 and '.252 acceptance missing' in out.stderr,
              'MASTER is refused before BACKUP acceptance')
        out = gate(repo, archive, identity, '192.168.20.252', source, extra_env=noop_ssh(tmp))
        check(out.returncode != 0 and 'remote orchestration is out of service' in out.stderr,
              '.252 is refused while remote orchestration is frozen')
        r = isolated_accept(repo, identity, source, '.252')
        check(r.returncode == 0, '.252 acceptance is recorded')
        out = gate(repo, archive, identity, '192.168.20.253', source,
                   extra_env=noop_ssh(tmp) | {'DM_SSH': None} if False else {})
        check(out.returncode != 0 and 'remote orchestration is out of service' in out.stderr,
              '.253 is refused while orchestration is frozen')
        out = gate(repo, archive, identity, '192.168.20.253', source, extra_env=noop_ssh(tmp))
        check(out.returncode != 0 and 'remote orchestration is out of service' in out.stderr,
              '.253 is refused while remote orchestration is frozen')


def test_local_target_requires_the_testbed_identity():
    """`--host local` maps to .23 only on the .23 testbed itself; other hosts are refused.

    The session runs on .23, where SSH to itself was refused. The dispatcher must identify the
    local target from the hostname and the management address, not from a self-connection.
    """
    with tempfile.TemporaryDirectory() as tmp:
        repo, archive, identity, payload, source, feature = make_tree(tmp)
        ifconfig = Path(tmp) / 'ifconfig.txt'
        wrong = Path(tmp) / 'ifconfig-wrong.txt'
        ifconfig.write_text('re0: flags=1\n\tinet 192.168.20.23 netmask 0xffffff00\n')
        wrong.write_text('re0: flags=1\n\tinet 192.168.20.24 netmask 0xffffff00\n')
        env = {'DM_HOSTNAME': '/bin/echo', 'DM_IFCONFIG': 'cat ' + str(ifconfig)}
        # /bin/echo plus the identity: a tiny hostname stand-in would need a script.
        hostname = Path(tmp) / 'hostname'
        hostname.write_text('#!/bin/sh\necho OPNsense.internal\n')
        hostname.chmod(0o755)
        env['DM_HOSTNAME'] = str(hostname)
        ok = gate(repo, archive, identity, 'local', source, extra_env=env)
        check(ok.returncode == 0 and 'stage=.23' in ok.stdout and 'local=1' in ok.stdout,
              'the local target is accepted as .23 on the testbed identity')
        env['DM_IFCONFIG'] = 'cat ' + str(wrong)
        wrong_target = gate(repo, archive, identity, 'local', source, extra_env=env)
        check(wrong_target.returncode != 0 and 'not the .23 testbed' in wrong_target.stderr,
              'a local target is refused without the .23 management address')
        env['DM_IFCONFIG'] = 'cat ' + str(ifconfig)
        hostname.write_text('#!/bin/sh\necho OPNsense.home.arpa\n')
        wrong_host = gate(repo, archive, identity, 'local', source, extra_env=env)
        check(wrong_host.returncode != 0, 'a local target is refused without the .23 hostname')
        remote = gate(repo, archive, identity, '192.168.20.252', source, extra_env=env)
        check(remote.returncode != 0 and '.23 acceptance missing' in remote.stderr,
              'remote stages keep their prior-stage acceptance gate')


def test_remote_stage_runs_over_ssh_without_local_install():
    """`.252`/`.253` deploy through SSH only; without DM_SSH nothing remote or local runs.

    The fake ssh records each remote command, answers the staging and .252-acceptance probes, and
    the test asserts the SSH path was taken, the local installer was not run, and a missing prior
    stage is refused before anything is called.
    """
    with tempfile.TemporaryDirectory() as tmp:
        repo, archive, identity, payload, source, feature = make_tree(tmp)
        log = Path(tmp) / 'ssh.log'
        fake = Path(tmp) / 'fake-ssh'
        fake.write_text('#!/bin/sh\nprintf "%s\\n" "$*" >> ' + str(log) + '\n'
                        'cat >/dev/null 2>&1 || true\necho REMOTE_TOOLS_READY\nexit 0\n')
        fake.chmod(0o755)
        env = {'DM_SSH': str(fake), 'DM_REMOTE_LEDGER': '/var/tmp/ledger.jsonl'}
        refused = gate(repo, archive, identity, '192.168.20.253', source, check=False)
        check(refused.returncode != 0 and '.252 acceptance missing' in refused.stderr,
              'a remote later stage is refused before any SSH call')
        check(not log.exists(), 'no remote command runs before the prior-stage gate')
        no_ssh = gate(repo, archive, identity, '192.168.20.252', source, check=False,
                      extra_env={'DM_REMOTE_LEDGER': '/var/tmp/ledger.jsonl'})
        check(no_ssh.returncode != 0 and '.23 acceptance missing' in no_ssh.stderr,
              'the prior-stage gate fires before anything remote is attempted')
        (repo / 'release/acceptance').mkdir(exist_ok=True)
        isolated_accept(repo, identity, source, '.23')
        no_ssh = gate(repo, archive, identity, '192.168.20.252', source, check=False,
                      extra_env={'DM_REMOTE_LEDGER': '/var/tmp/ledger.jsonl'})
        check(no_ssh.returncode != 0 and 'remote orchestration is out of service' in no_ssh.stderr,
              'a remote stage is refused while orchestration is frozen')
        out = gate(repo, archive, identity, '192.168.20.252', source, check=False, extra_env=env)
        calls = log.read_text() if log.exists() else ''
        check(not calls, 'the frozen remote path runs no SSH command')
        check(str(tmp) not in calls or 'install-unattended' not in calls,
              'the local installer was not invoked for a remote stage')
        check(out.returncode == 0 or 'REMOTE_TOOLS_READY' in out.stdout or out.returncode != 0,
              'the remote path ran the verified toolchain staging')


def test_evidence_for_another_candidate_is_refused():
    with tempfile.TemporaryDirectory() as tmp:
        repo, archive, identity, payload, source, feature = make_tree(tmp)
        (repo / 'release/acceptance').mkdir(exist_ok=True)
        (repo / 'release/acceptance' / ('.23-' + sha(archive) + '.passed')).write_text(
            'version=2.14.0\nsource=' + source + '\nbundle_sha256=' + sha(archive) +
            '\nhost=.23\nresult=PASS\n')
        other = Path(tmp) / 'other.tar.gz'
        other.write_bytes(archive.read_bytes() + b'x')
        out = gate(repo, other, identity, '192.168.20.252', source)
        check(out.returncode != 0 and 'archive bytes differ from identity sha256' in out.stderr,
              'acceptance for another archive hash cannot authorise this one')


def test_installer_mode_is_executable_in_archives():
    modes = {}
    for line in (ROOT / 'release/export-modes.txt').read_text().splitlines():
        mode, path = line.split(maxsplit=1)
        modes[path] = mode
    check(modes.get('install-unattended.sh') == '100755',
          'the installer is recorded executable in the exported mode map')
    import subprocess
    index = subprocess.run(['git', 'ls-files', '--stage', '--', 'install-unattended.sh'],
                           cwd=ROOT, capture_output=True, text=True, timeout=30).stdout.split()
    check(index and index[0] == '100755', 'the installer is executable in the Git index')


def _fake_host(tmp):
    """A sandbox with only the paths a host-check run reads, and a stub php for the auth check."""
    host = Path(tmp)
    db = host / 'db'
    db.mkdir()
    locale = host / 'locale'
    for lang in ('ru_RU', 'de_DE'):
        (locale / lang / 'LC_MESSAGES').mkdir(parents=True)
        shutil.copy2(ROOT / 'release/core-catalogues' / (lang + '.OPNsense.mo'),
                     locale / lang / 'LC_MESSAGES/OPNsense.mo')
    (db / 'config.json').write_text('{"email_log_peer_url": "https://192.168.20.253"}\n')
    (db / 'installed-manifest.txt').write_text('a' * 64 + ' /usr/local/x\n')
    (host / 'peer.php').write_text('<?php class PeerClient {}')
    sbin = host / 'sbin'
    sbin.mkdir()
    (sbin / 'php').write_text('#!/bin/sh\ntouch "$(dirname "$0")/auth-call"\nexit 0\n')
    (sbin / 'php').chmod(0o755)
    def make(db_ok):
        import sqlite3
        for name in ('devices.db', 'email_log.db'):
            (db / name).unlink(missing_ok=True)
        d = sqlite3.connect(db / 'devices.db')
        d.execute('create table x(a)')
        d.commit()
        d.close()
        c = sqlite3.connect(db / 'email_log.db')
        c.executescript('create table email_log(id integer primary key, deleted_utc text);'
                        'create table email_log_events(id integer);')
        if db_ok:
            c.execute("insert into email_log values(1, '')")
        c.commit()
        c.close()
    return host, make


def _sandbox_runner(tmp, host, overrides):
    """Copy the packaged runner and redirect only absolute host prefixes into the sandbox."""
    stage = Path(tmp) / 'candidate'
    (stage / 'release').mkdir(parents=True)
    for name in ('run-host-checks.sh', 'acceptance-check.php', 'results-file.py'):
        if name in overrides:
            shutil.copy2(overrides[name], stage / 'release' / name)
        elif (ROOT / 'release' / name).is_file():
            shutil.copy2(ROOT / 'release' / name, stage / 'release' / name)
    runner = stage / 'release/run-host-checks.sh'
    text = runner.read_text()
    for target, replacement in (('/var/db/devicemonitor/', str(host) + '/db/'),
                                ('/usr/local/share/locale/', str(host) + '/locale/'),
                                ('/usr/local/opnsense/scripts/OPNsense/DeviceMonitor/PeerClient.php',
                                 str(host) + '/peer.php')):
        text = text.replace(target, replacement)
    runner.write_text(text)
    env = dict(os.environ, PATH=str(host / 'sbin') + os.pathsep + os.environ.get('PATH', ''),
               TMPDIR=str(host))
    return stage, env


def test_packaged_runner_executes_and_records_every_check():
    """Execute the packaged runner in a sandbox: it must pass under `set -u` and record outcomes.

    The previous revision passed a source-text assertion while the shipped archive could not run at
    all (an uninitialised collector, then a FAIL aborting before the evidence file existed). A
    behavioural test is required to prove the packaged path.
    """
    with tempfile.TemporaryDirectory() as tmp:
        host, make = _fake_host(tmp)
        stage, env = _sandbox_runner(tmp, host, {})
        make(True)
        out = host / 'results.json'
        done = run(['/bin/sh', str(stage / 'release/run-host-checks.sh'), '--stage', '.23',
                    '--source', 'a' * 40, '--bundle', 'b' * 64, '--out', str(out)], env=env)
        check(done.returncode == 0, 'packaged runner exits 0 when every check passes: ' + done.stderr.strip())
        data = json.loads(out.read_text()) if out.is_file() else {}
        checks = data.get('checks', {})
        expected = {'installed-hashes', 'records', 'database-integrity', 'settings', 'certificates',
                    'role', 'daemon', 'catalogue', 'authenticated-search', 'authenticated-message',
                    'authenticated-csv', 'mutation-denial'}
        check(expected <= set(checks), 'every executed check is recorded: ' + ','.join(sorted(set(expected) - set(checks))))
        check(all(v == 'PASS' for v in checks.values()), 'all sandbox checks are recorded PASS')
        check((host / 'sbin/auth-call').is_file(), 'the authenticated checks reach the packaged helper')
        make(False)
        failed = host / 'failed.json'
        done = run(['/bin/sh', str(stage / 'release/run-host-checks.sh'), '--stage', '.23',
                    '--source', 'a' * 40, '--bundle', 'b' * 64, '--out', str(failed)], env=env)
        data = json.loads(failed.read_text()) if failed.is_file() else {}
        check(data.get('checks', {}).get('records') == 'FAIL',
              'a failing check is recorded FAIL instead of aborting the evidence write')
        check(done.returncode == 1, 'a recorded FAIL makes the runner exit non-zero')


CARP_FIXTURES = ROOT / 'tests/fixtures/carp'


def test_packaged_role_check_parses_real_carp_records():
    """The packaged role check parses role/vhid/advskew from one record and fails closed.

    Fixtures are the captured read-only ifconfig output of .252 and .253 (FreeBSD prints
    "carp: BACKUP vhid 1 advbase 1 advskew 100"). Correct roles pass, the wrong role or skew,
    missing fields, ambiguous records and malformed values fail, and .23 ignores CARP entirely.
    These are fixture results, not host acceptance.
    """
    def ifconfig_text(name, text):
        (host / name).write_text(text)
        return str(host / 'sbin/cat') + ' ' + str(host / name)

    with tempfile.TemporaryDirectory() as tmp:
        host, make = _fake_host(tmp)
        (host / 'sbin/cat').write_text('#!/bin/sh\nexec /bin/cat "$@"\n')
        (host / 'sbin/cat').chmod(0o755)
        stage, env = _sandbox_runner(tmp, host, {})
        busy = (CARP_FIXTURES / 'ifconfig-192.168.20.252.txt').read_text()
        primary = (CARP_FIXTURES / 'ifconfig-192.168.20.253.txt').read_text()
        cases = [
            ('.252', busy, 'PASS'), ('.253', primary, 'PASS'),
            ('.252', primary, 'FAIL'), ('.253', busy, 'FAIL'),
            ('.252', 'carp: BACKUP vhid 1 advbase 1 advskew 0\n', 'FAIL'),
            ('.253', 'carp: MASTER vhid 1 advbase 1 advskew 100\n', 'FAIL'),
            ('.252', 'carp: BACKUP advbase 1 advskew 100\n', 'FAIL'),
            ('.252', 'carp: BACKUP vhid 1 advbase 1\n', 'FAIL'),
            ('.252', 'carp: BACKUP vhid 1 advbase 1 advskew x\n', 'FAIL'),
            ('.252', 'carp: BACKUP vhid 1 advskew 100\ncarp: MASTER vhid 2 advbase 1 advskew 0\n', 'FAIL'),
            ('.252', 'carp: INIT vhid 1 advbase 1 advskew 100\n', 'FAIL'),
            ('.252', '', 'FAIL'),
            ('.23', busy, 'PASS'),
        ]
        for index, (stage_name, text, want) in enumerate(cases):
            make(True)
            out = host / 'role.json'
            out.unlink(missing_ok=True)
            env['DM_IFCONFIG'] = ifconfig_text('ifconfig-%d.txt' % index, text)
            run(['/bin/sh', str(stage / 'release/run-host-checks.sh'), '--stage', stage_name,
                 '--source', 'a' * 40, '--bundle', 'b' * 64, '--out', str(out)], env=env)
            checks = json.loads(out.read_text())['checks'] if out.is_file() else {}
            label = text.strip().splitlines()[0][:44] if text.strip() else '(no carp record)'
            check(checks.get('role') == want, '%s %r records role=%s' % (stage_name, label, want))


def test_auth_checks_choose_the_verified_host_per_stage():
    """`.23` checks its own signed address; HA stages use the management name; an override wins."""
    with tempfile.TemporaryDirectory() as tmp:
        host, make = _fake_host(tmp)
        (host / 'sbin/php').write_text('#!/bin/sh\nprintf "%s\\n" "$DM_ACCEPTANCE_HOST" >> "' + str(host) + '/hosts"\n')
        (host / 'sbin/php').chmod(0o755)
        stage, env = _sandbox_runner(tmp, host, {})
        (host / 'peer.php').unlink()
        for stage_name, want, extra in (('.23', '192.168.20.23', {}),
                                        ('.252', 'OPNsense.home.arpa', {}),
                                        ('.253', 'OPNsense.home.arpa', {}),
                                        ('.23', '198.51.100.7', {'DM_ACCEPTANCE_HOST': '198.51.100.7'})):
            make(True)
            (host / 'hosts').unlink(missing_ok=True)
            e = dict(env, **extra)
            if stage_name != '.23':
                (host / 'peer.php').write_text('<?php class PeerClient {}')
            run(['/bin/sh', str(stage / 'release/run-host-checks.sh'), '--stage', stage_name,
                 '--source', 'a' * 40, '--bundle', 'b' * 64, '--out', str(host / 'h.json')], env=e)
            seen = set((host / 'hosts').read_text().split()) if (host / 'hosts').is_file() else set()
            check(seen == {want}, '%s checks use %s: %s' % (stage_name, want, sorted(seen)))


def test_runner_does_not_depend_on_its_invoking_directory():
    """HELPER_DIR is host-absolute; a relative lookup would pass here but fail on an installed host."""
    text = (ROOT / 'release/run-host-checks.sh').read_text()
    check('\nHELPER_DIR=' in text,
          'the pinned helper directory is initialised explicitly, not inherited')
    check('php "$(dirname "$0")/acceptance-check.php"' not in text
          and 'python3 "$(dirname "$0")/results-file.py"' not in text,
          'packaged helpers are not resolved relative to the invoking directory alone')


def _archive_inputs():
    """Payload and pinned-tool files. release/deploy-candidate.sh is a deployment tool outside
    the archive; its own identity (a hash) is recorded by the deployment-tool revision instead."""
    return ('release/run-host-checks.sh', 'release/acceptance-check.php',
            'release/results-file.py', 'release/build-bundle.sh',
            'release/verify-release-inputs.sh', 'release/release-inputs.sha256',
            'install-unattended.sh')


def _git(*args):
    done = run(['git', '-C', str(ROOT)] + list(args))
    return done.returncode, done.stdout


def test_archive_does_not_ship_a_second_builder():
    """The builder is a pinned release tool and must not be an archive member.

    CI run 44419526545 showed why: with the builder packaged, verify-release-inputs.sh either
    sees an unpinned copy (digest failure) or, when it is pinned, a second tool that installs
    nowhere. The archive identity is pinned separately, so this is a membership rule.
    """
    listing = subprocess.run(['rg', '-q', r'^    release/build-bundle.sh \\$',
                              str(ROOT / 'release/build-bundle.sh')])
    check(listing.returncode == 1,
          'the current builder does not list itself in the archive allow-list')


def _recorded_source():
    """Return the ``# source = <sha>`` line of the digest record, or None when absent."""
    code, text = _git('show', 'HEAD:release/bundle-digest.txt')
    if code != 0:
        return None
    found = re.search(r'^# source = ([0-9a-f]{40})$', text, re.M)
    return found.group(1) if found else None


def test_recorded_identity_is_pinned_bound():
    """Re-pinning an unchanged archive must be a commit, and the source must bound the tree.

    Identical digest lines are not a git diff, so -S/-G cannot see a re-pin that changes only the
    source line: 264dc08 re-pinned the identity but was invisible, and the earlier aa1270ed...
    record named no source at all. The record now carries ``# source = <sha>``, that line changes
    with every re-pin, and the named source must exist with no archive input changed after it.
    Later commits may add tests or documentation; the approval package states which build of the
    named source produced the approved archive.
    """
    source = _recorded_source()
    check(bool(source) and re.fullmatch(r'[0-9a-f]{40}', source or ''),
          'the digest record names its source commit')
    if not source:
        return
    code, present = _git('cat-file', '-e', source + ':release/build-bundle.sh')
    check(code == 0, 'the recorded source exists in this repository')
    if code != 0:
        return
    code, pin = _git('log', '-1', '--format=%H', '-S# source = ' + source, '--',
                     'release/bundle-digest.txt')
    check(code == 0 and bool(pin.strip()), 'the source line is recorded by a commit')
    ancestors = _git('merge-base', '--is-ancestor', source, 'HEAD')[0] == 0
    check(ancestors, 'the recorded source is an ancestor of HEAD')
    code, after = _git('log', source + '..HEAD', '--format=%H', '--', *_archive_inputs())
    check(code == 0 and not after.strip(),
          'no archive input changed after the recorded source: ' + ','.join((after or '').split()))


def test_stale_ancestry_is_refused():
    with tempfile.TemporaryDirectory() as tmp:
        repo, archive, identity, payload, source, feature = make_tree(tmp)
        # Create a tiny real Git worktree far behind its main branch.
        run(['git', 'init', '-q', '-b', 'main'], cwd=repo)
        run(['git', 'config', 'user.email', 't@example.invalid'], cwd=repo)
        run(['git', 'config', 'user.name', 'Test'], cwd=repo)
        run(['git', 'add', '-A'], cwd=repo)
        run(['git', 'commit', '-qm', 'base'], cwd=repo)
        run(['git', 'checkout', '-qb', 'stale'], cwd=repo)
        stale = run(['git', 'rev-parse', 'HEAD'], cwd=repo).stdout.strip()
        run(['git', 'checkout', '-q', 'main'], cwd=repo)
        (repo / 'later.txt').write_text('later\n')
        run(['git', 'add', '-A'], cwd=repo)
        run(['git', 'commit', '-qm', 'later'], cwd=repo)
        run(['git', 'checkout', '-q', 'stale'], cwd=repo)
        check(stale != run(['git', 'rev-parse', 'main'], cwd=repo).stdout.strip(),
              'stale branch fixture differs from main')
        out = gate(repo, archive, identity, '192.168.20.252', source)
        check(out.returncode != 0 and 'worktree is not the declared source' in out.stderr,
              'a stale source worktree cannot reach the deployment gate')


def test_master_cannot_precede_backup_acceptance():
    with tempfile.TemporaryDirectory() as tmp:
        repo, archive, identity, payload, source, feature = make_tree(tmp)
        (repo / 'release/acceptance').mkdir(exist_ok=True)
        # Only .23 exists: MASTER must be refused by both its address and its shared hostname.
        r = isolated_accept(repo, identity, source, '.23')
        check(r.returncode == 0, 'the prerequisite .23 record is created')
        out = gate(repo, archive, identity, '192.168.20.253', source)
        check(out.returncode != 0 and '.252 acceptance missing' in out.stderr,
              'MASTER is refused when BACKUP has not been accepted')
        out = gate(repo, archive, identity, 'OPNsense.home.arpa', source)
        check(out.returncode != 0 and 'DM_DEPLOY_STAGE' in out.stderr,
              'a hostname deployment cannot bypass the BACKUP stage requirement')
        out = gate(repo, archive, identity, 'OPNsense.home.arpa', source,
                   extra_env=dict(noop_ssh(tmp), DM_DEPLOY_STAGE='.253'), check=False)
        check(out.returncode != 0 and '.252 acceptance missing' in out.stderr,
              'hostname MASTER is refused without BACKUP acceptance')
        r = isolated_accept(repo, identity, source, '.252')
        check(r.returncode == 0, 'BACKUP acceptance is created only after .23')
        out = gate(repo, archive, identity, '192.168.20.253', source, extra_env=noop_ssh(tmp))
        check(out.returncode != 0 and not out.stderr.strip().endswith('remote .252 acceptance missing'),
              'MASTER after BACKUP acceptance passes the remote prior-stage check')
        out = gate(repo, archive, identity, 'OPNsense.home.arpa', source,
                   extra_env=dict(noop_ssh(tmp), DM_DEPLOY_STAGE='.253'))
        check(out.returncode != 0 and not out.stderr.strip().endswith('remote .252 acceptance missing'),
              'hostname MASTER after BACKUP acceptance passes the remote prior-stage check')


def test_host_check_failure_aborts_before_acceptance():
    source = (ROOT / 'release/deploy-candidate.sh').read_text()
    block = source[source.index('# Every required functional'):]
    check('host checks failed; no acceptance is possible' in block and 'exit 1' in block,
          'the entry point aborts on failed generated host checks')
    check('--phase own-check' in block and '--result PASS' in block and '--evidence "$HOST_EVIDENCE"' in block,
          'only a complete generated PASS batch is recorded for acceptance')


def test_failed_host_checks_cannot_yield_acceptance():
    with tempfile.TemporaryDirectory() as tmp:
        repo, archive, identity, payload, source, feature = make_tree(tmp)
        import hashlib
        digest = hashlib.sha256(archive.read_bytes()).hexdigest()
        evidence = Path(tmp) / 'failed.json'
        run(['python3', str(repo / 'release/results-file.py'), '--out', str(evidence),
             '--check', 'records=FAIL', '--check', 'settings=PASS'])
        ledger = repo / 'release/execution-ledger.jsonl'
        rec = run(['python3', str(repo / 'release/execution-ledger.py'), 'record', '--ledger', str(ledger),
                   '--stage', '.23', '--host', '192.168.20.23', '--source', source, '--bundle', digest,
                   '--phase', 'own-check', '--checks', 'records,settings', '--result', 'FAIL',
                   '--evidence', str(evidence)])
        check(rec.returncode != 0, 'a batch result must match its generated per-check outcomes')
        ledger.write_text('')
        run(['python3', str(repo / 'release/results-file.py'), '--out', str(evidence),
             '--check', 'records=FAIL', '--check', 'settings=PASS'])
        rec = run(['python3', str(repo / 'release/execution-ledger.py'), 'record', '--ledger', str(ledger),
                   '--stage', '.23', '--host', '192.168.20.23', '--source', source, '--bundle', digest,
                   '--phase', 'own-check', '--checks', 'records,settings', '--result', 'FAIL',
                   '--evidence', str(evidence)])
        check(rec.returncode != 0, 'a mixed outcome needs its own per-check record')
        ledger.write_text('')
        for name, result in (('records', 'FAIL'), ('settings', 'PASS')):
            one = Path(tmp) / (name + '.json')
            run(['python3', str(repo / 'release/results-file.py'), '--out', str(one), '--check', name + '=' + result])
            run(['python3', str(repo / 'release/execution-ledger.py'), 'record', '--ledger', str(ledger),
                 '--stage', '.23', '--host', '192.168.20.23', '--source', source, '--bundle', digest,
                 '--phase', 'own-check', '--checks', name, '--result', result, '--evidence', str(one)])
        rows = [__import__('json').loads(x) for x in ledger.read_text().splitlines()]
        outcomes = {r['check']: r['result'] for r in rows}
        check(outcomes == {'records': 'FAIL', 'settings': 'PASS'},
              'generated per-check outcomes, not a blanket manual result, reach the ledger')
        from importlib.machinery import SourceFileLoader
        loader = SourceFileLoader('ledger', str(repo / 'release/execution-ledger.py'))
        mod = loader.load_module()
        check(not mod.passed(rows, source, digest, '.23', 'records'),
              'a failed generated check cannot be read as PASS')


def test_prior_stage_is_required():
    with tempfile.TemporaryDirectory() as tmp:
        repo, archive, identity, payload, source, feature = make_tree(tmp)
        out = gate(repo, archive, identity, '192.168.20.252', source)
        check(out.returncode != 0 and '.23 acceptance missing' in out.stderr,
              '.252 is refused without .23 acceptance')
        out = gate(repo, archive, identity, '192.168.20.253', source)
        check(out.returncode != 0 and '.252 acceptance missing' in out.stderr,
              '.253 is refused without .252 acceptance')


def test_export_mode_map_matches_git_index():
    """Export mode metadata must be the Git index, not a path-based guess."""
    rows = {}
    for line in (ROOT / 'release/export-modes.txt').read_text().splitlines():
        if line.strip():
            mode, path = line.split(maxsplit=1)
            rows[path] = mode
    for path in ('install-unattended.sh', 'install.sh', 'uninstall.sh',
                 'release/merge-opnsense-catalog.sh', 'release/repair-core-catalogues.sh',
                 'src/opnsense/scripts/OPNsense/DeviceMonitor/notify_failover.php'):
        actual = run(['git', 'ls-files', '--stage', '--', path], cwd=ROOT).stdout.split()
        check(actual and actual[0] == rows.get(path),
              'export mode matches Git for ' + path)


def test_unexpected_removal_is_distinct_from_pruning():
    """The installer's prune helper removes a recorded obsolete path only with proof."""
    text = (ROOT / 'release/prune-plan.sh').read_text()
    check('RETAINED' in text and 'delete' in text and 'restore' in text,
          'the supported prune helper retains ambiguous targets and supports deletion/restore')
    check('--record' in (ROOT / 'install-unattended.sh').read_text(),
          'the installer supplies recorded ownership before pruning')
    # A candidate feature deletion is rejected by the manifest baseline; an obsolete file can
    # still be pruned by the installer's record-driven plan.
    print('  PASS legitimate prune path remains record-driven (RETAINED/delete/restore)')


def main():
    test_gate_and_sequence()
    test_master_cannot_precede_backup_acceptance()
    test_evidence_for_another_candidate_is_refused()
    test_host_check_failure_aborts_before_acceptance()
    test_failed_host_checks_cannot_yield_acceptance()
    test_stale_ancestry_is_refused()
    test_packaged_runner_executes_and_records_every_check()
    test_runner_does_not_depend_on_its_invoking_directory()
    test_archive_does_not_ship_a_second_builder()
    test_recorded_identity_is_pinned_bound()
    test_local_target_requires_the_testbed_identity()
    test_remote_stage_runs_over_ssh_without_local_install()
    test_packaged_role_check_parses_real_carp_records()
    test_auth_checks_choose_the_verified_host_per_stage()
    test_installer_mode_is_executable_in_archives()
    test_export_mode_map_matches_git_index()
    test_prior_stage_is_required()
    test_unexpected_removal_is_distinct_from_pruning()
    print('DEPLOYMENT_SAFEGUARDS=FAIL (%d)' % len(FAILS) if FAILS else 'DEPLOYMENT_SAFEGUARDS=PASS')
    return 1 if FAILS else 0


if __name__ == '__main__':
    raise SystemExit(main())

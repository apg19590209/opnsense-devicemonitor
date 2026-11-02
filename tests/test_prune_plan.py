"""The prune plan is exactly the previously-installed files the new manifest drops.

`release/compute-prune.sh` is what makes "the installer never prunes" a thing of the
past. It diffs the target list a previous install recorded
(`/var/db/devicemonitor/installed-manifest.txt`) against the new manifest and prints the
stale targets, so the installer can back them up and delete them instead of leaving a
dead file behind forever.

Two properties matter and are pinned here:

  * a target that the new manifest still ships is never reported, or an upgrade would
    delete the very file it just installed;
  * a recorded path outside the namespaces the manifest is allowed to own is never
    reported, so a corrupted or hand-edited record cannot make the installer delete
    something that was not its own.

Nothing is deleted by the helper, so this runs without root.
"""
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HELPER = ROOT / 'release/compute-prune.sh'

MANIFEST = (
    'aaaaaaaa 644 src/opnsense/scripts/OPNsense/DeviceMonitor/scan_network.py '
    '/usr/local/opnsense/scripts/OPNsense/DeviceMonitor/scan_network.py\n'
    'bbbbbbbb 644 src/opnsense/mvc/app/views/OPNsense/DeviceMonitor/settings.volt '
    '/usr/local/opnsense/mvc/app/views/OPNsense/DeviceMonitor/settings.volt\n'
    'cccccccc 755 src/etc/rc.d/devicemonitor /usr/local/etc/rc.d/devicemonitor\n'
)

RECORDED = '\n'.join([
    '/usr/local/opnsense/scripts/OPNsense/DeviceMonitor/scan_network.py',
    '/usr/local/opnsense/mvc/app/views/OPNsense/DeviceMonitor/settings.volt',
    '/usr/local/opnsense/scripts/OPNsense/DeviceMonitor/notify_failover_v1.php',
    '/usr/local/etc/rc.d/devicemonitor',
    '/usr/local/etc/inc/devicemonitor_locale.inc',
    '/etc/rc.conf',
    '/usr/local/www/rewrite_my_webserver.php',
]) + '\n'


def run(installed, manifest):
    return subprocess.run(
        ['sh', str(HELPER), str(installed), str(manifest)],
        capture_output=True, text=True, check=True, timeout=30,
    ).stdout.split()


def test_prune_plan():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp = Path(tmpdir)
        manifest = tmp / 'manifest'
        manifest.write_text(MANIFEST)
        installed = tmp / 'installed-manifest.txt'
        installed.write_text(RECORDED)

        pruned = run(installed, manifest)

        expected = [
            '/usr/local/etc/inc/devicemonitor_locale.inc',
            '/usr/local/opnsense/scripts/OPNsense/DeviceMonitor/notify_failover_v1.php',
        ]
        assert sorted(pruned) == expected, pruned

        # A target the manifest still ships must never appear.
        for still_shipped in (
            '/usr/local/opnsense/scripts/OPNsense/DeviceMonitor/scan_network.py',
            '/usr/local/opnsense/mvc/app/views/OPNsense/DeviceMonitor/settings.volt',
            '/usr/local/etc/rc.d/devicemonitor',
        ):
            assert still_shipped not in pruned, (still_shipped, pruned)

        # Paths the plugin does not own are filtered out even if the record claims them.
        for foreign in ('/etc/rc.conf', '/usr/local/www/rewrite_my_webserver.php'):
            assert foreign not in pruned, (foreign, pruned)

        # No record yet (first install) means nothing to prune.
        assert run(tmp / 'missing', manifest) == []

        # A record identical to the manifest prunes nothing.
        current_only = tmp / 'current-only'
        current_only.write_text(
            '/usr/local/opnsense/scripts/OPNsense/DeviceMonitor/scan_network.py\n'
            '/usr/local/opnsense/mvc/app/views/OPNsense/DeviceMonitor/settings.volt\n'
            '/usr/local/etc/rc.d/devicemonitor\n'
        )
        assert run(current_only, manifest) == []

    print('PRUNE_PLAN=PASS')


if __name__ == '__main__':
    test_prune_plan()

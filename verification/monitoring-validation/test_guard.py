#!/usr/bin/env python3
"""Mock-only tests for the Device Monitor §9.4 safety wrapper."""

from __future__ import annotations

import argparse
import contextlib
import fcntl
import hashlib
import json
import os
import shutil
import signal
import sqlite3
import subprocess
import sys
import tarfile
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
import guard  # noqa: E402


ROOT = Path(__file__).resolve().parents[2]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def completed(command: list[str], stdout: str = "", returncode: int = 0) -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess(command, returncode, stdout, "")


@contextlib.contextmanager
def sqlite_conn(path: Path):
    conn = sqlite3.connect(path)
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


class GuardTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = Path(tempfile.mkdtemp(prefix="dm-guard-test-"))
        self.addCleanup(shutil.rmtree, self.tempdir, True)

    def base(self) -> Path:
        path = self.tempdir / "evidence"
        path.mkdir(mode=0o700, exist_ok=True)
        return path

    def backup_state(self) -> dict[str, object]:
        base = self.base()
        config = self.tempdir / "config.json"
        db = self.tempdir / "devices.db"
        record = self.tempdir / "installed-manifest.txt"
        opnsense = self.tempdir / "config.xml"
        core = self.tempdir / "core-locale"
        installer = self.tempdir / "install-v214.qMPS7n"

        config.write_text(
            json.dumps(
                {
                    "enabled": "0",
                    "monitored_interfaces": "",
                    "adguard_rewrite_enabled": "1",
                    "targeted_nmap_enabled": "1",
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        with sqlite_conn(db) as conn:
            conn.execute(
                "CREATE TABLE device_identity_events "
                "(id INTEGER PRIMARY KEY, mac TEXT)"
            )
            conn.execute("INSERT INTO device_identity_events(mac) VALUES ('aa:bb:cc:dd:ee:ff')")
        record.write_text(
            "# Device Monitor 2.14.0 install record (Decision 62)\n", encoding="utf-8"
        )
        opnsense.write_text("<opnsense/>\n", encoding="utf-8")
        core.mkdir()
        for index in range(guard.EXPECTED_CORE_LOCALE_FILES):
            (core / f"locale-{index}.mo").write_text(f"locale {index}\n", encoding="utf-8")
        installer.write_text("installer backup\n", encoding="utf-8")

        return {
            "version": 1,
            "base": str(base),
            "config": str(config),
            "db": str(db),
            "record": str(record),
            "opnsense_config": str(opnsense),
            "core_locale": str(core),
            "installer_backup": str(installer),
            "backup_config": str(base / "config.json"),
            "backup_db": str(base / "devices.db"),
            "recovery_db": str(base / "original-devices.db"),
            "poststate_db": str(base / "poststate-devices.db"),
            "poststate_summary": str(base / "poststate.json"),
            "backup_record": str(base / "installed-manifest.txt"),
            "backup_opnsense_config": str(base / "opnsense-config.xml"),
            "backup_core_locale": str(base / "core-locale"),
            "backup_installer": str(base / "install-v214.qMPS7n.tgz"),
            "cancel_file": str(base / "watchdog.cancel"),
            "cleanup_lock": str(base / "cleanup.lock"),
            "commands": {
                "service_stop": ["stop"],
                "service_start": ["start"],
                "service_status": ["status"],
                "process_list": ["ps"],
                "sockstat_listen": ["sockstat"],
            },
            "patterns": dict(guard.DEFAULT_PATTERNS),
            "stop_wait_seconds": 0.1,
            "lock_wait_seconds": 0.1,
        }

    def test_start_watchdog_is_detached_with_monotonic_deadline(self) -> None:
        state_path = self.base() / "guard-state.json"
        state = {
            "base": str(self.base()),
            "cancel_file": str(self.base() / "watchdog.cancel"),
            "watchdog_pid": None,
        }
        guard.write_json(state_path, state)
        process = mock.Mock(pid=43210)
        with mock.patch.object(guard, "pid_alive", return_value=False), mock.patch.object(
            guard.subprocess, "Popen", return_value=process
        ) as popen:
            pid = guard.start_watchdog(str(state_path))
        self.assertEqual(pid, 43210)
        self.assertTrue(popen.call_args.kwargs["start_new_session"])
        self.assertTrue(popen.call_args.kwargs["close_fds"])

    def test_watchdog_timeout_restores(self) -> None:
        state = {
            "base": str(self.base()),
            "cancel_file": str(self.base() / "watchdog.cancel"),
            "deadline_monotonic": time.monotonic() + 0.02,
            "deadline_epoch": time.time() + 0.02,
        }
        state_path = self.base() / "guard-state.json"
        guard.write_json(state_path, state)
        calls: list[tuple[str, str, str]] = []
        with mock.patch.object(
            guard, "cleanup", side_effect=lambda _state, reason, actor: calls.append((reason, actor, "")) or (True, "")
        ):
            result = guard.watchdog_main(str(state_path))
        self.assertEqual(result, 0)
        self.assertEqual(calls[0][:2], ("timeout", "watchdog"))

    def test_watchdog_signal_triggers_cleanup(self) -> None:
        state = {
            "base": str(self.base()),
            "cancel_file": str(self.base() / "watchdog.cancel"),
            "deadline_monotonic": time.monotonic() + 30,
            "deadline_epoch": time.time() + 30,
        }
        state_path = self.base() / "guard-state.json"
        guard.write_json(state_path, state)
        handlers: dict[int, object] = {}
        calls: list[str] = []

        def capture(signum: int, handler: object) -> None:
            handlers[signum] = handler

        def first_sleep(_seconds: float) -> None:
            callback = handlers[signal.SIGTERM]
            callback(signal.SIGTERM, None)  # type: ignore[operator]

        with mock.patch.object(guard.signal, "signal", side_effect=capture), mock.patch.object(
            guard.time, "sleep", side_effect=first_sleep
        ), mock.patch.object(
            guard,
            "cleanup",
            side_effect=lambda _state, reason, _actor: calls.append(reason) or (True, ""),
        ):
            result = guard.watchdog_main(str(state_path))
        self.assertEqual(result, 0)
        self.assertEqual(calls, ["watchdog_signal_15"])

    def test_watchdog_cancel_prevents_cleanup(self) -> None:
        state = {
            "base": str(self.base()),
            "cancel_file": str(self.base() / "watchdog.cancel"),
            "deadline_monotonic": time.monotonic() + 30,
            "deadline_epoch": time.time() + 30,
        }
        Path(str(state["cancel_file"])).write_text("cancel\n", encoding="utf-8")
        state_path = self.base() / "guard-state.json"
        guard.write_json(state_path, state)
        with mock.patch.object(guard, "cleanup") as cleanup:
            result = guard.watchdog_main(str(state_path))
        self.assertEqual(result, 0)
        cleanup.assert_not_called()

    def test_cleanup_stops_before_backup_validation_and_does_not_restart_on_failure(self) -> None:
        state = self.backup_state()
        calls: list[str] = []
        with mock.patch.object(
            guard,
            "stop_service_and_writers",
            side_effect=lambda _state: calls.append("stop") or (True, ""),
        ), mock.patch.object(
            guard,
            "find_writers",
            side_effect=lambda _state: calls.append("writers") or ([], None),
        ), mock.patch.object(
            guard,
            "validate_backup",
            side_effect=lambda _state: calls.append("validate") or (_ for _ in ()).throw(
                guard.GuardError("backup damaged")
            ),
        ), mock.patch.object(guard, "restore_files") as restore, mock.patch.object(
            guard, "start_and_verify_service"
        ) as start:
            ok, detail = guard.cleanup_locked(state, "timeout", "watchdog")
        self.assertFalse(ok)
        self.assertIn("backup damaged", detail)
        self.assertEqual(calls, ["stop", "writers", "validate"])
        restore.assert_not_called()
        start.assert_not_called()
        self.assertTrue(Path(str(state["base"])).is_dir())
        self.assertIn("FAIL", guard.restore_status(state))

    def test_writers_remaining_block_restoration(self) -> None:
        state = self.backup_state()
        with mock.patch.object(
            guard, "stop_service_and_writers", return_value=(False, "writers remain")
        ), mock.patch.object(guard, "restore_files") as restore, mock.patch.object(
            guard, "start_and_verify_service"
        ) as start:
            ok, _detail = guard.cleanup_locked(state, "interrupted", "supervisor")
        self.assertFalse(ok)
        restore.assert_not_called()
        start.assert_not_called()
        self.assertTrue(guard.restore_status(state).startswith("FAIL"))

    def test_overlapping_cleanup_cannot_restore(self) -> None:
        state = self.backup_state()
        lock = guard.acquire_cleanup_lock(state, 0)
        self.assertIsNotNone(lock)
        try:
            with mock.patch.object(guard, "restore_files") as restore:
                ok, detail = guard.cleanup(state, "timeout", "watchdog")
        finally:
            guard.release_cleanup_lock(lock)
        self.assertFalse(ok)
        self.assertIn("cleanup lock is held", detail)
        restore.assert_not_called()

    def test_restoration_failure_leaves_service_stopped_and_assets(self) -> None:
        state = self.backup_state()
        with mock.patch.object(
            guard, "stop_service_and_writers", return_value=(True, "")
        ), mock.patch.object(guard, "find_writers", return_value=([], None)), mock.patch.object(
            guard, "validate_backup"
        ), mock.patch.object(
            guard, "restore_files", side_effect=guard.GuardError("copy failed")
        ), mock.patch.object(guard, "start_and_verify_service") as start:
            ok, detail = guard.cleanup_locked(state, "timeout", "watchdog")
        self.assertFalse(ok)
        self.assertIn("copy failed", detail)
        start.assert_not_called()
        self.assertTrue(Path(str(state["base"])).is_dir())
        self.assertFalse(Path(str(state["cancel_file"])).exists())

    def test_failed_post_restore_service_check_forces_service_stop(self) -> None:
        state = self.backup_state()
        with mock.patch.object(
            guard, "stop_service_and_writers", return_value=(True, "")
        ), mock.patch.object(guard, "find_writers", return_value=([], None)), mock.patch.object(
            guard, "validate_backup"
        ), mock.patch.object(guard, "restore_files"), mock.patch.object(
            guard, "verify_restored", return_value=[]
        ), mock.patch.object(
            guard, "start_and_verify_service", return_value=(False, "not running")
        ), mock.patch.object(guard, "stop_after_failed_start") as force_stop:
            ok, _detail = guard.cleanup_locked(state, "payload_failed", "supervisor")
        self.assertFalse(ok)
        force_stop.assert_called_once_with(state)
        self.assertTrue(guard.restore_status(state).startswith("FAIL"))

    def test_service_start_retries_transient_configd_socket(self) -> None:
        state = self.backup_state()
        state["service_status_wait_seconds"] = 0.2
        state["service_status_poll_seconds"] = 0.01
        status_calls = 0

        def fake_run(command: list[str], timeout: float = 60) -> subprocess.CompletedProcess[str]:
            nonlocal status_calls
            if command == state["commands"]["service_start"]:
                return completed(command, "Starting devicemonitor.\n")
            status_calls += 1
            if status_calls == 1:
                return completed(
                    command,
                    "configd socket missing (@/var/run/configd.socket)\n",
                    returncode=255,
                )
            return completed(command, "running\n")

        with mock.patch.object(guard, "run_command", side_effect=fake_run):
            ok, detail = guard.start_and_verify_service(state)
        self.assertTrue(ok, detail)
        self.assertEqual(status_calls, 2)

    def test_service_start_retry_is_bounded(self) -> None:
        state = self.backup_state()
        state["service_status_wait_seconds"] = 0.0
        status_calls = 0

        def fake_run(command: list[str], timeout: float = 60) -> subprocess.CompletedProcess[str]:
            nonlocal status_calls
            if command == state["commands"]["service_start"]:
                return completed(command, "Starting devicemonitor.\n")
            status_calls += 1
            return completed(command, "configd socket missing\n", returncode=255)

        with mock.patch.object(guard, "run_command", side_effect=fake_run):
            ok, detail = guard.start_and_verify_service(state)
        self.assertFalse(ok)
        self.assertIn("did not report running", detail)
        self.assertEqual(status_calls, 1)

    def test_late_watchdog_sees_restored_status_and_does_not_cleanup(self) -> None:
        state = {
            "base": str(self.base()),
            "cancel_file": str(self.base() / "watchdog.cancel"),
            "deadline_monotonic": time.monotonic() + 30,
            "deadline_epoch": time.time() + 30,
        }
        (self.base() / "restore.status").write_text("PASS\n", encoding="utf-8")
        state_path = self.base() / "guard-state.json"
        guard.write_json(state_path, state)
        with mock.patch.object(guard, "cleanup") as cleanup:
            result = guard.watchdog_main(str(state_path))
        self.assertEqual(result, 0)
        cleanup.assert_not_called()

    def test_notified_at_migration_is_removed_by_exact_restore(self) -> None:
        state = self.backup_state()
        guard.create_backup(state)
        config_path = Path(str(state["config"]))
        db_path = Path(str(state["db"]))
        changed = json.loads(config_path.read_text(encoding="utf-8"))
        changed["monitored_interfaces"] = "opt1"
        config_path.write_text(json.dumps(changed, indent=2), encoding="utf-8")
        with sqlite_conn(db_path) as conn:
            conn.execute("ALTER TABLE device_identity_events ADD COLUMN notified_at DATETIME")
        Path(str(db_path) + "-wal").write_text("", encoding="utf-8")
        Path(str(db_path) + "-shm").write_text("", encoding="utf-8")

        with mock.patch.object(
            guard, "stop_service_and_writers", return_value=(True, "")
        ), mock.patch.object(guard, "find_writers", return_value=([], None)), mock.patch.object(
            guard, "start_and_verify_service", return_value=(True, "")
        ):
            ok, detail = guard.cleanup_locked(state, "payload_failed", "supervisor")
        self.assertTrue(ok, detail)
        self.assertEqual(config_path.read_bytes(), Path(str(state["backup_config"])).read_bytes())
        self.assertFalse(guard.sqlite_column_present(str(db_path), "device_identity_events", "notified_at"))
        self.assertFalse(Path(str(db_path) + "-wal").exists())
        self.assertFalse(Path(str(db_path) + "-shm").exists())
        self.assertTrue(guard.restore_status(state).startswith("PASS"))

    def test_original_and_snapshot_have_separate_physical_identities(self) -> None:
        state = self.backup_state()
        guard.create_backup(state)
        original = Path(str(state["recovery_db"]))
        snapshot = Path(str(state["backup_db"]))
        prestate = state["prestate"]

        self.assertEqual(sha(original), prestate["original_database"]["db"]["sha"])
        self.assertEqual(sha(snapshot), prestate["snapshot_database"]["db"]["sha"])
        self.assertNotEqual(sha(original), sha(snapshot))
        self.assertEqual(
            guard.sqlite_logical_sha_assets(str(original)),
            guard.sqlite_logical_sha_assets(str(snapshot)),
        )

    def test_snapshot_equivalence_does_not_satisfy_original_physical_identity(self) -> None:
        state = self.backup_state()
        guard.create_backup(state)
        original = Path(str(state["recovery_db"]))
        db_path = Path(str(state["db"]))
        snapshot = Path(str(state["backup_db"]))

        shutil.copyfile(snapshot, db_path)
        shutil.copystat(original, db_path)
        errors = guard.verify_restored(state)

        self.assertIn("restored database digest mismatch", errors)
        self.assertEqual(
            guard.sqlite_logical_sha_assets(str(db_path)),
            guard.sqlite_logical_sha_assets(str(original)),
        )

    def test_restoring_original_recovery_bytes_passes_physical_identity(self) -> None:
        state = self.backup_state()
        guard.create_backup(state)
        original = Path(str(state["recovery_db"]))
        db_path = Path(str(state["db"]))
        with sqlite_conn(db_path) as conn:
            conn.execute(
                "INSERT INTO device_identity_events(mac) VALUES ('11:22:33:44:55:66')"
            )
        self.assertNotEqual(sha(db_path), sha(original))

        with mock.patch.object(guard, "find_writers", return_value=([], None)):
            guard.restore_files(state)

        self.assertEqual(guard.database_assets(str(db_path)), guard.database_assets(str(original)))
        self.assertEqual(guard.verify_restored(state), [])

    def test_wal_and_shm_are_archived_before_restore(self) -> None:
        state = self.backup_state()
        guard.create_backup(state)
        db_path = Path(str(state["db"]))
        wal_payload = b"uncheckpointed-wal-content"
        shm_payload = b"shared-memory-content"
        Path(str(db_path) + "-wal").write_bytes(wal_payload)
        Path(str(db_path) + "-shm").write_bytes(shm_payload)

        with mock.patch.object(guard, "find_writers", return_value=([], None)):
            guard.restore_files(state)

        self.assertEqual(Path(str(state["poststate_db"]) + "-wal").read_bytes(), wal_payload)
        self.assertEqual(Path(str(state["poststate_db"]) + "-shm").read_bytes(), shm_payload)
        self.assertFalse(Path(str(db_path) + "-wal").exists())
        self.assertFalse(Path(str(db_path) + "-shm").exists())
        self.assertEqual(guard.verify_restored(state), [])

    def test_real_wal_and_shm_are_captured_and_restored_exactly(self) -> None:
        state = self.backup_state()
        db_path = Path(str(state["db"]))
        db_path.unlink()
        script = (
            "import os, sqlite3, sys\n"
            "conn = sqlite3.connect(sys.argv[1])\n"
            "conn.execute('PRAGMA journal_mode=wal')\n"
            "conn.execute('PRAGMA wal_autocheckpoint=0')\n"
            "conn.execute('CREATE TABLE device_identity_events (id INTEGER PRIMARY KEY, mac TEXT)')\n"
            "conn.execute(\"INSERT INTO device_identity_events(mac) VALUES ('aa:bb:cc:dd:ee:ff')\")\n"
            "conn.commit()\n"
            "os._exit(0)\n"
        )
        subprocess.run([sys.executable, "-c", script, str(db_path)], check=True)
        self.assertTrue(Path(str(db_path) + "-wal").exists())
        self.assertTrue(Path(str(db_path) + "-shm").exists())

        guard.create_backup(state)
        original = state["prestate"]["original_database"]
        self.assertTrue(original["wal"]["present"])
        self.assertTrue(original["shm"]["present"])
        self.assertFalse(state["prestate"]["snapshot_database"]["wal"]["present"])
        self.assertFalse(state["prestate"]["snapshot_database"]["shm"]["present"])
        db_path.write_bytes(b"mutated main database bytes")

        with mock.patch.object(guard, "find_writers", return_value=([], None)):
            guard.restore_files(state)

        self.assertEqual(guard.database_assets(str(db_path)), original)
        self.assertEqual(guard.verify_restored(state), [])

    def test_unsafe_capture_leaves_monitoring_stopped(self) -> None:
        state = self.backup_state()
        with mock.patch.object(
            guard, "stop_service_and_writers", return_value=(False, "writers remain")
        ), mock.patch.object(guard, "stop_after_failed_start") as force_stop, mock.patch.object(
            guard, "create_backup"
        ) as create, mock.patch.object(guard, "start_and_verify_service") as start:
            with self.assertRaisesRegex(guard.GuardError, "writers remain"):
                guard.capture_prestate(state)

        force_stop.assert_called_once_with(state)
        create.assert_not_called()
        start.assert_not_called()
        self.assertTrue(guard.restore_status(state).startswith("FAIL"))

    def test_unsafe_restoration_leaves_monitoring_stopped(self) -> None:
        state = self.backup_state()
        guard.create_backup(state)
        Path(str(state["recovery_db"])).write_bytes(b"damaged recovery copy")

        with mock.patch.object(
            guard, "stop_service_and_writers", return_value=(True, "")
        ), mock.patch.object(guard, "find_writers", return_value=([], None)), mock.patch.object(
            guard, "start_and_verify_service"
        ) as start:
            ok, detail = guard.cleanup_locked(state, "payload_failed", "supervisor")

        self.assertFalse(ok)
        self.assertIn("original database recovery copy changed", detail)
        start.assert_not_called()
        self.assertTrue(guard.restore_status(state).startswith("FAIL"))

    def test_directory_installer_backup_is_archived(self) -> None:
        state = self.backup_state()
        installer = Path(str(state["installer_backup"]))
        installer.unlink()
        installer.mkdir()
        (installer / "plan.txt").write_text("approved plan\n", encoding="utf-8")

        guard.create_backup(state)

        with tarfile.open(str(state["backup_installer"]), "r:gz") as archive:
            names = archive.getnames()
        self.assertIn("install-v214.qMPS7n/plan.txt", names)

    def test_empty_directory_installer_backup_is_rejected(self) -> None:
        state = self.backup_state()
        installer = Path(str(state["installer_backup"]))
        installer.unlink()
        installer.mkdir()

        with self.assertRaisesRegex(guard.GuardError, "installer backup directory is empty"):
            guard.create_backup(state)

    def test_watchdog_cancelled_only_after_restore_pass(self) -> None:
        state = self.backup_state()
        state["watchdog_pid"] = 99
        state_path = self.base() / "guard-state.json"
        guard.write_json(state_path, state)
        order: list[str] = []

        class Payload:
            pid = 123
            returncode = 0

            def poll(self) -> int:
                return 0

            def wait(self, timeout: float | None = None) -> int:
                return 0

        with mock.patch.object(guard, "pid_alive", return_value=True), mock.patch.object(
            guard.subprocess, "Popen", return_value=Payload()
        ), mock.patch.object(
            guard,
            "cleanup",
            side_effect=lambda *_args: order.append("cleanup") or (True, ""),
        ), mock.patch.object(
            guard, "cancel_watchdog", side_effect=lambda _state: order.append("cancel")
        ):
            result = guard.run_payload(
                argparse.Namespace(state=str(state_path), payload=["--", "/bin/true"])
            )
        self.assertEqual(result, 0)
        self.assertEqual(order, ["cleanup", "cancel"])

    def test_failed_restore_does_not_cancel_watchdog(self) -> None:
        state = self.backup_state()
        state["watchdog_pid"] = 99
        state_path = self.base() / "guard-state.json"
        guard.write_json(state_path, state)

        class Payload:
            pid = 123
            returncode = 1

            def poll(self) -> int:
                return 1

            def wait(self, timeout: float | None = None) -> int:
                return 1

        with mock.patch.object(guard, "pid_alive", return_value=True), mock.patch.object(
            guard.subprocess, "Popen", return_value=Payload()
        ), mock.patch.object(guard, "cleanup", return_value=(False, "restore failed")), mock.patch.object(
            guard, "cancel_watchdog"
        ) as cancel:
            result = guard.run_payload(
                argparse.Namespace(state=str(state_path), payload=["/bin/false"])
            )
        self.assertEqual(result, 1)
        cancel.assert_not_called()

    def test_interruption_terminates_payload_then_cleans(self) -> None:
        state = self.backup_state()
        state["watchdog_pid"] = 99
        state_path = self.base() / "guard-state.json"
        guard.write_json(state_path, state)
        handlers: dict[int, object] = {}
        order: list[str] = []

        def capture(signum: int, handler: object) -> None:
            handlers[signum] = handler

        class Payload:
            pid = 123
            returncode = 0

            def poll(self) -> None:
                callback = handlers[signal.SIGTERM]
                callback(signal.SIGTERM, None)  # type: ignore[operator]
                return None

            def wait(self, timeout: float | None = None) -> int:
                return 0

        with mock.patch.object(guard, "pid_alive", return_value=True), mock.patch.object(
            guard.signal, "signal", side_effect=capture
        ), mock.patch.object(
            guard.subprocess, "Popen", return_value=Payload()
        ), mock.patch.object(
            guard, "terminate_payload", side_effect=lambda _state: order.append("terminate")
        ), mock.patch.object(
            guard,
            "cleanup",
            side_effect=lambda _state, reason, _actor: order.append(reason) or (True, ""),
        ), mock.patch.object(guard, "cancel_watchdog"):
            result = guard.run_payload(
                argparse.Namespace(state=str(state_path), payload=["sleep", "60"])
            )
        self.assertEqual(result, 130)
        self.assertEqual(order, ["terminate", "interrupted"])

    def test_scope_config_and_target_validation(self) -> None:
        self.assertEqual(guard.validate_scope_config(dict(guard.SCOPE_KEYS)), [])
        self.assertEqual(guard.validate_targets(guard.EXPECTED_TARGET_LINE + "\n"), [])
        bad = dict(guard.SCOPE_KEYS)
        bad["monitored_interfaces"] = "lan,opt1"
        self.assertTrue(any("monitored_interfaces" in item for item in guard.validate_scope_config(bad)))
        for key, value in (
            ("email_to", "other@example.invalid"),
            ("smtp_host", "192.0.2.10"),
            ("adguard_rewrite_enabled", "1"),
            ("targeted_nmap_enabled", "1"),
            ("webhook_enabled", "1"),
        ):
            candidate = dict(guard.SCOPE_KEYS)
            candidate[key] = value
            with self.subTest(key=key):
                self.assertTrue(any(key in item for item in guard.validate_scope_config(candidate)))
        self.assertTrue(
            guard.validate_targets(
                guard.EXPECTED_TARGET_LINE + "\nlan: subnet=192.168.20.0/24\n"
            )
        )

    def test_scope_source_checks_pass_against_actual_commands(self) -> None:
        paths = {
            "scan": str(ROOT / "src/opnsense/scripts/OPNsense/DeviceMonitor/scan_network.py"),
            "notification": str(ROOT / "src/opnsense/scripts/OPNsense/DeviceMonitor/NotificationHandler.php"),
            "smtp": str(ROOT / "src/opnsense/scripts/OPNsense/DeviceMonitor/smtp_send.py"),
            "identity": str(ROOT / "src/opnsense/scripts/OPNsense/DeviceMonitor/notify_identity_mail.php"),
        }
        self.assertEqual(guard.scope_check(paths, dict(guard.SCOPE_KEYS), guard.EXPECTED_TARGET_LINE), [])

    def test_sockstat_is_detection_only(self) -> None:
        text = (
            "USER COMMAND PID FD PROTO LOCAL ADDRESS FOREIGN ADDRESS\n"
            "root python3 1 3 tcp4 127.0.0.1:5000 127.0.0.1:2525\n"
            "root php 2 4 tcp4 192.168.50.1:5001 192.168.50.1:2525\n"
        )
        self.assertEqual(guard.sockstat_connection_violations(text), [])
        bad = text + "root python3 3 5 tcp4 192.168.20.23:5002 203.0.113.9:443\n"
        violations = guard.sockstat_connection_violations(bad)
        self.assertEqual(len(violations), 1)
        self.assertIn("203.0.113.9", violations[0])

    def test_smtp_capture_normalizes_angle_brackets_and_esmtp_size(self) -> None:
        capture = self.tempdir / "smtp"
        capture.mkdir()
        envelopes = [
            {
                "mail_from": f"<{guard.TEST_EMAIL}> size=2659",
                "rcpt_to": [f"<{guard.TEST_EMAIL}>"],
            },
            {
                "mail_from": f"MAIL FROM:<{guard.TEST_EMAIL}> SIZE=8085",
                "rcpt_to": [f"RCPT TO:<{guard.TEST_EMAIL}>"],
            },
        ]
        (capture / "envelopes.jsonl").write_text(
            "".join(json.dumps(item) + "\n" for item in envelopes), encoding="utf-8"
        )
        for index in range(2):
            (capture / f"message-{index}.eml").write_text(
                f"X-Envelope-To: <{guard.TEST_EMAIL}>\n\nfixture\n", encoding="utf-8"
            )
        self.assertEqual(guard.smtp_capture_errors(str(capture)), [])
        envelopes[1]["rcpt_to"] = ["outside@example.invalid"]
        (capture / "envelopes.jsonl").write_text(
            "".join(json.dumps(item) + "\n" for item in envelopes), encoding="utf-8"
        )
        self.assertTrue(guard.smtp_capture_errors(str(capture)))

    def test_acceptance_uses_latest_monitoring_log_state(self) -> None:
        log = self.tempdir / "devicemonitor.log"
        log.write_text(
            "Monitoring ENABLED\nscan complete\nMonitoring DISABLED\n", encoding="utf-8"
        )
        self.assertEqual(guard.latest_monitoring_state(str(log)), "DISABLED")
        log.write_text("Monitoring DISABLED\nMonitoring ENABLED\n", encoding="utf-8")
        self.assertEqual(guard.latest_monitoring_state(str(log)), "ENABLED")
        self.assertIsNone(guard.latest_monitoring_state(str(self.tempdir / "missing.log")))

    def test_preflight_accepts_only_approved_mock_scope(self) -> None:
        config = self.tempdir / "config.json"
        db = self.tempdir / "devices.db"
        record = self.tempdir / "installed-manifest.txt"
        opnsense = self.tempdir / "config.xml"
        targets = [self.tempdir / "target-one", self.tempdir / "target-two"]
        config.write_text(json.dumps({"enabled": "0", "monitored_interfaces": ""}), encoding="utf-8")
        with sqlite_conn(db) as conn:
            conn.execute(
                "CREATE TABLE port_discovery_targets "
                "(mac TEXT, enabled INTEGER, next_scan_at TEXT)"
            )
        rows = []
        for target in targets:
            target.write_text(target.name, encoding="utf-8")
            rows.append(f"{sha(target)} {target}")
        record.write_text(
            "# Device Monitor 2.14.0 install record (Decision 62)\n"
            + "\n".join(rows)
            + "\n",
            encoding="utf-8",
        )
        opnsense.write_text(
            "<opnsense><interfaces><opt1><enable>1</enable><if>vlan0.50</if>"
            "<ipaddr>192.168.50.1</ipaddr><subnet>24</subnet><descr>DMTEST</descr>"
            "</opt1></interfaces></opnsense>\n",
            encoding="utf-8",
        )
        ifconfig = (
            "igb0: flags=1\n    inet 192.168.20.23 netmask 0xffffff00\n"
            "vlan0.50: flags=1\n    description: DMTEST (opt1)\n"
            "    inet 192.168.50.1 netmask 0xffffff00\n"
        )
        commands = {
            "hostname": ["host"],
            "ifconfig": ["ifconfig"],
            "service_status": ["status"],
            "sockstat_listen": ["sockstat"],
        }
        outputs = {
            "host": completed(["host"], guard.EXPECTED_HOSTNAME + "\n"),
            "ifconfig": completed(["ifconfig"], ifconfig),
            "status": completed(["status"], "running\n"),
            "sockstat": completed(["sockstat"], "USER COMMAND PID FD PROTO LOCAL ADDRESS\n"),
        }
        with mock.patch.object(
            guard, "run_command", side_effect=lambda command, timeout=60: outputs[command[0]]
        ), mock.patch.object(
            guard.shutil,
            "disk_usage",
            return_value=shutil._ntuple_diskusage(2 * 1024**3, 1 * 1024**3, 2 * 1024**3),
        ):
            guard.preflight(
                str(config),
                str(db),
                str(record),
                str(self.tempdir),
                opnsense_config=str(opnsense),
                commands=commands,
                expected_record_sha=sha(record),
                expected_record_rows=2,
            )
            bad_ifconfig = ifconfig + "carp0: flags=1\n"
            outputs["ifconfig"] = completed(["ifconfig"], bad_ifconfig)
            with self.assertRaisesRegex(guard.GuardError, "CARP"):
                guard.preflight(
                    str(config),
                    str(db),
                    str(record),
                    str(self.tempdir),
                    opnsense_config=str(opnsense),
                    commands=commands,
                    expected_record_sha=sha(record),
                    expected_record_rows=2,
                )

    def test_preflight_rejects_due_port_discovery_and_2525_listener(self) -> None:
        config = self.tempdir / "config.json"
        db = self.tempdir / "devices.db"
        record = self.tempdir / "installed-manifest.txt"
        opnsense = self.tempdir / "config.xml"
        target = self.tempdir / "target"
        config.write_text(json.dumps({"enabled": "0", "monitored_interfaces": ""}), encoding="utf-8")
        target.write_text("target\n", encoding="utf-8")
        record.write_text(
            "# Device Monitor 2.14.0 install record (Decision 62)\n"
            f"{sha(target)} {target}\n",
            encoding="utf-8",
        )
        opnsense.write_text(
            "<opnsense><interfaces><opt1><enable>1</enable><if>vlan0.50</if>"
            "<ipaddr>192.168.50.1</ipaddr><subnet>24</subnet><descr>DMTEST</descr>"
            "</opt1></interfaces></opnsense>\n",
            encoding="utf-8",
        )
        with sqlite_conn(db) as conn:
            conn.execute(
                "CREATE TABLE port_discovery_targets "
                "(mac TEXT, enabled INTEGER, next_scan_at TEXT)"
            )
            conn.execute(
                "INSERT INTO port_discovery_targets VALUES ('aa:bb:cc:dd:ee:ff', 1, '2000-01-01 00:00:00')"
            )
        commands = {
            "hostname": ["host"],
            "ifconfig": ["ifconfig"],
            "service_status": ["status"],
            "sockstat_listen": ["sockstat"],
        }
        outputs = {
            "host": completed(["host"], guard.EXPECTED_HOSTNAME + "\n"),
            "ifconfig": completed(
                ["ifconfig"],
                "igb0: flags=1\n    inet 192.168.20.23 netmask 0xffffff00\n"
                "vlan0.50: flags=1\n    description: DMTEST (opt1)\n"
                "    inet 192.168.50.1 netmask 0xffffff00\n",
            ),
            "status": completed(["status"], "running\n"),
            "sockstat": completed(["sockstat"], "python3 root 1 3 tcp4 *:2525 *:*\n"),
        }
        with mock.patch.object(
            guard, "run_command", side_effect=lambda command, timeout=60: outputs[command[0]]
        ), mock.patch.object(
            guard.shutil,
            "disk_usage",
            return_value=shutil._ntuple_diskusage(2 * 1024**3, 1 * 1024**3, 2 * 1024**3),
        ):
            with self.assertRaisesRegex(guard.GuardError, "port 2525"):
                guard.preflight(
                    str(config), str(db), str(record), str(self.tempdir),
                    opnsense_config=str(opnsense), commands=commands,
                    expected_record_sha=sha(record), expected_record_rows=1,
                )
            outputs["sockstat"] = completed(["sockstat"], "USER COMMAND PID FD PROTO LOCAL ADDRESS\n")
            with self.assertRaisesRegex(guard.GuardError, "port-discovery target is due"):
                guard.preflight(
                    str(config), str(db), str(record), str(self.tempdir),
                    opnsense_config=str(opnsense), commands=commands,
                    expected_record_sha=sha(record), expected_record_rows=1,
                )

    def test_record_target_set_rejects_missing_target(self) -> None:
        target = self.tempdir / "target"
        target.write_text("target\n", encoding="utf-8")
        record = self.tempdir / "record"
        record.write_text(
            "# Device Monitor 2.14.0 install record (Decision 62)\n"
            f"{sha(target)} {target}\n",
            encoding="utf-8",
        )
        target.unlink()
        errors = guard.validate_record_target_set(str(record), sha(record), 1)
        self.assertTrue(any("cannot be read" in item for item in errors))

    def test_normalize_payload_removes_separator(self) -> None:
        self.assertEqual(guard.normalize_payload_command(["--", "/bin/true"]), ["/bin/true"])
        with self.assertRaises(guard.GuardError):
            guard.normalize_payload_command([])

    def test_begin_parser_exposes_the_preflight_space_path(self) -> None:
        args = guard.build_parser().parse_args(
            ["begin", "--base", str(self.base() / "guard")]
        )
        self.assertEqual(args.space_path, "/")


if __name__ == "__main__":
    unittest.main(verbosity=2)

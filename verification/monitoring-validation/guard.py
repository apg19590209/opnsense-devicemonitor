#!/usr/bin/env python3
"""Guarded execution wrapper for the bounded Device Monitor §9.4 exercise.

The wrapper owns only the safety lifecycle: pre-state backup, an independently
detached watchdog, serialized cleanup, exact database/configuration restoration
and post-restoration acceptance. It does not enable monitoring by itself.

No host action occurs unless the operator explicitly invokes ``begin``/``run``
with the live paths. The unit tests use temporary state and mock commands.
"""

from __future__ import annotations

import argparse
import contextlib
import datetime as dt
import fcntl
import hashlib
import ipaddress
import json
import os
import re
import shutil
import signal
import sqlite3
import stat
import subprocess
import sys
import tarfile
import tempfile
import time
import urllib.parse
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any


TEST_EMAIL = "devicemonitor-test@example.invalid"
EXPECTED_RECORD_SHA = "d891ce68c9035b3bcd2384d6f3705d6c8d9bc20fb5ef13cc9ca80b2ae1c035a2"
EXPECTED_RECORD_ROWS = 63
EXPECTED_CORE_LOCALE_FILES = 19
EXPECTED_HOSTNAME = "OPNsense.internal"
EXPECTED_WAN_IPV4 = "192.168.20.23"
EXPECTED_INTERFACE = "opt1"
EXPECTED_DEVICE = "vlan0.50"
EXPECTED_INTERFACE_IPV4 = "192.168.50.1"
EXPECTED_SCOPE = ipaddress.ip_network("192.168.50.0/24")
EXPECTED_TARGET_LINE = (
    "opt1: description=DMTEST device=vlan0.50 subnet=192.168.50.0/24"
)

SERVICE_STATUS_RETRY_SECONDS = 30.0
SERVICE_STATUS_POLL_SECONDS = 0.5

DEFAULT_CONFIG = "/var/db/devicemonitor/config.json"
DEFAULT_DB = "/var/db/devicemonitor/devices.db"
DEFAULT_RECORD = "/var/db/devicemonitor/installed-manifest.txt"
DEFAULT_OPNSENSE_CONFIG = "/conf/config.xml"
DEFAULT_DAEMON_LOG = "/var/log/devicemonitor.log"
DEFAULT_CORE_LOCALE = "/var/backups/devicemonitor/core-locale"
DEFAULT_INSTALLER_BACKUP = "/var/backups/devicemonitor/install-v214.qMPS7n"

DEFAULT_COMMANDS = {
    "service_stop": ["/usr/sbin/service", "devicemonitor", "stop"],
    "service_start": ["/usr/sbin/service", "devicemonitor", "start"],
    "service_status": ["/usr/local/sbin/configctl", "devicemonitor", "status"],
    "process_list": ["/bin/ps", "-axo", "pid=,command="],
    "hostname": ["/bin/hostname"],
    "ifconfig": ["/sbin/ifconfig", "-a"],
    "sockstat_listen": ["/usr/bin/sockstat", "-4l"],
}

DEFAULT_PATTERNS = {
    "daemon": (
        r"^/usr/local/bin/python3 /usr/local/opnsense/scripts/"
        r"OPNsense/DeviceMonitor/monitor_daemon\.py$"
    ),
    "scan": (
        r"^/usr/local/bin/python3 /usr/local/opnsense/scripts/"
        r"OPNsense/DeviceMonitor/scan_network\.py(?: |$)"
    ),
}

SCOPE_KEYS = {
    "monitored_interfaces": "opt1",
    "enabled": "0",
    "scan_interval": 60,
    "visibility_prime_interval": 86400,
    "email_enabled": "0",
    "email_to": TEST_EMAIL,
    "email_from": TEST_EMAIL,
    "email_method": "smtp",
    "smtp_host": "127.0.0.1",
    "smtp_port": 2525,
    "smtp_encryption": "none",
    "smtp_username": "",
    "smtp_password": "",
    "identity_email_enabled": "0",
    "service_email_enabled": "0",
    "email_reminder_identity": 0,
    "email_reminder_service": 0,
    "email_reminder_new_device": 0,
    "email_reminder_scan": 0,
    "adguard_rewrite_enabled": "0",
    "pihole_enabled": "0",
    "unbound_enabled": "0",
    "targeted_nmap_enabled": "0",
    "webhook_enabled": "0",
    "identity_webhook_enabled": "0",
    "ha_carp_enabled": "1",
    "ha_role_override": "auto",
    "ha_notify_failover": "0",
}

SCAN_SOURCE_CHECKS = (
    (
        "visibility targets are derived only from selected networks",
        r"for address in network\.hosts\(\)",
    ),
    (
        "visibility priming pings only resolved target addresses",
        r"\['/sbin/ping', '-n', '-c', '1', address\]",
    ),
    (
        "probe candidates are filtered by ip_is_in_scope",
        r"if not ip_is_in_scope\(ip, networks\):",
    ),
    (
        "active and known service candidates pass the scope gate",
        r"def add_candidate\(mac, ip, interface\):.*?if not ip_is_in_scope\(ip, networks\):",
    ),
    (
        "structured Nmap candidates pass the scope gate",
        r"return \[row for row in rows if ip_is_in_scope\(row\[0\], networks\)\]",
    ),
    (
        "DHCP discovery is bound to the selected interface",
        r"broadcast-dhcp-discover.*?'-e',\s*interface",
    ),
    (
        "targeted scan accepts one literal IPv4 target",
        r"'-oX', '-',\s*ip",
    ),
    (
        "port discovery accepts one literal in-scope IPv4 target",
        r"'-p', '1-65535', '-oX', '-', ip",
    ),
    (
        "single-host Phase 3 Nmap receives one literal target",
        r"'-oX',\s*'-',\s*target_ip",
    ),
    (
        "SMB verification invokes Nmap on one literal target",
        r"'--script',\s*'smb-protocols',\s*ip",
    ),
    (
        "targeted Nmap is gated by configuration",
        r"config\.get\('targeted_nmap_enabled', True\)",
    ),
    (
        "targeted-Nmap rows are filtered to the selected networks",
        r"if ip_is_in_scope\(row\['ip'\], networks\):",
    ),
    (
        "port discovery requires an opted-in due target",
        r"WHERE t\.enabled = 1 AND t\.next_scan_at <= \?",
    ),
    (
        "port-discovery destinations are filtered to the selected networks",
        r"if ip_is_in_scope\(candidate\[1\], networks\)",
    ),
    (
        "local VPN probing requires an in-scope local address",
        r"if not local_ip or not ip_is_in_scope\(local_ip, networks\):",
    ),
    (
        "AdGuard enrichment is gated by configuration",
        r"if not config\.get\('adguard_rewrite_enabled'\):",
    ),
    (
        "Pi-hole enrichment is gated by configuration",
        r"if not config\.get\('pihole_enabled'\):",
    ),
)

NOTIFICATION_SOURCE_CHECKS = (
    (
        "SMTP and sendmail are separate branches",
        r"if \(\$email_method === 'smtp'\)",
    ),
    (
        "sendmail is reached only from the non-SMTP branch",
        r"\$sendResult = \$this->sendViaSendmail\(",
    ),
    (
        "disabled webhook exits before curl_init",
        r"if \(!\$configured_enabled \|\| \$configured_url === ''\)",
    ),
)

SMTP_SOURCE_CHECKS = (
    (
        "SMTP host comes from the Device Monitor configuration",
        r'host = str\(config\.get\("smtp_host", ""\)\)\.strip\(\)',
    ),
    (
        "SMTP sends to the configured recipient set",
        r"server\.sendmail\(mail_from, recipients, msg\.as_string\(\)\)",
    ),
)

IDENTITY_SOURCE_CHECK = (
    "identity email is gated by identity_email_enabled",
    r"identity_email_enabled",
)


class GuardError(RuntimeError):
    """A fail-closed guard error."""


def utc_stamp() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def iso_now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


def append_event(base: str | os.PathLike[str], event: str, detail: str = "") -> None:
    path = Path(base) / "guard-events.jsonl"
    record = {"ts": iso_now(), "event": event, "detail": detail}
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, sort_keys=True) + "\n")
        handle.flush()
        os.fsync(handle.fileno())


def write_text_atomic(path: str | os.PathLike[str], text: str, mode: int = 0o600) -> None:
    destination = Path(path)
    temporary = destination.with_name(destination.name + f".tmp-{os.getpid()}")
    with temporary.open("w", encoding="utf-8") as handle:
        handle.write(text)
        handle.flush()
        os.fsync(handle.fileno())
    os.chmod(temporary, mode)
    os.replace(temporary, destination)


def read_json(path: str | os.PathLike[str]) -> dict[str, Any]:
    with open(path, "r", encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise GuardError(f"JSON object required: {path}")
    return value


def write_json(path: str | os.PathLike[str], value: dict[str, Any]) -> None:
    write_text_atomic(path, json.dumps(value, indent=2, sort_keys=True) + "\n")


def sha256_file(path: str | os.PathLike[str]) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sqlite_uri(path: str | os.PathLike[str], *, immutable: bool = False) -> str:
    quoted = urllib.parse.quote(str(path), safe="/")
    suffix = "&immutable=1" if immutable else ""
    return f"file:{quoted}?mode=ro{suffix}"


def sqlite_integrity(path: str | os.PathLike[str], pragma: str = "integrity_check") -> str:
    conn = sqlite3.connect(sqlite_uri(path, immutable=True), uri=True, timeout=5)
    try:
        row = conn.execute(f"PRAGMA {pragma}").fetchone()
    finally:
        conn.close()
    return "" if row is None else str(row[0])


def sqlite_journal_mode(path: str | os.PathLike[str]) -> str:
    conn = sqlite3.connect(sqlite_uri(path, immutable=True), uri=True, timeout=5)
    try:
        row = conn.execute("PRAGMA journal_mode").fetchone()
    finally:
        conn.close()
    return "" if row is None else str(row[0]).lower()


def sqlite_integrity_live(path: str, pragma: str = "integrity_check") -> str:
    conn = sqlite3.connect(sqlite_uri(path), uri=True, timeout=5)
    try:
        row = conn.execute(f"PRAGMA {pragma}").fetchone()
    finally:
        conn.close()
    return "" if row is None else str(row[0])


def sqlite_journal_mode_live(path: str) -> str:
    conn = sqlite3.connect(sqlite_uri(path), uri=True, timeout=5)
    try:
        row = conn.execute("PRAGMA journal_mode").fetchone()
    finally:
        conn.close()
    return "" if row is None else str(row[0]).lower()


def sqlite_logical_sha(path: str | os.PathLike[str]) -> str:
    conn = sqlite3.connect(sqlite_uri(path, immutable=True), uri=True, timeout=5)
    digest = hashlib.sha256()
    try:
        for line in conn.iterdump():
            digest.update(line.encode("utf-8"))
            digest.update(b"\n")
    finally:
        conn.close()
    return digest.hexdigest()


def sqlite_backup(source: str, destination: str) -> None:
    src = sqlite3.connect(source, timeout=30)
    dst = sqlite3.connect(destination, timeout=30)
    try:
        src.backup(dst)
    finally:
        dst.close()
        src.close()


def file_metadata(path: str) -> dict[str, int]:
    info = os.stat(path)
    return {
        "mode": stat.S_IMODE(info.st_mode),
        "uid": info.st_uid,
        "gid": info.st_gid,
    }


def copy_with_metadata(source: str, destination: str, metadata: dict[str, int]) -> None:
    temporary = destination + f".restore-{os.getpid()}.tmp"
    shutil.copyfile(source, temporary)
    with open(temporary, "rb") as handle:
        os.fsync(handle.fileno())
    os.chmod(temporary, int(metadata["mode"]))
    if os.geteuid() == 0:
        os.chown(temporary, int(metadata["uid"]), int(metadata["gid"]))
    os.replace(temporary, destination)


DATABASE_ASSET_SUFFIXES = (("db", ""), ("wal", "-wal"), ("shm", "-shm"))


def file_asset(path: str) -> dict[str, Any]:
    if not os.path.exists(path):
        return {"present": False, "sha": None, "metadata": None}
    if not os.path.isfile(path):
        raise GuardError(f"database asset is not a regular file: {path}")
    return {
        "present": True,
        "sha": sha256_file(path),
        "metadata": file_metadata(path),
    }


def database_assets(path: str) -> dict[str, dict[str, Any]]:
    return {
        name: file_asset(path + suffix)
        for name, suffix in DATABASE_ASSET_SUFFIXES
    }


def copy_database_assets(source: str, destination: str) -> None:
    for _name, suffix in DATABASE_ASSET_SUFFIXES:
        source_path = source + suffix
        destination_path = destination + suffix
        if os.path.exists(source_path):
            copy_with_metadata(
                source_path,
                destination_path,
                file_metadata(source_path),
            )
        else:
            with contextlib.suppress(FileNotFoundError):
                os.unlink(destination_path)


@contextlib.contextmanager
def sqlite_readable_copy(path: str):
    if not os.path.isfile(path):
        raise GuardError(f"database does not exist: {path}")
    with tempfile.TemporaryDirectory(prefix="dm-guard-sqlite-") as directory:
        target = str(Path(directory) / "devices.db")
        copy_database_assets(path, target)
        for _name, suffix in DATABASE_ASSET_SUFFIXES:
            if os.path.exists(target + suffix):
                os.chmod(target + suffix, 0o600)
        connection = sqlite3.connect(target, timeout=5)
        try:
            yield connection
        finally:
            connection.close()


def sqlite_integrity_assets(path: str, pragma: str = "integrity_check") -> str:
    with sqlite_readable_copy(path) as connection:
        row = connection.execute(f"PRAGMA {pragma}").fetchone()
    return "" if row is None else str(row[0])


def sqlite_logical_sha_assets(path: str) -> str:
    digest = hashlib.sha256()
    with sqlite_readable_copy(path) as connection:
        for line in connection.iterdump():
            digest.update(line.encode("utf-8"))
            digest.update(b"\n")
    return digest.hexdigest()


def sqlite_journal_mode_assets(path: str) -> str:
    with sqlite_readable_copy(path) as connection:
        row = connection.execute("PRAGMA journal_mode").fetchone()
    return "" if row is None else str(row[0]).lower()


def sqlite_column_present_assets(path: str, table: str, column: str) -> bool:
    with sqlite_readable_copy(path) as connection:
        rows = connection.execute(f"PRAGMA table_info({table})").fetchall()
    return any(row[1] == column for row in rows)


def run_command(command: list[str], timeout: float = 60) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )


def command_output(command: list[str], timeout: float = 60) -> str:
    result = run_command(command, timeout=timeout)
    return (result.stdout or "") + (result.stderr or "")


def restore_status(state: dict[str, Any]) -> str:
    path = Path(state["base"]) / "restore.status"
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="replace").strip()


def ifconfig_blocks(text: str) -> dict[str, str]:
    blocks: dict[str, str] = {}
    matches = list(re.finditer(r"(?m)^([A-Za-z0-9_.-]+): flags=", text))
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        blocks[match.group(1)] = text[match.start():end]
    return blocks


def validate_ifconfig(text: str) -> list[str]:
    errors: list[str] = []
    blocks = ifconfig_blocks(text)
    if not blocks:
        return ["ifconfig output contains no interface blocks"]
    if re.search(rf"(?<![\d.]){re.escape(EXPECTED_WAN_IPV4)}(?![\d.])", text) is None:
        errors.append(f"ifconfig does not show {EXPECTED_WAN_IPV4}")
    interface = blocks.get(EXPECTED_DEVICE, "")
    if not interface:
        errors.append(f"ifconfig does not show {EXPECTED_DEVICE}")
    else:
        if "description: DMTEST (opt1)" not in interface:
            errors.append("vlan0.50 description is not DMTEST (opt1)")
        if re.search(
            rf"(?<![\d.]){re.escape(EXPECTED_INTERFACE_IPV4)}(?![\d.])",
            interface,
        ) is None:
            errors.append("vlan0.50 does not carry 192.168.50.1")
    carp = sorted(name for name in blocks if re.fullmatch(r"carp\d*", name))
    if carp:
        errors.append(f"CARP interface present: {','.join(carp)}")
    return errors


def validate_opnsense_interface(path: str) -> list[str]:
    try:
        root = ET.parse(path).getroot()
    except (OSError, ET.ParseError) as exc:
        return [f"cannot parse {path}: {exc}"]
    node = root.find(f"./interfaces/{EXPECTED_INTERFACE}")
    if node is None:
        return [f"/conf/config.xml has no {EXPECTED_INTERFACE} interface"]
    errors: list[str] = []
    expected = {
        "enable": "1",
        "if": EXPECTED_DEVICE,
        "ipaddr": EXPECTED_INTERFACE_IPV4,
        "subnet": "24",
    }
    for key, value in expected.items():
        actual = (node.findtext(key) or "").strip()
        if actual != value:
            errors.append(f"interfaces/{EXPECTED_INTERFACE}/{key}={actual!r}, expected {value!r}")
    description = (node.findtext("descr") or "").strip()
    if description != "DMTEST":
        errors.append(f"interfaces/{EXPECTED_INTERFACE}/descr={description!r}, expected 'DMTEST'")
    return errors


def validate_record_target_set(
    record_path: str,
    expected_sha: str,
    expected_rows: int,
) -> list[str]:
    errors: list[str] = []
    try:
        text = Path(record_path).read_text(encoding="utf-8")
    except OSError as exc:
        return [f"cannot read installation record: {exc}"]
    if sha256_file(record_path) != expected_sha:
        errors.append("installation record digest does not match the accepted 2.14.0 record")
    lines = text.splitlines()
    if not lines or not lines[0].startswith("# Device Monitor 2.14.0 install record"):
        errors.append("installation record does not identify Device Monitor 2.14.0")
    rows: list[tuple[str, str]] = []
    for line_number, line in enumerate(lines, start=1):
        if not line or line.startswith("#"):
            continue
        match = re.fullmatch(r"([0-9a-f]{64}) (.+)", line)
        if match is None:
            errors.append(f"installation record line {line_number} is malformed")
            continue
        rows.append((match.group(1), match.group(2)))
    if len(rows) != expected_rows:
        errors.append(f"installation record has {len(rows)} target rows, expected {expected_rows}")
    seen: set[str] = set()
    for expected_digest, target in rows:
        if target in seen:
            errors.append(f"installation record repeats target: {target}")
            continue
        seen.add(target)
        try:
            actual_digest = sha256_file(target)
        except OSError as exc:
            errors.append(f"installation target cannot be read: {target}: {exc}")
            continue
        if actual_digest != expected_digest:
            errors.append(f"installation target digest mismatch: {target}")
    return errors


def port_2525_entries(sockstat_output: str) -> list[str]:
    return [
        line.strip()
        for line in sockstat_output.splitlines()
        if re.search(r"(?<!\d):2525(?:\s|$)", line)
    ]


def parse_address_port(value: str) -> tuple[ipaddress.IPv4Address, int] | None:
    if ":" not in value:
        return None
    host, port_text = value.rsplit(":", 1)
    host = host.strip("[]")
    if host in {"", "*", "0.0.0.0"} or not port_text.isdigit():
        return None
    try:
        address = ipaddress.ip_address(host)
    except ValueError:
        return None
    if address.version != 4:
        return None
    return address, int(port_text)


def sockstat_connection_violations(sockstat_output: str) -> list[str]:
    """Detect Python/PHP connections outside loopback or the approved subnet.

    This is evidence gathering only. It never changes firewall state and is not
    a substitute for the configuration and command-construction checks.
    """
    violations: list[str] = []
    for line in sockstat_output.splitlines():
        fields = line.split()
        if len(fields) < 7 or fields[0] == "USER":
            continue
        command = fields[1].split("/")[-1]
        if re.fullmatch(r"(?:python3?(?:\.[0-9]+)?|php(?:-fpm)?)", command) is None:
            continue
        parsed = parse_address_port(fields[-1])
        if parsed is None:
            violations.append(f"unparseable {command} connection: {line.strip()}")
            continue
        address, _port = parsed
        if address.is_loopback or address in EXPECTED_SCOPE:
            continue
        violations.append(f"{command} connected outside approved scope: {address}")
    return violations


def acquire_cleanup_lock(state: dict[str, Any], wait_seconds: float) -> int | None:
    fd = os.open(state["cleanup_lock"], os.O_CREAT | os.O_RDWR, 0o600)
    deadline = time.monotonic() + max(0.0, wait_seconds)
    while True:
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            os.ftruncate(fd, 0)
            os.write(fd, f"{os.getpid()}\n".encode("ascii"))
            return fd
        except BlockingIOError:
            if time.monotonic() >= deadline:
                os.close(fd)
                return None
            time.sleep(0.1)


def release_cleanup_lock(fd: int | None) -> None:
    if fd is None:
        return
    with contextlib.suppress(OSError):
        fcntl.flock(fd, fcntl.LOCK_UN)
    with contextlib.suppress(OSError):
        os.close(fd)


def parse_processes(output: str) -> list[tuple[int, str]]:
    processes: list[tuple[int, str]] = []
    for line in output.splitlines():
        match = re.match(r"\s*(\d+)\s+(.*)$", line)
        if match:
            processes.append((int(match.group(1)), match.group(2).strip()))
    return processes


def find_writers(state: dict[str, Any]) -> tuple[list[tuple[int, str]], str | None]:
    result = run_command(state["commands"]["process_list"], timeout=15)
    if result.returncode != 0:
        return [], f"process-list command failed: {result.returncode}"
    patterns = [
        re.compile(state["patterns"]["daemon"]),
        re.compile(state["patterns"]["scan"]),
    ]
    writers = [
        (pid, command)
        for pid, command in parse_processes(result.stdout or "")
        if any(pattern.search(command) for pattern in patterns)
    ]
    return writers, None


def find_scan_processes(state: dict[str, Any]) -> tuple[list[tuple[int, str]], str | None]:
    result = run_command(state["commands"]["process_list"], timeout=15)
    if result.returncode != 0:
        return [], f"process-list command failed: {result.returncode}"
    pattern = re.compile(state["patterns"]["scan"])
    return [
        (pid, command)
        for pid, command in parse_processes(result.stdout or "")
        if pattern.search(command)
    ], None


def terminate_payload(state: dict[str, Any]) -> None:
    pid = int(state.get("payload_pid") or 0)
    if pid <= 1:
        return
    for sig, delay in ((signal.SIGTERM, 2.0), (signal.SIGKILL, 0.0)):
        try:
            os.killpg(pid, sig)
        except ProcessLookupError:
            return
        except PermissionError:
            with contextlib.suppress(ProcessLookupError, PermissionError):
                os.kill(pid, sig)
        if delay:
            time.sleep(delay)


def stop_service_and_writers(state: dict[str, Any]) -> tuple[bool, str]:
    append_event(state["base"], "cleanup_stop_begin")
    terminate_payload(state)

    stop_result = run_command(state["commands"]["service_stop"], timeout=60)
    append_event(
        state["base"],
        "service_stop",
        f"rc={stop_result.returncode} output={(stop_result.stdout + stop_result.stderr)[:500]}",
    )

    wait_seconds = float(state.get("stop_wait_seconds", 30))
    deadline = time.monotonic() + wait_seconds
    writers, probe_error = find_writers(state)
    if probe_error:
        return False, probe_error

    if writers:
        for pid, _command in writers:
            with contextlib.suppress(ProcessLookupError, PermissionError):
                os.kill(pid, signal.SIGTERM)
        time.sleep(min(2.0, wait_seconds))

    while time.monotonic() < deadline:
        writers, probe_error = find_writers(state)
        if probe_error:
            return False, probe_error
        if not writers:
            append_event(state["base"], "writers_stopped")
            return True, ""
        time.sleep(0.2)

    if writers:
        for pid, _command in writers:
            with contextlib.suppress(ProcessLookupError, PermissionError):
                os.kill(pid, signal.SIGKILL)
        time.sleep(min(1.0, wait_seconds))

    writers, probe_error = find_writers(state)
    if probe_error:
        return False, probe_error
    if writers:
        detail = "; ".join(f"{pid}:{command}" for pid, command in writers)
        return False, f"writers remain after stop: {detail}"
    append_event(state["base"], "writers_stopped")
    return True, ""


def assert_writers_absent(state: dict[str, Any]) -> None:
    writers, probe_error = find_writers(state)
    if probe_error:
        raise GuardError(probe_error)
    if writers:
        detail = "; ".join(f"{pid}:{command}" for pid, command in writers)
        raise GuardError(f"database writers are still active: {detail}")


def validate_backup(state: dict[str, Any]) -> None:
    prestate = state["prestate"]
    if sha256_file(state["backup_config"]) != prestate["config_sha"]:
        raise GuardError("configuration backup digest mismatch")
    if database_assets(state["recovery_db"]) != prestate["original_database"]:
        raise GuardError("original database recovery copy changed")
    if sqlite_integrity_assets(state["recovery_db"]) != "ok":
        raise GuardError("original database recovery copy integrity check failed")
    if sqlite_logical_sha_assets(state["recovery_db"]) != prestate["original_db_logical_sha"]:
        raise GuardError("original database recovery copy logical digest mismatch")
    if sqlite_journal_mode_assets(state["recovery_db"]) != prestate["original_db_journal_mode"]:
        raise GuardError("original database recovery copy journal_mode mismatch")

    if database_assets(state["backup_db"]) != prestate["snapshot_database"]:
        raise GuardError("consistent SQLite fallback snapshot changed")
    if sqlite_integrity_assets(state["backup_db"]) != "ok":
        raise GuardError("consistent SQLite fallback snapshot integrity check failed")
    if sqlite_logical_sha_assets(state["backup_db"]) != prestate["snapshot_db_logical_sha"]:
        raise GuardError("consistent SQLite fallback snapshot logical digest mismatch")
    if prestate["snapshot_db_logical_sha"] != prestate["original_db_logical_sha"]:
        raise GuardError("consistent SQLite fallback is not logically equal to the original database")

    for key in ("record_sha", "opnsense_config_sha"):
        path_key = "record" if key == "record_sha" else "opnsense_config"
        if sha256_file(state[path_key]) != prestate[key]:
            raise GuardError(f"{path_key} changed before restoration")


def archive_current_database(state: dict[str, Any]) -> None:
    assert_writers_absent(state)
    archive_db = state["poststate_db"]
    archive_summary = state["poststate_summary"]
    if any(os.path.exists(archive_db + suffix) for _name, suffix in DATABASE_ASSET_SUFFIXES):
        unique = f"{utc_stamp()}-{os.getpid()}"
        archive_db = f"{archive_db}.{unique}"
        archive_summary = f"{archive_summary}.{unique}"
    before = database_assets(state["db"])
    copy_database_assets(state["db"], archive_db)
    if database_assets(state["db"]) != before:
        raise GuardError("live database changed while archiving the post-state")
    archived = database_assets(archive_db)
    if archived != before:
        raise GuardError("post-state database archive does not match the live database")
    write_json(archive_summary, archived)
    append_event(
        state["base"],
        "poststate_database_archived",
        f"database={archive_db} summary={archive_summary}",
    )


def restore_files(state: dict[str, Any]) -> None:
    append_event(state["base"], "restore_copy_begin")
    archive_current_database(state)
    copy_with_metadata(
        state["backup_config"],
        state["config"],
        state["prestate"]["config_metadata"],
    )
    copy_database_assets(state["recovery_db"], state["db"])
    append_event(state["base"], "restore_copy_complete")


def verify_restored(state: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    config = read_json(state["config"])
    if config != read_json(state["backup_config"]):
        errors.append("restored configuration content differs from the saved pre-state")
    if str(config.get("enabled", "")) != "0":
        errors.append(f"enabled={config.get('enabled')!r}, expected '0'")
    if str(config.get("monitored_interfaces", "")) != "":
        errors.append(
            f"monitored_interfaces={config.get('monitored_interfaces')!r}, expected ''"
        )

    if sha256_file(state["config"]) != state["prestate"]["config_sha"]:
        errors.append("restored configuration digest mismatch")
    original = state["prestate"]["original_database"]
    try:
        restored = database_assets(state["db"])
    except GuardError as exc:
        errors.append(str(exc))
        restored = {}
    if restored:
        for name, label in (
            ("db", "database"),
            ("wal", "database WAL"),
            ("shm", "database SHM"),
        ):
            expected = original[name]
            actual = restored[name]
            if actual["sha"] != expected["sha"]:
                errors.append(f"restored {label} digest mismatch")
            if actual["metadata"] != expected["metadata"]:
                errors.append(f"restored {label} metadata mismatch")
    if sqlite_integrity_assets(state["db"]) != "ok":
        errors.append("restored database integrity check failed")
    if sqlite_journal_mode_assets(state["db"]) != state["prestate"]["original_db_journal_mode"]:
        errors.append("restored database journal_mode mismatch")
    if sqlite_logical_sha_assets(state["db"]) != state["prestate"]["original_db_logical_sha"]:
        errors.append("restored database logical digest mismatch")
    if sha256_file(state["record"]) != state["prestate"]["record_sha"]:
        errors.append("installation record changed")
    if sha256_file(state["opnsense_config"]) != state["prestate"]["opnsense_config_sha"]:
        errors.append("OPNsense configuration changed")
    if file_metadata(state["config"]) != state["prestate"]["config_metadata"]:
        errors.append("restored config metadata mismatch")
    return errors


def verify_current_database_assets(state: dict[str, Any]) -> list[str]:
    if database_assets(state["db"]) != state["prestate"]["original_database"]:
        return ["current database bytes or metadata differ from the original recovery copy"]
    if sha256_file(state["config"]) != state["prestate"]["config_sha"]:
        return ["current configuration differs from the captured pre-state"]
    return []


def start_and_verify_service(state: dict[str, Any]) -> tuple[bool, str]:
    start_result = run_command(state["commands"]["service_start"], timeout=60)
    append_event(
        state["base"],
        "service_start",
        f"rc={start_result.returncode} output={(start_result.stdout + start_result.stderr)[:500]}",
    )
    if start_result.returncode != 0:
        return False, f"service start failed: {start_result.returncode}"

    wait_seconds = max(
        0.0,
        float(state.get("service_status_wait_seconds", SERVICE_STATUS_RETRY_SECONDS)),
    )
    poll_seconds = max(
        0.01,
        float(state.get("service_status_poll_seconds", SERVICE_STATUS_POLL_SECONDS)),
    )
    deadline = time.monotonic() + wait_seconds
    attempt = 0
    while True:
        attempt += 1
        status_result = run_command(state["commands"]["service_status"], timeout=30)
        status_text = (status_result.stdout + status_result.stderr).strip().lower()
        append_event(
            state["base"],
            "service_status",
            f"attempt={attempt} rc={status_result.returncode} output={status_text[:500]}",
        )
        if status_result.returncode == 0 and "running" in status_text:
            return True, ""
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            break
        time.sleep(min(poll_seconds, remaining))
    return False, "Device Monitor did not report running after restoration"


def stop_after_failed_start(state: dict[str, Any]) -> None:
    stopped = False
    with contextlib.suppress(Exception):
        stopped, _detail = stop_service_and_writers(state)
    append_event(
        state["base"],
        "service_left_stopped" if stopped else "service_stop_unconfirmed",
    )


def cleanup_locked(state: dict[str, Any], reason: str, actor: str) -> tuple[bool, str]:
    status_path = Path(state["base"]) / "restore.status"
    previous = restore_status(state)
    if previous.startswith("PASS"):
        append_event(state["base"], "cleanup_already_complete", f"actor={actor}")
        return True, ""
    if previous.startswith("FAIL") and actor != "operator":
        append_event(
            state["base"],
            "cleanup_suppressed_after_failure",
            f"actor={actor} reason={reason}",
        )
        return False, previous.splitlines()[0]
    append_event(state["base"], "cleanup_begin", f"actor={actor} reason={reason}")
    write_text_atomic(status_path, "IN_PROGRESS\n")

    try:
        stopped, detail = stop_service_and_writers(state)
    except Exception as exc:
        write_text_atomic(status_path, f"FAIL\n{exc}\n")
        append_event(state["base"], "cleanup_end", f"result=FAIL error={exc}")
        return False, str(exc)
    if not stopped:
        write_text_atomic(status_path, f"FAIL\n{detail}\n")
        append_event(state["base"], "cleanup_end", f"result=FAIL error={detail}")
        return False, detail

    try:
        writers, probe_error = find_writers(state)
        if probe_error:
            raise GuardError(probe_error)
        if writers:
            detail = "; ".join(f"{pid}:{command}" for pid, command in writers)
            raise GuardError(f"writers present before restoration: {detail}")
        validate_backup(state)
        restore_files(state)
        errors = verify_restored(state)
        if errors:
            raise GuardError("; ".join(errors))
    except Exception as exc:
        write_text_atomic(status_path, f"FAIL\n{exc}\n")
        append_event(state["base"], "cleanup_end", f"result=FAIL error={exc}")
        return False, str(exc)

    started, detail = start_and_verify_service(state)
    if not started:
        stop_after_failed_start(state)
        write_text_atomic(status_path, f"FAIL\n{detail}\n")
        append_event(state["base"], "cleanup_end", f"result=FAIL error={detail}")
        return False, detail

    write_text_atomic(status_path, "PASS\n")
    append_event(state["base"], "cleanup_end", "result=PASS")
    return True, ""


def cleanup(state: dict[str, Any], reason: str, actor: str) -> tuple[bool, str]:
    previous = restore_status(state)
    if previous.startswith("PASS"):
        append_event(state["base"], "cleanup_already_complete", f"actor={actor}")
        return True, ""
    if previous.startswith("FAIL") and actor != "operator":
        detail = previous.splitlines()[0]
        append_event(
            state["base"],
            "cleanup_suppressed_after_failure",
            f"actor={actor} reason={reason}",
        )
        return False, detail
    lock = acquire_cleanup_lock(state, float(state.get("lock_wait_seconds", 30)))
    if lock is None:
        detail = "cleanup lock is held; no database restoration attempted"
        append_event(state["base"], "cleanup_blocked", detail)
        return False, detail
    try:
        previous = restore_status(state)
        if previous.startswith("PASS"):
            append_event(state["base"], "cleanup_already_complete", f"actor={actor}")
            return True, ""
        if previous.startswith("FAIL") and actor != "operator":
            detail = previous.splitlines()[0]
            append_event(
                state["base"],
                "cleanup_suppressed_after_failure",
                f"actor={actor} reason={reason}",
            )
            return False, detail
        return cleanup_locked(state, reason, actor)
    finally:
        release_cleanup_lock(lock)


def pid_alive(pid: int) -> bool:
    if pid <= 1:
        return False
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def start_watchdog(state_path: str) -> int:
    state = read_json(state_path)
    existing_pid = int(state.get("watchdog_pid") or 0)
    if pid_alive(existing_pid) and not os.path.exists(state["cancel_file"]):
        return existing_pid
    log_path = Path(state["base"]) / "watchdog.log"
    with log_path.open("a", encoding="utf-8") as log:
        process = subprocess.Popen(
            [sys.executable, os.path.abspath(__file__), "_watchdog", "--state", state_path],
            stdin=subprocess.DEVNULL,
            stdout=log,
            stderr=subprocess.STDOUT,
            start_new_session=True,
            close_fds=True,
        )
    state["watchdog_pid"] = process.pid
    write_json(state_path, state)
    append_event(state["base"], "watchdog_started", f"pid={process.pid}")
    return process.pid


def wait_for_pid_exit(pid: int, timeout: float) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if not pid_alive(pid):
            return True
        time.sleep(0.1)
    return not pid_alive(pid)


def cancel_watchdog(state: dict[str, Any]) -> None:
    write_text_atomic(state["cancel_file"], "cancel\n")
    pid = int(state.get("watchdog_pid") or 0)
    if pid and not wait_for_pid_exit(pid, 5.0):
        append_event(state["base"], "watchdog_cancel_wait_timeout", f"pid={pid}")


def watchdog_main(state_path: str) -> int:
    state = read_json(state_path)
    reason: str | None = None

    def on_signal(signum: int, _frame: Any) -> None:
        nonlocal reason
        reason = f"watchdog_signal_{signum}"

    signal.signal(signal.SIGTERM, on_signal)
    signal.signal(signal.SIGINT, on_signal)
    signal.signal(signal.SIGHUP, on_signal)
    append_event(state["base"], "watchdog_active", f"pid={os.getpid()} sid={os.getsid(0)}")

    while time.monotonic() < float(state["deadline_monotonic"]):
        if os.path.exists(state["cancel_file"]):
            append_event(state["base"], "watchdog_cancelled")
            return 0
        if restore_status(state).startswith("PASS"):
            append_event(state["base"], "watchdog_observed_restored")
            return 0
        if reason:
            break
        time.sleep(0.2)

    if reason is None and not os.path.exists(state["cancel_file"]):
        reason = "timeout"
    if reason is None:
        append_event(state["base"], "watchdog_cancelled")
        return 0

    ok, detail = cleanup(state, reason, "watchdog")
    append_event(
        state["base"],
        "watchdog_exit",
        f"result={'PASS' if ok else 'FAIL'} detail={detail}",
    )
    return 0 if ok else 1


def validate_scope_config(config: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for key, expected in SCOPE_KEYS.items():
        value = config.get(key)
        if isinstance(expected, int):
            try:
                value = int(value)
            except (TypeError, ValueError):
                pass
        else:
            value = str(value if value is not None else "")
        if value != expected:
            errors.append(f"{key}={value!r}, expected {expected!r}")
    return errors


def validate_targets(text: str) -> list[str]:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if lines != [EXPECTED_TARGET_LINE]:
        return [
            "target output must contain exactly one line: "
            f"{EXPECTED_TARGET_LINE!r}; got {lines!r}"
        ]
    return []


def source_checks(path: str, checks: tuple[tuple[str, str], ...]) -> list[str]:
    try:
        text = Path(path).read_text(encoding="utf-8")
    except OSError as exc:
        return [f"cannot read {path}: {exc}"]
    errors: list[str] = []
    for label, pattern in checks:
        if re.search(pattern, text, flags=re.DOTALL) is None:
            errors.append(f"source check failed: {label}")
    return errors


def scope_check(paths: dict[str, str], config: dict[str, Any], target_text: str) -> list[str]:
    errors = validate_scope_config(config)
    errors.extend(validate_targets(target_text))
    errors.extend(source_checks(paths["scan"], SCAN_SOURCE_CHECKS))
    errors.extend(source_checks(paths["notification"], NOTIFICATION_SOURCE_CHECKS))
    errors.extend(source_checks(paths["smtp"], SMTP_SOURCE_CHECKS))
    errors.extend(source_checks(paths["identity"], (IDENTITY_SOURCE_CHECK,)))
    return errors


def create_backup(state: dict[str, Any]) -> None:
    base = Path(state["base"])
    installer = Path(state["installer_backup"])
    if not installer.exists() or not (installer.is_file() or installer.is_dir()):
        raise GuardError(f"installer backup is missing: {state['installer_backup']}")
    if installer.is_dir():
        try:
            if not any(installer.iterdir()):
                raise GuardError(
                    f"installer backup directory is empty: {state['installer_backup']}"
                )
        except OSError as exc:
            raise GuardError(f"cannot inspect installer backup: {exc}") from exc
    locale = Path(state["core_locale"])
    if not locale.is_dir():
        raise GuardError(f"core-locale backup is missing: {locale}")
    locale_files = sum(
        1 for path in locale.rglob("*") if path.is_file() or path.is_symlink()
    )
    if locale_files != EXPECTED_CORE_LOCALE_FILES:
        raise GuardError(
            f"core-locale has {locale_files} files, expected {EXPECTED_CORE_LOCALE_FILES}"
        )
    copy_database_assets(state["db"], state["recovery_db"])
    original_database = database_assets(state["recovery_db"])
    if not original_database["db"]["present"]:
        raise GuardError(f"live database is missing: {state['db']}")
    if database_assets(state["db"]) != original_database:
        raise GuardError("live database changed during byte-preserving recovery-copy capture")
    if sqlite_integrity_assets(state["recovery_db"]) != "ok":
        raise GuardError("original database recovery copy failed integrity check")
    original_db_logical_sha = sqlite_logical_sha_assets(state["recovery_db"])
    original_db_journal_mode = sqlite_journal_mode_assets(state["recovery_db"])
    notified_at_present = sqlite_column_present_assets(
        state["recovery_db"], "device_identity_events", "notified_at"
    )

    sqlite_backup(state["db"], state["backup_db"])
    snapshot_database = database_assets(state["backup_db"])
    if not snapshot_database["db"]["present"]:
        raise GuardError("consistent SQLite fallback snapshot is missing")
    if snapshot_database["wal"]["present"] or snapshot_database["shm"]["present"]:
        raise GuardError("consistent SQLite fallback snapshot left WAL/SHM sidecars")
    if sqlite_integrity_assets(state["backup_db"]) != "ok":
        raise GuardError("consistent SQLite fallback snapshot failed integrity check")
    snapshot_db_logical_sha = sqlite_logical_sha_assets(state["backup_db"])
    if snapshot_db_logical_sha != original_db_logical_sha:
        raise GuardError("consistent SQLite fallback snapshot is not logically equal to the original database")

    shutil.copy2(state["config"], state["backup_config"])
    shutil.copy2(state["record"], state["backup_record"])
    shutil.copy2(state["opnsense_config"], state["backup_opnsense_config"])
    shutil.copytree(state["core_locale"], state["backup_core_locale"], symlinks=True)
    with tarfile.open(state["backup_installer"], "w:gz") as archive:
        archive.add(state["installer_backup"], arcname=Path(state["installer_backup"]).name)
    try:
        with tarfile.open(state["backup_installer"], "r:gz") as archive:
            members = archive.getmembers()
    except (OSError, tarfile.TarError) as exc:
        raise GuardError(f"installer backup archive is unreadable: {exc}") from exc
    if not members:
        raise GuardError("installer backup archive is empty")

    state["prestate"] = {
        "config_sha": sha256_file(state["backup_config"]),
        "original_database": original_database,
        "original_db_logical_sha": original_db_logical_sha,
        "original_db_journal_mode": original_db_journal_mode,
        "snapshot_database": snapshot_database,
        "snapshot_db_logical_sha": snapshot_db_logical_sha,
        "record_sha": sha256_file(state["backup_record"]),
        "opnsense_config_sha": sha256_file(state["backup_opnsense_config"]),
        "config_metadata": file_metadata(state["config"]),
        "notified_at_present": notified_at_present,
    }


def sqlite_column_present(path: str, table: str, column: str) -> bool:
    conn = sqlite3.connect(sqlite_uri(path, immutable=True), uri=True, timeout=5)
    try:
        rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
    finally:
        conn.close()
    return any(row[1] == column for row in rows)


def preflight(
    config_path: str,
    db_path: str,
    record_path: str,
    space_path: str,
    *,
    opnsense_config: str = DEFAULT_OPNSENSE_CONFIG,
    commands: dict[str, list[str]] | None = None,
    expected_hostname: str = EXPECTED_HOSTNAME,
    expected_record_sha: str = EXPECTED_RECORD_SHA,
    expected_record_rows: int = EXPECTED_RECORD_ROWS,
) -> None:
    commands = commands or DEFAULT_COMMANDS
    config = read_json(config_path)
    if str(config.get("enabled", "0")) != "0":
        raise GuardError("monitoring must be disabled before preflight")
    if str(config.get("monitored_interfaces", "")) != "":
        raise GuardError("monitored_interfaces must be empty before preflight")
    if os.path.exists(db_path + "-journal"):
        raise GuardError("database rollback journal exists before preflight")
    if sqlite_integrity_live(db_path) != "ok":
        raise GuardError("database integrity_check is not ok")
    if sqlite_journal_mode_live(db_path) not in ("delete", "wal"):
        raise GuardError("database journal_mode is not delete or wal")
    record_errors = validate_record_target_set(
        record_path, expected_record_sha, expected_record_rows
    )
    if record_errors:
        raise GuardError("; ".join(record_errors))
    interface_errors = validate_opnsense_interface(opnsense_config)
    if interface_errors:
        raise GuardError("; ".join(interface_errors))
    if shutil.disk_usage(space_path).free < 1024**3:
        raise GuardError("less than 1 GiB free on the selected filesystem")

    hostname = run_command(commands["hostname"], timeout=10)
    hostname_text = (hostname.stdout or hostname.stderr or "").strip()
    if hostname.returncode != 0 or hostname_text != expected_hostname:
        raise GuardError(
            f"hostname={hostname_text!r}, expected {expected_hostname!r} (rc={hostname.returncode})"
        )
    ifconfig = run_command(commands["ifconfig"], timeout=20)
    if ifconfig.returncode != 0:
        raise GuardError(f"ifconfig failed: {ifconfig.returncode}")
    ifconfig_errors = validate_ifconfig((ifconfig.stdout or "") + (ifconfig.stderr or ""))
    if ifconfig_errors:
        raise GuardError("; ".join(ifconfig_errors))
    status = run_command(commands["service_status"], timeout=30)
    status_text = ((status.stdout or "") + (status.stderr or "")).strip()
    if status.returncode != 0 or "running" not in status_text.lower():
        raise GuardError(
            f"configctl devicemonitor status is not running: rc={status.returncode} {status_text!r}"
        )
    listeners = run_command(commands["sockstat_listen"], timeout=20)
    if listeners.returncode != 0:
        raise GuardError(f"sockstat listener inspection failed: {listeners.returncode}")
    on_2525 = port_2525_entries((listeners.stdout or "") + (listeners.stderr or ""))
    if on_2525:
        raise GuardError(f"port 2525 already has a listener: {on_2525[0]}")

    conn = sqlite3.connect(sqlite_uri(db_path), uri=True, timeout=5)
    try:
        due = conn.execute(
            "SELECT mac, next_scan_at FROM port_discovery_targets "
            "WHERE enabled = 1 AND next_scan_at <= datetime('now') "
            "ORDER BY next_scan_at, mac"
        ).fetchall()
    except sqlite3.Error as exc:
        raise GuardError(f"unable to inspect port-discovery targets: {exc}") from exc
    finally:
        conn.close()
    if due:
        raise GuardError(f"enabled port-discovery target is due: {due[0]}")


def capture_prestate(state: dict[str, Any]) -> None:
    stopped, detail = stop_service_and_writers(state)
    if not stopped:
        write_text_atomic(
            Path(state["base"]) / "restore.status",
            f"FAIL\nprestate_capture_requires_stopped_writers\n{detail}\n",
        )
        with contextlib.suppress(Exception):
            stop_after_failed_start(state)
        raise GuardError(f"cannot capture pre-state while writers remain: {detail}")
    try:
        assert_writers_absent(state)
        create_backup(state)
    except Exception as exc:
        write_text_atomic(
            Path(state["base"]) / "restore.status",
            f"FAIL\nprestate_capture_failed\n{exc}\n",
        )
        with contextlib.suppress(Exception):
            stop_after_failed_start(state)
        raise


def begin(args: argparse.Namespace) -> int:
    base = Path(args.base)
    state_path = base / "guard-state.json"
    if state_path.exists():
        raise GuardError(f"guard state already exists: {state_path}")
    commands = {
        "service_stop": args.service_stop,
        "service_start": args.service_start,
        "service_status": args.service_status,
        "process_list": args.process_list,
        "hostname": args.hostname_command,
        "ifconfig": args.ifconfig_command,
        "sockstat_listen": args.sockstat_listen,
    }
    preflight(
        args.config,
        args.db,
        args.record,
        args.space_path,
        opnsense_config=args.opnsense_config,
        commands=commands,
    )
    base.mkdir(parents=True, mode=0o700, exist_ok=True)
    os.chmod(base, 0o700)

    state: dict[str, Any] = {
        "version": 1,
        "base": str(base),
        "config": args.config,
        "db": args.db,
        "record": args.record,
        "opnsense_config": args.opnsense_config,
        "daemon_log": args.daemon_log,
        "core_locale": args.core_locale,
        "installer_backup": args.installer_backup,
        "backup_config": str(base / "config.json"),
        "backup_db": str(base / "devices.db"),
        "recovery_db": str(base / "original-devices.db"),
        "poststate_db": str(base / "poststate-devices.db"),
        "poststate_summary": str(base / "poststate.json"),
        "backup_record": str(base / "installed-manifest.txt"),
        "backup_opnsense_config": str(base / "opnsense-config.xml"),
        "backup_core_locale": str(base / "core-locale"),
        "backup_installer": str(base / (Path(args.installer_backup).name + ".tgz")),
        "cancel_file": str(base / "watchdog.cancel"),
        "cleanup_lock": str(base / "cleanup.lock"),
        "commands": commands,
        "patterns": dict(DEFAULT_PATTERNS),
        "started_at": iso_now(),
        "deadline_epoch": time.time() + args.timeout_seconds,
        "deadline_monotonic": time.monotonic() + args.timeout_seconds,
        "timeout_seconds": args.timeout_seconds,
        "lock_wait_seconds": args.lock_wait_seconds,
        "stop_wait_seconds": args.stop_wait_seconds,
        "service_status_wait_seconds": SERVICE_STATUS_RETRY_SECONDS,
        "service_status_poll_seconds": SERVICE_STATUS_POLL_SECONDS,
        "watchdog_pid": None,
        "payload_pid": None,
    }
    watchdog_started = False
    try:
        capture_prestate(state)
        write_json(state_path, state)
        start_watchdog(str(state_path))
        watchdog_started = True
        started, detail = start_and_verify_service(state)
        if not started:
            raise GuardError(f"service restart after pre-state capture failed: {detail}")
        errors = verify_current_database_assets(state)
        if errors:
            raise GuardError("service start changed the captured pre-state: " + "; ".join(errors))
    except Exception as exc:
        if watchdog_started:
            with contextlib.suppress(Exception):
                cancel_watchdog(state)
        with contextlib.suppress(Exception):
            stop_after_failed_start(state)
        with contextlib.suppress(Exception):
            write_text_atomic(base / "restore.status", f"FAIL\nbegin_failed\n{exc}\n")
        raise

    print(f"GUARD_READY state={state_path} base={base}")
    return 0


def finish_or_recover(state_path: str, reason: str, actor: str) -> int:
    state = read_json(state_path)
    ok, detail = cleanup(state, reason, actor)
    if ok:
        cancel_watchdog(state)
        print("GUARD_RESTORED=PASS")
        print(f"RESTORE_STATUS={Path(state['base']) / 'restore.status'}")
        return 0
    print("GUARD_RESTORED=FAIL", file=sys.stderr)
    print(f"ERROR={detail}", file=sys.stderr)
    print("MONITORING=STOPPED_OR_UNCONFIRMED", file=sys.stderr)
    print(f"ASSETS_RETAINED={state['base']}", file=sys.stderr)
    return 1


def scope_check_command(args: argparse.Namespace) -> int:
    config = read_json(args.config)
    targets = Path(args.targets_file).read_text(encoding="utf-8")
    errors = scope_check(
        {
            "scan": args.scan_source,
            "notification": args.notification_source,
            "smtp": args.smtp_source,
            "identity": args.identity_source,
        },
        config,
        targets,
    )
    if errors:
        for error in errors:
            print(f"SCOPE_ERROR={error}", file=sys.stderr)
        return 1
    print("SCOPE_CHECK=PASS")
    print("TARGETS=opt1/DMTEST/vlan0.50/192.168.50.0/24")
    print("NMAP_PATH=service-discovery-only-on-selected-scope")
    print("NOTIFICATION_PATH=smtp-loopback-only-no-sendmail-fallback")
    return 0


def normalize_payload_command(payload: list[str]) -> list[str]:
    command = list(payload)
    if command and command[0] == "--":
        command = command[1:]
    if not command:
        raise GuardError("run requires a non-empty payload command after --")
    return command


def run_payload(args: argparse.Namespace) -> int:
    state = read_json(args.state)
    if not pid_alive(int(state.get("watchdog_pid") or 0)):
        start_watchdog(args.state)
        state = read_json(args.state)

    log_path = Path(state["base"]) / "payload.log"
    interrupted = False

    def on_signal(signum: int, _frame: Any) -> None:
        nonlocal interrupted
        interrupted = True

    signal.signal(signal.SIGTERM, on_signal)
    signal.signal(signal.SIGINT, on_signal)
    signal.signal(signal.SIGHUP, on_signal)
    payload_command = normalize_payload_command(args.payload)
    payload: subprocess.Popen[Any] | None = None
    reason = "payload_start_failed"

    try:
        with log_path.open("a", encoding="utf-8") as log:
            payload = subprocess.Popen(
                payload_command,
                stdin=subprocess.DEVNULL,
                stdout=log,
                stderr=subprocess.STDOUT,
                start_new_session=True,
                close_fds=True,
            )
            state["payload_pid"] = payload.pid
            write_json(args.state, state)
            append_event(state["base"], "payload_started", f"pid={payload.pid}")

            while payload.poll() is None and not interrupted:
                time.sleep(0.2)

            if interrupted:
                reason = "interrupted"
            else:
                reason = "payload_complete" if payload.returncode == 0 else "payload_failed"
    except Exception as exc:
        reason = "payload_supervision_failed"
        append_event(state["base"], reason, str(exc))
    finally:
        if interrupted or (payload is not None and payload.poll() is None):
            terminate_payload(state)
            if payload is not None:
                with contextlib.suppress(subprocess.TimeoutExpired):
                    payload.wait(timeout=5)
        state["payload_pid"] = None
        with contextlib.suppress(Exception):
            write_json(args.state, state)

    ok, detail = cleanup(state, reason, "supervisor")
    if ok:
        cancel_watchdog(state)
        print("GUARD_RESTORED=PASS")
        if interrupted:
            return 130
        return 0 if reason == "payload_complete" else 1
    print("GUARD_RESTORED=FAIL", file=sys.stderr)
    print(f"ERROR={detail}", file=sys.stderr)
    print(f"ASSETS_RETAINED={state['base']}", file=sys.stderr)
    return 130 if interrupted else 1


def display_status(state_path: str) -> int:
    state = read_json(state_path)
    watchdog_pid = int(state.get("watchdog_pid") or 0)
    print(f"BASE={state['base']}")
    print(f"DEADLINE={dt.datetime.fromtimestamp(state['deadline_epoch'], dt.timezone.utc).isoformat()}")
    print(f"WATCHDOG_PID={watchdog_pid}")
    print(f"WATCHDOG_ALIVE={str(pid_alive(watchdog_pid)).lower()}")
    status_path = Path(state["base"]) / "restore.status"
    print(f"RESTORE_STATUS={status_path.read_text(encoding='utf-8').strip() if status_path.exists() else 'NOT_RUN'}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    preflight_parser = subparsers.add_parser("preflight", help="read-only preflight checks")
    preflight_parser.add_argument("--config", default=DEFAULT_CONFIG)
    preflight_parser.add_argument("--db", default=DEFAULT_DB)
    preflight_parser.add_argument("--record", default=DEFAULT_RECORD)
    preflight_parser.add_argument("--space-path", default="/")
    preflight_parser.add_argument("--opnsense-config", default=DEFAULT_OPNSENSE_CONFIG)
    preflight_parser.add_argument("--hostname-command", nargs="+", default=DEFAULT_COMMANDS["hostname"])
    preflight_parser.add_argument("--ifconfig-command", nargs="+", default=DEFAULT_COMMANDS["ifconfig"])
    preflight_parser.add_argument("--service-status", nargs="+", default=DEFAULT_COMMANDS["service_status"])
    preflight_parser.add_argument("--sockstat-listen", nargs="+", default=DEFAULT_COMMANDS["sockstat_listen"])

    def preflight_command(args: argparse.Namespace) -> int:
        commands = {
            "hostname": args.hostname_command,
            "ifconfig": args.ifconfig_command,
            "service_status": args.service_status,
            "sockstat_listen": args.sockstat_listen,
        }
        preflight(
            args.config,
            args.db,
            args.record,
            args.space_path,
            opnsense_config=args.opnsense_config,
            commands=commands,
        )
        print("PREFLIGHT=PASS")
        return 0

    preflight_parser.set_defaults(handler=preflight_command)

    begin_parser = subparsers.add_parser("begin", help="back up pre-state and start the detached watchdog")
    begin_parser.add_argument("--base", required=True)
    begin_parser.add_argument("--config", default=DEFAULT_CONFIG)
    begin_parser.add_argument("--db", default=DEFAULT_DB)
    begin_parser.add_argument("--record", default=DEFAULT_RECORD)
    begin_parser.add_argument("--space-path", default="/")
    begin_parser.add_argument("--opnsense-config", default=DEFAULT_OPNSENSE_CONFIG)
    begin_parser.add_argument("--daemon-log", default=DEFAULT_DAEMON_LOG)
    begin_parser.add_argument("--core-locale", default=DEFAULT_CORE_LOCALE)
    begin_parser.add_argument("--installer-backup", default=DEFAULT_INSTALLER_BACKUP)
    begin_parser.add_argument("--timeout-seconds", type=float, default=900.0)
    begin_parser.add_argument("--lock-wait-seconds", type=float, default=30.0)
    begin_parser.add_argument("--stop-wait-seconds", type=float, default=30.0)
    begin_parser.add_argument("--service-stop", nargs="+", default=DEFAULT_COMMANDS["service_stop"])
    begin_parser.add_argument("--service-start", nargs="+", default=DEFAULT_COMMANDS["service_start"])
    begin_parser.add_argument("--service-status", nargs="+", default=DEFAULT_COMMANDS["service_status"])
    begin_parser.add_argument("--process-list", nargs="+", default=DEFAULT_COMMANDS["process_list"])
    begin_parser.add_argument("--hostname-command", nargs="+", default=DEFAULT_COMMANDS["hostname"])
    begin_parser.add_argument("--ifconfig-command", nargs="+", default=DEFAULT_COMMANDS["ifconfig"])
    begin_parser.add_argument("--sockstat-listen", nargs="+", default=DEFAULT_COMMANDS["sockstat_listen"])
    begin_parser.set_defaults(handler=begin)

    scope_parser = subparsers.add_parser("scope-check", help="validate approved configuration and source paths")
    scope_parser.add_argument("--config", default=DEFAULT_CONFIG)
    scope_parser.add_argument("--targets-file", required=True)
    scope_parser.add_argument(
        "--scan-source",
        default=str(Path(__file__).resolve().parents[2] / "src/opnsense/scripts/OPNsense/DeviceMonitor/scan_network.py"),
    )
    scope_parser.add_argument(
        "--notification-source",
        default=str(Path(__file__).resolve().parents[2] / "src/opnsense/scripts/OPNsense/DeviceMonitor/NotificationHandler.php"),
    )
    scope_parser.add_argument(
        "--smtp-source",
        default=str(Path(__file__).resolve().parents[2] / "src/opnsense/scripts/OPNsense/DeviceMonitor/smtp_send.py"),
    )
    scope_parser.add_argument(
        "--identity-source",
        default=str(Path(__file__).resolve().parents[2] / "src/opnsense/scripts/OPNsense/DeviceMonitor/notify_identity_mail.php"),
    )
    scope_parser.set_defaults(handler=scope_check_command)

    for name, help_text in (("finish", "restore after normal completion"), ("recover", "restore after interruption or timeout")):
        finish_parser = subparsers.add_parser(name, help=help_text)
        finish_parser.add_argument("--state", required=True)
        finish_parser.set_defaults(
            handler=lambda args, reason="requested_completion", actor="operator": finish_or_recover(
                args.state, reason if args.command == "finish" else "manual_recovery", actor
            )
        )

    accept_parser = subparsers.add_parser("accept", help="verify an already restored state without changing it")
    accept_parser.add_argument("--state", required=True)
    accept_parser.add_argument("--sockstat-log", required=True)
    accept_parser.add_argument("--smtp-capture", required=True)
    accept_parser.set_defaults(
        handler=lambda args: print_acceptance(
            args.state, args.sockstat_log, args.smtp_capture
        )
    )

    status_parser = subparsers.add_parser("status", help="show watchdog and restoration status")
    status_parser.add_argument("--state", required=True)
    status_parser.set_defaults(handler=lambda args: display_status(args.state))

    run_parser = subparsers.add_parser("run", help="run a mock or live payload under the watchdog")
    run_parser.add_argument("--state", required=True)
    run_parser.add_argument("--payload", nargs=argparse.REMAINDER, required=True)
    run_parser.set_defaults(handler=run_payload)

    watchdog_parser = subparsers.add_parser("_watchdog")
    watchdog_parser.add_argument("--state", required=True)
    watchdog_parser.set_defaults(handler=lambda args: watchdog_main(args.state))
    return parser


def normalize_smtp_address(value: str, *, allow_size: bool = False) -> str:
    text = str(value).strip()
    text = re.sub(
        r"^(?:X-Envelope-To|MAIL\s+FROM|RCPT\s+TO)\s*:\s*",
        "",
        text,
        flags=re.IGNORECASE,
    )
    if text.startswith("<"):
        match = re.fullmatch(r"<\s*([^<>\s]+)\s*>(.*)", text)
        if match is not None:
            suffix = match.group(2).strip()
            if not suffix or (
                allow_size and re.fullmatch(r"size\s*=\s*\d+", suffix, flags=re.IGNORECASE)
            ):
                return match.group(1).lower()
        return text.lower()
    if allow_size:
        text = re.sub(r"\s+size\s*=\s*\d+\s*$", "", text, flags=re.IGNORECASE).strip()
    return text.lower()


def smtp_capture_errors(capture_dir: str, expected_messages: int = 2) -> list[str]:
    directory = Path(capture_dir)
    errors: list[str] = []
    envelopes_path = directory / "envelopes.jsonl"
    if not envelopes_path.is_file():
        return [f"SMTP envelope log is missing: {envelopes_path}"]
    envelopes: list[dict[str, Any]] = []
    for line_number, line in enumerate(
        envelopes_path.read_text(encoding="utf-8").splitlines(), start=1
    ):
        if not line.strip():
            continue
        try:
            envelope = json.loads(line)
        except json.JSONDecodeError as exc:
            errors.append(f"SMTP envelope line {line_number} is invalid: {exc}")
            continue
        if not isinstance(envelope, dict):
            errors.append(f"SMTP envelope line {line_number} is not an object")
            continue
        envelopes.append(envelope)
    if len(envelopes) != expected_messages:
        errors.append(f"SMTP capture has {len(envelopes)} messages, expected {expected_messages}")
    for index, envelope in enumerate(envelopes, start=1):
        recipients = [
            normalize_smtp_address(item)
            for item in envelope.get("rcpt_to", [])
            if str(item).strip()
        ]
        if recipients != [TEST_EMAIL]:
            errors.append(f"SMTP message {index} recipients are {recipients!r}")
        sender = normalize_smtp_address(envelope.get("mail_from", ""), allow_size=True)
        if sender != TEST_EMAIL:
            errors.append(f"SMTP message {index} sender is {sender!r}")
    messages = sorted(directory.glob("*.eml"))
    if len(messages) != expected_messages:
        errors.append(f"SMTP capture has {len(messages)} message files, expected {expected_messages}")
    for message in messages:
        envelope_values: list[str] = []
        for line in message.read_text(encoding="utf-8", errors="replace").splitlines():
            if line.lower().startswith("x-envelope-to:"):
                envelope_values.append(line.split(":", 1)[1].strip())
        recipients = [
            normalize_smtp_address(value) for value in envelope_values if value
        ]
        if recipients != [TEST_EMAIL]:
            errors.append(f"SMTP message file {message.name} envelope recipients are {recipients!r}")
    return errors


def latest_monitoring_state(log_path: str) -> str | None:
    try:
        text = Path(log_path).read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None
    states = re.findall(r"Monitoring (ENABLED|DISABLED)", text)
    return states[-1] if states else None


def print_acceptance(state_path: str, sockstat_log: str, smtp_capture: str) -> int:
    state = read_json(state_path)
    errors = verify_restored(state)
    status = run_command(state["commands"]["service_status"], timeout=30)
    status_text = ((status.stdout or "") + (status.stderr or "")).strip()
    if status.returncode != 0 or "running" not in status_text.lower():
        errors.append(
            f"Device Monitor status is not running: rc={status.returncode} {status_text!r}"
        )
    scans, scan_error = find_scan_processes(state)
    if scan_error:
        errors.append(scan_error)
    if scans:
        errors.append(f"scan process remains: {scans[0][0]}:{scans[0][1]}")
    listeners = run_command(state["commands"]["sockstat_listen"], timeout=20)
    if listeners.returncode != 0:
        errors.append(f"sockstat listener inspection failed: {listeners.returncode}")
    else:
        on_2525 = port_2525_entries(
            (listeners.stdout or "") + (listeners.stderr or "")
        )
        if on_2525:
            errors.append(f"port 2525 listener remains: {on_2525[0]}")
    try:
        sockstat_text = Path(sockstat_log).read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        errors.append(f"cannot read sockstat evidence: {exc}")
    else:
        errors.extend(sockstat_connection_violations(sockstat_text))
    errors.extend(smtp_capture_errors(smtp_capture))
    log_state = latest_monitoring_state(state.get("daemon_log", DEFAULT_DAEMON_LOG))
    if log_state != "DISABLED":
        errors.append(f"latest monitoring log state is {log_state!r}, expected 'DISABLED'")
    if errors:
        for error in errors:
            print(f"ACCEPT_ERROR={error}", file=sys.stderr)
        return 1
    print("ACCEPTANCE=PASS")
    print("MONITORING=enabled=0 monitored_interfaces=''")
    print(f"ORIGINAL_DB_SHA={state['prestate']['original_database']['db']['sha']}")
    print(f"SNAPSHOT_DB_SHA={state['prestate']['snapshot_database']['db']['sha']}")
    print(f"RESTORED_DB_SHA={sha256_file(state['db'])}")
    print("DATABASE=integrity_ok logical_hash_match physical_hash_match")
    print("WRITERS=daemon_running scans=none database_restoration_serialized")
    print("CONNECTIONS=SOCKSTAT_DETECTION_ONLY")
    print("NOTIFICATIONS=smtp-loopback-only recipient_count=2")
    print(
        "NOTIFIED_AT=prestate_"
        + ("present" if state["prestate"]["notified_at_present"] else "absent")
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return int(args.handler(args))
    except (GuardError, OSError, sqlite3.Error, subprocess.SubprocessError) as exc:
        print(f"GUARD_ERROR={exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

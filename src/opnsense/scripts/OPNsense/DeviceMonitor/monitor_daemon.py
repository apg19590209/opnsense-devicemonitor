#!/usr/local/bin/python3

import time
import sys
import os
import signal
import json
import subprocess
from datetime import datetime

# ================================================================
# CONFIGURATION - ENABLE/DISABLE FEATURES
# ================================================================
INFO_LOGGING = True   # Important events such as daemon start and scan completion
DEBUG_LOGGING = False  # Detailed debug messages such as config reloads every 10 seconds

# ================================================================
# PATHS - ALL IN ONE PLACE
#
#          Pointer to the configuration file containing default values
#
# ================================================================
defaultsFile = '/usr/local/opnsense/mvc/app/models/OPNsense/DeviceMonitor/defaults.json'

def load_defaults():
    with open(defaultsFile, 'r') as f:
        return json.load(f)

# Load at startup
_defaults = load_defaults()
PATHS = _defaults['paths']

# Paths instead of hard-coded values
CONFIG_FILE = PATHS['configFile']
DB_FILE = PATHS['dbFile']
PID_FILE = PATHS['pidFile']
SCAN_SCRIPT = PATHS['scanScript']
DEFAULT_CONFIG = _defaults['config']
# ================================================================

running = True

def signal_handler(signum, frame):
    """Daemon shutdown handler"""
    global running
    log("Daemon stopping...", level='INFO')
    running = False

LOG_FILE = "/var/log/devicemonitor.log"

def log(message, level='INFO'):
    """
    Log directly to file and syslog
    """
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    if level == 'INFO' and INFO_LOGGING:
        # Write directly to the log file
        try:
            with open(LOG_FILE, 'a') as f:
                f.write(f"[{timestamp}] {message}\n")
                f.flush()
        except Exception as e:
            pass  # Silently ignore errors
        
        # Attempt syslog logging if available
        try:
            subprocess.run(['logger', '-t', 'devicemonitor', message], check=False)
        except:
            pass
        
    elif level == 'DEBUG' and DEBUG_LOGGING:
        try:
            with open(LOG_FILE, 'a') as f:
                f.write(f"[{timestamp}] DEBUG: {message}\n")
                f.flush()
        except:
            pass
        
        try:
            subprocess.run(['logger', '-t', 'devicemonitor', f"DEBUG: {message}"], check=False)
        except:
            pass

def load_config():
    """Load runtime configuration including enabled state, email and interval"""
    
    if not os.path.exists(CONFIG_FILE):
        log(f"Config file not found: {CONFIG_FILE}, using defaults", level='DEBUG')
        return {
            'enabled': DEFAULT_CONFIG['enabled'] == '1',
            'email_to': DEFAULT_CONFIG['email_to'],
            'email_from': DEFAULT_CONFIG['email_from'],
            'scan_interval': int(DEFAULT_CONFIG['scan_interval'])
        }
    
    try:
        with open(CONFIG_FILE, 'r') as f:
            config = json.load(f)
            
            enabled = config.get('enabled', '0') == '1'
            scan_interval = int(config.get('scan_interval', 300))
            
            # DEBUG level is shown only when DEBUG_LOGGING is True
            log(f"Config loaded: enabled={enabled}, interval={scan_interval}s", level='DEBUG')
            
            return {
                'enabled': enabled,
                'email_to': config.get('email_to', ''),
                'email_from': config.get('email_from', DEFAULT_CONFIG['email_from']),
                'scan_interval': scan_interval
            }
            
    except Exception as e:
        log(f"Config load error: {e}", level='INFO')  # Chyby jsou INFO
        return {
            'enabled': False,
            'email_to': '',
            'email_from': DEFAULT_CONFIG['email_from'],
            'scan_interval': int(DEFAULT_CONFIG['scan_interval'])
        }

def run_scan():
    """Run the scan script"""
    try:
        result = subprocess.run(
            ['/usr/local/bin/python3', SCAN_SCRIPT],
            capture_output=True,
            text=True,
            timeout=300
        )
        
        if result.returncode == 0:
            log("Scan completed successfully", level='INFO')
        else:
            log(f"Scan failed with code {result.returncode}", level='INFO')
            if result.stderr:
                log(f"Scan error: {result.stderr[:200]}", level='DEBUG')
        
        return result.returncode == 0
        
    except subprocess.TimeoutExpired:
        log(f"Scan timeout (>300s)", level='INFO')
        return False
    except Exception as e:
        log(f"Scan error: {e}", level='INFO')
        return False

def run_due_port_discovery():
    """Run at most one scheduled, explicitly enabled host after a normal scan."""
    try:
        result = subprocess.run(
            ['/usr/local/bin/python3', SCAN_SCRIPT, '--port-discovery-due'],
            capture_output=True, text=True, timeout=130
        )
        if result.returncode != 0:
            log(f"Port discovery failed: {result.stderr[:200]}", level='INFO')
    except subprocess.TimeoutExpired:
        log("Port discovery exceeded 130 seconds", level='INFO')
    except Exception as e:
        log(f"Port discovery error: {e}", level='INFO')

# Email-log maintenance cadence: hourly retention plus observation of queued mail.
# Kept deliberately slow and bounded so it cannot interfere with scanning.
MAIL_MAINTENANCE_INTERVAL = 3600
# Hard ceiling for one maintenance pass, so it cannot delay scheduled scans.
MAIL_MAINTENANCE_BUDGET = 20
PHP_MAINTENANCE = '/usr/local/bin/php'
SCRIPT_DIR_MAINT = '/usr/local/opnsense/scripts/OPNsense/DeviceMonitor'


def run_mail_maintenance():
    """Run retention and out-of-band observation within one total budget.

    The whole maintenance pass is bounded so it can never stall the monitoring
    loop: it starts both helpers, waits at most MAIL_MAINTENANCE_BUDGET seconds in
    total, then terminates anything still running.
    """
    procs = []
    try:
        for script in ('prune_email_log.php', 'observe_email_log.php'):
            try:
                procs.append(subprocess.Popen(
                    [PHP_MAINTENANCE, SCRIPT_DIR_MAINT + '/' + script],
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
                ))
            except Exception:
                pass
        deadline = time.time() + MAIL_MAINTENANCE_BUDGET
        for proc in procs:
            remaining = max(0.1, deadline - time.time())
            try:
                proc.wait(timeout=remaining)
            except subprocess.TimeoutExpired:
                try:
                    proc.kill()
                except Exception:
                    pass
            except Exception:
                pass
    finally:
        for proc in procs:
            try:
                if proc.poll() is None:
                    proc.kill()
                proc.wait(timeout=5)
            except Exception:
                pass


def main():
    """Main daemon loop"""
    global running
    
    # Registruj signal handlery
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    
    log("Daemon started", level='INFO')
    
    # Load configuration including paths
    config = load_config()
    
    last_scan = 0
    last_mail_maintenance = 0
    last_config_state = None  # Track configuration changes
    last_interval = None      # Track interval changes
    
    while running:
        try:
            # Reload settings without reloading paths
            config = load_config()
            
            # Log only state changes
            current_state = config['enabled']
            current_interval = config['scan_interval']
            
            if current_state != last_config_state:
                if current_state:
                    log(f"Monitoring ENABLED (interval: {current_interval}s)", level='INFO')
                else:
                    log("Monitoring DISABLED", level='INFO')
                last_config_state = current_state
            
            # Log interval changes even while enabled
            elif current_state and current_interval != last_interval:
                log(f"Scan interval changed to {current_interval}s", level='INFO')
            
            last_interval = current_interval
            
            # If monitoring is enabled
            if config['enabled']:
                current_time = time.time()
                interval = config['scan_interval']
                
                # Is it time to scan?
                if current_time - last_scan >= interval:
                    log(f"Running scheduled scan", level='INFO')
                    run_scan()
                    run_due_port_discovery()
                    last_scan = current_time
            
            # Email-log maintenance is scheduled here because the daemon is the
            # plugin's established periodic mechanism. It runs regardless of the
            # monitoring switch, is best-effort, and never blocks a scan.
            now = time.time()
            if now - last_mail_maintenance >= MAIL_MAINTENANCE_INTERVAL:
                run_mail_maintenance()
                last_mail_maintenance = now

            # Sleep 10 seconds before the next check
            time.sleep(10)
            
        except Exception as e:
            log(f"Daemon error: {e}", level='INFO')
            time.sleep(30)
    
    log("Daemon stopped", level='INFO')

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        log(f"Fatal error: {e}", level='INFO')
        sys.exit(1)

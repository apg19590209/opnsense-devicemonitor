# OPNsense Device Monitor Plugin - Makefile
# ==========================================

.PHONY: help install uninstall reinstall status start stop restart scan test-email clean backup

# Output colors
RED    = \033[0;31m
GREEN  = \033[0;32m
YELLOW = \033[0;33m
BLUE   = \033[0;34m
NC     = \033[0m # No Color

# Cesty
PLUGIN_NAME = DeviceMonitor
DB_DIR = /var/db/devicemonitor
BACKUP_DIR = /root/devicemonitor_backup

help:
	@echo "$(BLUE)━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━$(NC)"
	@echo "$(BLUE)  OPNsense Device Monitor - Makefile$(NC)"
	@echo "$(BLUE)━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━$(NC)"
	@echo ""
	@echo "$(GREEN)Installation:$(NC)"
	@echo "  make install      - Install plugin"
	@echo "  make uninstall    - Uninstall plugin"
	@echo "  make reinstall    - Reinstall plugin (uninstall + install)"
	@echo ""
	@echo "$(GREEN)Daemon:$(NC)"
	@echo "  make start        - Start daemon"
	@echo "  make stop         - Stop daemon"
	@echo "  make restart      - Restart daemon"
	@echo "  make status       - Show daemon status"
	@echo ""
	@echo "$(GREEN)Operations:$(NC)"
	@echo "  make scan         - Manual network scan"
	@echo "  make test-email   - Test email formats"
	@echo "  make logs         - Follow logs"
	@echo "  make db           - Show database"
	@echo ""
	@echo "$(GREEN)Maintenance:$(NC)"
	@echo "  make clean        - Clear cache"
	@echo "  make backup       - Back up database"
	@echo "  make restore      - Restore database"
	@echo ""

install:
	@echo "$(GREEN)Installing Device Monitor...$(NC)"
	@test -f install.sh || { echo "$(RED)ERROR: install.sh not found!$(NC)"; exit 1; }
	@chmod +x install.sh
	@./install.sh
	@echo "$(GREEN)Installation complete$(NC)"

	# Helper scripts for configd
	install -m 0755 src/opnsense/scripts/OPNsense/DeviceMonitor/notify_email.php \
		$(DESTDIR)/usr/local/opnsense/scripts/OPNsense/DeviceMonitor/
	install -m 0755 src/opnsense/scripts/OPNsense/DeviceMonitor/notify_webhook.php \
		$(DESTDIR)/usr/local/opnsense/scripts/OPNsense/DeviceMonitor/

uninstall:
	@echo "$(YELLOW)Uninstalling Device Monitor...$(NC)"
	@test -f uninstall.sh || { echo "$(RED)ERROR: uninstall.sh not found!$(NC)"; exit 1; }
	@chmod +x uninstall.sh
	@./uninstall.sh
	@echo "$(YELLOW)Uninstall complete$(NC)"

reinstall: uninstall
	@echo "$(BLUE)Waiting 3 seconds...$(NC)"
	@sleep 3
	@$(MAKE) install

start:
	@echo "$(GREEN)Starting daemon...$(NC)"
	@service devicemonitor start || echo "$(RED)Failed to start daemon$(NC)"
	@sleep 2
	@$(MAKE) status

stop:
	@echo "$(YELLOW)Stopping daemon...$(NC)"
	@service devicemonitor stop || echo "$(YELLOW)Daemon is not running$(NC)"
	@sleep 1
	@$(MAKE) status

restart:
	@echo "$(BLUE)Restartuji daemon...$(NC)"
	@service devicemonitor restart || { $(MAKE) stop; sleep 2; $(MAKE) start; }
	@sleep 2
	@$(MAKE) status

status:
	@echo "$(BLUE)Daemon status:$(NC)"
	@service devicemonitor status || echo "$(RED)Daemon is not running$(NC)"
	@if [ -f "/var/run/devicemonitor.pid" ]; then \
		echo "$(GREEN)PID: $$(cat /var/run/devicemonitor.pid)$(NC)"; \
	fi

scan:
	@echo "$(GREEN)Starting manual scan...$(NC)"
	@/usr/local/bin/python3 /usr/local/opnsense/scripts/OPNsense/DeviceMonitor/scan_network.py
	@echo "$(GREEN)Scan complete$(NC)"

test-email:
	@echo "$(BLUE)Testing email formats...$(NC)"
	@test -f test_email_formats.sh || { echo "$(RED)ERROR: test_email_formats.sh not found!$(NC)"; exit 1; }
	@chmod +x test_email_formats.sh
	@./test_email_formats.sh
	@echo "$(BLUE)Check the email inbox$(NC)"

logs:
	@echo "$(BLUE)Following logs (Ctrl+C to stop):$(NC)"
	@tail -f /var/log/system.log | grep --color=always devicemonitor

db:
	@echo "$(BLUE)Database contents:$(NC)"
	@if [ -f "$(DB_DIR)/devices.db" ]; then \
		echo "$(GREEN)Total devices:$(NC)"; \
		sqlite3 $(DB_DIR)/devices.db "SELECT COUNT(*) FROM devices;"; \
		echo ""; \
		echo "$(GREEN)Last 10 devices:$(NC)"; \
		sqlite3 $(DB_DIR)/devices.db "SELECT mac, ip, hostname, vlan, last_seen FROM devices ORDER BY last_seen DESC LIMIT 10;" | column -t -s '|'; \
	else \
		echo "$(RED)Database does not exist$(NC)"; \
	fi

clean:
	@echo "$(YELLOW)Clearing cache...$(NC)"
	@rm -f /tmp/opnsense_menu_cache.xml
	@rm -f /tmp/opnsense_acl_cache.json
	@rm -rf /var/cache/opnsense/templates/*
	@echo "$(YELLOW)Restarting services...$(NC)"
	@service configd restart
	@configctl webgui restart
	@echo "$(GREEN)Cache cleared$(NC)"

backup:
	@echo "$(BLUE)Backing up database...$(NC)"
	@mkdir -p $(BACKUP_DIR)
	@if [ -f "$(DB_DIR)/devices.db" ]; then \
		cp $(DB_DIR)/devices.db $(BACKUP_DIR)/devices_$$(date +%Y%m%d_%H%M%S).db; \
		echo "$(GREEN)Backup saved to $(BACKUP_DIR)$(NC)"; \
		ls -lh $(BACKUP_DIR)/devices_*.db | tail -1; \
	else \
		echo "$(RED)Database does not exist$(NC)"; \
	fi

restore:
	@echo "$(BLUE)Available backups:$(NC)"
	@ls -lh $(BACKUP_DIR)/devices_*.db 2>/dev/null || { echo "$(RED)No backups found$(NC)"; exit 1; }
	@echo ""
	@echo "$(YELLOW)Enter the filename to restore:$(NC)"
	@read -p "File: " file; \
	if [ -f "$(BACKUP_DIR)/$$file" ]; then \
		cp $(BACKUP_DIR)/$$file $(DB_DIR)/devices.db; \
		chmod 644 $(DB_DIR)/devices.db; \
		echo "$(GREEN)Database restored$(NC)"; \
	else \
		echo "$(RED)File not found!$(NC)"; \
	fi

# Developer targets
dev-watch:
	@echo "$(BLUE)Watching files for changes...$(NC)"
	@while true; do \
		inotifywait -r -e modify,create,delete src/ 2>/dev/null && \
		echo "$(YELLOW)Change detected, restarting...$(NC)" && \
		$(MAKE) reinstall; \
	done

dev-debug:
	@echo "$(BLUE)Debug information:$(NC)"
	@echo "$(GREEN)Config file:$(NC)"
	@cat /tmp/devicemonitor_config.json 2>/dev/null || echo "$(RED)Config does not exist$(NC)"
	@echo ""
	@echo "$(GREEN)PID file:$(NC)"
	@cat /var/run/devicemonitor.pid 2>/dev/null || echo "$(RED)PID file does not exist$(NC)"
	@echo ""
	@echo "$(GREEN)Daemon process:$(NC)"
	@ps aux | grep monitor_daemon | grep -v grep || echo "$(RED)Daemon is not running$(NC)"

# Quick commands
i: install
u: uninstall
r: reinstall
st: status
sc: scan
l: logs

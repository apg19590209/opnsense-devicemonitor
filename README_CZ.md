# OPNsense Device Monitor

**[🇬🇧 English version](README.md)** | **[👨‍💻 Další projekty autora](https://github.com/hacesoft?tab=repositories)**

---

Plugin pro automatické sledování síťových zařízení v OPNsense firewallu. Detekuje nová zařízení pomocí ARP skenování a odesílá emailová nebo webhook upozornění o nových zařízeních v síti.

---

## 📋 Obsah

- [Co plugin dělá](#co-plugin-dělá)
- [Verze](#verze)
- [Funkce](#funkce)
- [Instalace](#instalace)
  - [Metoda 1: WinSCP + Ruční instalace](#metoda-1-winscp--ruční-instalace-doporučeno)
  - [Metoda 2: Přímá SSH instalace](#metoda-2-přímá-ssh-instalace)
- [Nastavení](#nastavení)
- [Použití](#použití)
- [Struktura pluginu](#struktura-pluginu)
- [Řešení problémů](#řešení-problémů)
- [Verzování](#verzování)
- [Odinstalace](#odinstalace)

---

## Co plugin dělá

Plugin automaticky sleduje síť a upozorňuje na:

- 🆕 **Nová zařízení** připojující se do sítě
- 📊 **Historie zařízení** s časovými údaji první/poslední detekce
- 📧 **Email notifikace** s profesionálním HTML designem
- 🔔 **Webhook notifikace** (ntfy.sh, Discord, custom)

---

## Verze

Změny opravy v plugginu

- opnsense-devicemonitor31012026_1358.zip
  **Oprava kompatibility s OPNsense 26.x:**

    Po přechodu na OPNsense verzi 26.0 a vyšší měl plugin problémy kvůli volání funkce `$this->sessionClose()`, která byla v nových verzích odstraněna. Od verze 26.0 systém automaticky provádí uzavírání sessions, a pokud funkce zůstane v kódu, plugin způsobí CRASH systému.

    **Řešení:**
    Controller `DevicesController.php` byl doplněn o automatickou detekci verze OPNsense:

    ```php
    /**
     * Zjistí verzi OPNsense jako číslo (např. 26 pro verzi 26.x)
    */
    private function getOPNsenseVersion()
    {
        exec("opnsense-version | awk '{print $2}' | cut -d. -f1", $output, $return_code);
        
        if ($return_code === 0 && !empty($output[0])) {
            return (int)$output[0];
        }
        
        // Pro zpětnou kompatibilitu předpokládáme verzi 25
        return 25;
    }
    ```

    Tato metoda je volána před každým použitím `sessionClose()`:

    ```php
    public function searchAction()
    {
        $version = $this->getOPNsenseVersion();
        if ($version < 26) {
            $this->sessionClose();  // Volá se pouze na OPNsense 25.x a starších
        }
        
        // ... zbytek kódu
    }
    ```

---

## Funkce

### 🎯 **Základní funkce**

✅ **Automatické ARP skenování** - detekce zařízení každých 5-30 minut  
✅ **Emailová upozornění** - krásné HTML emaily s profesionálním designem  
✅ **Webhook upozornění** - podpora pro ntfy.sh, Discord a custom webhooky  
✅ **Historie zařízení** - sledování první a poslední detekce  
✅ **Vendor lookup** - automatická detekce výrobce z MAC adresy  

### 📧 **Notifikace**

✅ **Krásné HTML emaily** - profesionální design s inline CSS (funguje všude!)  
✅ **Test tlačítka** - ověření emailů i webhooků přímo z GUI  
✅ **Detailní logování** - sledování úspěchu/neúspěchu odesílání  
✅ **Webhook podpora**:
  - **ntfy.sh** - jednoduchý notification server
  - **Discord** - webhooky do Discord kanálů
  - **Generic** - jakýkoliv HTTP webhook endpoint

### 🖥️ **Webové rozhraní**

✅ **Dashboard** - přehled statistik, ruční spuštění skenování  
✅ **Správa zařízení** - mazání jednotlivých zařízení nebo celé databáze  
✅ **Nastavitelné intervaly** - skenování každých 5, 10, 15 nebo 30 minut  
✅ **Responzivní design** - funguje na mobilu i tabletu  

### 📊 **Technické funkce**

✅ **SQLite databáze** - rychlé ukládání a vyhledávání  
✅ **Vendor lookup** - automatická detekce výrobce z MAC adresy (IEEE OUI databáze)  
✅ **Daemon proces** - běží na pozadí jako systémová služba  
✅ **Logování** - detailní logy v `/var/log/devicemonitor.log`  

### 🚀 **Plánované funkce (budoucí verze)**

🔜 **VLAN filtrování** - sledování jen vybraných síťových segmentů  
🔜 **GUI pro logy** - prohlížení logů přímo z webového rozhraní  
🔜 **Historie IP adres** - sledování změn IP pro každé zařízení  

---

## Instalace

### Požadavky

- **OPNsense 24.x nebo novější**
- **SSH přístup povolen** (System → Settings → Administration → Secure Shell)
- **Admin účet** s přístupem do CLI (přes PuTTY, Terminál apod.)
- **Funkční SMTP nastavení** (System → Settings → Notifications) - **nutné pro provoz pluginu**

**Poznámka:** Plugin vyžaduje funkční SMTP pro odesílání notifikací. Bez SMTP nastavení plugin nebude fungovat správně.

---

### Metoda 1: WinSCP + Ruční instalace (Doporučeno)

Tato metoda je nejjednodušší pro uživatele, kteří nejsou zvyklí na příkazovou řádku.

#### Krok 1: Stáhni nejnovější verzi

Jdi na [**Releases**](../../releases) a stáhni nejnovější archiv:

```
opnsense-devicemonitor31122025_1339.zip
```

**Název souboru:**
- `opnsense-devicemonitor` = název pluginu
- `31122025` = datum (DD.MM.RRRR)
- `1339` = čas (HH:MM)
- `.zip` = formát archivu

**Příklad:** `opnsense-devicemonitor31122025_1254.zip` = 31. prosince 2025 ve 13:39

**Poznámka:** Starší verze najdeš ve složce `/old/` v releases.

#### Krok 2: Povolit SSH na OPNsense

```
1. Přihlas se do webového rozhraní OPNsense (jako admin)
2. Jdi na: System → Settings → Administration
3. Zapni "Secure Shell"
4. Zaškrtni "Permit root user login" (nebo použij admin účet)
5. Login Shell: /bin/csh (výchozí je OK)
6. Ulož
```

**Poznámka:** Můžeš se přihlásit buď jako `root` nebo jako `admin` - oba mají plná oprávnění pro instalaci.

#### Krok 3: Nahraj soubor přes WinSCP

**Stáhni WinSCP:** https://winscp.net/

**Připoj se k OPNsense:**
```
Host:     tvoje.opnsense.ip.adresa
Port:     22
Uživatel: root (nebo admin)
Heslo:    tvoje-heslo
```

**Poznámka:** Použij buď `root` nebo `admin` účet - oba fungují.

**Postup nahrání:**
1. Ve WinSCP jdi do `/tmp/`
2. Přetáhni `opnsense-devicemonitor31122025_1254.zip` do okna

#### Krok 4: Instalace přes SSH

Použij PuTTY (Windows) nebo Terminál (Mac/Linux) pro připojení:

```bash
ssh root@tvoje.opnsense.ip
```

Pak spusť:

```bash
# Přejdi do složky s archivem
cd /tmp

# Rozbal archiv
unzip opnsense-devicemonitor31122025_1254.zip
cd opnsense-devicemonitor

# Spusť instalaci
sh install.sh
```

**Poznámka:** Restart OPNsense **NENÍ potřeba** - instalační script se o vše postará!

---

### Metoda 2: Přímá SSH instalace

Pro pokročilé uživatele znalé příkazové řádky:

```bash
# Připoj se přes SSH
ssh root@tvoje.opnsense.ip

# Stáhni nejnovější verzi (UPRAV URL!)
cd /tmp
fetch https://github.com/hacesoft/opnsense-devicemonitor/releases/download/v31122025_1254/opnsense-devicemonitor31122025_1254.zip

# Rozbal
unzip opnsense-devicemonitor31122025_1254.zip
cd opnsense-devicemonitor

# Instaluj
sh install.sh
```

**Pro starší verze:**

Pokud chceš nainstalovat starší verzi, uprav URL:

```bash
fetch https://github.com/hacesoft/opnsense-devicemonitor/releases/download/old/opnsense-devicemonitorDDMMRRRR_HHMM.zip
```

---

## Nastavení

Po instalaci jdi na: **Services → DeviceMonitor → Settings**

### Základní konfigurace

| Nastavení | Popis | Příklad |
|-----------|-------|---------|
| **Enable Device Monitor** | Zapnout/vypnout sledování | ✅ Zaškrtnuto |
| **Scan Interval** | Jak často skenovat | `5 minutes` |
| **Show .local Domain** | Zobrazit `.local` v hostname | ❌ Nezaškrtnuto |

---

### Email notifikace

**⚠️ DŮLEŽITÉ:** Plugin vyžaduje funkční SMTP konfiguraci! Bez SMTP nebudou chodit notifikace.

**SMTP nastavení:**
```
System → Settings → Notifications → E-Mail
```
Zde nastav SMTP server, port, autentizaci (uživatel/heslo).

| Nastavení | Popis | Příklad |
|-----------|-------|---------|
| **Enable Email** | Zapnout email notifikace | ✅ Zaškrtnuto |
| **Email (To)** | Tvůj email pro upozornění | `admin@example.com` |
| **Email (From)** | Email odesílatele | `opnsense@tvojadomena.cz` |
| **Test Email** | Odeslat testovací email | 🧪 Tlačítko |

**Formát emailu:**
- 🎨 **Profesionální HTML design** s OPNsense barvami
- 📱 **Responzivní** - funguje na všech zařízeních
- 🎯 **Inline CSS** - zobrazí se správně v Gmail, Outlook, Seznam...
- 📊 **Přehledná tabulka** s MAC, Vendor, IP, Hostname
- 🔔 **Krásný header** s gradientem a ikonami

### Webhook notifikace

| Nastavení | Popis | Příklad |
|-----------|-------|---------|
| **Enable Webhook** | Zapnout webhook notifikace | ✅ Zaškrtnuto |
| **Webhook URL** | URL pro webhook | `https://ntfy.sh/mytopic` |
| **Test Webhook** | Odeslat testovací webhook | 🧪 Tlačítko |

**Podporované typy webhooků:**

#### 1. **ntfy.sh** (Doporučeno pro začátečníky)
```
https://ntfy.sh/mojeTajneSlovo123
```
- ✅ Zdarma, bez registrace
- ✅ Mobilní app (iOS/Android)
- ✅ Webové rozhraní
- 📱 Instant push notifikace na mobil

**Jak nastavit:**
1. Vymysli si unikátní jméno (např. `mojeTajneSlovo123`)
2. URL: `https://ntfy.sh/mojeTajneSlovo123`
3. Stáhni si ntfy app: https://ntfy.sh/
4. Přidej topic `mojeTajneSlovo123`
5. Hotovo! Teď dostaneš notifikace na mobil 📱

#### 2. **Discord**
```
https://discord.com/api/webhooks/1234567890/AbCdEfGhIjKlMnOpQrStUvWxYz
```
- ✅ Notifikace do Discord kanálu
- ✅ Embed zprávy s formátováním
- ✅ Ideální pro týmy

**Jak získat Discord webhook:**
1. Jdi do Discord serveru
2. Klikni na kanál → Upravit kanál → Integrace → Webhooky
3. Vytvoř nový webhook
4. Zkopíruj URL

#### 3. **Generic (Custom)**
Jakýkoliv HTTP POST endpoint:
```
https://moje.domena.cz/webhook
```
- ✅ Vlastní webhook server
- ✅ JSON payload s daty o zařízeních
- ✅ Pro pokročilé uživatele

### Test konfigurace

**Tlačítka v GUI:**
- 🧪 **Test Email** - odešle testovací email (ověří SMTP nastavení)
- 🧪 **Test Webhook** - odešle testovací webhook (ověří URL a dostupnost)

**Co se testuje:**
- ✅ Správnost konfigurace
- ✅ Dostupnost SMTP serveru / webhook URL
- ✅ Formát zprávy
- ✅ Logování výsledku

**Výsledek testu:**
- ✅ **Success** - vše funguje správně
- ❌ **Failed** - zkontroluj konfiguraci (viz logy)

---

## Použití

### Dashboard

**Services → DeviceMonitor → Dashboard**

**Zobrazuje:**
- 📊 **Celkový počet zařízení**
- 🆕 **Nová zařízení (dnes)**
- 🔔 **Čekající notifikace**
- ⏰ **Poslední skenování**

**Akce:**
- 🔄 **Scan Now** - okamžité spuštění skenování
- 📧 **Send Notifications** - manuální odeslání notifikací

### Seznam zařízení

**Services → DeviceMonitor → Devices**

**Tabulka:**
| Sloupec | Popis |
|---------|-------|
| **MAC** | MAC adresa zařízení (s vendor info) |
| **Vendor** | Výrobce (z IEEE OUI databáze) |
| **IP** | Aktuální IP adresa |
| **Hostname** | Název zařízení (z DNS) |
| **First Seen** | První detekce |
| **Last Seen** | Poslední aktivita |
| **Actions** | 🗑️ Smazat zařízení |

**Funkce:**
- 🔍 **Vyhledávání** - filtruj podle MAC, IP, Vendor...
- 📊 **Řazení** - klikni na sloupec pro seřazení
- 🗑️ **Mazání** - smaž jednotlivá zařízení nebo všechny najednou

### Logování

**Všechny operace se logují do:**
```
/var/log/devicemonitor.log
```

**Typy logů:**
- `[DAEMON]` - daemon proces (spouštění, skenování...)
- `[EMAIL]` - emailové notifikace (úspěch/chyba)
- `[WEBHOOK]` - webhook notifikace (úspěch/chyba)
- `[SCAN]` - skenování sítě
- `[DATABASE]` - databázové operace

**Příklad logu:**
```
[2026-01-10 15:34:25] [PHP-EMAIL] Preparing email for 38 devices
[2026-01-10 15:34:26] [PHP-EMAIL] SUCCESS: Email sent (REAL mode, 38 devices)
[2026-01-10 15:35:00] [PHP-WEBHOOK] SUCCESS: Webhook sent (REAL mode, 38 devices) - HTTP 200
```

**Zobrazení logů:**
```bash
# Poslední záznamy
tail -50 /var/log/devicemonitor.log

# Sledování v real-time
tail -f /var/log/devicemonitor.log

# Filtrace jen email logů
grep EMAIL /var/log/devicemonitor.log
```

---

## Struktura pluginu

### Soubory pluginu

```
/usr/local/opnsense/
├── mvc/app/
│   ├── controllers/OPNsense/DeviceMonitor/
│   │   ├── IndexController.php           # GUI stránky
│   │   └── Api/
│   │       ├── ConfigController.php       # API konfigurace
│   │       ├── DevicesController.php      # API zařízení
│   │       ├── ServiceController.php      # API služby
│   │       ├── DashboardController.php    # API dashboard
│   │       └── OuiController.php          # API OUI databáze
│   ├── models/OPNsense/DeviceMonitor/
│   │   ├── DeviceMonitor.php             # Model
│   │   ├── DeviceMonitor.xml             # Konfigurace
│   │   ├── defaults.json                 # Výchozí hodnoty
│   │   ├── Menu/Menu.xml                 # Menu
│   │   └── ACL/ACL.xml                   # Oprávnění
│   └── views/OPNsense/DeviceMonitor/
│       ├── index.volt                    # Dashboard
│       ├── settings.volt                 # Nastavení
│       └── devices.volt                  # Seznam zařízení
├── scripts/OPNsense/DeviceMonitor/
│   ├── monitor_daemon.py                 # Hlavní daemon
│   ├── scan_network.py                   # Skenovací script
│   ├── NotificationHandler.php           # Email/Webhook handler
│   ├── notify_email.php                  # Email CLI script
│   ├── notify_webhook.php                # Webhook CLI script
│   └── download_oui.py                   # OUI databáze download
├── service/conf/actions.d/
│   └── actions_devicemonitor.conf        # Configd akce
└── /var/db/devicemonitor/
    ├── devices.db                        # SQLite databáze
    ├── config.json                       # Runtime konfigurace
    └── oui.txt                           # IEEE OUI databáze
```

### Databázová struktura

**devices.db (SQLite3):**
```sql
CREATE TABLE devices (
    id INTEGER PRIMARY KEY,
    mac TEXT UNIQUE NOT NULL,
    vendor TEXT,
    ip TEXT,
    hostname TEXT,
    vlan TEXT,
    first_seen TEXT,
    last_seen TEXT,
    notification_pending INTEGER DEFAULT 1
);
```

### API Endpointy

**Konfigurace:**
- `GET  /api/devicemonitor/config/get` - Načíst konfiguraci
- `POST /api/devicemonitor/config/set` - Uložit konfiguraci
- `POST /api/devicemonitor/config/testemail` - Test emailu
- `POST /api/devicemonitor/config/testwebhook` - Test webhooku

**Zařízení:**
- `GET  /api/devicemonitor/devices/list` - Seznam zařízení
- `POST /api/devicemonitor/devices/delete` - Smazat zařízení
- `POST /api/devicemonitor/devices/deleteall` - Smazat všechny

**Dashboard:**
- `GET  /api/devicemonitor/dashboard/stats` - Statistiky

**Služba:**
- `POST /api/devicemonitor/service/start` - Start daemon
- `POST /api/devicemonitor/service/stop` - Stop daemon
- `POST /api/devicemonitor/service/restart` - Restart daemon
- `GET  /api/devicemonitor/service/status` - Status daemon
- `POST /api/devicemonitor/service/scan` - Manuální skenování

---

## Řešení problémů

### Plugin se neobjevuje v menu

```bash
# Restart configd
service configd restart

# Restart web interface
service php-fpm restart

# Vyčisti cache
rm -rf /tmp/templates_c/*
```

### Daemon se nespustí

```bash
# Zkontroluj status
service devicemonitor status

# Zkontroluj logy
tail -50 /var/log/devicemonitor.log

# Ruční start
/usr/local/opnsense/scripts/OPNsense/DeviceMonitor/monitor_daemon.py
```

### Email notifikace nefungují

**1. Zkontroluj SMTP nastavení:**
```
System → Settings → Notifications
```

**2. Test emailu z GUI:**
```
Services → DeviceMonitor → Settings → Test Email
```

**3. Zkontroluj logy:**
```bash
tail -50 /var/log/devicemonitor.log | grep EMAIL
```

**Časté problémy:**
- ❌ **SMTP server není dostupný** - zkontroluj firewall pravidla
- ❌ **Neplatný email** - zkontroluj formát emailové adresy
- ❌ **Autentizace selhala** - zkontroluj SMTP credentials

### Webhook notifikace nefungují

**1. Test webhooku z GUI:**
```
Services → DeviceMonitor → Settings → Test Webhook
```

**2. Zkontroluj logy:**
```bash
tail -50 /var/log/devicemonitor.log | grep WEBHOOK
```

**3. Zkontroluj dostupnost:**
```bash
# Test ntfy.sh
curl -d "test" https://ntfy.sh/mojeTajneSlovo123

# Test Discord (UPRAV URL!)
curl -X POST -H "Content-Type: application/json" \
     -d '{"content": "test"}' \
     https://discord.com/api/webhooks/TVOJE_WEBHOOK_URL
```

**Časté problémy:**
- ❌ **URL není dostupná** - zkontroluj firewall, internet připojení
- ❌ **Neplatný formát URL** - zkontroluj že začíná `https://`
- ❌ **Discord webhook vypršel** - vytvoř nový

### Zařízení se nedetekují

**1. Ruční test skenování:**
```bash
/usr/local/opnsense/scripts/OPNsense/DeviceMonitor/scan_network.py
```

**2. Zkontroluj ARP tabulku:**
```bash
arp -an
```

**3. Zkontroluj logy:**
```bash
tail -50 /var/log/devicemonitor.log | grep SCAN
```

**4. Zkontroluj že daemon běží:**
```bash
service devicemonitor status
```

---

```bash
# Zálohuj současnou databázi
cp /var/db/devicemonitor/devices.db /var/db/devicemonitor/devices.db.backup

# Smaž poškozenou databázi
rm /var/db/devicemonitor/devices.db

# Restart daemon (vytvoří novou)
service devicemonitor restart
```

### Databáze je poškozená

```bash
# Zálohuj současnou databázi
cp /var/db/devicemonitor/devices.db /var/db/devicemonitor/devices.db.backup

# Smaž poškozenou databázi
rm /var/db/devicemonitor/devices.db

# Restart daemon (vytvoří novou)
service devicemonitor restart
```

---

### Vysoká zátěž CPU

**Prodluž scan interval:**
```
Services → DeviceMonitor → Settings → Scan Interval
```
Nastav na 15 nebo 30 minut místo 5.

---

## Verzování

**Formát verze:**
```
DDMMYYYY_HHMM
```

**Příklad:**
- `31122025_1339` = 31. prosince 2025, 13:39
- `01012026_0900` = 1. ledna 2026, 09:00

**Kde najít verzi:**
```bash
# V GUI
Services → DeviceMonitor → Settings (v zápatí)

# V souborech
head -10 /usr/local/opnsense/scripts/OPNsense/DeviceMonitor/monitor_daemon.py
```

---

## Odinstalace

### Metoda 1: Uninstall script (Doporučeno)

```bash
ssh root@opnsense

cd /tmp
# Stáhni plugin (nebo použij existující)
unzip opnsense-devicemonitor*.zip
cd opnsense-devicemonitor

# Spusť uninstall
sh uninstall.sh
```

### Metoda 2: Manuální odinstalace

```bash
# Stop daemon
service devicemonitor stop

# Smaž soubory
rm -rf /usr/local/opnsense/mvc/app/controllers/OPNsense/DeviceMonitor
rm -rf /usr/local/opnsense/mvc/app/models/OPNsense/DeviceMonitor
rm -rf /usr/local/opnsense/mvc/app/views/OPNsense/DeviceMonitor
rm -rf /usr/local/opnsense/scripts/OPNsense/DeviceMonitor
rm -f /usr/local/opnsense/service/conf/actions.d/actions_devicemonitor.conf
rm -f /etc/rc.d/devicemonitor

# Smaž data (VOLITELNÉ - ztratíš databázi!)
rm -rf /var/db/devicemonitor
rm -f /var/log/devicemonitor.log

# Restart služeb
service configd restart
service php-fpm restart
```

**Poznámka:** Po odinstalaci zmizí plugin z menu. Může být potřeba vyčistit cache prohlížeče (Ctrl+Shift+R).

---

## Podpora

**GitHub Issues:**
https://github.com/hacesoft/opnsense-devicemonitor/issues

**Autor:**
- GitHub: [@hacesoft](https://github.com/hacesoft)
- Web: [hacesoft.cz](https://hacesoft.cz)

---

## License

MIT License - viz [LICENSE](LICENSE) soubor

---

**🎉 Hotovo! Užij si automatické sledování zařízení v OPNsense!**

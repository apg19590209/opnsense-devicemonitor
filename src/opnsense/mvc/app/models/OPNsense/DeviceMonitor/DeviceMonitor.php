<?php

namespace OPNsense\DeviceMonitor;

class DeviceMonitor
{
    // ================================================================
    // CESTY - VŠECHNO NA JEDNOM MÍSTĚ!
    //
    //          Ukazatel na konfigurační soubor s výchozími hodnotami
    //
    // ================================================================
    private static $defaultsFile = '/usr/local/opnsense/mvc/app/models/OPNsense/DeviceMonitor/defaults.json';
    private static $data = null;

    private static function loadDefaults()
    {
        if (self::$data === null) {
            $json = file_get_contents(self::$defaultsFile);
            self::$data = json_decode($json, true);
        }
        return self::$data;
    }

    public static function getPaths()
    {
        $data = self::loadDefaults();
        return $data['paths'];
    }
    
    public static function getPath($key)
    {
        $paths = self::getPaths();
        return isset($paths[$key]) ? $paths[$key] : null;
    }

    public static function getConfig()
    {
        $data = self::loadDefaults();
        $configFilePath = $data['paths']['configFile'];
        
        // Pokud existuje config.json, načti z něj
        if (file_exists($configFilePath)) {
            $json = file_get_contents($configFilePath);
            $savedConfig = json_decode($json, true);
            
            // Použij uložené hodnoty, ale zachovej cesty z defaults
            if ($savedConfig !== null && is_array($savedConfig)) {
                $savedConfig['paths'] = $data['paths'];
                return $savedConfig;
            }
        }
        
        // Jinak vrať defaults
        $config = $data['config'];
        $config['paths'] = $data['paths'];
        return $config;
    }


    // ========================================
    // GETTERY PRO CESTY (pro Controllery)
    // ========================================


    /**
     * Vrátí cestu k PID souboru
     */
    public function getPidFilePath()
    {
        return self::getPath('pidFile');
    }

    
    /**
     * Vrátí cestu k databázi
     */
    public function getDbFilePath()
    {
        return self::getPath('dbFile');
    }
    
    /**
     * Vrátí cestu ke konfiguračnímu souboru
     */
    public function getConfigFilePath()
    {
        return self::getPath('configFile');
    }
    
    public function updateHostname($mac, $hostname)
    {
        $db = $this->getDb();
        $hostname = trim($hostname);
        
        if ($hostname === '') {
            $stmt = $db->prepare('UPDATE devices SET custom_hostname = NULL WHERE mac = :mac');
            $stmt->bindValue(':mac', $mac, SQLITE3_TEXT);
        } else {
            $stmt = $db->prepare('UPDATE devices SET custom_hostname = :hn, hostname = :hn WHERE mac = :mac');
            $stmt->bindValue(':hn', $hostname, SQLITE3_TEXT);
            $stmt->bindValue(':mac', $mac, SQLITE3_TEXT);
        }
        
        $stmt->execute();
        $changes = $db->changes();
        $db->close();
        return $changes > 0;
    }


    /**
     * Uložení konfigurace
     * @param array $data Data k uložení
     * @return bool True pokud se podařilo uložit
     */
    public function setConfig($data)
    {
        $file_name = self::getPath('configFile');
        
        // Bezpečné zajištění adresáře - nesmí blokovat uložení!
        $dir = dirname($file_name);
        if (!is_dir($dir)) {
            try {
                @mkdir($dir, 0755, true);
            } catch (\Exception $e) {
                // Ignoruj chybu - zkusíme uložit soubor i tak
            }
        }
        
        // Ulož jako JSON s potlačením varování
        $json = json_encode($data, JSON_PRETTY_PRINT);
        $result = @file_put_contents($file_name, $json);
        
        if ($result !== false) {
            @chmod($file_name, 0644);
            return true;
        }
        
        return false;
    }

    
    // ========================================
    // DATABÁZE
    // ========================================
    
    private function getDb()
    {
        $file_mame = self::getPath('dbFile');
        $dbDir = dirname($file_mame);
        if (!is_dir($dbDir)) {
            mkdir($dbDir, 0755, true);
        }

        if (!file_exists($file_mame)) {
            $this->initDatabase();
        }

        $db = new \SQLite3($file_mame);
        $db->busyTimeout(5000);
        return $db;
    }


    private function initDatabase()
    {
        $file_mame = self::getPath('dbFile');
        $db = new \SQLite3($file_mame);
        
        $db->exec('CREATE TABLE IF NOT EXISTS devices (
            mac TEXT PRIMARY KEY,
            ip TEXT,
            hostname TEXT,
            vendor TEXT,
            vlan TEXT,
            last_seen DATETIME DEFAULT CURRENT_TIMESTAMP,
            notified INTEGER DEFAULT 0,
            is_active INTEGER DEFAULT 0,
            notification_pending INTEGER DEFAULT 0
        )');

        $db->exec('CREATE INDEX IF NOT EXISTS idx_last_seen ON devices(last_seen)');
        // Migration: add columns for older databases
        @$db->exec('ALTER TABLE devices ADD COLUMN first_seen DATETIME DEFAULT CURRENT_TIMESTAMP');
        @$db->exec('ALTER TABLE devices ADD COLUMN custom_hostname TEXT DEFAULT NULL');
        
        $db->close();
        chmod($file_mame, 0644);
    }

    // ========================================
    // ZAŘÍZENÍ - CRUD OPERACE
    // ========================================
    
    /**
     * Získání všech zařízení z databáze
     * @return array Seznam zařízení (upravený podle konfigurace)
     */
    public function getDevices()
    {
        $devices = [];
        $file_mame = self::getPath('dbFile');
        
        if (file_exists($file_mame)) {
            $db = new \SQLite3($file_mame);
            $result = $db->query('SELECT * FROM devices ORDER BY last_seen DESC');
            
            while ($row = $result->fetchArray(SQLITE3_ASSOC)) {
                
                // Status podle is_active sloupce (místo času)
                $row['status'] = (isset($row['is_active']) && $row['is_active'] == 1) ? 'online' : 'offline';
                
                // Vendor může být NULL - oprav to
                if (empty($row['vendor'])) {
                    $row['vendor'] = 'Unknown';
                }

                // Formátuj datum do českého formátu: 29.12.2025 - 18:37:51
                if (!empty($row['last_seen'])) {
                    $timestamp = strtotime($row['last_seen']);
                    if ($timestamp !== false) {
                        $row['last_seen'] = date('d.m.Y - H:i:s', $timestamp);
                    }
                }
                
                $devices[] = $row;
            }
            
            $db->close();
        }
        
        return $devices;
    }

    public function deleteDevice($mac)
    {
        $db = $this->getDb();
        $stmt = $db->prepare('DELETE FROM devices WHERE mac = :mac');
        $stmt->bindValue(':mac', $mac, SQLITE3_TEXT);
        $stmt->execute();
        $changes = $db->changes();
        $db->close();
        return $changes > 0;
    }

    public function clearAll()
    {
        $db = $this->getDb();
        $db->exec('DELETE FROM devices');
        $db->close();
        return true;
    }
}
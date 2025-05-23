import time
import json
import math
import os
from smartcard.System import readers
from smartcard.util import toHexString
from smartcard.Exceptions import NoCardException
from typing import Dict, Tuple, Optional

class NFCConfigWriter:
    def __init__(self, config_file: str = "config.json"):
        self.config_file = config_file
        self.bytes_pro_seite = 4
        self.start_seite = 8
        self.ndef_header_overhead = 12
        self.verbindung = None
        self.kartenleser = None
        
    def initialisiere_kartenleser(self) -> bool:
        """Initialisiert den NFC-Kartenleser"""
        try:
            kartenleser_liste = readers()
            if not kartenleser_liste:
                print("❌ Kein Kartenleser gefunden!")
                return False
            
            self.kartenleser = kartenleser_liste[0]
            print(f"✅ Kartenleser gefunden: {self.kartenleser}")
            return True
        except Exception as e:
            print(f"❌ Fehler beim Initialisieren des Kartenlesers: {e}")
            return False
    
    def verbinde_mit_tag(self) -> bool:
        """Stellt Verbindung zum NFC-Tag her"""
        if not self.kartenleser:
            return False
            
        print("\n📡 Bitte halte einen NFC-Tag an den Leser...")
        
        while True:
            try:
                self.verbindung = self.kartenleser.createConnection()
                self.verbindung.connect()
                print("✅ NFC-Tag erkannt!")
                return True
            except NoCardException:
                print("⏳ Warte auf NFC-Tag...")
                time.sleep(1)
            except Exception as e:
                print(f"❌ Fehler beim Verbinden: {e}")
                return False
    
    def lese_uid(self) -> Optional[str]:
        """Liest die UID des NFC-Tags"""
        try:
            apdu_befehl_uid = [0xFF, 0xCA, 0x00, 0x00, 0x00]
            antwort_uid, status1, status2 = self.verbindung.transmit(apdu_befehl_uid)
            
            if (status1, status2) == (0x90, 0x00):
                uid_hex = toHexString(antwort_uid)
                print(f"🏷️  UID: {uid_hex}")
                return uid_hex
            else:
                print(f"❌ Fehler beim Auslesen der UID: SW1={status1:02X}, SW2={status2:02X}")
                return None
        except Exception as e:
            print(f"❌ Fehler beim UID-Auslesen: {e}")
            return None
    
    def lese_tag_komplett(self) -> Optional[bytes]:
        """Liest den kompletten Tag-Inhalt aus"""
        try:
            gesamter_inhalt = b''
            start_seite = 0x00
            end_seite = 0xE9
            max_retries = 3
            
            print(f"\n📖 Lese Tag-Daten (Seiten {start_seite}-{end_seite})...")
            
            for seitennummer in range(start_seite, end_seite + 1):
                retries = 0
                while retries < max_retries:
                    try:
                        apdu_befehl = [0xFF, 0xB0, 0x00, seitennummer, 0x04]
                        antwort, status1, status2 = self.verbindung.transmit(apdu_befehl)
                        
                        if (status1, status2) == (0x90, 0x00):
                            gesamter_inhalt += bytes(antwort)
                            if seitennummer % 50 == 0:  # Progress-Anzeige
                                print(f"   Seite {seitennummer} gelesen...")
                            break
                        else:
                            print(f"⚠️  Seite {seitennummer}: SW1={status1:02X}, SW2={status2:02X}")
                    except Exception as e:
                        print(f"⚠️  Seite {seitennummer}: {e}")
                    
                    retries += 1
                    if retries < max_retries:
                        time.sleep(0.1)
                    else:
                        print(f"❌ Seite {seitennummer} nach {max_retries} Versuchen übersprungen")
                        gesamter_inhalt += b'\x00\x00\x00\x00'  # Padding
            
            print(f"✅ Tag-Daten komplett gelesen ({len(gesamter_inhalt)} Bytes)")
            return gesamter_inhalt
            
        except Exception as e:
            print(f"❌ Fehler beim Tag-Auslesen: {e}")
            return None
    
    def extrahiere_json_vom_tag_bytes(self, tag_bytes: bytes) -> Optional[str]:
        """Extrahiert JSON aus den rohen Tag-Bytes"""
        try:
            # Suche JSON-Start (erstes '{')
            json_start = -1
            for i, byte_val in enumerate(tag_bytes):
                if byte_val == ord('{'):
                    json_start = i
                    break
            
            if json_start == -1:
                print("❌ Kein JSON-Start '{' gefunden!")
                return None
            
            # Suche JSON-Ende (0xFE Marker)
            json_ende = -1
            for i in range(json_start, len(tag_bytes)):
                if tag_bytes[i] == 0xFE:
                    json_ende = i
                    break
            
            if json_ende == -1:
                print("❌ Kein JSON-Ende-Marker (0xFE) gefunden!")
                return None
            
            # Extrahiere JSON-Bytes
            json_bytes = tag_bytes[json_start:json_ende]
            json_string = json_bytes.decode('utf-8', errors='ignore')
            
            # Validiere JSON
            try:
                json.loads(json_string)
                print(f"✅ JSON erfolgreich extrahiert ({len(json_string)} Zeichen)")
                return json_string
            except json.JSONDecodeError as e:
                print(f"❌ Ungültiges JSON: {e}")
                return None
                
        except Exception as e:
            print(f"❌ Fehler bei JSON-Extraktion: {e}")
            return None
    
    def lade_config_datei(self) -> Optional[Dict]:
        """Lädt die lokale config.json Datei"""
        try:
            if not os.path.exists(self.config_file):
                print(f"❌ Config-Datei '{self.config_file}' nicht gefunden!")
                return None
                
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
                print(f"✅ Config-Datei geladen: Version '{config.get('title', 'Unbekannt')}'")
                return config
        except Exception as e:
            print(f"❌ Fehler beim Laden der Config-Datei: {e}")
            return None
    
    def berechne_ndef_header(self, json_laenge: int) -> Dict[str, bytes]:
        """Berechnet NDEF-Header basierend auf JSON-Länge"""
        ndef_gesamt = json_laenge + self.ndef_header_overhead
        
        # NDEF-Nachrichtenlänge (2 Bytes, Big Endian)
        ndef_high = (ndef_gesamt >> 8) & 0xFF
        ndef_low = ndef_gesamt & 0xFF
        
        # JSON-Payload-Länge (2 Bytes, Big Endian)
        payload_high = (json_laenge >> 8) & 0xFF
        payload_low = json_laenge & 0xFF
        
        print(f"📊 Header-Berechnung:")
        print(f"   JSON-Länge: {json_laenge} Bytes")
        print(f"   NDEF-Gesamt: {ndef_gesamt} Bytes")
        print(f"   Seite 4: 03 FF {ndef_high:02X} {ndef_low:02X}")
        print(f"   Seite 6: {payload_high:02X} {payload_low:02X} 72 2F")
        
        return {
            'seite_4': bytes([0x03, 0xFF, ndef_high, ndef_low]),
            'seite_6': bytes([payload_high, payload_low, 0x72, 0x2F])
        }
    
    def schreibe_seite(self, seitennummer: int, daten: bytes) -> bool:
        """Schreibt 4 Bytes auf eine Tag-Seite"""
        try:
            if len(daten) != 4:
                print(f"❌ Seite {seitennummer}: Daten müssen exakt 4 Bytes sein!")
                return False
            
            apdu_befehl = [0xFF, 0xD6, 0x00, seitennummer] + list(daten)
            antwort, status1, status2 = self.verbindung.transmit(apdu_befehl)
            
            if (status1, status2) == (0x90, 0x00):
                hex_str = ' '.join(f"{b:02X}" for b in daten)
                print(f"✅ Seite {seitennummer:3}: {hex_str}")
                return True
            else:
                print(f"❌ Seite {seitennummer}: Schreibfehler SW1={status1:02X}, SW2={status2:02X}")
                return False
                
        except Exception as e:
            print(f"❌ Seite {seitennummer}: Schreibfehler {e}")
            return False
    
    def schreibe_config_auf_tag(self, config_data: Dict) -> bool:
        """Schreibt die komplette Config auf den NFC-Tag"""
        try:
            # JSON komprimieren
            json_kompakt = json.dumps(config_data, separators=(',', ':'), ensure_ascii=False)
            json_bytes = json_kompakt.encode('utf-8')
            json_laenge = len(json_bytes)
            
            print(f"\n📝 Schreibe Config auf Tag:")
            print(f"   Komprimierte JSON-Länge: {json_laenge} Zeichen")
            
            # Header berechnen und schreiben
            header = self.berechne_ndef_header(json_laenge)
            
            print(f"\n🔧 Aktualisiere NDEF-Header...")
            if not self.schreibe_seite(4, header['seite_4']):
                return False
            if not self.schreibe_seite(6, header['seite_6']):
                return False
            
            # JSON-Daten schreiben
            print(f"\n📄 Schreibe JSON-Daten...")
            seite_nr = self.start_seite
            
            for i in range(0, len(json_bytes), self.bytes_pro_seite):
                chunk = json_bytes[i:i+self.bytes_pro_seite]
                
                # Letzte Seite: FE-Terminator hinzufügen
                if len(chunk) < self.bytes_pro_seite and i + self.bytes_pro_seite >= len(json_bytes):
                    chunk_list = list(chunk)
                    chunk_list.append(0xFE)  # Ende-Marker
                    while len(chunk_list) < self.bytes_pro_seite:
                        chunk_list.append(0x42)  # Padding
                    chunk = bytes(chunk_list)
                elif len(chunk) < self.bytes_pro_seite:
                    # Zwischenseite: Mit Nullen auffüllen
                    chunk += b'\x00' * (self.bytes_pro_seite - len(chunk))
                
                if not self.schreibe_seite(seite_nr, chunk):
                    return False
                
                seite_nr += 1
            
            print(f"✅ Config erfolgreich auf Tag geschrieben!")
            print(f"   Verwendete Seiten: {self.start_seite}-{seite_nr-1}")
            print(f"   FE-Terminator bei Seite: {seite_nr-1}")
            
            return True
            
        except Exception as e:
            print(f"❌ Fehler beim Schreiben der Config: {e}")
            return False
    
    def vergleiche_versionen(self, tag_json: str, config_data: Dict) -> Tuple[bool, str, str]:
        """Vergleicht Versionen zwischen Tag und Config-Datei"""
        try:
            tag_config = json.loads(tag_json)
            tag_version = tag_config.get('title', 'Unbekannt')
            config_version = config_data.get('title', 'Unbekannt')
            
            print(f"🔍 Tag-Version: '{tag_version}'")
            print(f"🔍 Config-Version: '{config_version}'")
            
            return tag_version == config_version, tag_version, config_version
        except Exception as e:
            print(f"❌ Fehler beim Versions-Vergleich: {e}")
            return False, "Fehler", "Fehler"
    
    def trenne_verbindung(self):
        """Trennt die Verbindung zum Tag"""
        if self.verbindung:
            try:
                self.verbindung.disconnect()
                print("🔌 Verbindung zum Tag getrennt")
            except:
                pass
            self.verbindung = None
    
    def verarbeite_tag_direkt(self) -> bool:
        """Hauptfunktion: Liest Tag direkt aus und schreibt neue Config"""
        try:
            # Kartenleser initialisieren
            if not self.initialisiere_kartenleser():
                return False
            
            # Mit Tag verbinden
            if not self.verbinde_mit_tag():
                return False
            
            # UID auslesen
            uid = self.lese_uid()
            if not uid:
                return False
            
            # Tag-Daten komplett auslesen
            print("\n🔍 Extrahiere aktuelle Tag-Konfiguration...")
            tag_bytes = self.lese_tag_komplett()
            if not tag_bytes:
                return False
            
            # JSON aus Tag extrahieren
            tag_json = self.extrahiere_json_vom_tag_bytes(tag_bytes)
            if not tag_json:
                return False
            
            # Lokale Config laden
            print("\n📄 Lade lokale Config-Datei...")
            config_data = self.lade_config_datei()
            if not config_data:
                return False
            
            # Versionen vergleichen
            print("\n🔄 Vergleiche Versionen...")
            versionen_gleich, tag_version, config_version = self.vergleiche_versionen(tag_json, config_data)
            
            if not versionen_gleich:
                print(f"\n⚠️  VERSIONS-KONFLIKT ERKANNT!")
                print(f"   Tag-Version:    '{tag_version}'")
                print(f"   Config-Version: '{config_version}'")
                
                antwort = input("\n❓ Trotzdem neue Config schreiben? (j/n): ").lower()
                if antwort not in ['j', 'ja', 'y', 'yes']:
                    print("❌ Vorgang abgebrochen!")
                    return False
            else:
                print(f"✅ Versionen stimmen überein: '{tag_version}'")
            
            # Neue Config schreiben
            print(f"\n📝 Schreibe neue Konfiguration auf Tag...")
            erfolg = self.schreibe_config_auf_tag(config_data)
            
            if erfolg:
                print(f"\n🎉 Tag erfolgreich aktualisiert!")
                print(f"   UID: {uid}")
                print(f"   Version: {config_data.get('title', 'Unbekannt')}")
            
            return erfolg
            
        except Exception as e:
            print(f"❌ Unerwarteter Fehler: {e}")
            return False
        finally:
            self.trenne_verbindung()

# Verwendungsbeispiel
if __name__ == "__main__":
    print("🚀 NFC Config Writer mit direktem Tag-Zugriff")
    print("=" * 50)
    
    writer = NFCConfigWriter("config.json")
    
    try:
        erfolg = writer.verarbeite_tag_direkt()
        if erfolg:
            print("\n✅ Vorgang erfolgreich abgeschlossen!")
        else:
            print("\n❌ Vorgang fehlgeschlagen!")
    except KeyboardInterrupt:
        print("\n\n⏹️  Vorgang vom Benutzer abgebrochen")
        writer.trenne_verbindung()
    except Exception as e:
        print(f"\n❌ Kritischer Fehler: {e}")
        writer.trenne_verbindung()

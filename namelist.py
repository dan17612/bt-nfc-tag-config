"""
NFC Tag Name Extractor
======================

Scannt NFC-Tags und extrahiert den Namen aus dem JSON-String.
Der Name wird aus properties.Name.value ausgelesen.

Autor: GitHub Copilot
Datum: 16. Oktober 2025
"""

import time
import json
from smartcard.System import readers
from smartcard.util import toHexString
from smartcard.Exceptions import NoCardException

# Konstanten
START_SEITE = 0x00
END_SEITE = 0xE9  
JSON_ENDE_MARKER_BYTE = 0xFE
MAX_RETRIES = 3

class NFCNameExtractor:
    """Klasse zum Extrahieren von Namen aus NFC-Tags"""
    
    def __init__(self):
        self.verbindung = None
        self.aktueller_leser = None
        self.namen_liste = []
    
    def finde_nfc_leser(self):
        """Findet verfügbare NFC-Lesegeräte"""
        try:
            kartenleser_liste = readers()
            if not kartenleser_liste:
                print("❌ Fehler: Kein NFC-Lesegerät gefunden.")
                return False
            
            self.aktueller_leser = kartenleser_liste[0]
            print(f"📱 Verwende Leser: {self.aktueller_leser}")
            return True
        except Exception as e:
            print(f"❌ Fehler beim Suchen der Lesegeräte: {e}")
            return False
    
    def warte_auf_tag(self):
        """Wartet auf einen NFC-Tag"""
        print("\n🔍 Bitte halte einen NFC-Tag an den Leser...")
        
        while True:
            try:
                self.verbindung = self.aktueller_leser.createConnection()
                self.verbindung.connect()
                print("✅ NFC-Tag erkannt. Starte Auslesevorgang...")
                return True
            except NoCardException:
                print("⏳ Warte auf NFC-Tag...")
                time.sleep(1)
            except Exception as e:
                print(f"❌ Fehler beim Verbinden: {e}")
                return False
    
    def lese_tag_daten(self):
        """Liest alle Daten vom NFC-Tag"""
        try:
            # UID auslesen
            apdu_befehl_uid_abrufen = [0xFF, 0xCA, 0x00, 0x00, 0x00]
            antwort_uid_daten, status1_uid, status2_uid = self.verbindung.transmit(apdu_befehl_uid_abrufen)
            
            if (status1_uid, status2_uid) == (0x90, 0x00):
                uid_hex_string = toHexString(antwort_uid_daten)
                print(f"🆔 UID: {uid_hex_string}")
            else:
                print(f"⚠️  Warnung: UID konnte nicht gelesen werden")
            
            # Alle Seiten lesen
            gesamter_inhalt_bytes = b''
            erfolgreiche_seiten = 0
            
            print("📖 Lese Tag-Daten...")
            for seitennummer in range(START_SEITE, END_SEITE + 1):
                retries = 0
                while retries < MAX_RETRIES:
                    apdu_befehl_seite_lesen = [0xFF, 0xB0, 0x00, seitennummer, 0x04]
                    try:
                        antwort_seite_daten, status1_seite, status2_seite = self.verbindung.transmit(apdu_befehl_seite_lesen)
                        if (status1_seite, status2_seite) == (0x90, 0x00):
                            gesamter_inhalt_bytes += bytes(antwort_seite_daten)
                            erfolgreiche_seiten += 1
                            break
                        else:
                            if retries == MAX_RETRIES - 1:
                                # Füge leere Bytes hinzu wenn alle Versuche fehlschlagen
                                gesamter_inhalt_bytes += b'\\x00\\x00\\x00\\x00'
                    except Exception as e:
                        if retries == MAX_RETRIES - 1:
                            gesamter_inhalt_bytes += b'\\x00\\x00\\x00\\x00'
                    
                    retries += 1
                    if retries < MAX_RETRIES:
                        time.sleep(0.1)
            
            print(f"✅ {erfolgreiche_seiten} Seiten erfolgreich gelesen")
            return gesamter_inhalt_bytes
            
        except Exception as e:
            print(f"❌ Fehler beim Lesen der Tag-Daten: {e}")
            return None
    
    def extrahiere_json_von_bytes(self, daten_bytes):
        """Extrahiert JSON-String aus den Byte-Daten"""
        try:
            # Suche nach JSON-Anfang '{'
            start_index = -1
            for i, byte_val in enumerate(daten_bytes):
                if byte_val == ord('{'):
                    start_index = i
                    break
            
            if start_index == -1:
                print("❌ Kein JSON-Anfang gefunden")
                return None
            
            # Suche nach Ende-Marker 0xFE
            ende_index = -1
            for i in range(start_index, len(daten_bytes)):
                if daten_bytes[i] == JSON_ENDE_MARKER_BYTE:
                    ende_index = i
                    break
            
            if ende_index == -1:
                print("❌ Kein JSON-Ende-Marker (0xFE) gefunden")
                return None
            
            # JSON-String extrahieren
            json_bytes = daten_bytes[start_index:ende_index]
            json_string = json_bytes.decode('utf-8', errors='ignore')
            
            return json_string
            
        except Exception as e:
            print(f"❌ Fehler beim Extrahieren des JSON: {e}")
            return None
    
    def extrahiere_name_aus_json(self, json_string):
        """Extrahiert den Namen aus dem JSON-String"""
        try:
            # JSON parsen
            json_data = json.loads(json_string)
            
            # Name aus properties.Name.value extrahieren
            if 'properties' in json_data:
                if 'Name' in json_data['properties']:
                    if 'value' in json_data['properties']['Name']:
                        name = json_data['properties']['Name']['value']
                        return name
            
            print("❌ Name nicht im erwarteten Format gefunden")
            print("📋 Verfügbare JSON-Struktur:")
            print(json.dumps(json_data, indent=2, ensure_ascii=False))
            return None
            
        except json.JSONDecodeError as e:
            print(f"❌ JSON-Parsing Fehler: {e}")
            print("📋 Raw JSON-String:")
            print(json_string)
            return None
        except Exception as e:
            print(f"❌ Fehler beim Name-Extrahieren: {e}")
            return None
    
    def scanne_einzelnen_tag(self):
        """Scannt einen einzelnen NFC-Tag und extrahiert den Namen"""
        if not self.finde_nfc_leser():
            return None
        
        if not self.warte_auf_tag():
            return None
        
        try:
            # Tag-Daten lesen
            tag_daten = self.lese_tag_daten()
            if not tag_daten:
                return None
            
            # JSON extrahieren
            json_string = self.extrahiere_json_von_bytes(tag_daten)
            if not json_string:
                return None
            
            # Namen extrahieren
            name = self.extrahiere_name_aus_json(json_string)
            if name:
                print(f"🏷️  Extrahierter Name: {name}")
                return name
            else:
                return None
                
        finally:
            if self.verbindung:
                try:
                    self.verbindung.disconnect()
                    print("🔌 Verbindung getrennt")
                except Exception:
                    pass
    
    def kontinuierlich_scannen(self):
        """Scannt kontinuierlich NFC-Tags und sammelt Namen"""
        print("🔄 Kontinuierlicher NFC-Tag Scan")
        print("="*40)
        print("Drücken Sie Strg+C zum Beenden\\n")
        
        tag_counter = 1
        
        try:
            while True:
                print(f"\\n{'='*40}")
                print(f"TAG #{tag_counter}")
                print(f"{'='*40}")
                
                name = self.scanne_einzelnen_tag()
                
                if name:
                    if name not in self.namen_liste:
                        self.namen_liste.append(name)
                        print(f"✅ Neuer Name hinzugefügt: {name}")
                    else:
                        print(f"ℹ️  Name bereits bekannt: {name}")
                    
                    print(f"\\n📋 Gefundene Namen ({len(self.namen_liste)}):")
                    for i, gefundener_name in enumerate(self.namen_liste, 1):
                        print(f"{gefundener_name}")
                else:
                    print("❌ Kein Name gefunden oder Fehler beim Scannen")
                
                print("\\n🔄 Entferne den Tag und lege den nächsten auf...")
                
                # Warten bis Tag entfernt wird
                self.warte_bis_tag_entfernt()
                
                tag_counter += 1
                time.sleep(1)
                
        except KeyboardInterrupt:
            print(f"\\n\\n🛑 Scan beendet. Insgesamt {len(self.namen_liste)} Namen gefunden:")
            for i, name in enumerate(self.namen_liste, 1):
                print(f"   {i}. {name}")
            
            # Namen in Datei speichern
            self.speichere_namen_liste()
    
    def warte_bis_tag_entfernt(self):
        """Wartet bis der aktuelle Tag entfernt wird"""
        if not self.aktueller_leser:
            return
        
        while True:
            try:
                test_verbindung = self.aktueller_leser.createConnection()
                test_verbindung.connect()
                test_verbindung.disconnect()
                time.sleep(0.5)
            except NoCardException:
                print("✅ Tag entfernt. Bereit für nächsten Tag...")
                break
            except Exception:
                break
    
    def speichere_namen_liste(self):
        """Speichert die gesammelten Namen in eine Datei"""
        if not self.namen_liste:
            print("ℹ️  Keine Namen zum Speichern gefunden")
            return
        
        try:
            dateiname = f"nfc_namen_liste_{int(time.time())}.txt"
            with open(dateiname, 'w', encoding='utf-8') as datei:
                datei.write("NFC Tag Namen Liste\\n")
                datei.write("="*30 + "\\n")
                datei.write(f"Erstellt am: {time.strftime('%d.%m.%Y %H:%M:%S')}\\n")
                datei.write(f"Anzahl Namen: {len(self.namen_liste)}\\n\\n")
                
                for i, name in enumerate(self.namen_liste, 1):
                    datei.write(f"{i:2}. {name}\\n")
            
            print(f"💾 Namen-Liste gespeichert in: {dateiname}")
            
        except Exception as e:
            print(f"❌ Fehler beim Speichern: {e}")

def main():
    """Hauptfunktion"""
    extractor = NFCNameExtractor()
    
    print("🏷️  NFC Tag Name Extractor")
    print("="*30)
    
    print("\\nWas möchten Sie tun?")
    print("1. Einzelnen Tag scannen")
    print("2. Kontinuierlich scannen (mehrere Tags)")
    
    while True:
        try:
            wahl = input("\\nBitte wählen Sie (1 oder 2): ").strip()
            
            if wahl == "1":
                print("\\n🔍 Einzelner Tag-Scan:")
                name = extractor.scanne_einzelnen_tag()
                if name:
                    print(f"\\n🎉 Erfolgreich! Gefundener Name: {name}")
                else:
                    print("\\n❌ Kein Name gefunden")
                break
                
            elif wahl == "2":
                extractor.kontinuierlich_scannen()
                break
                
            else:
                print("❌ Ungültige Eingabe! Bitte 1 oder 2 eingeben.")
                
        except KeyboardInterrupt:
            print("\\n\\n👋 Programm durch Benutzer beendet.")
            break
    
    input("\\n📝 Drücken Sie Enter zum Beenden...")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\\n\\n👋 Programm durch Benutzer beendet.")
    except Exception as e:
        print(f"\\n❌ Unerwarteter Fehler: {e}")

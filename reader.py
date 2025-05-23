import time
from smartcard.System import readers
from smartcard.util import toHexString
from smartcard.Exceptions import NoCardException

START_SEITE = 0x00
END_SEITE = 0xE9  
JSON_ENDE_MARKER_BYTE = 0xFE
MAX_RETRIES = 3

def bytes_zu_utf8_string(byte_liste):
    """Wandelt eine Liste von 4 Bytes in einen UTF-8 String um"""
    try:
        return bytes(byte_liste).decode('utf-8')
    except UnicodeDecodeError:
        return bytes(byte_liste).decode('latin-1', errors='replace')

def erstelle_neue_daten_textdatei(uid_daten, gesamte_daten):
    """Erstellt eine TXT-Datei mit dem NEUE_DATEN Dictionary"""
    
    # Finde JSON-Start und Ende
    json_start_seite = None
    json_ende_seite = None
    
    for seite in range(8, len(gesamte_daten)):
        if seite in gesamte_daten:
            daten = gesamte_daten[seite]
            if any(b == ord('{') for b in daten):
                json_start_seite = seite
                break
    
    if json_start_seite is not None:
        for seite in range(json_start_seite, len(gesamte_daten)):
            if seite in gesamte_daten:
                daten = gesamte_daten[seite]
                if JSON_ENDE_MARKER_BYTE in daten:
                    json_ende_seite = seite
                    break
    
    # Erstelle Dateiname basierend auf UID
    uid_string = "_".join([f"{b:02X}" for b in uid_daten])
    dateiname = f"NEUE_DATEN_{uid_string}.txt"
    
    with open(dateiname, 'w', encoding='utf-8') as datei:
        datei.write("# === NEUE_DATEN Dictionary für Writer-Script ===\n")
        datei.write("# Diese Datei kann bearbeitet werden, bevor die Daten ins Writer-Script kopiert werden\n\n")
        datei.write("NEUE_DATEN = {\n")
        
        # Header (Seiten 3-7)
        datei.write("    # === Anfang Header ===\n")
        for seite in range(3, 8):
            if seite in gesamte_daten:
                daten = gesamte_daten[seite]
                hex_string = ", ".join([f"0x{b:02X}" for b in daten])
                datei.write(f"    {seite}: [{hex_string}],\n")
        datei.write("    # === Ende Header ===\n")
        
        # Config (JSON-Daten als UTF-8 Strings)
        if json_start_seite and json_ende_seite:
            datei.write("    # === Anfang Config ===\n")
            for seite in range(8, json_ende_seite + 1):
                if seite in gesamte_daten:
                    daten = gesamte_daten[seite]
                    utf8_string = bytes_zu_utf8_string(daten)
                    # Escape-Zeichen für Python-String
                    escaped_string = utf8_string.replace('\\', '\\\\').replace('"', '\\"')
                    datei.write(f"    {seite}: \"{escaped_string}\",\n")
            datei.write("    # === Ende Config ===\n")
        
        # Footer (alle Seiten nach JSON-Ende mit Daten)
        footer_gefunden = False
        for seite in range((json_ende_seite + 1) if json_ende_seite else 202, END_SEITE + 1):
            if seite in gesamte_daten:
                daten = gesamte_daten[seite]
                # Nur Seiten mit relevanten Daten (nicht nur Nullen)
                if any(b != 0 for b in daten):
                    if not footer_gefunden:
                        datei.write("    # === Anfang Footer ===\n")
                        footer_gefunden = True
                    hex_string = ", ".join([f"0x{b:02X}" for b in daten])
                    datei.write(f"    {seite}: [{hex_string}],\n")
        
        if footer_gefunden:
            datei.write("    # === Ende Footer ===\n")
        
        datei.write("}\n\n")
        
        # Zusätzliche Informationen für Bearbeitung
        datei.write("# === Anpassungshinweise ===\n")
        datei.write("# 1. Header (Seiten 3-7): Normalerweise nicht ändern\n")
        datei.write("# 2. Config (JSON-Daten): Hier können Werte angepasst werden\n")
        datei.write("#    - Achten Sie darauf, dass die Gesamtlänge gleich bleibt\n")
        datei.write("#    - Jede Seite muss genau 4 Zeichen haben\n")
        datei.write("# 3. Footer: Normalerweise nicht ändern\n\n")
        
        datei.write("# === Verwendung ===\n")
        datei.write("# 1. Diese Datei nach Bedarf bearbeiten\n")
        datei.write("# 2. Das NEUE_DATEN Dictionary kopieren\n")
        datei.write("# 3. In das Writer-Script einfügen\n")
        datei.write("# 4. Writer-Script ausführen\n")
    
    print(f"NEUE_DATEN Dictionary wurde in '{dateiname}' gespeichert.")
    print("Die TXT-Datei kann vor der Verwendung bearbeitet werden.")
    return dateiname

def lese_tag_und_erstelle_neue_daten():
    """Liest einen NFC-Tag aus und erstellt das NEUE_DATEN Dictionary"""
    verbindung = None
    kartenleser_liste = readers()

    if not kartenleser_liste:
        print("Fehler: Kein Kartenleser gefunden.")
        return

    aktueller_kartenleser = kartenleser_liste[0]
    print(f"Verwende Leser: {aktueller_kartenleser}")

    print("\nBitte halte einen NFC-Tag an den Leser...")
    while True:
        try:
            verbindung = aktueller_kartenleser.createConnection()
            verbindung.connect()
            print("NFC-Tag erkannt. Starte Auslesevorgang...")
            break
        except NoCardException:
            print("Warte auf NFC-Tag...")
            time.sleep(1)
        except Exception as e:
            print(f"Fehler beim Verbinden: {e}")
            return

    try:
        # UID auslesen
        apdu_befehl_uid_abrufen = [0xFF, 0xCA, 0x00, 0x00, 0x00]
        antwort_uid_daten, status1_uid, status2_uid = verbindung.transmit(apdu_befehl_uid_abrufen)
        
        if (status1_uid, status2_uid) != (0x90, 0x00):
            print(f"Fehler beim Auslesen der UID: SW1={status1_uid:02X}, SW2={status2_uid:02X}")
            return
        
        uid_hex_string = toHexString(antwort_uid_daten)
        print(f"UID: {uid_hex_string}")

        # Alle Seiten auslesen
        gesamte_daten = {}
        
        print("\nLese Tag-Daten aus...")
        for seitennummer in range(START_SEITE, END_SEITE + 1):
            retries = 0
            while retries < MAX_RETRIES:
                apdu_befehl_seite_lesen = [0xFF, 0xB0, 0x00, seitennummer, 0x04]
                try:
                    antwort_seite_daten, status1_seite, status2_seite = verbindung.transmit(apdu_befehl_seite_lesen)
                    if (status1_seite, status2_seite) == (0x90, 0x00):
                        gesamte_daten[seitennummer] = antwort_seite_daten
                        break
                    else:
                        print(f"Seite {seitennummer}: Fehler SW1={status1_seite:02X}, SW2={status2_seite:02X}")
                except Exception as e:
                    print(f"Seite {seitennummer}: Fehler {e}")
                
                retries += 1
                if retries < MAX_RETRIES:
                    time.sleep(0.1)

        print(f"✓ {len(gesamte_daten)} Seiten erfolgreich ausgelesen")
        
        # NEUE_DATEN TXT-Datei erstellen
        dateiname = erstelle_neue_daten_textdatei(antwort_uid_daten, gesamte_daten)
        
        return dateiname

    finally:
        if verbindung:
            try:
                verbindung.disconnect()
                print("Verbindung zum Leser getrennt.")
            except Exception:
                pass

def main_loop():
    """Hauptschleife für kontinuierliches Tag-Auslesen"""
    tag_zaehler = 1
    print("=== NFC Tag zu NEUE_DATEN TXT Converter ===")
    print("Erstellt bearbeitbare TXT-Dateien mit NEUE_DATEN Dictionary")
    print("Drücken Sie Strg+C zum Beenden\n")
    
    try:
        while True:
            print(f"\n{'='*50}")
            print(f"WARTE AUF TAG: {tag_zaehler}")
            print(f"{'='*50}")
            
            # Tag auslesen und NEUE_DATEN erstellen
            dateiname = lese_tag_und_erstelle_neue_daten()
            
            if dateiname:
                print(f"\n✓ Tag {tag_zaehler} erfolgreich konvertiert: {dateiname}")
                print("📝 TXT-Datei kann vor Verwendung bearbeitet werden!")
                print("\nEntferne den Tag und lege den nächsten Tag auf...")
                
                # Warten bis Tag entfernt wird
                kartenleser_liste = readers()
                if kartenleser_liste:
                    aktueller_kartenleser = kartenleser_liste[0]
                    
                    while True:
                        try:
                            verbindung = aktueller_kartenleser.createConnection()
                            verbindung.connect()
                            verbindung.disconnect()
                            time.sleep(0.5)
                        except NoCardException:
                            print("Tag entfernt. Bereit für nächsten Tag...")
                            break
                        except Exception:
                            break
                
                tag_zaehler += 1
                time.sleep(1)
            else:
                print("Fehler beim Auslesen. Versuche es erneut...")
                time.sleep(2)
            
    except KeyboardInterrupt:
        print(f"\n\nProgramm beendet. Insgesamt {tag_zaehler - 1} Tags konvertiert.")
    except Exception as e:
        print(f"\nFehler in der Hauptschleife: {e}")

if __name__ == "__main__":
    print("Wählen Sie eine Option:")
    print("1. Einzelnen Tag konvertieren")
    print("2. Kontinuierliche Konvertierung (mehrere Tags)")
    
    try:
        wahl = input("\nEingabe (1 oder 2): ").strip()
        
        if wahl == "1":
            lese_tag_und_erstelle_neue_daten()
        elif wahl == "2":
            main_loop()
        else:
            print("Ungültige Eingabe. Programm wird beendet.")
    except KeyboardInterrupt:
        print("\nProgramm beendet.")

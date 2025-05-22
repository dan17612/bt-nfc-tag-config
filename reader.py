import time
from smartcard.System import readers
from smartcard.util import toHexString
from smartcard.Exceptions import NoCardException
import json

START_SEITE = 0x00
END_SEITE = 0xE9  
JSON_ENDE_MARKER_BYTE = 0xFE  # Hexadezimaler Ende-Marker
MAX_RETRIES = 3  

def speichern_json_in_datei(json_data, dateiname='config.json'):
    with open(dateiname, 'w', encoding='utf-8') as datei:
        json.dump(json_data, datei, ensure_ascii=False, indent=4)
    print(f"\nJSON-Daten wurden in '{dateiname}' gespeichert.")

def lese_nfc_tag_und_extrahiere_json_bis_marker():
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
        # UID ausgeben
        apdu_befehl_uid_abrufen = [0xFF, 0xCA, 0x00, 0x00, 0x00]
        antwort_uid_daten, status1_uid, status2_uid = verbindung.transmit(apdu_befehl_uid_abrufen)
        if (status1_uid, status2_uid) == (0x90, 0x00):
            uid_hex_string = toHexString(antwort_uid_daten)
            print(f"UID: {uid_hex_string}")
        else:
            print(f"Fehler beim Auslesen der UID: Statusbytes SW1={status1_uid:02X}, SW2={status2_uid:02X}")

        gesamter_gelesener_inhalt_bytes = b''

        print("\nSeite | HEX             | String")
        print("-------------------------------------------")

        for seitennummer in range(START_SEITE, END_SEITE + 1):
            retries = 0
            while retries < MAX_RETRIES:
                apdu_befehl_seite_lesen = [0xFF, 0xB0, 0x00, seitennummer, 0x04]
                try:
                    antwort_seite_daten, status1_seite, status2_seite = verbindung.transmit(apdu_befehl_seite_lesen)
                    if (status1_seite, status2_seite) == (0x90, 0x00):
                        gesamter_gelesener_inhalt_bytes += bytes(antwort_seite_daten)
                        hex_str = toHexString(antwort_seite_daten)
                        ascii_str = bytes(antwort_seite_daten).decode('latin1')
                        print(f"{seitennummer:3}   | {hex_str:15} | {ascii_str}")
                        break  # Erfolgreich, nächste Seite lesen
                    else:
                        print(f"{seitennummer:3}   | Fehler: SW1={status1_seite:02X}, SW2={status2_seite:02X} (Versuch {retries+1}/{MAX_RETRIES})")
                except Exception as e:
                    print(f"{seitennummer:3}   | Fehler beim Lesen: {e} (Versuch {retries+1}/{MAX_RETRIES})")
                retries += 1
                if retries < MAX_RETRIES:
                    print(f"Erneuter Versuch für Seite {seitennummer}...")
                    time.sleep(0.5)
                else:
                    print(f"Abbruch nach {MAX_RETRIES} Fehlversuchen für Seite {seitennummer}.")

        # Suche nach dem JSON-Anfang und dem Ende-Marker (0xFE)
        start_byte_index = -1
        ende_byte_index = -1
        
        # Suche nach dem ersten '{' als Anfang des JSON
        for i, byte_val in enumerate(gesamter_gelesener_inhalt_bytes):
            if byte_val == ord('{'):
                start_byte_index = i
                break
        
        # Suche nach dem Ende-Marker 0xFE nach dem JSON-Start
        if start_byte_index != -1:
            for i in range(start_byte_index, len(gesamter_gelesener_inhalt_bytes)):
                if gesamter_gelesener_inhalt_bytes[i] == JSON_ENDE_MARKER_BYTE:
                    ende_byte_index = i
                    break
        
        if start_byte_index == -1 or ende_byte_index == -1:
            print("\nKonnte keinen gültigen JSON-Block mit Ende-Marker 0xFE erkennen!")
            print("Rohdaten (zur Analyse):")
            print(gesamter_gelesener_inhalt_bytes.hex(' '))
            return

        # Extrahiere JSON-Daten (ohne den Ende-Marker)
        json_bytes = gesamter_gelesener_inhalt_bytes[start_byte_index:ende_byte_index]
        json_string = json_bytes.decode('utf-8', errors='ignore')
        
        try:
            json_data = json.loads(json_string)
            print("\n--- JSON-Datei erfolgreich extrahiert ---")
            # print(json.dumps(json_data, indent=4, ensure_ascii=False))
        except json.JSONDecodeError as e:
            print(f"\nFehler beim Parsen des JSON-Blocks: {e}")
            print("\nHEX-Dump zur Analyse:")
            print(gesamter_gelesener_inhalt_bytes.hex(' '))
    finally:
        if verbindung:
            try:
                verbindung.disconnect()
                print("\nVerbindung zum Leser getrennt.")
            except Exception:
                pass

if __name__ == "__main__":
    lese_nfc_tag_und_extrahiere_json_bis_marker()

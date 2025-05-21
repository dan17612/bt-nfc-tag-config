import time
from smartcard.System import readers
from smartcard.util import toHexString
from smartcard.Exceptions import NoCardException, CardConnectionException
import json

START_SEITE = 0x00
END_SEITE = 0xE9  
JSON_ENDE_MARKER = '}}}'

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
            apdu_befehl_seite_lesen = [0xFF, 0xB0, 0x00, seitennummer, 0x04]
            try:
                antwort_seite_daten, status1_seite, status2_seite = verbindung.transmit(apdu_befehl_seite_lesen)
                if (status1_seite, status2_seite) == (0x90, 0x00):
                    gesamter_gelesener_inhalt_bytes += bytes(antwort_seite_daten)
                    hex_str = toHexString(antwort_seite_daten)
                    # Hier wird latin1 verwendet, KEINE Ersetzung, KEINE Punkte!
                    ascii_str = bytes(antwort_seite_daten).decode('latin1')
                    print(f"{seitennummer:3}   | {hex_str:15} | {ascii_str}")
                else:
                    print(f"{seitennummer:3}   | Fehler: SW1={status1_seite:02X}, SW2={status2_seite:02X}")
            except Exception as e:
                print(f"{seitennummer:3}   | Fehler beim Lesen: {e}")

        # Gesamten Inhalt als String (latin1, robust gegen Sonderzeichen)
        raw_string = gesamter_gelesener_inhalt_bytes.decode('latin1', errors='ignore')

        # JSON-Block bis zum ersten Vorkommen von '}}}'
        start = raw_string.find('{')
        ende_marker = raw_string.find(JSON_ENDE_MARKER)
        if start == -1 or ende_marker == -1 or ende_marker < start:
            print("\nKonnte keinen gültigen JSON-Block mit Marker '}}}' erkennen!")
            print("Rohdaten (zur Analyse):")
            print(raw_string)
            return

        json_string = raw_string[start:ende_marker + len(JSON_ENDE_MARKER)]
        try:
            json_data = json.loads(json_string)
            print("\n--- JSON-Daten erfolgreich extrahiert ---")
            print(json.dumps(json_data, indent=4, ensure_ascii=False))
            print("\n--- RAW String zur Analyse:")
            print(raw_string)
        except json.JSONDecodeError as e:
            print(f"\nFehler beim Parsen des JSON-Blocks: {e}")
            print("JSON-String zur Analyse:")
            print(json_string)
            print("\nRAW String zur Analyse:")
            print(raw_string)
    finally:
        if verbindung:
            try:
                verbindung.disconnect()
                print("\nVerbindung zum Leser getrennt.")
            except Exception:
                pass

if __name__ == "__main__":
    lese_nfc_tag_und_extrahiere_json_bis_marker()

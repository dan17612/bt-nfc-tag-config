import time
from smartcard.System import readers
from smartcard.util import toHexString
from smartcard.Exceptions import NoCardException, CardConnectionException
import json

MAX_SEITEN = 255  # Sicherheitsgrenze, wird meist früher abgebrochen

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
        marker = '}}}'  # Hier kannst du auch z.B. '}}' oder eine andere Endsequenz wählen

        for seitennummer in range(MAX_SEITEN):
            apdu_befehl_seite_lesen = [0xFF, 0xB0, 0x00, seitennummer, 0x04]
            try:
                antwort_seite_daten, status1_seite, status2_seite = verbindung.transmit(apdu_befehl_seite_lesen)
                if (status1_seite, status2_seite) == (0x90, 0x00):
                    gesamter_gelesener_inhalt_bytes += bytes(antwort_seite_daten)
                    # Prüfe, ob der Marker schon im aktuellen String enthalten ist
                    current_str = gesamter_gelesener_inhalt_bytes.decode('latin1', errors='ignore')
                    if marker in current_str:
                        print(f"Marker '{marker}' gefunden, Lesevorgang wird beendet.")
                        break
            except Exception as e:
                print(f"Fehler beim Lesen der Seite {seitennummer}: {e}")

        # Suche nach erstem '{' und letztem '}'
        raw_string = gesamter_gelesener_inhalt_bytes.decode('latin1', errors='ignore')
        start = raw_string.find('{')
        end = raw_string.rfind('}') + 1
        if start == -1 or end == -1 or end <= start:
            print("Konnte keinen gültigen JSON-Block erkennen!")
            print("Rohdaten (zur Analyse):")
            print(raw_string)
            return

        json_string = raw_string[start:end]
        try:
            json_data = json.loads(json_string)
            print("\n--- JSON-Daten erfolgreich extrahiert ---")
            print(json.dumps(json_data, indent=4, ensure_ascii=False))
        except json.JSONDecodeError as e:
            print(f"Fehler beim Parsen des JSON-Blocks: {e}")
            print("JSON-String zur Analyse:")
            print(json_string)
    finally:
        if verbindung:
            try:
                verbindung.disconnect()
                print("\nVerbindung zum Leser getrennt.")
            except Exception:
                pass

if __name__ == "__main__":
    lese_nfc_tag_und_extrahiere_json_bis_marker()

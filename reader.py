import time
from smartcard.System import readers
from smartcard.util import toHexString
from smartcard.Exceptions import NoCardException
import json

START_SEITE = 0x00
END_SEITE = 0xE9
MAX_RETRIES = 3  # Maximale Anzahl an Leseversuchen pro Seite
gesamter_gelesener_inhalt_bytes = ''
raw_string = 'empty'

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

        # Gesamten Inhalt als String (latin1, robust gegen Sonderzeichen)
        raw_string = gesamter_gelesener_inhalt_bytes.decode('latin1', errors='ignore')
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

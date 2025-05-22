import time
from smartcard.System import readers
from smartcard.util import toHexString
from smartcard.Exceptions import NoCardException

START_SEITE = 0x00
END_SEITE = 0xE9
MAX_RETRIES = 3

# Neue Daten für bestimmte Seiten:
# Sie können entweder eine Liste von Bytes ODER einen 4-Zeichen-String angeben!
NEUE_DATEN = {
    33: "\":\"S",
    34: "F-77",
    35: "7000",
    36: "2\"},"
    # Beispiel: 40: "TEST",
    # Beispiel: 41: [0x41, 0x42, 0x43, 0x44],
}

def string_zu_bytes(s):
    """Wandelt einen 4-Zeichen-String in eine Liste von 4 Bytes um."""
    b = s.encode('latin1')
    if len(b) != 4:
        raise ValueError(f"String '{s}' muss genau 4 Zeichen lang sein!")
    return list(b)

def schreibe_nfc_tag_seiten_um():
    kartenleser_liste = readers()

    if not kartenleser_liste:
        print("Fehler: Kein Kartenleser gefunden.")
        return

    aktueller_kartenleser = kartenleser_liste[0]
    print(f"Verwende Leser: {aktueller_kartenleser}")

    print("\nBitte halte einen NFC-Tag an den Leser zum Schreiben...")

    while True:
        try:
            verbindung = aktueller_kartenleser.createConnection()
            verbindung.connect()
            print("NFC-Tag erkannt. Starte Schreibvorgang...")
            break
        except NoCardException:
            print("Warte auf NFC-Tag zum Schreiben...")
            time.sleep(1)
        except Exception as e:
            print(f"Fehler beim Verbinden: {e}")
            return

    # UID ausgeben
    try:
        apdu_befehl_uid_abrufen = [0xFF, 0xCA, 0x00, 0x00, 0x00]
        antwort_uid_daten, status1_uid, status2_uid = verbindung.transmit(apdu_befehl_uid_abrufen)
        if (status1_uid, status2_uid) == (0x90, 0x00):
            uid_hex_string = toHexString(antwort_uid_daten)
            print(f"UID: {uid_hex_string}")
        else:
            print(f"Fehler beim Auslesen der UID: Statusbytes SW1={status1_uid:02X}, SW2={status2_uid:02X}")
    except Exception as e:
        print(f"Fehler beim Lesen der UID: {e}")

    print("\nStarte Schreibvorgang...")
    print("\nSeite | HEX (geschrieben) | Status")
    print("-------------------------------------------")

    for seitennummer in range(START_SEITE, END_SEITE + 1):
        if seitennummer < 2:
            print(f"{seitennummer:3}   | Übersprungen      | Systemseiten werden nicht modifiziert")
            continue

        if seitennummer in NEUE_DATEN:
            daten = NEUE_DATEN[seitennummer]
            if isinstance(daten, str):
                try:
                    daten_zum_schreiben = string_zu_bytes(daten)
                except ValueError as ve:
                    print(f"{seitennummer:3}   | Fehler: {ve}")
                    continue
            elif isinstance(daten, (list, tuple)) and len(daten) == 4:
                daten_zum_schreiben = list(daten)
            else:
                print(f"{seitennummer:3}   | Fehler: Datenformat für Seite {seitennummer} ungültig!")
                continue
            print(f"{seitennummer:3}   | {toHexString(daten_zum_schreiben):15} | Neue Daten werden geschrieben", end="")
        else:
            # Für andere Seiten: Zuerst lesen, dann zurückschreiben
            apdu_befehl_seite_lesen = [0xFF, 0xB0, 0x00, seitennummer, 0x04]
            try:
                antwort_seite_daten, status1_seite, status2_seite = verbindung.transmit(apdu_befehl_seite_lesen)
                if (status1_seite, status2_seite) == (0x90, 0x00):
                    daten_zum_schreiben = antwort_seite_daten
                    print(f"{seitennummer:3}   | {toHexString(daten_zum_schreiben):15} | Unverändert übernommen", end="")
                else:
                    print(f"{seitennummer:3}   | Lesefehler: SW1={status1_seite:02X}, SW2={status2_seite:02X} | Übersprungen")
                    continue
            except Exception as e:
                print(f"{seitennummer:3}   | Lesefehler: {e} | Übersprungen")
                continue

        apdu_befehl_seite_schreiben = [0xFF, 0xD6, 0x00, seitennummer, 0x04] + daten_zum_schreiben
        retries = 0

        while retries < MAX_RETRIES:
            try:
                antwort_schreiben, status1_schreiben, status2_schreiben = verbindung.transmit(apdu_befehl_seite_schreiben)
                if (status1_schreiben, status2_schreiben) == (0x90, 0x00):
                    print(" ✓")
                    break
                else:
                    print(f" ✗ SW1={status1_schreiben:02X}, SW2={status2_schreiben:02X} (Versuch {retries+1}/{MAX_RETRIES})")
            except Exception as e:
                print(f" ✗ Fehler: {e} (Versuch {retries+1}/{MAX_RETRIES})")

            retries += 1
            if retries < MAX_RETRIES:
                print(f"   Erneuter Versuch für Seite {seitennummer}...")
                time.sleep(0.5)
            else:
                print(f"   Abbruch nach {MAX_RETRIES} Fehlversuchen für Seite {seitennummer}.")

    try:
        verbindung.disconnect()
        print("\nVerbindung zum Leser getrennt. Schreibvorgang abgeschlossen.")
    except Exception:
        pass

    

if __name__ == "__main__":
    schreibe_nfc_tag_seiten_um()

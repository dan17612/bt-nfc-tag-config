import time
from smartcard.System import readers
from smartcard.util import toHexString
from smartcard.Exceptions import NoCardException, CardConnectionException

# Konstante für die Anzahl der zu lesenden Seiten
ANZAHL_ZU_LESENDER_SEITEN = 254 # Sie können dies anpassen

def lese_nfc_tag_als_plain_text_mit_fehlerersetzung():
    """
    Wartet auf einen NFC-Tag, liest UID, ATR und eine festgelegte Anzahl von Speicherseiten.
    Gibt den gesamten Inhalt als Plain Text (ASCII-ähnlich) aus, wobei Lesefehler
    und nicht-druckbare Zeichen durch Punkte ersetzt werden.
    """
    verbindung = None
    kartenleser_liste = readers()

    if not kartenleser_liste:
        print("Fehler: Kein Kartenleser gefunden.")
        return

    print(f"Verfügbare Leser: {kartenleser_liste}")
    aktueller_kartenleser = kartenleser_liste[0]
    print(f"Verwende Leser: {aktueller_kartenleser}")

    print(f"\nBitte halten Sie einen NFC-Tag an den Leser...")
    karte_verbunden = False
    while not karte_verbunden:
        try:
            verbindung = aktueller_kartenleser.createConnection()
            verbindung.connect()
            print("NFC-Tag erkannt. Starte Auslesevorgang...")
            karte_verbunden = True
        except NoCardException:
            print("Warte auf NFC-Tag...")
            time.sleep(1)
            continue
        except CardConnectionException as verbindungs_fehler_detail:
            print(f"Verbindungsfehler zum Leser/Karte (wird erneut versucht): {verbindungs_fehler_detail}")
            time.sleep(1)
            if verbindung:
                try: verbindung.disconnect()
                except: pass
            continue
        except Exception as allgemeiner_fehler_beim_warten:
            print(f"Unerwarteter Fehler beim Warten auf die Karte: {allgemeiner_fehler_beim_warten}")
            if verbindung:
                try: verbindung.disconnect()
                except: pass
            return

    try:
        atr_daten_bytes = verbindung.getATR()
        print(f"\nATR (Hex): {toHexString(atr_daten_bytes)}")
        atr_text_darstellung = "".join([chr(b) if 32 <= b <= 126 else '.' for b in atr_daten_bytes])
        print(f"ATR (Text): {atr_text_darstellung}")

        apdu_befehl_uid_abrufen = [0xFF, 0xCA, 0x00, 0x00, 0x00]
        antwort_uid_daten, status1_uid, status2_uid = verbindung.transmit(apdu_befehl_uid_abrufen)
        
        if (status1_uid, status2_uid) == (0x90, 0x00):
            uid_hex_string = toHexString(antwort_uid_daten)
            print(f"UID: {uid_hex_string}")
        else:
            print(f"Fehler beim Auslesen der UID: Statusbytes SW1={status1_uid:02X}, SW2={status2_uid:02X}")

        print(f"\nLese Speicherinhalt von {ANZAHL_ZU_LESENDER_SEITEN} Seiten...")
        
        gesamter_plain_text_output = [] # Liste für die Zeichen des Fließtextes

        for seitennummer in range(ANZAHL_ZU_LESENDER_SEITEN):
            # APDU-Befehl zum Lesen einer Speicherseite (4 Bytes)
            apdu_befehl_seite_lesen = [0xFF, 0xB0, 0x00, seitennummer, 0x04]
            
            try:
                antwort_seite_daten, status1_seite, status2_seite = verbindung.transmit(apdu_befehl_seite_lesen)
                
                if (status1_seite, status2_seite) == (0x90, 0x00):
                    # Erfolgreich gelesen, konvertiere jedes Byte zu einem Zeichen (oder '.')
                    for byte_wert in antwort_seite_daten:
                        if 32 <= byte_wert <= 126: # Druckbares ASCII-Zeichen
                            gesamter_plain_text_output.append(chr(byte_wert))
                        else: # Nicht-druckbares Zeichen oder Fehler
                            gesamter_plain_text_output.append('.')
                else:
                    # Fehler beim Lesen dieser Seite, füge 4 Punkte für die 4 Bytes dieser Seite hinzu
                    # (oder die Anzahl der Bytes, die versucht wurden zu lesen, hier 0x04)
                    print(f"Info: Fehler beim Lesen von Seite {seitennummer:03d} (SW1={status1_seite:02X} SW2={status2_seite:02X}). Ersetze durch Punkte.")
                    for _ in range(4): # 4 Bytes pro Seite wurden versucht zu lesen
                        gesamter_plain_text_output.append('.')
            except Exception as uebertragungsfehler_seite:
                # Kritischer Fehler bei der Übertragung für diese Seite
                print(f"Info: Kritischer Übertragungsfehler bei Seite {seitennummer:03d} ({uebertragungsfehler_seite}). Ersetze durch Punkte.")
                for _ in range(4): # 4 Bytes pro Seite wurden versucht zu lesen
                    gesamter_plain_text_output.append('.')
        
        print(f"Auslesen von {ANZAHL_ZU_LESENDER_SEITEN} Seiten abgeschlossen (oder versucht).")

        # --- Gesamten Inhalt als Plain Text ausgeben ---
        if gesamter_plain_text_output:
            print("\n--- Gesamter Speicherinhalt als Plain Text (Fehler als '.') ---")
            finaler_text = "".join(gesamter_plain_text_output)
            
            # Für bessere Lesbarkeit bei sehr langen Texten, könnte man Zeilenumbrüche einfügen:
            breite = 80 # Anzahl Zeichen pro Zeile
            for i in range(0, len(finaler_text), breite):
                print(finaler_text[i:i+breite])
            print("-------------------------------------------------------------")
        else:
            print("\nEs konnten keine Daten ausgelesen werden, um sie als Plain Text darzustellen.")

    except Exception as haupt_lesefehler:
        print(f"Ein Fehler ist während des Auslesens der Tag-Daten aufgetreten: {haupt_lesefehler}")
        import traceback
        traceback.print_exc()
    finally:
        if verbindung:
            try:
                verbindung.disconnect()
                print("\nVerbindung zum Leser getrennt.")
            except Exception as fehler_beim_trennen:
                print(f"Fehler beim Trennen der Verbindung: {fehler_beim_trennen}")

if __name__ == "__main__":
    lese_nfc_tag_als_plain_text_mit_fehlerersetzung()

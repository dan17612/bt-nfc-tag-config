import time
from smartcard.System import readers
from smartcard.util import toHexString
from smartcard.Exceptions import NoCardException

START_SEITE = 0x00
END_SEITE = 0xE9
MAX_RETRIES = 3
# num = 1
# dyn_seite2 = 7000

# # Dem Zaeller muss man an die Seiten anpassen 
# Falls man es nutzen möchte Auskomentiren und anpassen unten nach //// suchen und auch auskomentieren
# def dynamische_seite_zaeller():
#     global num, dyn_seite2
#     if num <= 9:
#         dyn_seite1 = str(num) + "\"},"
#         num += 1
#     else:
#         num = 0
#         dyn_seite2 += 1
#         dyn_seite1 = str(num) + "\"},"
    
#     # NEUE_DATEN Dictionary aktualisieren
#     NEUE_DATEN[36] = dyn_seite1
#     NEUE_DATEN[35] = str(dyn_seite2)
#     return dyn_seite1, dyn_seite2

# Neue Daten für bestimmte Seiten:
# Sie können entweder eine Liste von Bytes ODER einen 4-Zeichen-String angeben!
# Seite | HEX             | String
# --------------------------------
#  33   | 22 3A 22 53     | ":"S
#  34   | 46 2D 37 37     | F-77
#  35   | 37 30 30 30     | 7000
#  36   | 32 22 7D 2C     | 2"},
# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
# Die Daten sollen andere Seiten nicht verschieben sonnst muss der Header angepasst werden und halt der Padding!!!
# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! 
NEUE_DATEN = {
    3: [0xE1, 0x10, 0xEF, 0x00],
    4: [0x03, 0xFF, 0x02, 0xA5],
    5: [0xC2, 0x06, 0x00, 0x00],
    6: [0x02, 0x99, 0x72, 0x2F],
    7: [0x6A, 0x73, 0x6F, 0x6E],
    8: "{\"ti",
    9: "tle\"",
    10: ":\"3.",
    11: "0.2\"",
    12: ",\"In",
    13: "fo\":",
    14: "\"BLE",
    15: "_FW\"",
    16: ",\"FW",
    17: "_RS\"",
    18: ":\"rc",
    19: "2\",\"",
    20: "prop",
    21: "erti",
    22: "es\":",
    23: "{\"Na",
    24: "me\":",
    25: "{\"in",
    26: "it\":",
    27: "\"BPU",
    28: "CK_I",
    29: "D_15",
    30: "CHAR",
    31: "\",\"v",
    32: "alue",
    33: "\":\"S",
    34: "F-77",
    35: "7000",  
    36: "1\"},",
    37: "\"EN\"",
    38: ":{\"i",
    39: "nit\"",
    40: ":0,\"",
    41: "valu",
    42: "e\":1",
    43: "},\"P",
    44: "ower",
    45: "\":{\"",
    46: "item",
    47: "s\":[",
    48: "-40,",
    49: "-20,",
    50: "-16,",
    51: "-12,",
    52: "-8,-",
    53: "4,0,",
    54: "3,4]",
    55: ",\"in",
    56: "it\":",
    57: "0,\"v",
    58: "alue",
    59: "\":4}",
    60: ",\"Fo",
    61: "rmat",
    62: "\":{\"",
    63: "item",
    64: "s\":[",
    65: "\"Id\"",
    66: ",\"iB",
    67: "eaco",
    68: "n\",\"",
    69: "Eddy",
    70: "ston",
    71: "e\"],",
    72: "\"ini",
    73: "t\":\"",
    74: "Id\",",
    75: "\"val",
    76: "ue\":",
    77: "\"Edd",
    78: "ysto",
    79: "ne\"}",
    80: ",\"Ad",
    81: "vRec",
    82: "\":{\"",
    83: "mini",
    84: "mum\"",
    85: ":0.1",
    86: "0,\"m",
    87: "axim",
    88: "um\":",
    89: "10.0",
    90: "0,\"i",
    91: "nit\"",
    92: ":3.0",
    93: "0,\"v",
    94: "alue",
    95: "\":10",
    96: ".00}",
    97: ",\"Mf",
    98: "rDat",
    99: "a\":{",
    100: "\"ini",
    101: "t\":0",
    102: ",\"va",
    103: "lue\"",
    104: ":1},",
    105: "\"Mfr",
    106: "ID\":",
    107: "{\"in",
    108: "it\":",
    109: "\"010",
    110: "2030",
    111: "4050",
    112: "6\",\"",
    113: "valu",
    114: "e\":\"",
    115: "0000",
    116: "0000",
    117: "0000",
    118: "\"},\"",
    119: "Batt",
    120: "Volt",
    121: "SR\":",
    122: "{\"in",
    123: "it\":",
    124: "0,\"v",
    125: "alue",
    126: "\":1}",
    127: ",\"UU",
    128: "ID\":",
    129: "{\"in",
    130: "it\":",
    131: "\"010",
    132: "2030",
    133: "4050",
    134: "6070",
    135: "8090",
    136: "A0B0",
    137: "C0D0",
    138: "E0F1",
    139: "0\",\"",
    140: "valu",
    141: "e\":\"",
    142: "0102",
    143: "0304",
    144: "0506",
    145: "0708",
    146: "090A",
    147: "0B0C",
    148: "0D0E",
    149: "0F10",
    150: "\"},\"",
    151: "Majo",
    152: "r\":{",
    153: "\"ini",
    154: "t\":\"",
    155: "020B",
    156: "\",\"v",
    157: "alue",
    158: "\":\"0",
    159: "20B\"",
    160: "},\"M",
    161: "inor",
    162: "\":{\"",
    163: "init",
    164: "\":\"0",
    165: "10A\"",
    166: ",\"va",
    167: "lue\"",
    168: ":\"01",
    169: "0A\"}",
    170: ",\"NI",
    171: "D\":{",
    172: "\"ini",
    173: "t\":\"",
    174: "0102",
    175: "0304",
    176: "0506",
    177: "0708",
    178: "090A",
    179: "\",\"v",
    180: "alue",
    181: "\":\"0",
    182: "1020",
    183: "3040",
    184: "5060",
    185: "7080",
    186: "90A\"",
    187: "},\"B",
    188: "ID\":",
    189: "{\"in",
    190: "it\":",
    191: "\"010",
    192: "2030",
    193: "40A0",
    194: "B\",\"",
    195: "valu",
    196: "e\":\"",
    197: "0102",
    198: "0304",
    199: "0A0B",
    200: "\"}}}",
    201: "þBBB",
    202: [0x42, 0x42, 0x42, 0x42],
    203: [0x42, 0x42, 0x42, 0x42],
    204: [0x44, 0x22, 0x3A, 0x7B],
    205: [0x22, 0x69, 0x6E, 0x69],
    206: [0x74, 0x22, 0x3A, 0x22],
    207: [0x30, 0x31, 0x30, 0x32],
    208: [0x30, 0x33, 0x30, 0x34],
    209: [0x30, 0x41, 0x30, 0x42],
    210: [0x22, 0x2C, 0x22, 0x76],
    211: [0x61, 0x6C, 0x75, 0x65],
    212: [0x22, 0x3A, 0x22, 0x30],
    213: [0x31, 0x30, 0x32, 0x30],
    214: [0x33, 0x30, 0x34, 0x30],
    215: [0x41, 0x30, 0x42, 0x22],
    216: [0x7D, 0x2C, 0x22, 0x4C],
    217: [0x6F, 0x67, 0x45, 0x4E],
    218: [0x22, 0x3A, 0x7B, 0x22],
    219: [0x69, 0x6E, 0x69, 0x74],
    220: [0x22, 0x3A, 0x30, 0x2C],
    221: [0x22, 0x76, 0x61, 0x6C],
    222: [0x75, 0x65, 0x22, 0x3A],
    223: [0x30, 0x7D, 0x2C, 0x22],
    227: [0x00, 0x00, 0x00, 0xFF],
    232: [0x09, 0x32, 0xF8, 0x48],
    233: [0x08, 0x01, 0x00, 0x00],
}

def string_zu_bytes(s):
    """Wandelt einen 4-Zeichen-String in eine Liste von 4 Bytes um."""
    b = s.encode('latin1')
    if len(b) != 4:
        raise ValueError(f"String '{s}' muss genau 4 Zeichen lang sein!")
    return list(b)

def schreibe_nfc_tag_seiten_um():
    # WICHTIG: Dynamische Daten VOR dem Schreibvorgang aktualisieren
    # //// FALLS BENOETIGT AUSKOMENTIREN  dynamische_seite_zaeller()
    
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

def main_loop():
    """Hauptschleife mit Tagzähler und Warteschleife"""
    tag_zaehler = 1
    print("=== NFC Tag Writer mit automatischer Warteschleife ===")
    print("Drücken Sie Strg+C zum Beenden\n")
    
    try:
        while True:
            print(f"\n{'='*60}")
            print(f"WARTE AUF TAG: {tag_zaehler}")
            print(f"{'='*60}")
            
            # Tag schreiben
            schreibe_nfc_tag_seiten_um()
            
            print(f"\n✓ Tag {tag_zaehler} erfolgreich geschrieben!")
            print("\nEntferne den Tag und lege den nächsten Tag auf...")
            
            # Warten bis der aktuelle Tag entfernt wird
            kartenleser_liste = readers()
            if kartenleser_liste:
                aktueller_kartenleser = kartenleser_liste[0]
                
                # Warten bis Tag entfernt wird
                while True:
                    try:
                        verbindung = aktueller_kartenleser.createConnection()
                        verbindung.connect()
                        verbindung.disconnect()
                        time.sleep(0.5)  # Tag ist noch da
                    except NoCardException:
                        print("Tag entfernt. Bereit für nächsten Tag...")
                        break
                    except Exception:
                        break
            
            tag_zaehler += 1
            
            time.sleep(1)  # Kurze Pause zwischen den Tags
            
    except KeyboardInterrupt:
        print(f"\n\nProgramm beendet. Insgesamt {tag_zaehler - 1} Tags geschrieben.")
    except Exception as e:
        print(f"\nFehler in der Hauptschleife: {e}")

if __name__ == "__main__":
    main_loop()

#!/usr/bin/env python3
import re
import argparse
from smartcard.System import readers
from smartcard.util import toHexString # Nützlich für die Fehlersuche oder erweiterte Datenanzeige
import sys

# ACS ACR122U NFC Reader
GET_UID_COMMAND = [0xFF, 0xCA, 0x00, 0x00, 0x00]

reader_connection = None
waiting_for_beacon = 1

def initialize_reader(reader_idx=0):
    global reader_connection
    try:
        r = readers()
        if not r:
            print("Fehler: Keine Lesegeräte verfügbar!")
            sys.exit(1)
        print("Verfügbare Lesegeräte:", r)

        if not (0 <= reader_idx < len(r)):
            print(f"Fehler: Ungültiger Reader Index {reader_idx}. Verwende Standard-Reader 0.")
            reader_idx = 0
        
        selected_reader = r[reader_idx]
        print("Verwende Lesegerät:", selected_reader)
        
        reader_connection = selected_reader.createConnection()
        reader_connection.connect()
        reader_connection.transmit(GET_UID_COMMAND) # Initiales "Aufwecken"
        return True
    except Exception as e:
        print(f"Fehler bei der Initialisierung des Lesegeräts: {e}")
        sys.exit(1)

def bytes_to_hex_string(byte_list):
    if byte_list is None:
        return ""
    return "".join(format(val, '02X') for val in byte_list)

def hex_string_to_text(hex_str, encoding='utf-8', errors='replace'):
    """Konvertiert einen Hex-String in einen Text-String."""
    if not hex_str:
        return ""
    try:
        if len(hex_str) % 2 != 0:
            # Ungerade Hex-Strings können nicht direkt konvertiert werden.
            # Man könnte hier einen Fehler werfen oder den String ignorieren/anpassen.
            # Für die seitenweise Anzeige ist es vielleicht besser, eine Warnung auszugeben
            # und zu versuchen, den Rest zu dekodieren, oder einen leeren String zurückzugeben.
            print(f"Warnung: Hex-String '{hex_str}' für Textkonvertierung hat ungerade Länge.")
            # Option: return "" oder hex_str = hex_str[:-1] (letztes Zeichen entfernen)
            # Hier wird er belassen, was zu einem Fehler in fromhex führen kann
            
        byte_data = bytes.fromhex(hex_str)
        # Null-Bytes am Ende entfernen, die oft als Füllmaterial dienen
        cleaned_byte_data = byte_data.rstrip(b'\x00')
        return cleaned_byte_data.decode(encoding, errors=errors)
    except ValueError:
        # Dieser Fehler tritt auf, wenn hex_str keine gültige Hex-Sequenz ist (z.B. ungerade Länge, ungültige Zeichen)
        # print(f"Hinweis: '{hex_str}' ist kein gültiger Hex-String für die direkte Textkonvertierung oder enthält ungültige Zeichen.")
        return f"[Nicht dekodierbar: {hex_str}]" # Zeigt an, dass die Konvertierung fehlschlug
    except Exception as e:
        print(f"Fehler beim Dekodieren des Hex-Strings '{hex_str}' zu Text: {e}")
        return f"[Dekodierungsfehler: {hex_str}]"

def read_tag_page(page_number, current_encoding='utf-8'):
    """Liest 4 Bytes von einer spezifizierten Seite und gibt Hex-Daten und Text zurück."""
    global reader_connection
    if reader_connection is None:
        print("Fehler: Lesegerät nicht initialisiert.")
        return None, None # Gibt jetzt ein Tupel zurück

    read_page_command = [0xFF, 0xB0, 0x00, int(page_number), 0x04]
    
    loop = True
    while loop:
        try:
            # data_uid, sw1_uid, sw2_uid = reader_connection.transmit(GET_UID_COMMAND) # Ggf. für jede Interaktion
            # if not (sw1_uid == 0x90 and sw2_uid == 0x00):
            # print(f"Warnung: Get UID Befehl nicht erfolgreich für Seite {page_number}: SW1={sw1_uid:02X}, SW2={sw2_uid:02X}")

            data, sw1, sw2 = reader_connection.transmit(read_page_command)
            
            if sw1 == 0x90 and sw2 == 0x00:
                hex_data = bytes_to_hex_string(data)
                text_data = hex_string_to_text(hex_data, encoding=current_encoding)
                # Die Hex-Rohdaten direkt hier ausgeben
                print(f"Seite {page_number} [Roh-Hex]: {hex_data}")
                return hex_data, text_data # Gibt Hex und Text zurück
            elif sw1 == 0x6A and sw2 == 0x82:
                 print(f"Info: Seite {page_number} nicht gefunden (oder außerhalb des Bereichs). SW1={sw1:02X}, SW2={sw2:02X}")
                 return "", "" # Leere Strings für nicht gefundene Seiten
            else:
                print(f"Fehler beim Lesen von Seite {page_number}: SW1={sw1:02X}, SW2={sw2:02X}")
                if waiting_for_beacon == 1:
                    print("Warte auf Tag...")
                    try:
                        reader_connection.connect()
                        reader_connection.transmit(GET_UID_COMMAND)
                    except Exception as conn_e:
                        print(f"Fehler beim Wiederverbinden: {conn_e}. Warte kurz.")
                        import time
                        time.sleep(0.5)
                    continue
                else:
                    return None, None
        except Exception as e:
            print(f"Ausnahme beim Lesen von Seite {page_number}: {e}")
            if waiting_for_beacon == 1:
                print("Verbindung möglicherweise verloren. Versuche erneut...")
                try:
                    reader_connection.connect()
                    reader_connection.transmit(GET_UID_COMMAND)
                except:
                    pass
                continue
            else:
                loop = False
                return None, None
        break # Verlässt die while-Schleife nach erfolgreichem Lesen oder Fehler ohne Warteoption

def write_tag_page(page_number, hex_value_string):
    global reader_connection
    if reader_connection is None:
        print("Fehler: Lesegerät nicht initialisiert.")
        return False

    if not isinstance(hex_value_string, str) or len(hex_value_string) != 8 or not all(c in '0123456789abcdefABCDEF' for c in hex_value_string):
        print("Fehler: Ungültiger Hex-Wert. Muss ein 8-stelliger Hex-String sein (4 Bytes).")
        return False

    bytes_to_write = [int(hex_value_string[i:i+2], 16) for i in range(0, 8, 2)]
    write_page_command = [0xFF, 0xD6, 0x00, int(page_number), 0x04] + bytes_to_write
    
    loop = True
    while loop:
        try:
            data, sw1, sw2 = reader_connection.transmit(write_page_command)
            
            if sw1 == 0x90 and sw2 == 0x00:
                print(f"Erfolgreich '{hex_value_string}' auf Seite {page_number} geschrieben.")
                return True
            else:
                print(f"Fehler beim Schreiben auf Seite {page_number}: SW1={sw1:02X}, SW2={sw2:02X}")
                if waiting_for_beacon == 1:
                    print("Warte auf Tag...")
                    try:
                        reader_connection.connect()
                        reader_connection.transmit(GET_UID_COMMAND)
                    except: pass
                    continue
                else:
                    return False
        except Exception as e:
            print(f"Ausnahme beim Schreiben auf Seite {page_number}: {e}")
            if waiting_for_beacon == 1:
                print("Verbindung möglicherweise verloren. Versuche erneut...")
                try:
                    reader_connection.connect()
                    reader_connection.transmit(GET_UID_COMMAND)
                except:
                    pass
                continue
            else:
                loop = False
                return False
        break

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Lese oder schreibe NFC Tag Seiten mit ACR122U.')
    parser.add_argument('--reader', type=int, default=0, metavar='ID', help='Index des zu verwendenden Lesegeräts (Standard: 0)')
    parser.add_argument('--wait', type=int, choices=[0, 1], default=1, metavar='0|1', help='Warte auf Tag, wenn nicht präsent (0=Nein, 1=Ja, Standard: 1)')
    parser.add_argument('--encoding', type=str, default='utf-8', help="Textkodierung für die Ausgabe der gelesenen Daten (z.B. 'utf-8', 'ascii', 'latin-1', Standard: 'utf-8')")
    
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--read', nargs='+', metavar='SEITE', help='Zu lesende Seitennummern. Kann ein Bereich (z.B. 4-7) oder eine Liste von Seiten sein (z.B. 4 5 8).')
    group.add_argument('--write', nargs=2, metavar=('SEITE', 'HEXDATEN'), help='Seitennummer und 4-Byte Hex-Wert (8 Zeichen, z.B. 00112233) zum Schreiben.')

    args = parser.parse_args()

    waiting_for_beacon = args.wait
    
    if not initialize_reader(args.reader):
        sys.exit(1)

    all_read_hex_data_collected = [] # Liste zum Sammeln der Hex-Daten für die Gesamtausgabe

    try:
        if args.write:
            page_to_write = int(args.write[0])
            data_to_write = args.write[1]
            if not (0 <= page_to_write <= 255):
                raise argparse.ArgumentTypeError(f"Seitennummer {page_to_write} ist außerhalb des gültigen Bereichs.")
            write_tag_page(page_to_write, data_to_write)
        
        elif args.read:
            pages_to_read_list = []
            for page_arg in args.read:
                if "-" in page_arg:
                    try:
                        start_page, end_page = map(int, page_arg.split("-"))
                        if start_page > end_page:
                             raise ValueError("Startseite muss kleiner oder gleich Endseite sein.")
                        if not (0 <= start_page <= 255 and 0 <= end_page <= 255): # Typische Seitengröße für Ultralight, anpassen falls nötig
                             raise ValueError("Seitennummern im Bereich außerhalb des gültigen Bereichs.")
                        pages_to_read_list.extend(range(start_page, end_page + 1))
                    except ValueError as e:
                        raise argparse.ArgumentTypeError(f"Ungültiger Seitenbereich '{page_arg}': {e}")
                else:
                    try:
                        page_num = int(page_arg)
                        if not (0 <= page_num <= 255):
                            raise ValueError("Seitennummer außerhalb des gültigen Bereichs.")
                        pages_to_read_list.append(page_num)
                    except ValueError:
                        raise argparse.ArgumentTypeError(f"Ungültige Seitennummer '{page_arg}'.")
            
            unique_pages = sorted(list(set(pages_to_read_list)))
            print(f"\nLese Seiten: {unique_pages} mit Kodierung '{args.encoding}'\n" + "-"*30)

            for page in unique_pages:
                hex_data_from_page, text_data_from_page = read_tag_page(page, current_encoding=args.encoding)
                
                if hex_data_from_page is not None: # Überprüft, ob der Leseversuch nicht komplett fehlschlug
                    # Die Hex-Daten wurden bereits in read_tag_page ausgegeben
                    # Gebe hier den Text der einzelnen Seite aus
                    if text_data_from_page: # Nur ausgeben, wenn Text vorhanden ist
                        printable_page_text = ''.join(filter(lambda x: x.isprintable() or x in '\n\r\t', text_data_from_page))
                        print(f"Seite {page} [Text]:    '{printable_page_text}'")
                    else:
                        # Falls text_data_from_page leer ist (z.B. nur Nullen oder nicht dekodierbar und "" zurückgegeben)
                        print(f"Seite {page} [Text]:    (Kein Text oder nur Nullen)")
                    
                    all_read_hex_data_collected.append(hex_data_from_page) # Sammle Hex-Daten für die Gesamtausgabe
                else:
                    # Fehler beim Lesen dieser Seite, wurde schon in read_tag_page behandelt
                    print(f"Seite {page}: Konnte nicht gelesen werden.")
                print("-" * 10) # Trennlinie zwischen den Seiten
            
            if all_read_hex_data_collected:
                full_hex_string = "".join(all_read_hex_data_collected)
                print(f"\n--- Gelesene Hex-Daten (gesamt) ---\n{full_hex_string}")
                
                combined_text_from_tag = hex_string_to_text(full_hex_string, encoding=args.encoding)
                print(f"\n--- Gesamter gelesener Text ({args.encoding}) ---")
                printable_combined_text = ''.join(filter(lambda x: x.isprintable() or x in '\n\r\t', combined_text_from_tag))
                print(printable_combined_text)
                if not printable_combined_text.strip(): # strip() entfernt Whitespace für die Prüfung
                     print("(Kein druckbarer Text im gesamten Datensatz gefunden oder Daten waren leer/nur Nullen)")

    except argparse.ArgumentTypeError as e:
        print(f"Fehler bei Kommandozeilenargumenten: {e}")
    except Exception as e:
        print(f"Ein unerwarteter Fehler ist aufgetreten: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if reader_connection:
            try:
                pass # reader_connection.disconnect()
            except Exception as e:
                print(f"Fehler beim Trennen der Verbindung: {e}")

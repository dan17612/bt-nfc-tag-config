"""
NFC Lesegerät Ein-/Ausschalt Tool für BLE Beacon Konfiguration
============================================================

Dieses Skript ermöglicht es, das NFC-Lesegerät über die Konsole zu steuern:
- Lesegerät ein-/ausschalten
- Status abfragen
- Power-Management für den Pip-Zon des NFC-Lesegeräts

Autor: GitHub Copilot
Datum: 10. Oktober 2025
"""

import time
import sys
import subprocess
import platform
from smartcard.System import readers
from smartcard.Exceptions import NoCardException, CardConnectionException

class NFCLeserKontrolle:
    """Klasse zur Steuerung des NFC-Lesegeräts"""
    
    def __init__(self):
        self.ist_verbunden = False
        self.aktueller_leser = None
        self.verbindung = None
        self.pip_ton_status = True  # Standard: Ton ist an
        
    def zeige_verfuegbare_leser(self):
        """Zeigt alle verfügbaren NFC-Lesegeräte an"""
        try:
            leser_liste = readers()
            if not leser_liste:
                print("❌ Keine NFC-Lesegeräte gefunden!")
                return False
            
            print("📱 Verfügbare NFC-Lesegeräte:")
            
            # Suche nach ACR122 Lesegerät (bevorzugt für Buzzer-Steuerung)
            acr122_leser = None
            for i, leser in enumerate(leser_liste):
                leser_name = str(leser)
                print(f"  {i+1}. {leser_name}")
                
                # Prüfe auf ACR122 Lesegerät
                if 'ACR122' in leser_name or 'ACS' in leser_name:
                    acr122_leser = leser
                    print(f"     ✅ ACR122 erkannt - unterstützt Buzzer-Steuerung")
                elif 'Windows Hello' in leser_name:
                    print(f"     ⚠️  Windows Hello - keine Buzzer-Steuerung")
            
            # Verwende ACR122 falls verfügbar, sonst den ersten Leser
            if acr122_leser:
                self.aktueller_leser = acr122_leser
                print(f"🎯 Verwende: {acr122_leser}")
            else:
                self.aktueller_leser = leser_liste[0]
                print(f"🎯 Verwende: {leser_liste[0]} (Buzzer-Steuerung möglicherweise nicht unterstützt)")
            
            return True
            
        except Exception as e:
            print(f"❌ Fehler beim Suchen der Lesegeräte: {e}")
            return False
    
    def leser_einschalten(self):
        """Schaltet das NFC-Lesegerät ein / aktiviert es"""
        print("🔄 Aktiviere NFC-Lesegerät...")
        
        if not self.zeige_verfuegbare_leser():
            return False
        
        try:
            # Versuche eine Verbindung zum Lesegerät herzustellen
            print(f"🔌 Verbinde mit: {self.aktueller_leser}")
            
            # Test-Verbindung um sicherzustellen, dass das Gerät aktiv ist
            test_verbindung = self.aktueller_leser.createConnection()
            
            # Teste die Verbindung ohne Karte
            try:
                test_verbindung.connect()
                print("✅ NFC-Lesegerät ist aktiv und bereit!")
                test_verbindung.disconnect()
                self.ist_verbunden = True
                return True
                
            except NoCardException:
                # Das ist normal - keine Karte auf dem Leser
                print("✅ NFC-Lesegerät ist aktiv und bereit!")
                self.ist_verbunden = True
                return True
                
        except Exception as e:
            print(f"❌ Fehler beim Aktivieren des Lesegeräts: {e}")
            return False
    
    def leser_ausschalten(self):
        """Schaltet das NFC-Lesegerät aus / deaktiviert es"""
        print("🔄 Deaktiviere NFC-Lesegerät...")
        
        try:
            if self.verbindung:
                self.verbindung.disconnect()
                self.verbindung = None
            
            # Auf Windows: Versuche den PC/SC Service zu stoppen/starten
            if platform.system() == "Windows":
                print("🔄 Stoppe PC/SC Smart Card Service...")
                try:
                    subprocess.run(["net", "stop", "SCardSvr"], 
                                 capture_output=True, text=True, check=False)
                    time.sleep(2)
                    
                    print("✅ NFC-Lesegerät deaktiviert!")
                    self.ist_verbunden = False
                    return True
                    
                except Exception as e:
                    print(f"⚠️  Service-Stop nicht möglich: {e}")
                    print("✅ Verbindung getrennt (Lesegerät bleibt aktiv)")
                    self.ist_verbunden = False
                    return True
            else:
                print("✅ Verbindung getrennt (Lesegerät bleibt aktiv)")
                self.ist_verbunden = False
                return True
                
        except Exception as e:
            print(f"❌ Fehler beim Deaktivieren: {e}")
            return False
    
    def leser_neu_starten(self):
        """Startet das NFC-Lesegerät neu"""
        print("🔄 Starte NFC-Lesegerät neu...")
        
        if platform.system() == "Windows":
            try:
                # Service stoppen
                print("⏹️  Stoppe PC/SC Service...")
                subprocess.run(["net", "stop", "SCardSvr"], 
                             capture_output=True, text=True, check=False)
                time.sleep(3)
                
                # Service starten
                print("▶️  Starte PC/SC Service...")
                result = subprocess.run(["net", "start", "SCardSvr"], 
                                      capture_output=True, text=True, check=False)
                time.sleep(2)
                
                if result.returncode == 0:
                    print("✅ NFC-Lesegerät erfolgreich neu gestartet!")
                    return self.leser_einschalten()
                else:
                    print("⚠️  Service-Neustart nicht erfolgreich")
                    return self.leser_einschalten()
                    
            except Exception as e:
                print(f"❌ Fehler beim Neustart: {e}")
                return False
        else:
            print("ℹ️  Neustart auf diesem System nicht unterstützt")
            return self.leser_einschalten()
    
    def status_pruefen(self):
        """Prüft den Status des NFC-Lesegeräts"""
        print("🔍 Prüfe NFC-Lesegerät Status...")
        
        try:
            leser_liste = readers()
            if not leser_liste:
                print("❌ Status: Keine Lesegeräte gefunden")
                return False
            
            print(f"📊 Status-Report:")
            print(f"   Lesegeräte gefunden: {len(leser_liste)}")
            
            for i, leser in enumerate(leser_liste):
                print(f"   Lesegerät {i+1}: {leser}")
                
                try:
                    # Teste Verbindung
                    test_verbindung = leser.createConnection()
                    test_verbindung.connect()
                    print(f"   ✅ Status: Aktiv und bereit")
                    
                    # Prüfe auf Karte
                    try:
                        apdu_befehl = [0xFF, 0xCA, 0x00, 0x00, 0x00]
                        antwort, sw1, sw2 = test_verbindung.transmit(apdu_befehl)
                        if (sw1, sw2) == (0x90, 0x00):
                            uid_hex = " ".join([f"{b:02X}" for b in antwort])
                            print(f"   📇 Karte erkannt: UID = {uid_hex}")
                        else:
                            print(f"   📇 Karte: Fehler beim Lesen (SW1={sw1:02X}, SW2={sw2:02X})")
                    except Exception:
                        pass
                    
                    test_verbindung.disconnect()
                    
                except NoCardException:
                    print(f"   ✅ Status: Aktiv (keine Karte)")
                except Exception as e:
                    print(f"   ❌ Status: Fehler - {e}")
            
            return True
            
        except Exception as e:
            print(f"❌ Fehler bei Statusprüfung: {e}")
            return False
    
    def pip_ton_ausschalten(self):
        """Schaltet den Pip-Ton des NFC-Lesegeräts aus"""
        print("🔇 Schalte Pip-Ton aus...")
        
        if not self.zeige_verfuegbare_leser():
            return False
        
        # Versuche mehrere Verbindungsarten
        for verbindungs_versuch in range(3):
            try:
                print(f"🔄 Verbindungsversuch {verbindungs_versuch + 1}/3...")
                verbindung = self.aktueller_leser.createConnection()
                
                # Verschiedene Verbindungsprotokolle versuchen
                protokolle = ['T0', 'T1', '*']
                
                for protokoll in protokolle:
                    try:
                        if protokoll == '*':
                            verbindung.connect()
                        else:
                            verbindung.connect(protocol=protokoll)
                        print(f"✅ Verbindung hergestellt (Protokoll: {protokoll})")
                        break
                    except Exception as e:
                        print(f"⚠️  Protokoll {protokoll} fehlgeschlagen: {str(e)[:50]}...")
                        continue
                else:
                    # Wenn alle Protokolle fehlschlagen
                    continue
                
                # ACR122U spezifische Befehle zum Ausschalten des Buzzers
                buzzer_befehle = [
                    [0xFF, 0x00, 0x52, 0x00, 0x00],  # Standard Buzzer-Aus
                    [0xFF, 0x00, 0x40, 0x0F, 0x04, 0x01, 0x01, 0x00, 0x00],  # Alternative 1
                    [0xFF, 0x00, 0x40, 0x0E, 0x04, 0x01, 0x01, 0x00, 0x00]   # Alternative 2
                ]
                
                for i, befehl in enumerate(buzzer_befehle):
                    try:
                        print(f"🔧 Versuche Befehl {i + 1}/3...")
                        antwort, sw1, sw2 = verbindung.transmit(befehl)
                        
                        if (sw1, sw2) == (0x90, 0x00):
                            print("✅ Pip-Ton erfolgreich ausgeschaltet!")
                            self.pip_ton_status = False
                            verbindung.disconnect()
                            return True
                        else:
                            print(f"⚠️  Befehl {i + 1}: SW1={sw1:02X}, SW2={sw2:02X}")
                            
                    except Exception as e:
                        print(f"⚠️  Befehl {i + 1} fehlgeschlagen: {str(e)[:50]}...")
                        continue
                
                # Wenn alle Befehle fehlschlagen, versuche Disconnect/Reconnect
                try:
                    verbindung.disconnect()
                    time.sleep(1)
                except:
                    pass
                    
            except Exception as e:
                print(f"⚠️  Verbindungsversuch {verbindungs_versuch + 1}: {str(e)[:50]}...")
                time.sleep(1)
                continue
        
        print("❌ Alle Verbindungsversuche fehlgeschlagen")
        return False
    
    def pip_ton_einschalten(self):
        """Schaltet den Pip-Ton des NFC-Lesegeräts ein"""
        print("🔊 Schalte Pip-Ton ein...")
        
        if not self.zeige_verfuegbare_leser():
            return False
        
        # Versuche mehrere Verbindungsarten
        for verbindungs_versuch in range(3):
            try:
                print(f"🔄 Verbindungsversuch {verbindungs_versuch + 1}/3...")
                verbindung = self.aktueller_leser.createConnection()
                
                # Verschiedene Verbindungsprotokolle versuchen
                protokolle = ['T0', 'T1', '*']
                
                for protokoll in protokolle:
                    try:
                        if protokoll == '*':
                            verbindung.connect()
                        else:
                            verbindung.connect(protocol=protokoll)
                        print(f"✅ Verbindung hergestellt (Protokoll: {protokoll})")
                        break
                    except Exception as e:
                        print(f"⚠️  Protokoll {protokoll} fehlgeschlagen: {str(e)[:50]}...")
                        continue
                else:
                    # Wenn alle Protokolle fehlschlagen
                    continue
                
                # ACR122U spezifische Befehle zum Einschalten des Buzzers
                buzzer_befehle = [
                    [0xFF, 0x00, 0x52, 0xFF, 0x00],  # Standard Buzzer-Ein
                    [0xFF, 0x00, 0x40, 0x0F, 0x04, 0x01, 0x01, 0x03, 0x03],  # Alternative 1
                    [0xFF, 0x00, 0x40, 0x0E, 0x04, 0x01, 0x01, 0x01, 0x01]   # Alternative 2
                ]
                
                for i, befehl in enumerate(buzzer_befehle):
                    try:
                        print(f"🔧 Versuche Befehl {i + 1}/3...")
                        antwort, sw1, sw2 = verbindung.transmit(befehl)
                        
                        if (sw1, sw2) == (0x90, 0x00):
                            print("✅ Pip-Ton erfolgreich eingeschaltet!")
                            self.pip_ton_status = True
                            verbindung.disconnect()
                            return True
                        else:
                            print(f"⚠️  Befehl {i + 1}: SW1={sw1:02X}, SW2={sw2:02X}")
                            
                    except Exception as e:
                        print(f"⚠️  Befehl {i + 1} fehlgeschlagen: {str(e)[:50]}...")
                        continue
                
                # Wenn alle Befehle fehlschlagen, versuche Disconnect/Reconnect
                try:
                    verbindung.disconnect()
                    time.sleep(1)
                except:
                    pass
                    
            except Exception as e:
                print(f"⚠️  Verbindungsversuch {verbindungs_versuch + 1}: {str(e)[:50]}...")
                time.sleep(1)
                continue
        
        print("❌ Alle Verbindungsversuche fehlgeschlagen")
        return False
    
    def _alternative_buzzer_steuerung(self, verbindung, einschalten):
        """Alternative Methoden zur Buzzer-Steuerung"""
        try:
            # Alternative 1: Direct Control Command
            if einschalten:
                befehl = [0xFF, 0x00, 0x40, 0x0F, 0x04, 0x01, 0x01, 0x03, 0x03]  # Buzzer ein
                aktion = "eingeschaltet"
            else:
                befehl = [0xFF, 0x00, 0x40, 0x0F, 0x04, 0x01, 0x01, 0x00, 0x00]  # Buzzer aus
                aktion = "ausgeschaltet"
            
            antwort, sw1, sw2 = verbindung.transmit(befehl)
            if (sw1, sw2) == (0x90, 0x00):
                print(f"✅ Pip-Ton erfolgreich {aktion} (Alternative Methode)!")
                self.pip_ton_status = einschalten
                verbindung.disconnect()
                return True
            
            # Alternative 2: LED und Buzzer Control
            if einschalten:
                befehl2 = [0xFF, 0x00, 0x40, 0x0E, 0x04, 0x01, 0x01, 0x01, 0x01]
            else:
                befehl2 = [0xFF, 0x00, 0x40, 0x0E, 0x04, 0x01, 0x01, 0x00, 0x00]
                
            antwort2, sw1_2, sw2_2 = verbindung.transmit(befehl2)
            if (sw1_2, sw2_2) == (0x90, 0x00):
                print(f"✅ Audio-Feedback erfolgreich {aktion} (LED-Control)!")
                self.pip_ton_status = einschalten
                verbindung.disconnect()
                return True
            
            print(f"⚠️  Alternative Methoden nicht erfolgreich")
            print(f"    Versuch 1: SW1={sw1:02X}, SW2={sw2:02X}")
            print(f"    Versuch 2: SW1={sw1_2:02X}, SW2={sw2_2:02X}")
            verbindung.disconnect()
            return False
            
        except Exception as e:
            print(f"❌ Alternative Buzzer-Steuerung fehlgeschlagen: {e}")
            try:
                verbindung.disconnect()
            except:
                pass
            return False
    
    def pip_ton_status_pruefen(self):
        """Prüft den aktuellen Status des Pip-Tons"""
        print("🔍 Prüfe Pip-Ton Status...")
        
        try:
            status_text = "EIN 🔊" if self.pip_ton_status else "AUS 🔇"
            print(f"📊 Pip-Ton Status: {status_text}")
            
            # Versuche Hardware-Status abzufragen (falls möglich)
            if self.zeige_verfuegbare_leser():
                try:
                    verbindung = self.aktueller_leser.createConnection()
                    verbindung.connect()
                    
                    # Versuche Gerätestatus abzufragen
                    status_befehl = [0xFF, 0x00, 0x48, 0x00, 0x00]
                    antwort, sw1, sw2 = verbindung.transmit(status_befehl)
                    
                    if (sw1, sw2) == (0x90, 0x00) and len(antwort) > 0:
                        print(f"🔧 Hardware-Status: {' '.join([f'{b:02X}' for b in antwort])}")
                    
                    verbindung.disconnect()
                    
                except Exception:
                    pass  # Hardware-Status nicht verfügbar
            
            return True
            
        except Exception as e:
            print(f"❌ Fehler bei Pip-Ton Statusprüfung: {e}")
            return False
    
    def power_management_info(self):
        """Zeigt Informationen zum Power-Management"""
        print("\n💡 Power-Management Informationen:")
        print("="*50)
        print("🔋 NFC-Lesegerät Energieverwaltung:")
        print("   • 'ein'        - Aktiviert das Lesegerät")
        print("   • 'aus'        - Deaktiviert das Lesegerät")  
        print("   • 'neustart'   - Startet das Lesegerät neu")
        print("   • 'status'     - Zeigt aktuellen Status")
        print("\n🔊 Audio-Steuerung (Pip-Ton):")
        print("   • 'tonaus'     - Schaltet den Pip-Ton aus")
        print("   • 'tonein'     - Schaltet den Pip-Ton ein")
        print("   • 'tonstatus'  - Zeigt Pip-Ton Status")
        print("\n⚠️  Hinweise:")
        print("   • Auf Windows wird der PC/SC Service gesteuert")
        print("   • Administrative Rechte könnten erforderlich sein")
        print("   • Das Lesegerät verbraucht wenig Strom im Standby")
        print("   • Pip-Ton Steuerung funktioniert mit ACR122U Lesern")
        print("   • Ton-Einstellungen bleiben bis zum Neustart erhalten")

def zeige_hilfe():
    """Zeigt die Hilfeinformationen an"""
    print("\n🔧 NFC-Lesegerät Kontrolle - Befehle:")
    print("="*50)
    print("📱 Gerät-Steuerung:")
    print("   ein        - NFC-Lesegerät einschalten/aktivieren")
    print("   aus        - NFC-Lesegerät ausschalten/deaktivieren") 
    print("   neustart   - NFC-Lesegerät neu starten")
    print("   status     - Status des Lesegeräts prüfen")
    print("\n🔊 Audio-Steuerung (Pip-Ton):")
    print("   tonaus     - Pip-Ton ausschalten 🔇")
    print("   tonein     - Pip-Ton einschalten 🔊")  
    print("   tonstatus  - Pip-Ton Status prüfen")
    print("\n📋 Informationen:")
    print("   info       - Power-Management Informationen")
    print("   hilfe      - Diese Hilfe anzeigen")
    print("   exit       - Programm beenden")
    print("\nBeispiele:")
    print("   tonausmachen.py tonaus     # Pip-Ton ausschalten")
    print("   tonausmachen.py tonein     # Pip-Ton einschalten")
    print("   tonausmachen.py status     # Geräte-Status prüfen")
    print("="*50)

def main():
    """Hauptfunktion des Programms"""
    nfc_kontrolle = NFCLeserKontrolle()
    
    print("� NFC-Lesegerät Pip-Ton Steuerung")
    print("="*40)
    
    # Einfache Benutzerabfrage
    print("\nWas möchten Sie tun?")
    print("1. Pip-Ton ausschalten 🔇")
    print("2. Pip-Ton einschalten 🔊")
    
    while True:
        try:
            wahl = input("\nBitte wählen Sie (1 oder 2): ").strip()
            
            if wahl == "1":
                befehl = "tonaus"
                break
            elif wahl == "2":
                befehl = "tonein"
                break
            else:
                print("❌ Ungültige Eingabe! Bitte 1 oder 2 eingeben.")
                
        except KeyboardInterrupt:
            print("\n\n👋 Programm durch Benutzer beendet.")
            sys.exit(0)
    
    # Befehl ausführen
    if befehl == "tonaus":
        print("\n🔄 Schalte Pip-Ton aus...")
        erfolg = nfc_kontrolle.pip_ton_ausschalten()
        if erfolg:
            print("\n✅ Pip-Ton wurde erfolgreich ausgeschaltet! 🔇")
        else:
            print("\n❌ Fehler beim Ausschalten des Pip-Tons!")
            
    elif befehl == "tonein":
        print("\n🔄 Schalte Pip-Ton ein...")
        erfolg = nfc_kontrolle.pip_ton_einschalten()
        if erfolg:
            print("\n✅ Pip-Ton wurde erfolgreich eingeschaltet! 🔊")
        else:
            print("\n❌ Fehler beim Einschalten des Pip-Tons!")
    
    # Programm beenden
    input("\n📝 Drücken Sie Enter zum Beenden...")
    print("👋 Programm beendet.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Programm durch Benutzer beendet.")
    except Exception as e:
        print(f"\n❌ Unerwarteter Fehler: {e}")
        sys.exit(1)

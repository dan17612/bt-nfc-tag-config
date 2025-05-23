# NFC Tag Reader/Writer System - README

## Übersicht

Dieses System besteht aus drei Python-Scripts für das Auslesen und Beschreiben von NFC-Tags:

1. **Reader Script** - Liest NFC-Tags aus und extrahiert Konfigurationen von einem Tag
2. **Writer Script** - Beschreibt NFC-Tags mit neuen Konfigurationen

## Systemanforderungen

## Hardware

* NFC-Kartenleser (z.B. ACR122U)
* NFC-Tags (NTAG213/215/216 oder kompatibel)

## Software

* Python 3.7 oder höher
* Erforderliche Python-Pakete:

  `pip install pyscard`

## Installation

1. **Python-Pakete installieren: `pip install pyscard`**
2. **NFC-Reader anschließen** und sicherstellen, dass er vom System erkannt wird
3. **Scripts herunterladen** und in einem Ordner speichern


## Benutzen

1. Wenn die Installation fertig ist, haben Sie reader.py und writer.py in dem Ordner.
2. Sie haben einen NFC-Kartenleser angeschlossen und starten reader.py.
3. Es wird eine TXT-Datei erstellt.
4. Mit dieser passt man dann writer.py an, um die Daten auf die nächsten Tags zu kopieren.
5. Erst wenn writer.py angepasst wurde, wird es gestartet und es können die Tags nach den Aufforderungen der Konsole nacheinander aufgelegt werden.

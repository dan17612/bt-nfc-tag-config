# NFC Tag Configuration Tool for BLE Beacons

A Python-based toolkit for reading, writing, and managing BLE beacon configurations stored on NFC tags (NTAG213/215/216). Built for batch-configuring Bluetooth beacons via an ACR122U NFC reader.

## Features

- **Read** NFC tags and extract embedded JSON beacon configurations
- **Write** modified configurations back to tags with automatic sequential naming (e.g. `SF-7770001`, `SF-7770002`, ...)
- **Batch mode** for programming multiple tags in sequence
- **Debug reader** with full hex/ASCII memory dump and JSON extraction
- **Name list extraction** from multiple tags for inventory tracking
- **Reader control** (power management, buzzer on/off)

## Hardware Requirements

- NFC card reader (ACR122U or compatible)
- NFC tags (NTAG213 / NTAG215 / NTAG216)

## Installation

```bash
# Python 3.7+
pip install pyscard
```

Optional dependencies for advanced functionality:

```bash
pip install nfcpy ndeflib pyserial libusb1
```

## Usage

### 1. Read a Tag

```bash
python reader.py
```

- Select single or continuous reading mode
- A `.txt` file is generated with the tag's data as an editable Python dictionary (named by tag UID)

### 2. Write Tags

```bash
python writer.py
```

- Paste the `NEUE_DATEN` dictionary from the reader output into `writer.py`
- Optionally enable dynamic naming for sequential beacon IDs
- Present tags one by one — the writer programs each tag and increments the counter

### 3. Debug / Inspect

```bash
python debug_reader.py
```

- Displays all NFC tag memory pages in hex and ASCII
- Extracts and saves the embedded JSON configuration to `config.json`

### 4. Extract Beacon Names

```bash
python namelist.py
```

- Reads beacon names from multiple tags
- Saves a timestamped list to `nfc_namen_liste_*.txt`

### 5. Reader Control

```bash
python tonausmachen.py
```

- Toggle reader buzzer and power state

## Beacon Configuration

The tags store a JSON configuration with the following BLE beacon properties:

| Property   | Description                        | Example Value      |
|------------|------------------------------------|--------------------|
| `Name`     | Beacon identifier (max 15 chars)   | `SF-7770001`       |
| `Power`    | TX power level (dBm)               | `4` (-40 to 4)     |
| `Format`   | Broadcast format                   | `Eddystone`        |
| `AdvRec`   | Advertisement interval (seconds)   | `10.0` (0.1 - 10)  |
| `UUID`     | iBeacon UUID                       | `01020304...0F10`  |
| `Major`    | iBeacon Major                      | `020B`             |
| `Minor`    | iBeacon Minor                      | `010A`             |
| `NID`      | Eddystone Namespace ID             | `01020304...090A`  |
| `BID`      | Eddystone Beacon ID                | `010203040A0B`     |

## NFC Memory Layout

| Pages    | Content                              |
|----------|--------------------------------------|
| 0 - 2    | Manufacturer data (read-only)        |
| 3 - 7    | NDEF message header                  |
| 8 - 201  | JSON configuration (UTF-8 encoded)   |
| 202+     | Footer / additional data             |

End marker: `0xFE` byte after JSON payload.

## Project Structure

```
reader.py           # Read tags and generate editable config files
writer.py           # Write configurations to tags (batch mode)
debug_reader.py     # Full memory dump and JSON extraction
namelist.py         # Extract beacon names from multiple tags
tonausmachen.py     # NFC reader power/buzzer control
config.json         # Example beacon configuration template
```

## Tech Stack

- **pyscard** - Smartcard/NFC reader communication via APDU commands
- **nfcpy** / **ndeflib** - NFC Data Exchange Format handling
- Python 3.7+

# BT-Beacons-Konfiguration mit Python ändern. (In Entwicklung)

Folgendes Passiert wenn man namen ändert

| Vorher                                                         | Danach                                                           |
| -------------------------------------------------------------- | ---------------------------------------------------------------- |
| ![1747835517437](image/readme/1747835517437.png)<br />15 Zeichen | ![1747835900233](image/readme/1747835900233.png) <br />9 Zeichen  |

Die HEX Zahlen haben sich um 6 verkleinert

![1747835562327](image/readme/1747835562327.png)

der Speicher Block hat sich wegen dem um 6 Zeichen kürzeren namen um 2 Speicher böcke verschoben.

![1747835660126](image/readme/1747835660126.png)

Unsere Dummy Speicher Blöcke wurden genutzt: Es ist um 6 byte verschoben

![1747836011905](image/readme/1747836011905.png)

| Vorher                                         | Nacher                                         |
| ---------------------------------------------- | ---------------------------------------------- |
| ![1747895480935](image/readme/1747895480935.png) | ![1747895495084](image/readme/1747895495084.png) |

2 HEX Zahlen haben sich um ein Wert erhöht

![1747895725213](image/readme/1747895725213.png)

Unser wert in der Config hat alles verschoben
![1747895788058](image/readme/1747895788058.png)

Dummy  Speicher  Blöcke haben sich auch um eine stelle gekürzt

![1747895935188](image/readme/1747895935188.png)

## License

MIT

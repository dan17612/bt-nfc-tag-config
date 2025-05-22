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

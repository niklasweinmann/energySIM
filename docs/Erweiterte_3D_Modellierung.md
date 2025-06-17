# Erweiterte 3D-Gebäudemodellierung für energyOS

## Überblick

Die erweiterte 3D-Gebäudemodellierung ermöglicht eine detaillierte Planung und Visualisierung von Gebäuden mit allen relevanten Bauteilen für eine präzise Wärmepumpenauslegung nach deutschen Normen.

## 🎯 Hauptfunktionen

### Detaillierte Bauteile
- **Wände** mit Schichtaufbau und U-Werten nach DIN 4108
- **Fenster** mit Verglasungstypen, U- und g-Werten
- **Türen** mit verschiedenen Materialien und Dämmwerten
- **Dachflächen** mit PV-Potenzialanalyse
- **Bodenplatten** mit Erdkopplungsberechnung
- **Heizkörper** optimiert für Wärmepumpen
- **Wärmebrücken** nach DIN 4108 Beiblatt 2
- **Verschattungselemente** für solare Gewinne

### Normgerechte Berechnungen
- **U-Wert-Berechnung** nach DIN EN ISO 6946
- **Wärmeverluste** nach DIN EN 12831
- **Materialien** nach DIN 4108-4
- **Standards**: GEG 2020, EnEV 2016, KfW 55/40, Passivhaus
- **Wärmepumpenauslegung** mit COP-Berechnung

### 3D-Visualisierung
- **WebGL-basierte Darstellung** mit Three.js
- **Farbkodierung** nach thermischen Eigenschaften
- **Interaktive Objektauswahl** mit Detailinformationen
- **Wireframe-Modus** für technische Ansichten
- **Echtzeit-Navigation** und Kamerasteuerung

## 🚀 Installation und Start

### Voraussetzungen
```bash
pip install Flask Flask-CORS numpy
```

### Erweiterte 3D-Anwendung starten
```bash
python run_building_editor.py
```
→ Öffnet automatisch http://localhost:8080

### Demo der Funktionen
```bash
python demo_building_editor.py
```

## 📱 Benutzeroberfläche

### Tab: Gebäude
- **Dimensionen**: Breite, Tiefe, Höhe, Geschosse
- **Energiestandard**: GEG, EnEV, KfW, Passivhaus
- **Zusammenfassung**: Wärmeverluste, U-Werte, Heizwärmebedarf

### Tab: Bauteile
Kollapsible Bereiche für:
- **Wände**: Mit Schichteditor und U-Wert-Berechnung
- **Fenster**: Verglasungstypen und thermische Eigenschaften
- **Türen**: Materialien und Dämmwerte
- **Dach**: Neigung, Dämmung, PV-Eignung
- **Boden**: Bodentyp, Erdkopplung, Fußbodenheizung

### Tab: Heizung
- **Heizsystem**: Heizkörper, Fußbodenheizung, kombiniert
- **Vorlauf-/Rücklauftemperatur**: Optimiert für Wärmepumpen
- **Heizkörperverwaltung**: Position und Leistung
- **Wärmepumpenauslegung**: Automatische Berechnung

### Tab: Analyse
- **Simulation**: Vollständige Gebäudesimulation
- **Ergebnisse**: Heizwärmebedarf, Effizienzklasse
- **Export/Import**: Gebäudedaten speichern/laden

## 🔧 Komponenten-Editor

### Wand bearbeiten
- **Name**: Bezeichnung der Wand
- **Fläche/Dimensionen**: Automatische Berechnung
- **Orientierung**: N, NE, E, SE, S, SW, W, NW
- **Wandtyp**: Außenwand/Innenwand
- **Schichtaufbau**: Materialauswahl und Dicken
- **U-Wert**: Automatische Berechnung

### Fenster bearbeiten
- **Abmessungen**: Breite × Höhe
- **Thermische Werte**: U-Wert, g-Wert
- **Verglasungstyp**: 2-fach, 3-fach
- **Eigenschaften**: Öffenbar, Rahmenanteil
- **Verschattung**: Sonnenschutz berücksichtigen

### Heizkörper bearbeiten
- **Heizleistung**: In Watt bei Normtemperaturen
- **Abmessungen**: Breite × Höhe × Tiefe
- **Typ**: Plattenheizkörper, Konvektor, Fußbodenheizung
- **Betriebstemperaturen**: Vorlauf/Rücklauf
- **Regelung**: Thermostatventil, Smart Control

## 🏗️ Standard-Materialien

### Mauerwerk
- **Mauerziegel**: λ = 0.79 W/(m·K)
- **Stahlbeton**: λ = 2.1 W/(m·K)
- **Kalksandstein**: λ = 0.99 W/(m·K)

### Dämmstoffe
- **EPS-Dämmung**: λ = 0.035 W/(m·K)
- **Mineralwolle**: λ = 0.035 W/(m·K)
- **PIR-Dämmung**: λ = 0.022 W/(m·K)
- **PUR-Dämmung**: λ = 0.024 W/(m·K)

### Putze und Estriche
- **Innenputz**: λ = 0.87 W/(m·K)
- **Außenputz**: λ = 0.87 W/(m·K)
- **Estrich**: λ = 1.4 W/(m·K)

## 📏 Standard-Konstruktionen

### Außenwand GEG (U ≤ 0.28 W/(m²·K))
1. Innenputz: 15 mm
2. Mauerziegel: 175 mm
3. EPS-Dämmung: 140 mm
4. Außenputz: 20 mm

### Außenwand Passivhaus (U ≤ 0.15 W/(m²·K))
1. Innenputz: 15 mm
2. Mauerziegel: 175 mm
3. Mineralwolle: 240 mm
4. Außenputz: 20 mm

### Dach GEG (U ≤ 0.20 W/(m²·K))
1. Innenverkleidung: 15 mm
2. Konstruktionsholz: 40 mm
3. Mineralwolle: 200 mm
4. Dachziegel: 25 mm

### Bodenplatte GEG (U ≤ 0.30 W/(m²·K))
1. Estrich: 60 mm
2. EPS-Dämmung: 140 mm
3. Stahlbeton: 200 mm

## 🔥 Wärmepumpenauslegung

### Heizlastberechnung
```
Gesamtheizlast = Transmissionsverluste + Lüftungsverluste

Transmissionsverluste = Σ(Ai × Ui × ΔT)
- Ai: Bauteilfläche [m²]
- Ui: U-Wert [W/(m²·K)]
- ΔT: Temperaturdifferenz [K]

Lüftungsverluste = V × n × ρ × cp × ΔT / 3600
- V: Gebäudevolumen [m³]
- n: Luftwechselrate [1/h]
- ρ: Luftdichte [kg/m³]
- cp: spez. Wärmekapazität [J/(kg·K)]
```

### Wärmepumpe dimensionieren
- **Auslegungstemperatur**: -12°C (Standort Deutschland)
- **Sicherheitsfaktor**: 1.2
- **COP-Schätzung**: Abhängig von Temperaturdifferenz
- **Empfohlene Leistung**: Gerundet auf nächste kW

### Optimierung für Wärmepumpen
- **Niedrige Vorlauftemperaturen**: 35-55°C
- **Große Heizflächen**: Für bessere Effizienz
- **Gute Gebäudedämmung**: Reduziert Heizlast
- **Kontinuierlicher Betrieb**: Vermeidet Takten

## 🌐 3D-Navigation

### Maussteuerung
- **Linke Maustaste + Ziehen**: Kamera drehen
- **Rechte Maustaste + Ziehen**: Kamera verschieben
- **Mausrad**: Zoomen
- **Objekt anklicken**: Auswählen und Informationen anzeigen

### Tastaturkürzel
- **R**: Kamera zurücksetzen
- **W**: Wireframe-Modus umschalten
- **ESC**: Objektauswahl aufheben
- **DELETE**: Ausgewähltes Objekt löschen

### Objektinformationen
Beim Anklicken eines Objekts werden angezeigt:
- **Grunddaten**: Name, Typ, Fläche
- **Thermische Eigenschaften**: U-Wert, g-Wert
- **Konstruktionsdetails**: Material, Schichten
- **Betriebsparameter**: Temperaturen, Leistung

## 📊 Analyse und Optimierung

### Energieeffizienzbewertung
- **U-Wert-Durchschnitt**: Bewertung der Gebäudehülle
- **Wärmeverluste**: Aufschlüsselung nach Bauteilen
- **Normerfüllung**: Vergleich mit GEG, KfW, Passivhaus
- **Verbesserungsvorschläge**: Automatische Empfehlungen

### Wärmebrückenanalyse
- **Lineare Wärmebrücken**: ψ-Werte nach DIN 4108
- **Geometrische Wärmebrücken**: Ecken, Vorsprünge
- **Materialwärmebrücken**: Metallische Verbindungen
- **Lösungsvorschläge**: Dämmmaßnahmen

### PV-Potenzialanalyse
- **Dacheignung**: Neigung, Orientierung
- **Verschattungsanalyse**: Umgebung berücksichtigen
- **Flächenberechnung**: Verfügbare Modulfläche
- **Ertragsprognose**: kWh/Jahr basierend auf Standort

## 🔌 API-Endpunkte

### Gebäudedaten
```
GET  /api/building/load              # Vollständige Gebäudedaten
POST /api/building/components/{type} # Komponente hinzufügen
PUT  /api/building/components/{id}   # Komponente aktualisieren
DEL  /api/building/components/{id}   # Komponente löschen
```

### Materialien und Standards
```
GET /api/materials/standard     # Standard-Materialien
GET /api/constructions/standard # Standard-Konstruktionen
```

### Berechnungen
```
POST /api/simulation/heat-pump-sizing # Wärmepumpenauslegung
POST /api/simulation/run              # Vollständige Simulation
```

## 🛠️ Entwicklung und Erweiterung

### Modulstruktur
```
src/core/
├── detailed_building_components.py  # Erweiterte Bauteile
├── building.py                      # Basis-Gebäudemodell
└── standards.py                     # Normen und Berechnungen

src/ui/
├── web_app.py                       # Flask-App
├── templates/building_editor.html   # Web-Interface
└── static/js/building_editor.js     # 3D-Visualisierung
```

### Neue Komponenten hinzufügen
1. **Datenklasse** in `detailed_building_components.py`
2. **3D-Darstellung** in `building_editor.js`
3. **UI-Integration** in `building_editor.html`
4. **API-Endpunkt** in `web_app.py`

### Neue Materialien
```python
materials["neues_material"] = Material(
    name="Neues Material",
    lambda_value=0.040,  # W/(m·K)
    density=100,         # kg/m³
    specific_heat=1000,  # J/(kg·K)
    vapor_diffusion=50.0 # μ-Wert
)
```

### Neue Standards
```python
constructions["neue_konstruktion"] = [
    Layer(materials["material1"], 0.020),
    Layer(materials["material2"], 0.150),
    Layer(materials["material3"], 0.015)
]
```

## 🎯 Anwendungsfälle

### Neubau-Planung
1. **Gebäude modellieren**: Alle Bauteile detailliert erfassen
2. **Normen prüfen**: GEG, KfW, Passivhaus-Anforderungen
3. **Heizlast berechnen**: Für Wärmepumpenauslegung
4. **Optimieren**: U-Werte und Konstruktionen verbessern
5. **Visualisieren**: 3D-Darstellung für Presentation

### Sanierung-Planung
1. **Bestand erfassen**: Vorhandene Bauteile dokumentieren
2. **Schwachstellen identifizieren**: Wärmebrücken, hohe U-Werte
3. **Maßnahmen planen**: Dämmung, Fenstertausch, Heizung
4. **Wirtschaftlichkeit**: Kosten-Nutzen-Analyse
5. **Förderung**: KfW-Konformität prüfen

### Wärmepumpen-Auslegung
1. **Heizlast ermitteln**: Nach DIN EN 12831
2. **Temperaturniveau**: Vorlauftemperatur optimieren
3. **Heizkörper dimensionieren**: Große Heizflächen
4. **COP maximieren**: Betriebsoptimierung
5. **Monitoring**: Verbrauchskontrolle

## 📚 Literatur und Normen

### Deutsche Normen
- **DIN 4108**: Wärmeschutz und Energie-Einsparung in Gebäuden
- **DIN EN ISO 6946**: Berechnung des Wärmedurchgangskoeffizienten
- **DIN EN 12831**: Heizungsanlagen - Verfahren zur Berechnung der Norm-Heizlast
- **DIN EN 673**: Bestimmung des Wärmedurchgangskoeffizienten von Verglasungen

### Gesetze und Verordnungen
- **GEG 2020**: Gebäudeenergiegesetz
- **EnEV 2016**: Energieeinsparverordnung
- **KfW-Effizienzhäuser**: 55, 40, 40 Plus
- **Passivhaus-Standard**: PHI-Kriterien

### Technische Regeln
- **DIN V 18599**: Energetische Bewertung von Gebäuden
- **DIN 4108 Beiblatt 2**: Wärmebrücken
- **VDI 6007**: Berechnung des instationären thermischen Verhaltens

## 🎉 Fazit

Das erweiterte 3D-Gebäudemodellierungssystem bietet eine vollständige Lösung für die detaillierte Planung und Optimierung von Gebäuden nach deutschen Standards. Mit der Integration aller relevanten Bauteile, normgerechten Berechnungen und intuitiver 3D-Visualisierung können Planer und Ingenieure effizient arbeiten und optimale Ergebnisse für Wärmepumpenanlagen erzielen.

Die modulare Architektur ermöglicht einfache Erweiterungen und Anpassungen für spezifische Anforderungen, während die webbasierte Benutzeroberfläche plattformunabhängigen Zugriff bietet.

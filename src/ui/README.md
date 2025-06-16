# energyOS 3D Building Editor

## Überblick

Die 3D-Benutzeroberfläche ermöglicht es, Gebäude interaktiv zu visualisieren und zu bearbeiten. Sie basiert auf modernen Web-Technologien und integriert sich nahtlos in das bestehende energyOS-System.

## Funktionen

### 3D-Visualisierung
- **Interaktive 3D-Darstellung** des Gebäudes mit Wänden, Fenstern, Dach und Boden
- **Echtzeit-Rendering** mit Three.js
- **Kamerasteuerung** (Orbit, Zoom, Pan)
- **Wireframe-Modus** für technische Ansichten
- **Objektauswahl** durch Mausklick

### Gebäude-Editor
- **Gebäudedimensionen** interaktiv ändern (Breite, Tiefe, Höhe)
- **Wandeigenschaften** bearbeiten (U-Werte, Materialien)
- **Fenster hinzufügen/entfernen** mit verschiedenen Orientierungen
- **Dachparameter** anpassen (Neigung, Materialien)
- **Energiestandards** auswählen (Standard, EnEV, Passivhaus, KfW)

### Simulation
- **Direkte Integration** mit der energyOS-Simulation
- **Echtzeit-Energiekennwerte** (Wärmebedarf, COP, PV-Ertrag)
- **Visuelle Indikatoren** für Energieeffizienz
- **Parametrische Studien** möglich

## Installation

### Abhängigkeiten installieren

```bash
# Zusätzliche Web-UI Abhängigkeiten
pip install Flask Flask-CORS
```

### Starten der 3D-UI

```bash
# Aus dem Projektverzeichnis
python run_3d_editor.py
```

Der Editor öffnet sich automatisch im Browser unter `http://localhost:8080`.

## Bedienung

### 3D-Navigation
- **Linke Maustaste + Ziehen**: Kamera drehen
- **Rechte Maustaste + Ziehen**: Kamera verschieben
- **Mausrad**: Zoomen
- **Objekte anklicken**: Auswählen und bearbeiten

### Gebäude bearbeiten
1. **Dimensionen ändern**: Eingabefelder in der Seitenleiste
2. **Wände bearbeiten**: Wandtyp und Orientierung auswählen
3. **Fenster hinzufügen**: Position und Größe festlegen
4. **Dach anpassen**: Neigung und Material wählen

### Simulation ausführen
1. **Standort eingeben**: Breitengrad und Längengrad
2. **Zeitraum wählen**: Start- und Enddatum
3. **Simulation starten**: Button klicken
4. **Ergebnisse analysieren**: Energiekennwerte in Echtzeit

## Technische Details

### Architektur
```
┌─────────────────┐    HTTP/JSON    ┌──────────────────┐
│   Web Browser   │ ←──────────────→ │   Flask Server   │
│   (Three.js)    │                 │   (Python)       │
└─────────────────┘                 └──────────────────┘
                                             │
                                             ▼
                                    ┌──────────────────┐
                                    │   energyOS Core  │
                                    │   (Simulation)   │
                                    └──────────────────┘
```

### Dateienstruktur
```
src/ui/
├── web_app.py              # Flask-Server
├── templates/
│   └── index.html          # Haupt-HTML-Template
├── static/
│   └── building3d.js       # 3D-JavaScript-Klasse
└── README.md               # Diese Dokumentation
```

### API-Endpunkte

#### `GET /api/building/load`
Lädt die aktuellen Gebäudedaten als 3D-Format.

**Response:**
```json
{
  "geometry": {
    "walls": [...],
    "windows": [...],
    "roof": {...},
    "floor": {...},
    "dimensions": {...}
  },
  "energy_data": {...},
  "properties": {...}
}
```

#### `POST /api/building/update`
Aktualisiert das Gebäude basierend auf 3D-Editor-Änderungen.

#### `POST /api/simulation/run`
Führt eine Energiesimulation aus.

**Request:**
```json
{
  "latitude": 52.52,
  "longitude": 13.41,
  "start_date": "2025-01-01",
  "end_date": "2025-01-07"
}
```

**Response:**
```json
{
  "status": "success",
  "results": {
    "heat_demand_kWh": 150.5,
    "cop_average": 3.8,
    "pv_production_kWh": 85.2,
    ...
  }
}
```

## Erweiterungsmöglichkeiten

### Geplante Features
- **Materialeditor** für detaillierte Bauteilspezifikationen
- **PV-Modul-Platzierung** auf dem Dach
- **Landschaftsgestaltung** und Umgebung
- **Export/Import** von Gebäudedaten
- **Collaboration-Features** für Teams
- **VR/AR-Unterstützung**

### Integration mit CAD-Software
- **IFC-Import/Export** für Kompatibilität mit BIM-Software
- **DXF-Support** für 2D-Pläne
- **GBXML-Export** für andere Simulationstools

### Performance-Optimierungen
- **Level-of-Detail (LOD)** für große Gebäude
- **Instancing** für wiederholende Elemente
- **Web Workers** für Berechnungen im Hintergrund

## Troubleshooting

### Häufige Probleme

**3D-Ansicht lädt nicht:**
- Browser-Kompatibilität prüfen (WebGL erforderlich)
- Browser-Konsole auf JavaScript-Fehler überprüfen

**Simulation startet nicht:**
- Internetverbindung für Wetterdaten erforderlich
- Backend-Logs in der Terminal-Ausgabe prüfen

**Performance-Probleme:**
- Hardware-Beschleunigung im Browser aktivieren
- Weniger detaillierte Gebäudemodelle verwenden

### Browser-Kompatibilität
- **Chrome/Chromium**: ✅ Vollständig unterstützt
- **Firefox**: ✅ Vollständig unterstützt
- **Safari**: ✅ Mit Einschränkungen
- **Edge**: ✅ Vollständig unterstützt

## Beitragen

Das 3D-Interface ist offen für Beiträge:

1. **Frontend-Entwicklung**: Three.js, HTML/CSS/JavaScript
2. **Backend-Integration**: Flask, Python, energyOS-APIs
3. **UX/UI-Design**: Benutzerfreundlichkeit und Design
4. **Testing**: Cross-Browser-Tests, Performance-Tests

## Lizenz

Wie das Hauptprojekt energyOS steht auch die 3D-Benutzeroberfläche unter der entsprechenden Open-Source-Lizenz.

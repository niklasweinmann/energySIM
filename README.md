# EnergySIM 
## Residential Energy System Simulation & Optimization

Ein intelligentes System zur Modellierung und Simulation von Gebäude-Energiesystemen mit Machine Learning Unterstützung.

## Funktionen

- Heizlastberechnung
- Simulation von:
  - Wärmepumpen
  - Photovoltaik-Anlagen
  - Solarthermie-Systemen
  - Klimaanlagen
- Integration von Wetterdaten
- Automatische Beschaffung von Modul- und Wechselrichterdaten
- Maschinelles Lernen zur Optimierung
- Benutzerfreundliche Oberfläche

## Projektstruktur

```
energyOS/
├── data/                   # Daten und Datenbankdateien
│   ├── weather/           # Wetterdaten
│   └── components/        # Komponenten-Datenbank
├── docs/                  # Dokumentation
├── src/                   # Quellcode
│   ├── core/             # Kernfunktionalität
│   ├── models/           # ML-Modelle und Simulationsmodelle
│   ├── data_handlers/    # Datenverarbeitung
│   ├── simulation/       # Simulationsmodule
│   └── ui/              # Benutzeroberfläche
└── tests/                # Tests
```

## Installation

### Mit Conda:

1. Conda-Umgebung erstellen:
```bash
conda create -n energyos python=3.11
conda activate energyos
```

2. Erforderliche Pakete installieren:
```bash
conda install numpy pandas tensorflow scikit-learn dash plotly pytest black isort
```

## Entwicklung

Dieses Projekt befindet sich in aktiver Entwicklung.

### Git Workflow

Wir verwenden einen Feature-Branch-Workflow:

1. `main`: Produktionscode
2. `development`: Aktive Entwicklung
3. Feature Branches: `feature/name-der-funktion`

Workflow für neue Features:
1. Von `development` auschecken: `git checkout -b feature/name`
2. Änderungen committen
3. Pull Request in `development` erstellen
4. Code Review und Tests
5. Nach erfolgreichen Tests: Merge in `development`

### Code-Standards

- Wir verwenden Black für Code-Formatierung
- isort für Import-Sortierung
- Type Hints für bessere Code-Qualität
- Docstrings im Google-Style
- Tests mit pytest

### Pre-commit Hooks

Installiere pre-commit hooks:
```bash
pip install pre-commit
pre-commit install
```

## Tests

Tests ausführen:
```bash
pytest
```

## Dokumentation

Ausführliche Dokumentation finden Sie im `docs/`-Verzeichnis.

## Lizenz

Dieses Projekt ist unter der Creative Commons Attribution-NonCommercial 4.0 International Lizenz lizenziert.
Das bedeutet, dass Sie den Code frei verwenden, anpassen und teilen können, solange dies nicht für kommerzielle Zwecke geschieht.

Siehe [LICENSE](LICENSE) für den vollständigen Lizenztext.

## 3D-Benutzeroberfläche

energyOS verfügt über eine moderne webbasierte 3D-Benutzeroberfläche für die Gebäudevisualisierung und -bearbeitung.

### Starten der 3D-UI

```bash
python run_3d_editor.py
```

Die 3D-Benutzeroberfläche öffnet sich automatisch im Browser unter http://localhost:8080 und bietet:

- **Interaktive 3D-Visualisierung** des Gebäudes
- **Echtzeit-Bearbeitung** von Gebäudeparametern  
- **Direkte Simulation** mit sofortigen Ergebnissen
- **Energieeffizienz-Indikatoren** in Echtzeit

Weitere Details finden Sie in der [3D-UI Dokumentation](src/ui/README.md).

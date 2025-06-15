# energyOS Benutzerhandbuch

## Übersicht

energyOS ist ein Simulationstool für Energiesysteme in Gebäuden nach deutschen Normen. Es ermöglicht die Simulation von Gebäuden, Wärmepumpen, PV-Anlagen und deren Zusammenspiel unter Berücksichtigung von Wetterdaten.

## Schnellstart

### Installation

```bash
pip install -r requirements.txt
```

### Grundlegende Verwendung

```python
from src.main import run_simulation

# Beispiel für eine einfache Simulation
results = run_simulation(
    latitude=52.52,        # Breitengrad (Berlin)
    longitude=13.41,       # Längengrad (Berlin)
    building_type="single_family",
    heated_area=150,       # m²
    building_year=2015,
    heatpump_power=9,      # kW
    pv_peak_power=10,      # kWp
    time_step_minutes=15,  # 15-Minuten-Zeitschritte
    save_output=True       # Ergebnisse in CSV speichern
)
```

## Eingabeparameter

### Standort
- **latitude**: Breitengrad des Gebäudestandorts (z.B. 52.52 für Berlin)
- **longitude**: Längengrad des Gebäudestandorts (z.B. 13.41 für Berlin)

### Gebäude
- **building_type**: Gebäudetyp (`single_family`, `multi_family`, `apartment`)
- **heated_area**: Beheizte Fläche in m²
- **building_year**: Baujahr des Gebäudes
- **building_standard**: Optional, Baustandard (`EnEV2014`, `EnEV2016`, `GEG2020`, `KfW55`, `KfW40`, `KfW40plus`)

### Heiztechnik
- **heatpump_type**: Wärmepumpentyp (`air_water`, `brine_water`, `water_water`)
- **heatpump_power**: Nennleistung der Wärmepumpe in kW
- **storage_volume**: Speichervolumen in Liter
- **heating_system**: Heizungssystem (`radiator`, `floor_heating`)

### Photovoltaik
- **pv_peak_power**: Spitzenleistung der PV-Anlage in kWp
- **pv_orientation**: Ausrichtung der Module in Grad (0=Süd, -90=Ost, 90=West)
- **pv_tilt**: Neigung der Module in Grad (0=horizontal, 90=vertikal)

### Simulation
- **start_date**: Startdatum der Simulation (Format: 'YYYY-MM-DD')
- **end_date**: Enddatum der Simulation (Format: 'YYYY-MM-DD')
- **time_step_minutes**: Zeitschritt in Minuten (Standard: 60, möglich: 1-60)
- **save_output**: Wenn True, werden detaillierte Simulationsergebnisse in einer CSV-Datei gespeichert
- **output_file**: Optionaler Pfad für die Ausgabedatei (Standard: 'simulation_results_{Datum}.csv')

## Ausgabeparameter

Die Simulation liefert ein Dictionary mit folgenden Schlüsseln:

- **energy_demand**: Energiebedarf in kWh
- **energy_production**: Energieproduktion in kWh
- **self_consumption**: Eigenverbrauch in kWh
- **costs**: Kosten in Euro
- **emissions**: CO2-Emissionen in kg
- **renewable_share**: Anteil erneuerbarer Energien (0-1)
- **temperatures**: Zeitreihe der Temperaturen
- **power_flows**: Zeitreihe der Energieflüsse
- **output_file**: Pfad zur Ausgabedatei (wenn save_output=True)

### Ausgabedatei-Format

Wenn `save_output=True` gesetzt wird, erstellt die Simulation eine CSV-Datei mit folgenden Spalten:

- **timestamp**: Zeitstempel im Format YYYY-MM-DD HH:MM:SS
- **outside_temperature**: Außentemperatur in °C
- **flow_temperature**: Vorlauftemperatur in °C
- **solar_radiation**: Solare Einstrahlung in W/m²
- **heat_demand**: Wärmebedarf in kWh
- **heat_output**: Wärmeabgabe in kWh
- **cop**: Leistungszahl der Wärmepumpe
- **power_input**: Stromaufnahme der Wärmepumpe in kWh
- **pv_dc_output**: DC-Leistung der PV-Anlage in kWh
- **pv_ac_output**: AC-Leistung der PV-Anlage in kWh

## Beispiele

### Gebäudesimulation
```python
from src.core.building import Building, BuildingProperties, Wall, Window, Roof, Floor

# Gebäudeeigenschaften definieren
properties = BuildingProperties(
    walls=[Wall(area=120, orientation="S", layers=[(0.2, 0.035)], ...)],
    windows=[Window(area=8, u_value=1.0, g_value=0.6, orientation="S", ...)],
    roof=Roof(area=100, tilt=30, layers=[(0.3, 0.022)]),
    floor=Floor(area=100, layers=[(0.2, 0.035)], ground_coupling=True),
    volume=500,
    infiltration_rate=0.5,
    thermal_mass=120
)

# Gebäude erstellen
building = Building(properties)

# Heizlast berechnen
trans_loss, vent_loss, solar_gain = building.calculate_heat_load(
    outside_temp=-10,
    solar_radiation={'S': 100, 'N': 20, 'E': 50, 'W': 50},
    inside_temp=20
)
```

### Simulation mit verschiedenen Zeitschritten

```python
# Stündliche Simulation (Standard)
results_hourly = run_simulation(
    latitude=52.52,
    longitude=13.41,
    building_type="single_family",
    heated_area=150,
    time_step_minutes=60,
    save_output=True
)

# 15-Minuten-Simulation für höhere Genauigkeit
results_detailed = run_simulation(
    latitude=52.52,
    longitude=13.41,
    building_type="single_family",
    heated_area=150,
    time_step_minutes=15,
    save_output=True,
    output_file="ergebnisse_15min.csv"
)
```

### Wärmepumpensimulation
```python
from src.simulation.heat_pump import HeatPump, HeatPumpSpecifications

# Wärmepumpenspezifikationen definieren
specs = HeatPumpSpecifications(
    nominal_heating_power=9.0,
    cop_rating_points={
        (-7, 35): 2.7,
        (2, 35): 3.4,
        (7, 35): 4.0,
        (7, 45): 3.2
    },
    min_outside_temp=-20.0,
    max_flow_temp=55.0,
    min_part_load_ratio=0.3
)

# Wärmepumpe erstellen
heat_pump = HeatPump(specs)

# Leistung berechnen
heat_output, power_input = heat_pump.get_power_output(
    outside_temp=0,
    flow_temp=35,
    demand=5.0,
    time_step=1.0
)
```

### PV-Simulation
```python
from src.simulation.pv_system import PVSystem

# PV-System erstellen
pv_system = PVSystem(
    peak_power=10.0,
    orientation=0,  # Süd
    tilt=30,
    efficiency=0.97
)

# Energieertrag berechnen
energy = pv_system.calculate_energy_production(
    solar_radiation=800,  # W/m²
    temperature=25,       # °C
    time_step=1.0         # Stunden
)
```

## Auswertung der Ausgabedateien

Die generierten CSV-Dateien eignen sich für:

1. **Detaillierte Analysen** des zeitlichen Verlaufs von Energieströmen
2. **Visualisierungen** mit Tools wie Excel, Python (matplotlib, seaborn) oder R
3. **Optimierungsberechnungen** für Anlagengrößen und -steuerung
4. **Export** in andere Energiemanagement- oder Monitoring-Systeme

Beispiel für das Laden und Analysieren der Ausgabedatei:

```python
import pandas as pd
import matplotlib.pyplot as plt

# Daten laden
df = pd.read_csv("simulation_results_20250615_120000.csv")

# Tageswerte aggregieren
daily = df.groupby(pd.to_datetime(df['timestamp']).dt.date).sum()

# Visualisierung
fig, ax = plt.subplots(figsize=(10, 6))
ax.plot(daily.index, daily['heat_demand'], 'r-', label='Wärmebedarf')
ax.plot(daily.index, daily['pv_ac_output'], 'g-', label='PV-Produktion')
ax.legend()
plt.savefig('tagesenergiebilanz.png')
```

## Normkonformität

energyOS implementiert Berechnungen gemäß aktueller deutscher Normen:
- GEG 2023 (Gebäudeenergiegesetz)
- DIN 4108 (Wärmeschutz im Hochbau)
- DIN EN 12831 (Heizlastberechnung)
- VDI 4645 (Wärmepumpen)
- DIN V 18599 (Energetische Bewertung)
- VDI 2067 (Wirtschaftlichkeitsberechnung)

## Fehlerbehebung

Häufige Fehler:
- **ValueError: Keine geeignete Station gefunden**: Überprüfen Sie die Koordinaten oder vergrößern Sie den Suchradius.
- **ImportError: No module named...**: Stellen Sie sicher, dass alle Abhängigkeiten installiert sind (`pip install -r requirements.txt`).
- **RuntimeError: Convergence failed**: Überprüfen Sie die Eingabeparameter auf Plausibilität.
- **MemoryError**: Reduzieren Sie den Simulationszeitraum oder erhöhen Sie den Zeitschritt.

Bei weiteren Fragen wenden Sie sich an den Support oder erstellen Sie einen Issue auf GitHub.

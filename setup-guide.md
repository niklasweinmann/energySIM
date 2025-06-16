# Schritt-für-Schritt Anleitung: Datenbankintegration für Python-Energiesimulation

## Übersicht

Diese Anleitung zeigt Ihnen, wie Sie aktuelle Datenbanken für PV-Module, Wechselrichter und Batterien in Ihr Python-Energiesimulationsprogramm integrieren können.

## 1. Voraussetzungen und Installation

### Python-Bibliotheken installieren

```bash
# Grundlegende Bibliotheken
pip install pandas numpy sqlite-utils

# Für PV-Simulationen
pip install pvlib

# Für API-Zugriffe
pip install requests aiohttp

# Für Datenverarbeitung
pip install openpyxl xlsxwriter

# Optional: Für erweiterte Funktionen
pip install sqlalchemy plotly streamlit
```

### API-Schlüssel beantragen

1. **NREL Developer Network**: Registrierung unter https://developer.nrel.gov/signup/
2. **PVGIS**: Kein API-Schlüssel erforderlich, aber Nutzungslimits beachten
3. **Open Energy Platform**: Registrierung unter https://openenergy-platform.org/

## 2. Datenquellen und ihre Integration

### A) SAM-Datenbank (NREL) - Empfohlen für PV-Module und Wechselrichter

**Vorteile:**
- Kostenlos und umfangreich
- Direkte Integration über pvlib
- Regelmäßig aktualisiert
- Hohe Datenqualität

**Integration:**

```python
import pvlib

# PV-Module laden
cec_modules = pvlib.pvsystem.retrieve_sam('CECMod')
sandia_modules = pvlib.pvsystem.retrieve_sam('SandiaMod')

# Wechselrichter laden
cec_inverters = pvlib.pvsystem.retrieve_sam('CECInverter')
adr_inverters = pvlib.pvsystem.retrieve_sam('ADRInverter')
```

### B) PVGIS (Europäische Kommission) - Für Wetterdaten und Standortanalyse

**Integration:**

```python
import pvlib

# Meteorologische Daten abrufen
weather_data, meta = pvlib.iotools.get_pvgis_tmy(latitude=52.5, longitude=13.4)
```

### C) Open Energy Platform (Deutschland) - Für deutsche Energiedaten

**API-Zugriff:**

```python
import requests

base_url = "https://openenergy-platform.org/api/v0/"
endpoint = "schema/supply/tables/bnetza_mastr_wind/rows"

response = requests.get(f"{base_url}{endpoint}")
data = response.json()
```

### D) Batteriedatenbanken

**DOE Global Energy Storage Database:**

```python
import requests
import pandas as pd

# Beispiel-API-Aufruf (falls verfügbar)
url = "https://sandia.gov/ess-ssl/GESDB/public/statistics.html"
# Manuelle Datenaufbereitung erforderlich
```

## 3. Lokale Datenbankstruktur einrichten

### SQLite-Datenbank erstellen

```python
import sqlite3

conn = sqlite3.connect('energy_components.db')

# PV-Module Tabelle
conn.execute("""
CREATE TABLE IF NOT EXISTS pv_modules (
    id TEXT PRIMARY KEY,
    manufacturer TEXT,
    model TEXT,
    technology TEXT,
    power_stc REAL,
    voltage_oc REAL,
    current_sc REAL,
    efficiency REAL,
    price_per_wp REAL,
    last_updated TIMESTAMP,
    data_source TEXT
)
""")

# Wechselrichter Tabelle
conn.execute("""
CREATE TABLE IF NOT EXISTS inverters (
    id TEXT PRIMARY KEY,
    manufacturer TEXT,
    model TEXT,
    power_ac REAL,
    power_dc REAL,
    efficiency_euro REAL,
    price REAL,
    last_updated TIMESTAMP,
    data_source TEXT
)
""")

# Batterien Tabelle
conn.execute("""
CREATE TABLE IF NOT EXISTS batteries (
    id TEXT PRIMARY KEY,
    manufacturer TEXT,
    model TEXT,
    capacity_kwh REAL,
    power_kw REAL,
    efficiency REAL,
    chemistry TEXT,
    price REAL,
    last_updated TIMESTAMP,
    data_source TEXT
)
""")

conn.commit()
conn.close()
```

## 4. Datenaktualisierung automatisieren

### Caching-Strategie implementieren

```python
from datetime import datetime, timedelta
import sqlite3

class DatabaseManager:
    def __init__(self, db_path='energy_components.db', cache_days=7):
        self.db_path = db_path
        self.cache_days = cache_days
    
    def needs_update(self, table_name):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.execute(
            f"SELECT MAX(last_updated) FROM {table_name}"
        )
        last_update = cursor.fetchone()[0]
        conn.close()
        
        if not last_update:
            return True
        
        last_update_dt = datetime.fromisoformat(last_update)
        return datetime.now() - last_update_dt > timedelta(days=self.cache_days)
    
    def update_if_needed(self):
        if self.needs_update('pv_modules'):
            self.update_pv_modules()
        if self.needs_update('inverters'):
            self.update_inverters()
        if self.needs_update('batteries'):
            self.update_batteries()
```

## 5. Komponentensuche und -auswahl

### Suchfunktionen implementieren

```python
import pandas as pd

def search_pv_modules(min_power=None, max_price=None, technology=None):
    conn = sqlite3.connect('energy_components.db')
    
    query = "SELECT * FROM pv_modules WHERE 1=1"
    params = []
    
    if min_power:
        query += " AND power_stc >= ?"
        params.append(min_power)
    
    if max_price:
        query += " AND price_per_wp <= ?"
        params.append(max_price)
    
    if technology:
        query += " AND technology LIKE ?"
        params.append(f"%{technology}%")
    
    results = pd.read_sql_query(query, conn, params=params)
    conn.close()
    
    return results

# Beispielverwendung
modules = search_pv_modules(min_power=300, technology='mono')
```

## 6. Integration in Simulationsprogramm

### Komponentendaten abrufen

```python
class EnergySimulation:
    def __init__(self):
        self.db_manager = DatabaseManager()
    
    def get_component_parameters(self, component_type, component_id):
        conn = sqlite3.connect(self.db_manager.db_path)
        
        table_mapping = {
            'pv': 'pv_modules',
            'inverter': 'inverters',
            'battery': 'batteries'
        }
        
        table = table_mapping.get(component_type)
        if not table:
            return None
        
        cursor = conn.execute(
            f"SELECT * FROM {table} WHERE id = ?", 
            (component_id,)
        )
        
        result = cursor.fetchone()
        conn.close()
        
        return result
    
    def run_simulation(self, pv_id, inverter_id, battery_id=None):
        # Komponentenparameter abrufen
        pv_params = self.get_component_parameters('pv', pv_id)
        inverter_params = self.get_component_parameters('inverter', inverter_id)
        
        # Simulation durchführen...
        pass
```

## 7. Datenqualität und Validierung

### Validierungsregeln definieren

```python
def validate_pv_module(module_data):
    checks = []
    
    # Plausibilitätsprüfungen
    if module_data.get('power_stc', 0) <= 0:
        checks.append("Invalid STC power")
    
    if module_data.get('efficiency', 0) > 25:
        checks.append("Efficiency too high (>25%)")
    
    if module_data.get('voltage_oc', 0) <= 0:
        checks.append("Invalid open circuit voltage")
    
    return checks

def validate_database():
    conn = sqlite3.connect('energy_components.db')
    
    # PV-Module validieren
    modules = pd.read_sql_query("SELECT * FROM pv_modules", conn)
    
    for idx, module in modules.iterrows():
        errors = validate_pv_module(module)
        if errors:
            print(f"Module {module['id']}: {', '.join(errors)}")
    
    conn.close()
```

## 8. Wartung und Updates

### Regelmäßige Updates planen

```python
import schedule
import time

def scheduled_update():
    manager = DatabaseManager()
    manager.update_if_needed()
    print(f"Database updated at {datetime.now()}")

# Tägliche Updates um 6:00 Uhr
schedule.every().day.at("06:00").do(scheduled_update)

# Wöchentliche vollständige Updates
schedule.every().monday.at("02:00").do(lambda: DatabaseManager().full_update())

# Scheduler laufen lassen
while True:
    schedule.run_pending()
    time.sleep(60)
```

## 9. Troubleshooting

### Häufige Probleme und Lösungen

**Problem: API-Limits erreicht**
- Lösung: Caching verwenden, Anfragen zeitlich verteilen
- Implementierung von Retry-Mechanismen mit exponential backoff

**Problem: Veraltete Daten**
- Lösung: Automatische Update-Überprüfung
- Timestamp-basierte Cache-Invalidierung

**Problem: Inkompatible Datenformate**
- Lösung: Datenvalidierung und -transformation
- Einheitliche Datenmodelle definieren

**Problem: Netzwerkfehler**
- Lösung: Offline-Fallback auf lokale Daten
- Robuste Fehlerbehandlung

## 10. Erweiterte Features

### Web-Interface für Datenverwaltung

```python
import streamlit as st

def create_web_interface():
    st.title("Energy Component Database Manager")
    
    # Suchbereich
    st.header("Component Search")
    component_type = st.selectbox(
        "Component Type", 
        ["PV Modules", "Inverters", "Batteries"]
    )
    
    if component_type == "PV Modules":
        min_power = st.number_input("Min Power (W)", min_value=0)
        results = search_pv_modules(min_power=min_power)
        st.dataframe(results)
    
    # Datenbankstatistiken
    st.header("Database Statistics")
    manager = DatabaseManager()
    stats = manager.get_statistics()
    st.json(stats)

if __name__ == "__main__":
    create_web_interface()
```

## Zusammenfassung

Diese Anleitung bietet einen umfassenden Ansatz für die Integration aktueller Energiekomponentendatenbanken in Python-Simulationsprogramme. Die Kombination aus lokaler SQLite-Datenbank und API-Integration ermöglicht sowohl Offline-Fähigkeiten als auch aktuelle Daten.

**Nächste Schritte:**
1. Beginnen Sie mit der SAM-Datenbankintegration über pvlib
2. Implementieren Sie die lokale SQLite-Datenbank
3. Fügen Sie schrittweise weitere Datenquellen hinzu
4. Implementieren Sie Validierung und Fehlerbehandlung
5. Planen Sie regelmäßige Updates

Bei Fragen oder Problemen konsultieren Sie die Dokumentation der jeweiligen APIs oder wenden Sie sich an die Entwicklergemeinschaften.
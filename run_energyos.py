#!/usr/bin/env python3
"""
Hauptprogramm für energyOS - direkter Zugriff auf Funktionen
"""

import sys
from pathlib import Path
import json
from datetime import datetime
import traceback

# Import der run_simulation Funktion
sys.path.insert(0, str(Path(__file__).parent))

# Diese Datei importiert src.main
from src.main import run_simulation as _run_simulation

def run_simulation(**kwargs):
    """Wrapper für die run_simulation Funktion aus src.main"""
    return _run_simulation(**kwargs)

if __name__ == "__main__":
    # Beispiel für eine Simulation mit der Funktion
    try:
        print("Starte Simulation mit folgenden Parametern:")
        print(f"  - Standort: 52.52°N, 13.41°E (Berlin)")
        print(f"  - Gebäude: Einfamilienhaus, 150 m², Baujahr 2015")
        print(f"  - Heizung: Wärmepumpe 9 kW")
        print(f"  - PV: 10 kWp")
        print(f"  - Zeitraum: 01.01.2025 - 03.01.2025")
        print(f"  - Zeitschritt: 30 Minuten")
        
        results = run_simulation(
            latitude=52.52,
            longitude=13.41,
            building_type="single_family",
            heated_area=150,
            building_year=2015,
            heatpump_power=9,
            pv_peak_power=10,
            start_date="2025-01-01",
            end_date="2025-01-03",
            time_step_minutes=30,  # 30-Minuten-Zeitschritte
            save_output=True
        )
        
        print("\nSimulationsergebnisse:")
        print(json.dumps(results, indent=2))
        
    except Exception as e:
        print(f"\nFEHLER bei der Simulation: {type(e).__name__}: {e}")
        print("\nDetaillierter Fehler:")
        traceback.print_exc()
        sys.exit(1)

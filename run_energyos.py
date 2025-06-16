#!/usr/bin/env python3
"""
Hauptprogramm für energyOS - direkter Zugriff auf Funktionen
"""

import sys
import logging
from pathlib import Path
import json
from datetime import datetime
import traceback
import os

# Import der run_simulation Funktion
sys.path.insert(0, str(Path(__file__).parent))

# Importiere das Logging-Modul
from src.utils.logging_config import configure_logging

# Diese Datei importiert src.main
from src.main import run_simulation as _run_simulation

def run_simulation(**kwargs):
    """Wrapper für die run_simulation Funktion aus src.main"""
    return _run_simulation(**kwargs)

if __name__ == "__main__":
    # Konfiguriere das Logging-System
    log_file = Path(__file__).parent / "output_log.txt"
    configure_logging(log_file_path=log_file)
    
    # Beispiel für eine Simulation mit der Funktion
    try:
        logging.info("Starte Simulation mit folgenden Parametern:")
        logging.info(f"  - Standort: 52.52°N, 13.41°E (Berlin)")
        logging.info(f"  - Gebäude: Einfamilienhaus, 150 m², Baujahr 2015")
        logging.info(f"  - Heizung: Wärmepumpe 9 kW")
        logging.info(f"  - PV: 10 kWp")
        logging.info(f"  - Zeitraum: 01.06.2023 - 03.06.2023")
        logging.info(f"  - Zeitschritt: 30 Minuten")
        
        results = run_simulation(
            latitude=52.52,
            longitude=13.41,
            building_type="single_family",
            heated_area=150,
            building_year=2015,
            heatpump_power=9,
            pv_peak_power=10,
            start_date="2023-06-01",
            end_date="2023-06-03",
            time_step_minutes=30,  # 30-Minuten-Zeitschritte
            save_output=True
        )
        
        logging.info("\nSimulationsergebnisse:")
        logging.info(json.dumps(results, indent=2))
        
    except Exception as e:
        logging.error(f"\nFEHLER bei der Simulation: {type(e).__name__}: {e}")
        logging.error("\nDetaillierter Fehler:")
        logging.error(traceback.format_exc())
        sys.exit(1)
    
    # Ausgabe der erfolgreichen Ausführung
    logging.info(f"Simulation erfolgreich abgeschlossen. Ausgaben in Datei gespeichert.")

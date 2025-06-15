#!/usr/bin/env python3
"""
Test für die Simulation mit verschiedenen Zeitschritten.
"""

import os
import sys
from pathlib import Path
import json
from datetime import datetime

# Importiere von run_energyos.py
from run_energyos import run_simulation

def main():
    """Führt Simulationen mit verschiedenen Zeitschritten aus."""
    
    # Erstelle Ausgabeverzeichnis, falls es nicht existiert
    output_dir = Path(__file__).parent / "output"
    output_dir.mkdir(exist_ok=True)
    
    print("Starte Simulationen mit verschiedenen Zeitschritten...")
    
    # Simulationen mit verschiedenen Zeitschritten
    time_steps = [60, 30, 15]
    
    for time_step in time_steps:
        print(f"\nSimulation mit {time_step}-Minuten-Zeitschritten:")
        
        try:
            results = run_simulation(
                latitude=52.52,
                longitude=13.41,
                building_type="single_family",
                heated_area=150,
                building_year=2015,
                heatpump_power=9,
                pv_peak_power=10,
                start_date="2025-01-01",
                end_date="2025-01-02",  # Kurzer Zeitraum für schnellere Tests
                time_step_minutes=time_step,
                save_output=True,
                output_file=f"output/simulation_timestep_{time_step}min.csv"
            )
            
            # Ausgabe der Ergebnisse
            print(f"Anzahl der Zeitschritte: 24*60/{time_step} = {24*60/time_step}")
            print(f"Wärmebedarf: {results['energy_demand']['heat_demand_kWh']:.2f} kWh")
            print(f"PV-Ertrag: {results['energy_demand']['pv_production_kWh']:.2f} kWh")
            
            # Speichere Ergebnisse als JSON
            with open(f"output/results_timestep_{time_step}min.json", "w") as f:
                json.dump(results, f, indent=2)
        except Exception as e:
            print(f"Fehler bei Zeitschritt {time_step} min: {str(e)}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    main()

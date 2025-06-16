#!/usr/bin/env python3
"""
Test der DWD API um zu verstehen, welche Daten verfügbar sind
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from datetime import datetime, timedelta
from wetterdienst.provider.dwd.observation import DwdObservationRequest
from wetterdienst import Settings
import pandas as pd

def test_dwd_api():
    """Teste DWD API um verfügbare Daten zu verstehen"""
    
    print("=== DWD API Test ===")
    
    # Settings
    settings = Settings(ts_shape="long", ts_humanize=True, ts_convert_units=True)
    
    # Test 1: Prüfe verfügbare Stationen
    print("\n1. Prüfe verfügbare Stationen für Berlin...")
    request = DwdObservationRequest(
        parameters=[("hourly", "temperature_air", "temperature_air_mean_2m")],
        start_date=datetime(2023, 1, 1),
        end_date=datetime(2023, 1, 2),
        settings=settings
    )
    
    # Finde Stationen in der Nähe von Berlin
    stations = request.filter_by_distance((52.52, 13.41), 50)  # 50km Radius
    stations_df = stations.df.to_pandas()
    print(f"Gefundene Stationen: {len(stations_df)}")
    print(stations_df[['station_id', 'name', 'start_date', 'end_date']].head())
    
    # Test 2: Teste eine bekannte aktive Station
    if len(stations_df) > 0:
        test_station = stations_df.iloc[0]['station_id']
        print(f"\n2. Teste Station {test_station}...")
        
        try:
            values = stations.values.all()
            values_df = values.df.to_pandas()
            print(f"Erfolgreich Daten abgerufen: {len(values_df)} Einträge")
            print(f"Spalten: {values_df.columns.tolist()}")
            if len(values_df) > 0:
                print(f"Erste paar Zeilen:")
                print(values_df.head())
        except Exception as e:
            print(f"Fehler beim Abrufen der Daten: {e}")
    
    # Test 3: Teste verschiedene Zeiträume
    print("\n3. Teste verschiedene Zeiträume...")
    test_dates = [
        (datetime(2023, 6, 1), datetime(2023, 6, 2)),  # Sommer 2023
        (datetime(2023, 12, 1), datetime(2023, 12, 2)),  # Winter 2023
        (datetime(2024, 6, 1), datetime(2024, 6, 2)),  # Sommer 2024
    ]
    
    for start_date, end_date in test_dates:
        print(f"\nTeste Zeitraum: {start_date.strftime('%Y-%m-%d')} bis {end_date.strftime('%Y-%m-%d')}")
        try:
            request = DwdObservationRequest(
                parameters=[("hourly", "temperature_air", "temperature_air_mean_2m")],
                start_date=start_date,
                end_date=end_date,
                settings=settings
            )
            
            stations = request.filter_by_distance((52.52, 13.41), 20)
            if len(stations.df) > 0:
                values = stations.values.all()
                values_df = values.df.to_pandas()
                print(f"  -> {len(values_df)} Datenpunkte gefunden")
            else:
                print("  -> Keine Stationen gefunden")
                
        except Exception as e:
            print(f"  -> Fehler: {e}")

if __name__ == "__main__":
    test_dwd_api()

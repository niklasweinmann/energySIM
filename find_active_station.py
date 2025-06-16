#!/usr/bin/env python3
"""
Finde eine aktive DWD-Station für echte Daten
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from datetime import datetime
from wetterdienst.provider.dwd.observation import DwdObservationRequest
from wetterdienst import Settings
import pandas as pd

def find_active_station():
    """Finde eine aktive Station mit Daten für 2023"""
    
    print("=== Suche nach aktiver DWD-Station ===")
    
    settings = Settings(ts_shape="long", ts_humanize=True, ts_convert_units=True)
    
    # Teste verschiedene Stationen für Juni 2023
    request = DwdObservationRequest(
        parameters=[("hourly", "temperature_air", "temperature_air_mean_2m")],
        start_date=datetime(2023, 6, 1),
        end_date=datetime(2023, 6, 2),
        settings=settings
    )
    
    # Finde alle Stationen in der Nähe von Berlin
    stations = request.filter_by_distance((52.52, 13.41), 50)
    stations_df = stations.df.to_pandas()
    
    print(f"Gefundene Stationen: {len(stations_df)}")
    
    # Teste jede Station auf verfügbare Daten
    for idx, station in stations_df.iterrows():
        station_id = station['station_id']
        station_name = station['name']
        end_date = station['end_date']
        
        print(f"\nTeste Station {station_id} ({station_name})")
        print(f"  Enddatum: {end_date}")
        
        if pd.to_datetime(end_date).tz_localize(None) > pd.to_datetime('2023-06-01'):
            try:
                # Erstelle eine neue Anfrage für diese spezifische Station
                station_request = DwdObservationRequest(
                    parameters=[("hourly", "temperature_air", "temperature_air_mean_2m")],
                    start_date=datetime(2023, 6, 1),
                    end_date=datetime(2023, 6, 2),
                    settings=settings
                )
                
                # Filtere nach dieser Station  
                station_data = station_request.filter_by_station_id(station_id=[station_id])
                values = station_data.values.all()
                values_df = values.df.to_pandas()
                
                if len(values_df) > 0:
                    print(f"  ✓ Daten verfügbar: {len(values_df)} Einträge")
                    print(f"  Verwendbare Station gefunden: {station_id} - {station_name}")
                    
                    # Zeige verfügbare Parameter
                    params = values_df['parameter'].unique()
                    print(f"  Verfügbare Parameter: {params}")
                    
                    return station_id, station_name
                else:
                    print(f"  ✗ Keine Daten")
                    
            except Exception as e:
                print(f"  ✗ Fehler: {e}")
        else:
            print(f"  ✗ Station nicht aktiv für 2023")
    
    return None, None

if __name__ == "__main__":
    station_id, station_name = find_active_station()
    if station_id:
        print(f"\n=== EMPFEHLUNG ===")
        print(f"Station verwenden: {station_id} ({station_name})")
    else:
        print("\nKeine aktive Station gefunden!")

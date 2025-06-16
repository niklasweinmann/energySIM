#!/usr/bin/env python3
"""
DWD Daten-Management Tool
Verwaltet und organisiert die gespeicherten DWD-Wetterdaten.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.data_handlers.dwd_weather import DWDDataManager
import pandas as pd
from datetime import datetime
import argparse

def main():
    parser = argparse.ArgumentParser(description='DWD Daten-Management Tool')
    parser.add_argument('--list', '-l', action='store_true', help='Liste verfügbare Daten auf')
    parser.add_argument('--stations', '-s', action='store_true', help='Liste verfügbare Stationen auf')
    parser.add_argument('--cleanup', '-c', type=int, help='Lösche Daten älter als X Tage')
    parser.add_argument('--generate', '-g', nargs=4, metavar=('STATION_ID', 'START_DATE', 'END_DATE', 'REASON'),
                       help='Generiere Daten für Station (ID, Start-Datum YYYY-MM-DD, End-Datum YYYY-MM-DD, Grund)')
    
    args = parser.parse_args()
    
    # DWD Manager initialisieren
    dwd_manager = DWDDataManager()
    
    if args.list:
        print("=== Verfügbare DWD-Datendateien ===")
        data_files = dwd_manager.list_available_data()
        if not data_files.empty:
            print(data_files.to_string(index=False))
            print(f"\nGesamt: {len(data_files)} Datendateien")
            total_size = data_files['file_size_kb'].sum()
            print(f"Gesamtgröße: {total_size:.1f} KB")
        else:
            print("Keine Datendateien gefunden.")
    
    elif args.stations:
        print("=== Verfügbare DWD-Stationen ===")
        stations = dwd_manager.get_station_info()
        print(stations[['id', 'name', 'state', 'latitude', 'longitude', 'active']].to_string(index=False))
    
    elif args.cleanup:
        print(f"=== Bereinige Daten älter als {args.cleanup} Tage ===")
        dwd_manager.cleanup_old_data(args.cleanup)
    
    elif args.generate:
        station_id, start_date_str, end_date_str, reason = args.generate
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
            
            print(f"=== Generiere Daten für Station {station_id} ===")
            print(f"Zeitraum: {start_date_str} bis {end_date_str}")
            print(f"Grund: {reason}")
            
            # Prüfe ob Station existiert
            station_info = dwd_manager.get_station_info(station_id)
            if station_info.empty:
                print(f"Fehler: Station {station_id} nicht gefunden!")
                return
            
            station_name = station_info.iloc[0]['name']
            print(f"Station: {station_name}")
            
            # Generiere Daten
            data = dwd_manager.get_synthetic_data(station_id, start_date, end_date)
            print(f"✓ {len(data)} Datenpunkte generiert")
            
            # Zeige Statistiken
            print("\n=== Daten-Statistiken ===")
            print(f"Temperatur: {data['temperature'].min():.1f}°C bis {data['temperature'].max():.1f}°C")
            print(f"Sonnenstrahlung: max {data['solar_radiation'].max():.0f} W/m²")
            print(f"Windgeschwindigkeit: max {data['wind_speed'].max():.1f} m/s")
            print(f"Luftfeuchtigkeit: {data['humidity'].min():.1f}% bis {data['humidity'].max():.1f}%")
            
        except ValueError as e:
            print(f"Fehler beim Datum-Parsing: {e}")
            print("Format: YYYY-MM-DD (z.B. 2025-06-15)")
    
    else:
        # Zeige Übersicht wenn keine spezifische Aktion gewählt
        print("=== DWD Daten-Management Dashboard ===")
        
        # Stationen-Info
        stations = dwd_manager.get_station_info()
        active_stations = stations[stations['active'] == True]
        print(f"Verfügbare Stationen: {len(stations)} (davon {len(active_stations)} aktiv)")
        
        # Daten-Info
        data_files = dwd_manager.list_available_data()
        if not data_files.empty:
            print(f"Gespeicherte Datendateien: {len(data_files)}")
            total_size = data_files['file_size_kb'].sum()
            print(f"Gesamtgröße: {total_size:.1f} KB")
            
            # Zeige neueste Datei
            latest_file = data_files.loc[data_files['last_modified'].idxmax()]
            print(f"Neueste Datei: {latest_file['start_date']} - {latest_file['end_date']} (Station {latest_file['station_id']})")
        else:
            print("Keine Datendateien vorhanden.")
        
        print("\nVerfügbare Kommandos:")
        print("  --list, -l           : Liste alle Datendateien")
        print("  --stations, -s       : Liste alle Stationen")
        print("  --cleanup TAGE, -c   : Lösche alte Cache-Dateien")
        print("  --generate ID START END GRUND : Generiere neue Daten")
        print("\nBeispiel:")
        print("  python tools/dwd_manager.py --generate 10384 2025-06-15 2025-06-20 'Test für nächste Woche'")

if __name__ == '__main__':
    main()

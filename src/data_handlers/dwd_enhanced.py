"""
Erweiterte DWD-Wetterintegration mit strukturierter Datenspeicherung.
"""

import os
import pandas as pd
import numpy as np
import requests
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import zipfile
import tempfile
from pathlib import Path

class DWDDataManager:
    """
    Verwaltet DWD-Wetterdaten mit strukturierter Speicherung.
    """
    
    def __init__(self, data_dir: str = None):
        if data_dir is None:
            project_root = Path(__file__).parents[2]
            data_dir = project_root / "data" / "weather" / "dwd"
        
        self.data_dir = Path(data_dir)
        self.stations_dir = self.data_dir / "stations"
        self.historical_dir = self.data_dir / "historical"
        self.forecast_dir = self.data_dir / "forecast"
        self.cache_dir = self.data_dir / "cache"
        
        self._ensure_directories()
        self.stations: Dict[str, dict] = {}
        self._load_stations()
    
    def _ensure_directories(self):
        """Erstellt alle notwendigen Verzeichnisse."""
        for directory in [self.stations_dir, self.historical_dir, 
                         self.forecast_dir, self.cache_dir]:
            directory.mkdir(parents=True, exist_ok=True)
    
    def _load_stations(self):
        """Lädt verfügbare DWD-Stationen."""
        stations_file = self.stations_dir / "stations.json"
        
        if stations_file.exists():
            with open(stations_file, 'r', encoding='utf-8') as f:
                stations_data = json.load(f)
        else:
            # Standard-Stationen für Deutschland
            stations_data = [
                {
                    'id': '10384',
                    'name': 'Berlin-Tempelhof',
                    'state': 'Berlin',
                    'latitude': 52.4675,
                    'longitude': 13.4021,
                    'altitude': 48.0,
                    'active': True
                },
                {
                    'id': '10385',
                    'name': 'Berlin-Tegel',
                    'state': 'Berlin', 
                    'latitude': 52.5644,
                    'longitude': 13.3088,
                    'altitude': 36.0,
                    'active': True
                },
                {
                    'id': '01048',
                    'name': 'Hamburg-Fuhlsbüttel',
                    'state': 'Hamburg',
                    'latitude': 53.6333,
                    'longitude': 9.9833,
                    'altitude': 11.0,
                    'active': True
                },
                {
                    'id': '10147',
                    'name': 'München-Flughafen',
                    'state': 'Bayern',
                    'latitude': 48.3537,
                    'longitude': 11.7751,
                    'altitude': 447.0,
                    'active': True
                },
                {
                    'id': '02014',
                    'name': 'Frankfurt/Main',
                    'state': 'Hessen',
                    'latitude': 50.1109,
                    'longitude': 8.6821,
                    'altitude': 112.0,
                    'active': True
                }
            ]
            
            # Speichere Standard-Stationen
            with open(stations_file, 'w', encoding='utf-8') as f:
                json.dump(stations_data, f, ensure_ascii=False, indent=2)
        
        # Lade in Dictionary
        for station in stations_data:
            self.stations[station['id']] = station
    
    def find_nearest_station(self, lat: float, lon: float) -> dict:
        """Findet die nächstgelegene Station."""
        min_distance = float('inf')
        nearest_station = None
        
        for station in self.stations.values():
            if not station.get('active', True):
                continue
                
            # Berechne Entfernung (einfache Näherung)
            distance = np.sqrt(
                (station['latitude'] - lat) ** 2 + 
                (station['longitude'] - lon) ** 2
            )
            
            if distance < min_distance:
                min_distance = distance
                nearest_station = station
        
        return nearest_station
    
    def get_synthetic_data(self, 
                          station_id: str,
                          start_date: datetime,
                          end_date: datetime) -> pd.DataFrame:
        """
        Generiert synthetische Wetterdaten für eine Station.
        Diese Funktion wird verwendet, wenn echte DWD-Daten nicht verfügbar sind.
        """
        # Lade Station
        station = self.stations.get(station_id)
        if not station:
            raise ValueError(f"Station {station_id} nicht gefunden")
        
        # Generiere stündliche Zeitstempel
        timestamps = pd.date_range(
            start=start_date,
            end=end_date,
            freq='h'
        )
        
        # Berechne Sonnenstand basierend auf Stationskoordinaten
        lat = station['latitude']
        lon = station['longitude']
        
        data = []
        for ts in timestamps:
            # Tag im Jahr (1-365)
            day_of_year = ts.timetuple().tm_yday
            hour = ts.hour
            
            # Jahresgang der Temperatur
            base_temp = 10 + 15 * np.sin(2 * np.pi * (day_of_year - 80) / 365)
            # Tagesgang
            daily_temp = 8 * np.sin(2 * np.pi * (hour - 6) / 24)
            temperature = base_temp + daily_temp + np.random.normal(0, 2)
            
            # Sonnenstrahlung
            max_radiation = 1000 if 6 <= hour <= 18 else 0
            sun_elevation = max(0, np.sin(np.pi * (hour - 6) / 12))
            solar_radiation = max_radiation * sun_elevation * np.random.uniform(0.7, 1.0)
            
            # Wind
            wind_speed = np.random.normal(4, 2)
            wind_speed = max(0, wind_speed)
            
            # Luftfeuchtigkeit (invers zur Temperatur)
            humidity = 90 - temperature * 1.5 + np.random.normal(0, 10)
            humidity = np.clip(humidity, 30, 100)
            
            # Bewölkung
            cloud_cover = np.random.uniform(0, 100)
            
            # Niederschlag (selten)
            precipitation = np.random.exponential(0.1) if np.random.random() < 0.1 else 0
            
            data.append({
                'timestamp': ts,
                'station_id': station_id,
                'temperature': round(temperature, 2),
                'solar_radiation': round(solar_radiation, 2),
                'wind_speed': round(wind_speed, 2),
                'humidity': round(humidity, 1),
                'cloud_cover': round(cloud_cover, 1),
                'precipitation': round(precipitation, 2)
            })
        
        df = pd.DataFrame(data)
        
        # Speichere die generierten Daten
        output_file = self.historical_dir / f"{station_id}_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}.csv"
        df.to_csv(output_file, index=False)
        
        print(f"Synthetische Wetterdaten gespeichert: {output_file}")
        return df
    
    def get_historical_data(self, 
                           station_id: str,
                           start_date: datetime,
                           end_date: datetime) -> pd.DataFrame:
        """
        Lädt historische Wetterdaten für eine Station.
        Versucht zuerst echte DWD-Daten zu laden, fällt auf synthetische Daten zurück.
        """
        # Prüfe Cache
        cache_file = self.historical_dir / f"{station_id}_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}.csv"
        
        if cache_file.exists():
            return pd.read_csv(cache_file, parse_dates=['timestamp'])
        
        # Versuche echte DWD-Daten zu laden
        try:
            return self._download_dwd_data(station_id, start_date, end_date)
        except Exception as e:
            print(f"Warnung: Konnte keine DWD-Daten laden ({e})")
            print("Generiere synthetische Daten...")
            return self.get_synthetic_data(station_id, start_date, end_date)
    
    def _download_dwd_data(self, 
                          station_id: str,
                          start_date: datetime,
                          end_date: datetime) -> pd.DataFrame:
        """
        Lädt echte DWD-Daten (aktuell nicht implementiert - würde echte API-Calls erfordern).
        """
        # TODO: Implementiere echte DWD-API-Integration
        raise NotImplementedError("Echte DWD-API noch nicht implementiert")
    
    def list_available_data(self) -> pd.DataFrame:
        """Listet alle verfügbaren Datendateien auf."""
        files = []
        
        for file in self.historical_dir.glob("*.csv"):
            parts = file.stem.split('_')
            if len(parts) >= 3:
                station_id = parts[0]
                start_date = parts[1]
                end_date = parts[2]
                
                file_size = file.stat().st_size
                modification_time = datetime.fromtimestamp(file.stat().st_mtime)
                
                files.append({
                    'station_id': station_id,
                    'start_date': start_date,
                    'end_date': end_date,
                    'file_path': str(file),
                    'file_size_kb': round(file_size / 1024, 1),
                    'last_modified': modification_time
                })
        
        return pd.DataFrame(files)
    
    def get_station_info(self, station_id: str = None) -> pd.DataFrame:
        """Gibt Informationen über Stationen zurück."""
        if station_id:
            station = self.stations.get(station_id)
            if station:
                return pd.DataFrame([station])
            else:
                return pd.DataFrame()
        else:
            return pd.DataFrame(list(self.stations.values()))
    
    def cleanup_old_data(self, days_old: int = 30):
        """Löscht alte Cache-Dateien."""
        cutoff_date = datetime.now() - timedelta(days=days_old)
        
        deleted_count = 0
        for file in self.cache_dir.glob("*"):
            if file.is_file():
                file_time = datetime.fromtimestamp(file.stat().st_mtime)
                if file_time < cutoff_date:
                    file.unlink()
                    deleted_count += 1
        
        print(f"Cache bereinigt: {deleted_count} alte Dateien gelöscht")

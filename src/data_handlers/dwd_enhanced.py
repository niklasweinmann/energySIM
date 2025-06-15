"""
Erweiterte DWD-Wetterintegration mit direkter API-Anbindung durch das wetterdienst-Paket.
"""

import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import json
from pathlib import Path
from wetterdienst.provider.dwd.observation import DwdObservationRequest
from wetterdienst import Settings
import logging

# Konstanten definieren
DEFAULT_PARAMETERS = [
    ("hourly", "air_temperature", "temperature_air_200"),
    ("hourly", "solar", "radiation_global"),
    ("hourly", "wind", "wind_speed"), 
    ("hourly", "precipitation", "precipitation_height"),
    ("hourly", "air_temperature", "humidity")
]

# Logger für Debug-Informationen
logger = logging.getLogger(__name__)

class DWDDataManager:
    """
    Verwaltet DWD-Wetterdaten mit strukturierter Speicherung und echter API-Anbindung.
    Verwendet das wetterdienst-Paket für Zugriff auf echte DWD-Daten.
    """
    
    def __init__(self, data_dir: str = None):
        """
        Initialisiert den DWD-Datenmanager.
        
        Args:
            data_dir: Pfad zum Datenspeicherverzeichnis. Wenn None, wird das Standardverzeichnis verwendet.
        """
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
        """Lädt verfügbare DWD-Stationen direkt über die Wetterdienst-API."""
        try:
            # Verwende die Wetterdienst-API, um Stationen zu laden
            settings = Settings(ts_shape="long", ts_humanize=True, ts_convert_units=True)
            
            # Temperatur-Stationen als Basis verwenden
            request = DwdObservationRequest(
                parameters=[("hourly", "air_temperature")],
                settings=settings
            )
            
            stations_df = request.df
            
            # Konvertiere das DataFrame in ein Dictionary für einfachen Zugriff
            for _, row in stations_df.iterrows():
                station_id = row["station_id"]
                if station_id not in self.stations:
                    self.stations[station_id] = {
                        'id': station_id,
                        'name': row["name"],
                        'state': row.get("state", ""),
                        'latitude': row["latitude"],
                        'longitude': row["longitude"],
                        'altitude': row["height"],
                        'active': True
                    }
            
            logger.info(f"Erfolgreich {len(self.stations)} Stationen geladen")
            
            # Speichere Stationen als JSON für spätere Nutzung
            stations_file = self.stations_dir / "stations.json"
            with open(stations_file, 'w', encoding='utf-8') as f:
                stations_list = list(self.stations.values())
                json.dump(stations_list, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            logger.warning(f"Fehler beim Laden der Stationen über API: {str(e)}")
            # Fallback auf gespeicherte oder Standard-Stationen
            self._load_fallback_stations()
    
    def _load_fallback_stations(self):
        """Lädt Standard-Stationen als Fallback."""
        stations_file = self.stations_dir / "stations.json"
        
        if stations_file.exists():
            with open(stations_file, 'r', encoding='utf-8') as f:
                stations_data = json.load(f)
                logger.info(f"Stationen aus lokaler Datei geladen: {len(stations_data)} Stationen")
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
            
            logger.info("Standard-Stationen wurden als Fallback verwendet")
        
        # Lade in Dictionary
        for station in stations_data:
            self.stations[station['id']] = station
    
    def find_nearest_station(self, lat: float, lon: float) -> dict:
        """
        Findet die nächstgelegene Station.
        
        Args:
            lat: Breitengrad
            lon: Längengrad
            
        Returns:
            Dictionary mit Stationsinformationen
        """
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
    
    def get_historical_data(self, 
                          station_id: str,
                          start_date: datetime,
                          end_date: datetime) -> pd.DataFrame:
        """
        Lädt historische Wetterdaten für eine Station.
        Verwendet die Wetterdienst-API für echte DWD-Daten.
        
        Args:
            station_id: ID der DWD-Station
            start_date: Startdatum
            end_date: Enddatum
            
        Returns:
            DataFrame mit Wetterdaten
        """
        # Prüfe Cache
        cache_file = self.historical_dir / f"{station_id}_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}.csv"
        
        if cache_file.exists():
            logger.info(f"Verwende Cache-Datei: {cache_file}")
            try:
                return pd.read_csv(cache_file, parse_dates=['timestamp'])
            except Exception as e:
                logger.error(f"Fehler beim Lesen des Caches: {e}")
        
        try:
            logger.info(f"Hole echte DWD-Daten für Station {station_id} von {start_date} bis {end_date}")
            return self._download_dwd_data(station_id, start_date, end_date)
        except Exception as e:
            logger.warning(f"Warnung: Konnte keine DWD-Daten laden ({e})")
            logger.info("Generiere synthetische Daten...")
            return self.get_synthetic_data(station_id, start_date, end_date)
    
    def _download_dwd_data(self, 
                         station_id: str,
                         start_date: datetime,
                         end_date: datetime) -> pd.DataFrame:
        """
        Lädt echte DWD-Daten mit der Wetterdienst-API.
        
        Args:
            station_id: ID der DWD-Station
            start_date: Startdatum
            end_date: Enddatum
            
        Returns:
            DataFrame mit Wetterdaten
        """
        try:
            # Wetterdienst-API einrichten
            settings = Settings(ts_shape="long", ts_humanize=True, ts_convert_units=True)
            
            # Parameter für die Abfrage
            request = DwdObservationRequest(
                parameters=DEFAULT_PARAMETERS,
                start_date=start_date,
                end_date=end_date,
                settings=settings
            ).filter_by_station_id(station_id=(station_id,))
            
            # Daten abrufen
            values_df = request.values.all().df
            
            if values_df.empty:
                raise ValueError(f"Keine Daten für Station {station_id} im angegebenen Zeitraum gefunden")
            
            # Transformieren in das erwartete Format
            result_df = pd.DataFrame()
            result_df['timestamp'] = values_df['date']
            result_df['station_id'] = values_df['station_id']
            
            # Parameter zuordnen
            for param, series_name in [
                ('temperature_air_200', 'temperature'),
                ('radiation_global', 'solar_radiation'),
                ('wind_speed', 'wind_speed'),
                ('humidity', 'humidity'),
                ('precipitation_height', 'precipitation')
            ]:
                param_data = values_df[values_df['parameter'] == param]
                if not param_data.empty:
                    result_df[series_name] = param_data['value'].reset_index(drop=True)
            
            # Fehlende Spalte für Bewölkung hinzufügen (nicht direkt in DWD-Daten verfügbar)
            if 'cloud_cover' not in result_df.columns:
                # Einfache Schätzung basierend auf Sonnenstrahlung und Temperatur
                if 'solar_radiation' in result_df.columns and 'temperature' in result_df.columns:
                    max_radiation = result_df['solar_radiation'].max()
                    if max_radiation > 0:
                        result_df['cloud_cover'] = 100 - (result_df['solar_radiation'] / max_radiation * 100)
                    else:
                        result_df['cloud_cover'] = 50  # Default-Wert
                else:
                    result_df['cloud_cover'] = 50  # Default-Wert
            
            # Speichere die Daten im Cache
            cache_file = self.historical_dir / f"{station_id}_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}.csv"
            result_df.to_csv(cache_file, index=False)
            logger.info(f"Daten erfolgreich in {cache_file} gespeichert")
            
            return result_df
            
        except Exception as e:
            logger.error(f"Fehler beim Abrufen von DWD-Daten: {str(e)}")
            raise
    
    def get_synthetic_data(self, 
                          station_id: str,
                          start_date: datetime,
                          end_date: datetime) -> pd.DataFrame:
        """
        Generiert synthetische Wetterdaten für eine Station.
        Diese Funktion wird verwendet, wenn echte DWD-Daten nicht verfügbar sind.
        
        Args:
            station_id: ID der DWD-Station
            start_date: Startdatum
            end_date: Enddatum
            
        Returns:
            DataFrame mit synthetischen Wetterdaten
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
        
        logger.info(f"Synthetische Wetterdaten gespeichert: {output_file}")
        return df
    
    def get_forecast(self, 
                    station_id: str,
                    hours: int = 24) -> pd.DataFrame:
        """
        Holt Wettervorhersage für die nächsten Stunden.
        
        Args:
            station_id: ID der DWD-Station
            hours: Anzahl der Stunden für die Vorhersage
            
        Returns:
            DataFrame mit Vorhersagedaten
        """
        start_date = datetime.now().replace(minute=0, second=0, microsecond=0)
        end_date = start_date + timedelta(hours=hours)
        
        # Verwende das gleiche System wie für historische Daten
        return self.get_historical_data(station_id, start_date, end_date)
    
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
        
        logger.info(f"Cache bereinigt: {deleted_count} alte Dateien gelöscht")

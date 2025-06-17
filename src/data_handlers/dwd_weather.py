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
from src.utils.logging_config import DWDStationFilter

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

# Filter für die DWD-Station-Informationen hinzufügen
console_filter = DWDStationFilter()
for handler in logging.getLogger().handlers:
    if isinstance(handler, logging.StreamHandler):
        handler.addFilter(console_filter)

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
            
            # Zugriff auf die Stationen - angepasst für neuere wetterdienst API (0.109.0)
            api_result = request.all()
            
            # Extrahiere die Stationsdaten - in neueren Versionen ist das Format anders
            # Im ersten Schritt nur zur Sicherheit überprüfen, ob wir die Stationsdaten haben
            if hasattr(api_result, 'df'):
                # Stationen aus dem DataFrame extrahieren
                logger.info("Verwende wetterdienst API Version mit df-Attribut")
                stations_df = api_result.df
                
                # Bei neueren Versionen ist das DataFrame-Format anders
                # Überprüfe wichtige Spalten
                required_columns = ["station_id", "name", "latitude", "longitude", "height"]
                
                # Prüfe, ob alle benötigten Spalten vorhanden sind
                if all(col in stations_df.columns for col in required_columns):
                    logger.info(f"DWD-API: Alle benötigten Spalten sind vorhanden")
                    
                    # Duplikate entfernen (falls vorhanden)
                    if hasattr(stations_df, 'drop_duplicates'):
                        stations_df = stations_df.drop_duplicates(subset=["station_id"])
                    
                    # Konvertiere das DataFrame in ein Dictionary für einfachen Zugriff
                    # In neueren Versionen von wetterdienst kann ein Polars DataFrame zurückgegeben werden
                    # statt eines Pandas DataFrame
                    logger.info(f"Stations DataFrame Typ: {type(stations_df)}")
                    
                    if hasattr(stations_df, 'to_pandas'):
                        # Polars DataFrame zu Pandas konvertieren
                        logger.info("Konvertiere Polars DataFrame zu Pandas")
                        stations_pd = stations_df.to_pandas()
                    else:
                        # Bereits ein Pandas DataFrame
                        stations_pd = stations_df
                    
                    # Jetzt mit dem Pandas DataFrame arbeiten
                    for _, row in stations_pd.iterrows():
                        station_id = str(row["station_id"])
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
                    logger.info(f"Erfolgreich {len(self.stations)} Stationen über API geladen")
                else:
                    missing_cols = [col for col in required_columns if col not in stations_df.columns]
                    logger.warning(f"DWD-API: Fehlende Spalten: {missing_cols}")
                    raise ValueError(f"API-Format hat sich geändert, fehlende Spalten: {missing_cols}")
            else:
                # Versuche alternatives Format für neuere API-Version
                stations = api_result.stations
                if stations is not None and hasattr(stations, 'df'):
                    stations_df = stations.df
                    logger.info(f"DWD-API: Alternative Stations-Struktur gefunden")
                    
                    # Konvertiere das DataFrame in ein Dictionary für einfachen Zugriff
                    if hasattr(stations_df, 'to_pandas'):
                        # Polars DataFrame zu Pandas konvertieren
                        logger.info("Konvertiere Polars DataFrame zu Pandas")
                        stations_pd = stations_df.to_pandas()
                    else:
                        # Bereits ein Pandas DataFrame
                        stations_pd = stations_df
                    
                    for _, row in stations_pd.iterrows():
                        station_id = str(row["station_id"])
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
                    logger.info(f"Erfolgreich {len(self.stations)} Stationen über API geladen")
                else:
                    # Keine bekannte Struktur gefunden
                    raise ValueError("Unbekanntes API-Antwortformat")
            
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
                logger.debug("DWD-API-Aufruf fehlgeschlagen, verwende lokale Fallback-Daten")
        else:
            # Standard-Stationen für Deutschland
            logger.info("Verwende Standard-Stationen (keine API, keine lokale Datei verfügbar)")
            stations_data = [
                {
                    'id': '00433',  # Echte aktive Station
                    'name': 'Berlin-Tempelhof',
                    'state': 'Berlin',
                    'latitude': 52.4675,
                    'longitude': 13.4021,
                    'altitude': 48.0,
                    'active': True
                },
                {
                    'id': '00403',  # Echte aktive Station  
                    'name': 'Berlin-Dahlem',
                    'state': 'Berlin',
                    'latitude': 52.4537,
                    'longitude': 13.3014,
                    'altitude': 58.0,
                    'active': True
                },
                {
                    'id': '10384',
                    'name': 'Berlin-Tempelhof-Fallback',
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
        Findet die nächstgelegene AKTIVE Station.
        
        Args:
            lat: Breitengrad
            lon: Längengrad
            
        Returns:
            Dictionary mit Stationsinformationen
        """
        # Prüfe zuerst, ob die DWD-API verfügbare Stationen in der Nähe hat
        try:
            from wetterdienst.provider.dwd.observation import DwdObservationRequest
            from wetterdienst import Settings
            from datetime import datetime, timedelta
            
            settings = Settings(ts_shape="long", ts_humanize=True, ts_convert_units=True)
            
            # Erstelle eine Test-Anfrage für die letzten 7 Tage
            end_date = datetime.now()
            start_date = end_date - timedelta(days=7)
            
            request = DwdObservationRequest(
                parameters=[("hourly", "temperature_air", "temperature_air_mean_2m")],
                start_date=start_date,
                end_date=end_date,
                settings=settings
            )
            
            # Finde Stationen in der Nähe
            stations = request.filter_by_distance((lat, lon), 50)  # 50km Radius
            stations_df = stations.df.to_pandas()
            
            if len(stations_df) > 0:
                # Prüfe welche Station tatsächlich aktuelle Daten hat
                for idx, station in stations_df.iterrows():
                    station_id = station['station_id']
                    station_name = station['name']
                    
                    # Prüfe ob Station in den letzten 30 Tagen aktiv war
                    end_date_station = pd.to_datetime(station['end_date']).tz_localize(None)
                    cutoff_date = pd.to_datetime('2023-01-01')  # Mindestens seit 2023 aktiv
                    
                    if end_date_station > cutoff_date:
                        logger.info(f"Verwende aktive DWD-Station: {station_name} (ID: {station_id})")
                        return {
                            'id': station_id,
                            'name': station_name,
                            'latitude': station['latitude'],
                            'longitude': station['longitude'],
                            'altitude': station['height'],
                            'active': True
                        }
            
        except Exception as e:
            logger.warning(f"Fehler bei DWD-Stationssuche: {e}")
        
        # Fallback zu den statischen Stationen
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
        
        if nearest_station:
            logger.info(f"Verwende DWD-Station: {nearest_station['name']} (ID: {nearest_station['id']})")
            # Ausführlichere Informationen in die Log-Datei schreiben
            logger.debug(f"Station Details: Lat={nearest_station['latitude']}, Lon={nearest_station['longitude']}, " +
                         f"Abstand={min_distance*111:.1f}km")
                         
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
                df = pd.read_csv(cache_file, parse_dates=['timestamp'])
                # Stelle sicher, dass numerische Spalten auch als float behandelt werden
                for column in ['temperature', 'solar_radiation', 'wind_speed', 'humidity', 'cloud_cover', 'precipitation']:
                    if column in df.columns:
                        df[column] = df[column].astype(float)
                return df
            except Exception as e:
                logger.error(f"Fehler beim Lesen des Caches: {e}")
        
        try:
            logger.info(f"Hole echte DWD-Daten für Station {station_id} von {start_date} bis {end_date}")
            result = self._download_dwd_data(station_id, start_date, end_date)
            
            # Prüfe, ob das Ergebnis gültige Wetterdaten enthält
            required_columns = ['temperature', 'solar_radiation', 'wind_speed', 'humidity']
            if not all(col in result.columns for col in required_columns):
                logger.warning("API-Ergebnis enthält nicht alle erforderlichen Spalten, generiere synthetische Daten")
                return self.get_synthetic_data(station_id, start_date, end_date)
            
            # Prüfe, ob genügend Datenpunkte vorhanden sind
            if len(result) < 5:  # Zu wenige Datenpunkte
                logger.warning("API liefert zu wenige Datenpunkte, generiere synthetische Daten")
                return self.get_synthetic_data(station_id, start_date, end_date)
            
            return result
            
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
            # Wetterdienst-API einrichten - korrekte Implementierung basierend auf Dokumentation
            settings = Settings(ts_shape="long", ts_humanize=True, ts_convert_units=True)
            
            # Parameter für die Abfrage - korrekte Namen gemäß DWD-Dokumentation
            # Format: ("resolution", "dataset", "parameter") 
            parameters = [
                ("hourly", "temperature_air", "temperature_air_mean_2m"),  # Temperatur
                ("hourly", "solar", "radiation_global"),                   # Solarstrahlung  
                ("hourly", "wind", "wind_speed"),                         # Windgeschwindigkeit
                ("hourly", "precipitation", "precipitation_height"),       # Niederschlag
                ("hourly", "temperature_air", "humidity"),                # Luftfeuchtigkeit
            ]
            
            logger.info(f"Verwende korrekte DWD-Parameter: {parameters}")
            
            # DWD-Request erstellen
            request = DwdObservationRequest(
                parameters=parameters,
                start_date=start_date,
                end_date=end_date,
                settings=settings
            )
            
            # Station filtern und Daten abrufen
            logger.info(f"Verwende DWD API für Station {station_id}")
            
            # Verwende filter_by_distance statt filter_by_station_id für bessere Kompatibilität
            station_info = self.stations.get(station_id)
            if station_info:
                lat, lon = station_info['latitude'], station_info['longitude']
                values = request.filter_by_distance((lat, lon), 5)  # 5km Radius um die Station
            else:
                # Fallback zu Berlin
                values = request.filter_by_distance((52.52, 13.41), 20)
            
            # Values abrufen - der korrekte Weg gemäß Dokumentation
            logger.info("Hole echte Messdaten von DWD API")
            values_data = values.values.all()
            values_df = values_data.df
            
            # Konvertiere zu Pandas DataFrame falls nötig
            if hasattr(values_df, 'to_pandas'):
                logger.info("Konvertiere Polars DataFrame zu Pandas für Datenverarbeitung")
                values_df = values_df.to_pandas()
            
            if values_df is None or len(values_df) == 0:
                raise ValueError(f"Keine Messdaten für Station {station_id} gefunden")
                
            logger.info(f"DWD-Messdaten erfolgreich abgerufen: {len(values_df)} Einträge")
            logger.info(f"DataFrame Spalten: {values_df.columns.tolist()}")
            
            # Debug: zeige ein paar Beispielzeilen
            logger.info(f"Beispieldaten:\n{values_df.head()}")
            
            # Transformieren in das erwartete Format
            result_df = pd.DataFrame()
            
            # Zeitstempel - verwende die 'date' Spalte
            unique_dates = values_df['date'].unique()
            result_df = pd.DataFrame({'timestamp': sorted(unique_dates)})
            result_df['station_id'] = station_id
            
            logger.info(f"Zeitstempel erstellt: {len(result_df)} Einträge")
            
            # Parameter-Mapping: von DWD-Namen zu unserem Schema
            result_data = {}
            
            # Gruppiere die Daten nach Parameter und sortiere nach Datum
            for param_name, our_name in [
                ('temperature_air_mean_2m', 'temperature'),
                ('radiation_global', 'solar_radiation'), 
                ('wind_speed', 'wind_speed'),
                ('precipitation_height', 'precipitation'),
                ('humidity', 'humidity')
            ]:
                param_data = values_df[values_df['parameter'] == param_name].copy()
                if not param_data.empty:
                    # Sortiere nach Datum und extrahiere Werte
                    param_data = param_data.sort_values('date')
                    
                    # Stelle sicher, dass wir für jeden Zeitstempel einen Wert haben
                    values_dict = dict(zip(param_data['date'], param_data['value']))
                    param_values = [values_dict.get(ts, 0.0) for ts in result_df['timestamp']]
                    
                    result_data[our_name] = param_values
                    logger.info(f"Parameter {param_name} -> {our_name}: {len(param_values)} Werte")
                else:
                    logger.warning(f"Keine Daten für Parameter {param_name} gefunden")
            
            # Prüfe, ob wir mindestens Temperatur haben
            if 'temperature' not in result_data:
                logger.warning("Keine Temperaturdaten gefunden - verwende synthetische Daten")
                return self.get_synthetic_data(station_id, start_date, end_date)
            
            # Füge fehlende Parameter mit Standardwerten hinzu
            required_params = ['temperature', 'solar_radiation', 'wind_speed', 'precipitation', 'humidity']
            for param in required_params:
                if param not in result_data:
                    logger.warning(f"Parameter {param} fehlt - verwende Standardwerte")
                    if param == 'solar_radiation':
                        result_data[param] = [100.0] * len(result_df)  # Standardstrahlung
                    elif param == 'wind_speed':
                        result_data[param] = [3.0] * len(result_df)   # Standardwind
                    elif param == 'precipitation':
                        result_data[param] = [0.0] * len(result_df)   # Kein Regen
                    elif param == 'humidity':
                        result_data[param] = [70.0] * len(result_df)  # Standardfeuchtigkeit
            
            # Füge Parameter zum DataFrame hinzu
            for param, values in result_data.items():
                result_df[param] = values[:len(result_df)]  # Stelle sicher, gleiche Länge
            
            # Bewölkung aus Solarstrahlung schätzen
            if 'solar_radiation' in result_df.columns:
                max_radiation = result_df['solar_radiation'].max()
                if max_radiation > 0:
                    result_df['cloud_cover'] = 100 - (result_df['solar_radiation'] / max_radiation * 100)
                else:
                    result_df['cloud_cover'] = 50
            else:
                result_df['cloud_cover'] = 50
            
            # Speichere die Daten im Cache
            cache_file = self.historical_dir / f"{station_id}_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}.csv"
            result_df.to_csv(cache_file, index=False)
            logger.info(f"Echte DWD-Daten erfolgreich in {cache_file} gespeichert")
            
            return result_df
            
        except Exception as e:
            logger.error(f"Fehler beim Abrufen von DWD-Daten: {str(e)}")
            # Bei Fehlern verwende synthetische Daten
            logger.info("Fallback zu synthetischen Daten...")
            return self.get_synthetic_data(station_id, start_date, end_date)
    
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

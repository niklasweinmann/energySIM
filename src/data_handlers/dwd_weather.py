"""
DWD (Deutscher Wetterdienst) Wetterdaten-Integration.
Implementiert nach den OpenData-Spezifikationen des DWD.
"""

import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import json
import os
import ftplib
from dateutil.parser import parse

class DWDStation:
    """Repräsentiert eine DWD-Wetterstation nach CDC (Climate Data Center) Format."""
    
    def __init__(self, station_id: str, name: str, latitude: float, longitude: float, altitude: float):
        self.id = station_id
        self.name = name
        self.latitude = latitude
        self.longitude = longitude
        self.altitude = altitude

class DWDWeatherAPI:
    """
    Interface zum Deutschen Wetterdienst (DWD) OpenData Server.
    Implementiert nach den technischen Spezifikationen des DWD.
    """
    
    BASE_URL = "https://opendata.dwd.de/climate_environment/CDC"
    FTP_SERVER = "opendata.dwd.de"
    
    def __init__(self, cache_dir: str = None):
        if cache_dir is None:
            # Projektverzeichnis ermitteln
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            cache_dir = os.path.join(project_root, "data", "weather", "dwd_cache")
        
        self.cache_dir = cache_dir
        self._ensure_cache_dir()
        self.stations: Dict[str, DWDStation] = {}
        self._load_station_list()
    
    def _ensure_cache_dir(self):
        """Erstellt Cache-Verzeichnis falls nicht vorhanden."""
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)
    
    def _load_station_list(self):
        """Lädt die Liste aller DWD-Stationen."""
        stations_file = os.path.join(self.cache_dir, "stations.json")
        
        if os.path.exists(stations_file):
            with open(stations_file, 'r', encoding='utf-8') as f:
                stations_data = json.load(f)
                for station in stations_data:
                    self.stations[station['id']] = DWDStation(
                        station['id'],
                        station['name'],
                        station['latitude'],
                        station['longitude'],
                        station['altitude']
                    )
        else:
            # Lade Stationsliste vom DWD-Server
            ftp = ftplib.FTP(self.FTP_SERVER)
            ftp.login()
            
            # Navigiere zum Stationsverzeichnis
            ftp.cwd("/climate_environment/CDC/observations_germany/climate/hourly")
            
            # Lade Stationsliste
            station_file = "TU_Stundenwerte_Beschreibung_Stationen.txt"
            with open(os.path.join(self.cache_dir, station_file), 'wb') as f:
                ftp.retrbinary(f'RETR {station_file}', f.write)
            
            # Verarbeite Stationsdaten
            stations_data = []
            with open(os.path.join(self.cache_dir, station_file), 'r', encoding='utf-8') as f:
                next(f)  # Überspringe Header
                for line in f:
                    parts = line.strip().split()
                    if len(parts) >= 6:
                        station = {
                            'id': parts[0],
                            'name': parts[1],
                            'latitude': float(parts[2]),
                            'longitude': float(parts[3]),
                            'altitude': float(parts[4])
                        }
                        stations_data.append(station)
                        self.stations[station['id']] = DWDStation(**station)
            
            # Speichere Stationsliste im Cache
            with open(stations_file, 'w', encoding='utf-8') as f:
                json.dump(stations_data, f, ensure_ascii=False, indent=2)
            
            ftp.quit()
    
    def get_hourly_data(self, station_id: str, parameter: str, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """
        Lädt stündliche Wetterdaten für eine bestimmte Station.
        
        Args:
            station_id: ID der DWD-Station
            parameter: Wetterparameter (z.B. 'air_temperature', 'precipitation', 'solar')
            start_date: Startdatum
            end_date: Enddatum
            
        Returns:
            DataFrame mit stündlichen Wetterdaten
        """
        cache_file = os.path.join(
            self.cache_dir, 
            f"hourly_{station_id}_{parameter}_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}.parquet"
        )
        
        if os.path.exists(cache_file):
            return pd.read_parquet(cache_file)
            
        # DWD-Pfadstruktur für stündliche Daten
        path = f"/climate_environment/CDC/observations_germany/climate/hourly/{parameter}/recent/"
        filename = f"stundenwerte_{parameter}_{station_id}_akt.zip"
        
        url = f"{self.BASE_URL}{path}{filename}"
        response = requests.get(url)
        
        if response.status_code == 200:
            # Temporäre Datei für ZIP-Download
            temp_zip = os.path.join(self.cache_dir, "temp.zip")
            with open(temp_zip, 'wb') as f:
                f.write(response.content)
            
            # Daten einlesen und verarbeiten
            df = pd.read_csv(temp_zip, sep=';', skiprows=2, na_values='-999')
            os.remove(temp_zip)
            
            # Zeitstempel konvertieren
            df['MESS_DATUM'] = pd.to_datetime(df['MESS_DATUM'].astype(str), format='%Y%m%d%H')
            
            # Daten filtern
            mask = (df['MESS_DATUM'] >= start_date) & (df['MESS_DATUM'] <= end_date)
            df = df[mask]
            
            # Cache speichern
            df.to_parquet(cache_file)
            return df
        else:
            raise Exception(f"Fehler beim Abrufen der DWD-Daten: {response.status_code}")
    
    def find_nearest_station(self, latitude: float, longitude: float) -> DWDStation:
        """
        Findet die nächstgelegene DWD-Station zu den gegebenen Koordinaten.
        
        Args:
            latitude: Breitengrad
            longitude: Längengrad
            
        Returns:
            DWDStation-Objekt der nächstgelegenen Station
        """
        min_distance = float('inf')
        nearest_station = None
        
        for station in self.stations.values():
            distance = self._haversine_distance(
                latitude, longitude,
                station.latitude, station.longitude
            )
            if distance < min_distance:
                min_distance = distance
                nearest_station = station
        
        return nearest_station
    
    def _haversine_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        Berechnet die Entfernung zwischen zwei Koordinaten mittels Haversine-Formel.
        
        Returns:
            Entfernung in Kilometern
        """
        R = 6371  # Erdradius in km
        
        lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
        
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        a = np.sin(dlat/2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon/2)**2
        c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1-a))
        
        return R * c
    
    def get_historical_data(self,
                          station: DWDStation,
                          start_date: datetime,
                          end_date: datetime) -> pd.DataFrame:
        """
        Lädt historische Wetterdaten einer Station.
        
        Args:
            station: DWD-Station
            start_date: Startdatum
            end_date: Enddatum
            
        Returns:
            DataFrame mit Wetterdaten
        """
        # Cache-Dateiname
        cache_file = os.path.join(
            self.cache_dir,
            f"hist_{station.id}_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}.csv"
        )
        
        if os.path.exists(cache_file):
            return pd.read_csv(cache_file, parse_dates=['timestamp'])
        
        # Lade Daten vom DWD-Server
        ftp = ftplib.FTP(self.FTP_SERVER)
        ftp.login()
        
        # Parameter für verschiedene Messgrößen
        parameters = {
            'air_temperature': 'TU',
            'solar': 'ST',
            'wind': 'FF',
            'precipitation': 'RR'
        }
        
        data_frames = []
        
        for param, code in parameters.items():
            path = f"/climate_environment/CDC/observations_germany/climate/hourly/{code}/historical"
            ftp.cwd(path)
            
            # Finde relevante Datei
            files = []
            ftp.retrlines('NLST', files.append)
            
            target_file = None
            for file in files:
                if file.startswith(f"{code}_{station.id}"):
                    target_file = file
                    break
            
            if target_file:
                local_file = os.path.join(self.cache_dir, target_file)
                with open(local_file, 'wb') as f:
                    ftp.retrbinary(f'RETR {target_file}', f.write)
                
                # Lese und verarbeite Daten
                df = pd.read_csv(local_file, sep=';', skiprows=2)
                df['timestamp'] = pd.to_datetime(df['MESS_DATUM'], format='%Y%m%d%H')
                
                # Selektiere relevante Spalten
                if param == 'air_temperature':
                    df = df[['timestamp', 'TT_TU']]
                    df.columns = ['timestamp', 'temperature']
                elif param == 'solar':
                    df = df[['timestamp', 'FG_LBERG']]
                    df.columns = ['timestamp', 'solar_radiation']
                elif param == 'wind':
                    df = df[['timestamp', 'F']]
                    df.columns = ['timestamp', 'wind_speed']
                elif param == 'precipitation':
                    df = df[['timestamp', 'R1']]
                    df.columns = ['timestamp', 'precipitation']
                
                data_frames.append(df)
        
        ftp.quit()
        
        # Kombiniere alle Daten
        combined_data = data_frames[0]
        for df in data_frames[1:]:
            combined_data = pd.merge(combined_data, df, on='timestamp', how='outer')
        
        # Filtere Zeitbereich
        mask = (combined_data['timestamp'] >= start_date) & (combined_data['timestamp'] <= end_date)
        combined_data = combined_data[mask]
        
        # Interpoliere fehlende Werte
        combined_data = combined_data.interpolate(method='linear')
        
        # Speichere im Cache
        combined_data.to_csv(cache_file, index=False)
        
        return combined_data
    
    def get_forecast(self,
                    station: DWDStation,
                    hours: int = 24) -> pd.DataFrame:
        """
        Lädt Wettervorhersage für eine Station.
        
        Args:
            station: DWD-Station
            hours: Anzahl der Vorhersagestunden
            
        Returns:
            DataFrame mit Vorhersagedaten
        """
        # MOSMIX-Vorhersage-API des DWD
        url = f"{self.BASE_URL}/weather/forecasts/mosmix/{station.id}/kml"
        
        try:
            response = requests.get(url)
            response.raise_for_status()
            
            # Verarbeite KML-Daten (vereinfacht)
            forecast_data = []
            # TODO: Implementiere KML-Parser für MOSMIX-Daten
            
            return pd.DataFrame(forecast_data)
            
        except requests.exceptions.RequestException as e:
            print(f"Fehler beim Laden der Vorhersage: {e}")
            return pd.DataFrame()

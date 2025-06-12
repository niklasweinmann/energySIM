"""
Wetteranalyse-Modul für die Verarbeitung von DWD-Daten.
Implementiert nach VDI 4655 für die Erstellung von Referenzlastprofilen.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from datetime import datetime
from ..data_handlers.dwd_weather import DWDWeatherAPI

class WeatherAnalyzer:
    """
    Analysiert Wetterdaten nach VDI 4655 für Energiesimulationen.
    """
    
    def __init__(self, dwd_api: DWDWeatherAPI):
        self.dwd_api = dwd_api
        
    def create_reference_year(self, latitude: float, longitude: float) -> pd.DataFrame:
        """
        Erstellt ein Referenzjahr nach VDI 4655 für den gegebenen Standort.
        
        Args:
            latitude: Breitengrad des Standorts
            longitude: Längengrad des Standorts
            
        Returns:
            DataFrame mit stündlichen Wetterdaten für das Referenzjahr
        """
        station = self.dwd_api.find_nearest_station(latitude, longitude)
        
        # Zeitraum für die Analyse (letzte 10 Jahre)
        end_date = datetime.now()
        start_date = datetime(end_date.year - 10, 1, 1)
        
        # Wetterdaten abrufen
        temp_data = self.dwd_api.get_hourly_data(
            station.id, 'air_temperature',
            start_date, end_date
        )
        solar_data = self.dwd_api.get_hourly_data(
            station.id, 'solar',
            start_date, end_date
        )
        
        # Daten zusammenführen
        weather_data = pd.merge(
            temp_data, solar_data,
            on='MESS_DATUM',
            suffixes=('_temp', '_solar')
        )
        
        # Tagestypen nach VDI 4655 klassifizieren
        weather_data['day_type'] = self._classify_day_types(weather_data)
        
        # Referenzjahr erstellen
        reference_year = self._select_reference_days(weather_data)
        
        return reference_year
    
    def _classify_day_types(self, weather_data: pd.DataFrame) -> pd.Series:
        """
        Klassifiziert Tage nach VDI 4655 in:
        - Werktag/Wochenende
        - Übergangszeit/Winter/Sommer
        - Bewölkt/Heiter
        
        Returns:
            Series mit Tagestyp-Klassifikationen
        """
        # Tagesmitteltemperaturen berechnen
        daily_temp = weather_data.groupby(
            weather_data['MESS_DATUM'].dt.date
        )['TT_TU'].mean()
        
        # Tagestypen bestimmen
        day_types = []
        for date, temp in daily_temp.items():
            # Werktag/Wochenende
            is_weekend = pd.Timestamp(date).weekday() >= 5
            
            # Jahreszeit
            if temp < 5:
                season = 'winter'
            elif temp > 15:
                season = 'summer'
            else:
                season = 'transition'
                
            day_type = f"{'weekend' if is_weekend else 'workday'}_{season}"
            day_types.append(day_type)
        
        return pd.Series(day_types, index=daily_temp.index)
    
    def _select_reference_days(self, weather_data: pd.DataFrame) -> pd.DataFrame:
        """
        Wählt repräsentative Tage für jede Kategorie nach VDI 4655 aus.
        
        Returns:
            DataFrame mit Referenzjahr-Daten
        """
        reference_days = pd.DataFrame()
        
        # Für jeden Tagestyp den repräsentativsten Tag auswählen
        for day_type in weather_data['day_type'].unique():
            type_data = weather_data[weather_data['day_type'] == day_type]
            
            # Mittlere Temperatur und Strahlung für den Tagestyp
            mean_temp = type_data['TT_TU'].mean()
            mean_rad = type_data['FG_LBERG'].mean()
            
            # Tag mit geringster Abweichung vom Mittel finden
            best_day = None
            min_deviation = float('inf')
            
            for date in type_data['MESS_DATUM'].dt.date.unique():
                day_data = type_data[type_data['MESS_DATUM'].dt.date == date]
                temp_dev = abs(day_data['TT_TU'].mean() - mean_temp)
                rad_dev = abs(day_data['FG_LBERG'].mean() - mean_rad)
                
                total_dev = temp_dev + rad_dev
                if total_dev < min_deviation:
                    min_deviation = total_dev
                    best_day = day_data
            
            if best_day is not None:
                reference_days = pd.concat([reference_days, best_day])
        
        return reference_days.sort_values('MESS_DATUM')

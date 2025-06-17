"""
Vereinfachtes Wetteranalyse-Modul für die Verarbeitung von DWD-Daten.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from ..data_handlers.dwd_weather import DWDDataManager

class WeatherAnalyzer:
    """
    Analysiert Wetterdaten für Energiesimulationen.
    """
    
    def __init__(self, dwd_manager: DWDDataManager = None):
        if dwd_manager is None:
            self.dwd_manager = DWDDataManager()
        else:
            self.dwd_manager = dwd_manager
        
    def create_reference_year(self, latitude: float, longitude: float) -> pd.DataFrame:
        """
        Erstellt ein vereinfachtes Referenzjahr für den gegebenen Standort.
        
        Args:
            latitude: Breitengrad des Standorts
            longitude: Längengrad des Standorts
            
        Returns:
            DataFrame mit stündlichen Wetterdaten für das Referenzjahr
        """
        # Finde nächstgelegene Station
        station = self.dwd_manager.find_nearest_station(latitude, longitude)
        if not station:
            raise ValueError("Keine geeignete Station gefunden")
        
        # Generiere ein Jahr synthetischer Daten
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 12, 31)
        
        weather_data = self.dwd_manager.get_synthetic_data(
            station['id'], start_date, end_date
        )
        
        # Einfache Tagestyp-Klassifikation
        weather_data['day_type'] = self._classify_day_types(weather_data)
        
        return weather_data
    
    def _classify_day_types(self, weather_data: pd.DataFrame) -> pd.Series:
        """
        Vereinfachte Klassifikation von Tagen.
        
        Returns:
            Series mit Tagestyp-Klassifikationen
        """
        # Konvertiere timestamp zu datetime falls nötig
        if 'timestamp' in weather_data.columns:
            timestamps = pd.to_datetime(weather_data['timestamp'])
        else:
            timestamps = weather_data.index
        
        # Tagesmitteltemperaturen berechnen  
        daily_data = weather_data.groupby(timestamps.dt.date).agg({
            'temperature': 'mean',
            'solar_radiation': 'mean'
        })
        
        # Tagestypen bestimmen
        day_types = []
        for date, row in daily_data.iterrows():
            temp = row['temperature']
            
            # Werktag/Wochenende
            is_weekend = pd.Timestamp(date).weekday() >= 5
            
            # Jahreszeit basierend auf Temperatur
            if temp < 5:
                season = 'winter'
            elif temp > 20:
                season = 'summer'
            else:
                season = 'transition'
                
            day_type = f"{'weekend' if is_weekend else 'workday'}_{season}"
            day_types.append(day_type)
        
        # Erweitere auf stündliche Daten
        hourly_day_types = []
        for i, timestamp in enumerate(timestamps):
            date = timestamp.date()
            day_index = list(daily_data.index).index(date)
            hourly_day_types.append(day_types[day_index])
        
        return pd.Series(hourly_day_types, index=weather_data.index)
    
    def get_typical_days(self, weather_data: pd.DataFrame) -> Dict[str, pd.DataFrame]:
        """
        Extrahiert typische Tage für jede Kategorie.
        
        Returns:
            Dictionary mit typischen Tagen pro Kategorie
        """
        typical_days = {}
        
        for day_type in weather_data['day_type'].unique():
            type_data = weather_data[weather_data['day_type'] == day_type]
            
            if len(type_data) > 24:  # Mindestens ein vollständiger Tag
                # Finde repräsentativsten Tag (mittlere Werte)
                daily_groups = type_data.groupby(
                    pd.to_datetime(type_data['timestamp']).dt.date
                )
                
                best_day = None
                best_score = float('inf')
                
                for date, day_data in daily_groups:
                    if len(day_data) >= 20:  # Fast vollständiger Tag
                        # Score basierend auf Abweichung vom Mittel
                        temp_mean = type_data['temperature'].mean()
                        rad_mean = type_data['solar_radiation'].mean()
                        
                        temp_dev = abs(day_data['temperature'].mean() - temp_mean)
                        rad_dev = abs(day_data['solar_radiation'].mean() - rad_mean)
                        
                        score = temp_dev + rad_dev / 100  # Normalisierung
                        
                        if score < best_score:
                            best_score = score
                            best_day = day_data
                
                if best_day is not None:
                    typical_days[day_type] = best_day
        
        return typical_days
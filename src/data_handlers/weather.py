from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List, Optional, Tuple
import pandas as pd
import numpy as np
import logging
from .dwd_enhanced import DWDDataManager
try:
    from .dwd_enhanced_real import DWDRealDataManager
    REAL_DWD_AVAILABLE = True
except ImportError:
    REAL_DWD_AVAILABLE = False

# Logger konfigurieren
logger = logging.getLogger(__name__)

@dataclass
class WeatherData:
    """Struktur für Wetterdaten nach DWD-Standard."""
    timestamp: datetime
    temperature: float  # °C
    solar_radiation: float  # W/m²
    humidity: float  # %
    wind_speed: float  # m/s
    cloud_cover: float  # %
    precipitation: float  # mm/h

class WeatherDataHandler:
    """Klasse zur Verwaltung von Wetterdaten mit DWD-Integration."""
    
    def __init__(self, use_dwd: bool = True, use_real_api: bool = True):
        """
        Initialisiert den WeatherDataHandler.
        
        Args:
            use_dwd: Ob DWD-Daten verwendet werden sollen
            use_real_api: Ob die echte DWD-API anstelle synthetischer Daten verwendet werden soll
        """
        self.cached_data: pd.DataFrame = pd.DataFrame()
        self.use_dwd = use_dwd
        self.use_real_api = use_real_api and REAL_DWD_AVAILABLE
        
        if self.use_dwd:
            if self.use_real_api:
                logger.info("Verwende echte DWD-API für Wetterdaten")
                try:
                    self.dwd_manager = DWDRealDataManager()
                except Exception as e:
                    logger.error(f"Fehler beim Initialisieren der echten DWD-API: {e}")
                    logger.info("Fallback auf synthetische Daten")
                    self.use_real_api = False
                    self.dwd_manager = DWDDataManager()
            else:
                logger.info("Verwende synthetische DWD-Daten")
                self.dwd_manager = DWDDataManager()
        else:
            self.dwd_manager = None
    
    def get_historical_data(self, 
                          location: tuple[float, float],
                          start_date: datetime,
                          end_date: datetime) -> pd.DataFrame:
        """
        Lädt Wetterdaten für einen bestimmten Zeitraum.
        
        Args:
            location: Tuple mit (Breitengrad, Längengrad)
            start_date: Startdatum
            end_date: Enddatum
            
        Returns:
            DataFrame mit Wetterdaten
        """
        if self.use_dwd and self.dwd_manager:
            # Verwende DWD-Daten
            latitude, longitude = location
            
            # Finde nächstgelegene Station
            nearest_station = self.dwd_manager.find_nearest_station(latitude, longitude)
            if not nearest_station:
                logger.error("Keine DWD-Station in der Nähe gefunden")
                raise ValueError("Keine DWD-Station in der Nähe gefunden")
            
            logger.info(f"Verwende DWD-Station: {nearest_station['name']} (ID: {nearest_station['id']})")
            print(f"Verwende DWD-Station: {nearest_station['name']} (ID: {nearest_station['id']})")
            
            # Lade Daten für die Station
            data = self.dwd_manager.get_historical_data(
                nearest_station['id'], 
                start_date, 
                end_date
            )
            
            # Cache aktualisieren
            self.cached_data = data
            
            return data
        else:
            # Fallback auf synthetische Daten
            logger.info("Verwende selbstgenerierte synthetische Daten")
            return self._generate_synthetic_data(location, start_date, end_date)
    
    def _generate_synthetic_data(self, 
                               location: tuple[float, float],
                               start_date: datetime,
                               end_date: datetime) -> pd.DataFrame:
        """
        Generiert synthetische Wetterdaten als Fallback.
        """
        # Generiere stündliche Zeitstempel
        timestamps = pd.date_range(
            start=start_date,
            end=end_date,
            freq='h',  # Verwende 'h' statt 'H' für zukünftige Kompatibilität
            inclusive='left'  # Exkludiere das Ende, um 24 Stunden pro Tag zu haben
        )
        
        # Berechne Tag des Jahres (0-365) für Sonnenstand
        day_of_year = timestamps.dayofyear.values
        hour_of_day = timestamps.hour.values
        
        # Temperaturmodell
        base_temp = 20  # Basistemperatur
        yearly_amplitude = 10  # Jahresschwankung
        daily_amplitude = 5   # Tagesschwankung
        
        # Jahresgang der Temperatur
        yearly_temp = base_temp + yearly_amplitude * np.sin(2 * np.pi * (day_of_year - 180) / 365)
        # Tagesgang
        daily_temp = daily_amplitude * np.sin(2 * np.pi * (hour_of_day - 4) / 24)
        temperature = yearly_temp + daily_temp
        
        # Strahlungsmodell
        max_radiation = 1000  # Maximum Strahlung in W/m²
        max_elevation = 90 - abs(location[0] - 23.5 * np.sin(2 * np.pi * (day_of_year - 172) / 365))
        solar_elevation = max_elevation * np.sin(np.pi * (hour_of_day - 6) / 12)
        solar_elevation = np.clip(solar_elevation, 0, 90)
        solar_radiation = max_radiation * np.sin(np.deg2rad(solar_elevation))
        solar_radiation = np.where((hour_of_day >= 6) & (hour_of_day <= 18), solar_radiation, 0)
        
        # Windmodell (mit Tagesgang)
        base_wind = 3  # Basis-Windgeschwindigkeit in m/s
        wind_speed = base_wind + 2 * np.random.random(len(timestamps)) * \
                    (1 + 0.5 * np.sin(2 * np.pi * (hour_of_day - 12) / 24))
        
        # Luftfeuchtigkeitsmodell (invers korreliert mit Temperatur)
        temp_range = np.max(temperature) - np.min(temperature)
        if temp_range > 0:
            humidity = 80 - (temperature - np.min(temperature)) / temp_range * 30
        else:
            humidity = np.full_like(temperature, 80)
        
        humidity += np.random.normal(0, 5, len(timestamps))
        humidity = np.clip(humidity, 30, 100)
        
        # Bewölkungsmodell (zufällig mit Tagesgang)
        cloud_base = 40 + 20 * np.sin(2 * np.pi * (hour_of_day - 12) / 24)
        cloud_cover = np.clip(cloud_base + np.random.normal(0, 20, len(timestamps)), 0, 100)
        
        # Niederschlagsmodell (einfach)
        precipitation = np.random.exponential(0.1, len(timestamps)) * (cloud_cover > 70)
        
        # Erstelle DataFrame mit Timestamp als Index und Spalte
        data = pd.DataFrame({
            'timestamp': timestamps,
            'temperature': temperature,
            'solar_radiation': solar_radiation,
            'wind_speed': wind_speed,
            'humidity': humidity,
            'cloud_cover': cloud_cover,
            'precipitation': precipitation
        })
        
        # Aktualisiere Cache
        self.cached_data = data
        
        return data
    
    def get_forecast(self, 
                    location: tuple[float, float],
                    hours: int = 24) -> pd.DataFrame:
        """
        Holt Wettervorhersage für die nächsten Stunden.
        Nutzt das gleiche System wie historische Daten.
        
        Args:
            location: Tuple mit (Breitengrad, Längengrad)
            hours: Anzahl der Stunden für die Vorhersage
            
        Returns:
            DataFrame mit Vorhersagedaten
        """
        start_date = datetime.now().replace(minute=0, second=0, microsecond=0)
        end_date = start_date + timedelta(hours=hours)
        
        # Verwende das gleiche System wie für historische Daten
        return self.get_historical_data(location, start_date, end_date)

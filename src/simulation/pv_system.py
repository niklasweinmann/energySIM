from dataclasses import dataclass
from typing import Optional
import numpy as np
import pvlib

@dataclass
class PVModuleSpecifications:
    """Technische Spezifikationen eines PV-Moduls."""
    peak_power: float  # Wp
    area: float  # m²
    efficiency_stc: float  # % bei Standard-Testbedingungen
    temp_coefficient: float  # %/°C Temperaturkoeffizient
    noct: float = 45.0  # °C Nominal Operating Cell Temperature

@dataclass
class PVArrayConfiguration:
    """Konfiguration einer PV-Anlage."""
    modules_count: int
    tilt: float  # Neigungswinkel in Grad
    azimuth: float  # Azimutwinkel in Grad (0=Nord, 90=Ost, 180=Süd, 270=West)
    albedo: float = 0.2  # Bodenreflexion

class PVSystem:
    """Simulation einer Photovoltaik-Anlage."""
    
    def __init__(self, 
                module_specs: PVModuleSpecifications,
                config: PVArrayConfiguration,
                location: tuple[float, float],  # (latitude, longitude)
                altitude: float):  # Höhe über Meeresspiegel in m
        self.specs = module_specs
        self.config = config
        self.location = location
        self.altitude = altitude
        
        # Gesamtleistung der Anlage
        self.total_peak_power = self.specs.peak_power * self.config.modules_count
        self.total_area = self.specs.area * self.config.modules_count
        
        # PVlib Solar Position Calculator
        self.solar_position = pvlib.solarposition.SolarPosition
        
    def calculate_cell_temperature(self,
                                ambient_temp: float,
                                solar_irradiance: float,
                                wind_speed: float) -> float:
        """
        Berechnet die Zelltemperatur basierend auf Umgebungsbedingungen.
        
        Args:
            ambient_temp: Umgebungstemperatur in °C
            solar_irradiance: Solare Einstrahlung in W/m²
            wind_speed: Windgeschwindigkeit in m/s
            
        Returns:
            Zelltemperatur in °C
        """
        # Vereinfachtes NOCT-Modell mit Windkorrektur
        wind_correction = max(1.0, wind_speed) / 1.0  # Normierung auf 1 m/s
        delta_t = (self.specs.noct - 20) * (solar_irradiance / 800) / wind_correction
        return ambient_temp + delta_t
        
    def calculate_power_output(self,
                            solar_irradiance: float,
                            ambient_temp: float,
                            wind_speed: float,
                            timestamp) -> tuple[float, float]:
        """
        Berechnet die Leistungsabgabe der PV-Anlage.
        
        Args:
            solar_irradiance: Direkte + diffuse Strahlung auf der Modulfläche in W/m²
            ambient_temp: Umgebungstemperatur in °C
            wind_speed: Windgeschwindigkeit in m/s
            timestamp: Zeitstempel für Sonnenposition
            
        Returns:
            Tuple aus (DC_Leistung, AC_Leistung) in kW
        """
        # Sonnenposition berechnen
        solar_pos = self.solar_position.get_solarposition(
            timestamp,
            self.location[0],
            self.location[1],
            self.altitude
        )
        
        # Einfallswinkelkorrektur
        aoi = pvlib.irradiance.aoi(
            self.config.tilt,
            self.config.azimuth,
            solar_pos['apparent_zenith'],
            solar_pos['azimuth']
        )
        
        # Einfallswinkel-Verluste
        iam = pvlib.iam.physical(aoi, n=1.526, K=4.0)  # Physikalisches IAM-Modell
        
        # Zelltemperatur
        cell_temp = self.calculate_cell_temperature(ambient_temp, solar_irradiance, wind_speed)
        
        # Temperatur-Verluste
        temp_loss = 1 + (self.specs.temp_coefficient / 100) * (cell_temp - 25)
        
        # DC-Leistung berechnen
        dc_power = (self.total_peak_power / 1000 *  # Umrechnung in kW
                   (solar_irradiance / 1000) *  # Normierung auf STC
                   iam *  # Einfallswinkel-Verluste
                   temp_loss)  # Temperatur-Verluste
        
        # Vereinfachte Wechselrichter-Verluste (95% Wirkungsgrad)
        ac_power = dc_power * 0.95
        
        return max(0, dc_power), max(0, ac_power)
    
    def estimate_yearly_yield(self,
                           yearly_radiation: float,  # kWh/m²/Jahr
                           avg_temp: float,  # °C
                           system_losses: float = 0.14  # 14% Systemverluste
                           ) -> float:
        """
        Schätzt den jährlichen Energieertrag.
        
        Args:
            yearly_radiation: Jährliche Einstrahlung auf der Modulfläche
            avg_temp: Durchschnittstemperatur
            system_losses: Systemverluste (Verschmutzung, Leitungen, etc.)
            
        Returns:
            Geschätzter Jahresertrag in kWh
        """
        # Vereinfachte Berechnung nach der PR-Methode (Performance Ratio)
        temp_loss = 1 + (self.specs.temp_coefficient / 100) * (avg_temp - 25)
        pr = (1 - system_losses) * temp_loss
        
        return (self.total_peak_power / 1000) * yearly_radiation * pr

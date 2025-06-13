"""
Simulation of a photovoltaic system.
"""

from dataclasses import dataclass
from typing import Optional, Tuple
import numpy as np
from datetime import datetime
import pvlib
import pandas as pd

@dataclass
class PVModuleSpecifications:
    """Technical specifications of a PV module."""
    peak_power: float  # Wp
    area: float  # m²
    efficiency_stc: float  # % at standard test conditions
    temp_coefficient: float  # %/°C temperature coefficient
    noct: float = 45.0  # °C Nominal Operating Cell Temperature

@dataclass
class PVArrayConfiguration:
    """Configuration of a PV array."""
    modules_count: int
    tilt: float  # Tilt angle in degrees
    azimuth: float  # Azimuth angle in degrees (0=North, 90=East, 180=South, 270=West)
    albedo: float = 0.2  # Ground reflection

class PVSystem:
    """Simulation of a photovoltaic system."""
    
    def __init__(self, 
                module_specs: PVModuleSpecifications,
                config: PVArrayConfiguration,
                location: tuple[float, float],  # (latitude, longitude)
                altitude: float) -> None:  # Height above sea level in m
        """Initialize the PV system.
        
        Args:
            module_specs: Technical specifications of the PV modules
            config: Configuration of the PV array
            location: (latitude, longitude) tuple
            altitude: Height above sea level in meters
        """
        self.specs = module_specs
        self.config = config
        self.location = location
        self.altitude = altitude
        
        # Calculate total system capacity
        self.total_peak_power = self.specs.peak_power * self.config.modules_count
        self.total_area = self.specs.area * self.config.modules_count
        
        # Initialize pvlib components
        self.location_info = pvlib.location.Location(
            latitude=location[0],
            longitude=location[1],
            altitude=altitude,
            tz='Europe/Berlin'
        )
        
        self.surface_tilt = config.tilt
        self.surface_azimuth = config.azimuth

    def get_irradiance(self, 
                      timestamp: datetime,
                      weather_data: dict) -> tuple[float, float, float]:
        """Calculate irradiance on the tilted module surface.
        
        Args:
            timestamp: Current timestamp
            weather_data: Dictionary with weather data (ghi, dni, dhi)
            
        Returns:
            Tuple of (poa_global, poa_direct, poa_diffuse) in W/m²
        """
        # Calculate solar position
        solar_position = self.location_info.get_solarposition(timestamp)
        
        # Calculate irradiance on tilted surface
        poa_irradiance = pvlib.irradiance.get_total_irradiance(
            surface_tilt=self.surface_tilt,
            surface_azimuth=self.surface_azimuth,
            solar_zenith=solar_position['zenith'],
            solar_azimuth=solar_position['azimuth'],
            dni=weather_data['dni'],
            ghi=weather_data['ghi'],
            dhi=weather_data['dhi'],
            albedo=self.config.albedo
        )
        
        return (poa_irradiance['poa_global'],
                poa_irradiance['poa_direct'],
                poa_irradiance['poa_diffuse'])

    def calculate_cell_temperature(self,
                                ambient_temp: float,
                                solar_irradiance: float,
                                wind_speed: float = 1.0) -> float:
        """Calculate cell temperature based on environmental conditions.
        
        Args:
            ambient_temp: Ambient temperature in °C
            solar_irradiance: Irradiance in W/m²
            wind_speed: Wind speed in m/s (Optional, default = 1.0 m/s)
            
        Returns:
            Cell temperature in °C
        """
        # Simplified NOCT model with wind correction
        wind_correction = np.sqrt(wind_speed / 1.0)  # Correction relative to 1 m/s
        delta_t = (self.specs.noct - 20) * (solar_irradiance / 800) / wind_correction
        return ambient_temp + delta_t
    
    def calculate_power_output(self,
                            timestamp: datetime,
                            weather_data: dict) -> tuple[float, float]:
        """Calculate power output of the PV system.
        
        Args:
            timestamp: Timestamp for solar position calculation
            weather_data: Dictionary with weather data:
                - ghi: Global horizontal irradiance in W/m²
                - dni: Direct normal irradiance in W/m²
                - dhi: Diffuse horizontal irradiance in W/m²
                - temp_air: Air temperature in °C
                - wind_speed: Wind speed in m/s
            
        Returns:
            Tuple of (DC_power, AC_power) in kW
        """
        # Calculate irradiance on tilted surface
        poa_global, poa_direct, poa_diffuse = self.get_irradiance(
            timestamp,
            weather_data
        )
        
        # Calculate solar position
        solar_pos = self.location_info.get_solarposition(timestamp)
        
        # Calculate angle of incidence correction
        aoi = pvlib.irradiance.aoi(
            surface_tilt=self.surface_tilt,
            surface_azimuth=self.surface_azimuth,
            solar_zenith=solar_pos['apparent_zenith'],
            solar_azimuth=solar_pos['azimuth']
        )
        
        # Calculate incidence angle losses
        iam = pvlib.iam.physical(aoi, n=1.526, K=4.0)  # Physical IAM model
        
        # Calculate cell temperature
        cell_temp = self.calculate_cell_temperature(
            weather_data['temp_air'],
            poa_global,
            weather_data.get('wind_speed', 1.0)
        )
        
        # Calculate temperature losses
        temp_loss = 1 + (self.specs.temp_coefficient / 100) * (cell_temp - 25)
        
        # Calculate DC power
        dc_power = (self.total_peak_power / 1000 *  # Convert to kW
                   (poa_global / 1000) *  # Normalize to STC
                   iam *  # Incidence angle losses
                   temp_loss *  # Temperature losses
                   0.95)  # Other losses (soiling, mismatch, etc.)
        
        # Apply simplified inverter losses (95% efficiency)
        ac_power = dc_power * 0.95
        
        # Ensure non-negative values using numpy operations
        dc_power = dc_power.clip(lower=0)
        ac_power = ac_power.clip(lower=0)
        
        return dc_power, ac_power
    
    def estimate_yearly_yield(self,
                           yearly_radiation: float,  # kWh/m²/year
                           avg_temp: float,  # °C
                           system_losses: float = 0.14  # 14% system losses
                           ) -> float:
        """Estimate annual energy yield.
        
        Args:
            yearly_radiation: Annual irradiation on module surface
            avg_temp: Average temperature
            system_losses: System losses (soiling, wiring, etc.)
            
        Returns:
            Estimated annual yield in kWh
        """
        # Simple calculation using the PR method (Performance Ratio)
        temp_loss = 1 + (self.specs.temp_coefficient / 100) * (avg_temp - 25)
        pr = (1 - system_losses) * temp_loss
        
        return (self.total_peak_power / 1000) * yearly_radiation * pr

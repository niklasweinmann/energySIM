"""
Simulation of a photovoltaic system.
Uses real component data from the components database.
"""

from dataclasses import dataclass
from typing import Optional, Tuple, Dict, Any
import numpy as np
from datetime import datetime
import pandas as pd
from src.data_handlers.components import ComponentsDatabase

try:
    import pvlib
    PVLIB_AVAILABLE = True
except ImportError:
    PVLIB_AVAILABLE = False
    print("Warning: pvlib not available. Using simplified PV calculations.")

@dataclass
class PVModuleSpecifications:
    """Technical specifications of a PV module."""
    manufacturer: str
    model: str
    peak_power: float  # Wp
    area: float  # m²
    efficiency: float  # % at standard test conditions
    temp_coefficient: float  # %/°C temperature coefficient
    noct: float = 45.0  # °C Nominal Operating Cell Temperature
    warranty_years: int = 25
    
    @classmethod
    def from_database(cls, module_key: str, db: ComponentsDatabase) -> 'PVModuleSpecifications':
        """Create PVModuleSpecifications from database entry."""
        module = db.get_pv_module(module_key)
        if module is None:
            raise ValueError(f"PV module {module_key} not found in database")
        
        return cls(
            manufacturer=module.manufacturer,
            model=module.model,
            peak_power=module.peak_power,
            area=module.area,
            efficiency=module.efficiency,
            temp_coefficient=module.temp_coefficient,
            noct=module.noct,
            warranty_years=module.warranty_years
        )

@dataclass
class InverterSpecifications:
    """Technical specifications of an inverter."""
    manufacturer: str
    model: str
    nominal_ac_power: float  # W
    max_dc_power: float  # W
    euro_efficiency: float
    max_efficiency: float
    mppt_channels: int
    voltage_range: tuple[float, float]
    warranty_years: int = 10
    
    @classmethod
    def from_database(cls, inverter_key: str, db: ComponentsDatabase) -> 'InverterSpecifications':
        """Create InverterSpecifications from database entry."""
        inverter = db.get_inverter(inverter_key)
        if inverter is None:
            raise ValueError(f"Inverter {inverter_key} not found in database")
        
        return cls(
            manufacturer=inverter.manufacturer,
            model=inverter.model,
            nominal_ac_power=inverter.nominal_ac_power,
            max_dc_power=inverter.max_dc_power,
            euro_efficiency=inverter.euro_efficiency,
            max_efficiency=inverter.max_efficiency,
            mppt_channels=inverter.mppt_channels,
            voltage_range=inverter.voltage_range,
            warranty_years=inverter.warranty_years
        )

@dataclass
class PVArrayConfiguration:
    """Configuration of a PV array."""
    modules_count: int
    tilt: float  # Tilt angle in degrees
    azimuth: float  # Azimuth angle in degrees (0=North, 90=East, 180=South, 270=West)
    albedo: float = 0.2  # Ground reflection
    module_key: str = "SunPower_MAX6_440"  # Default module from database
    inverter_key: str = "SMA_Sunny_Tripower_10"  # Default inverter from database

class PVSystem:
    """Simulation of a photovoltaic system with real component data."""
    
    def __init__(self, 
                config: PVArrayConfiguration,
                location: tuple[float, float],  # (latitude, longitude)
                altitude: float,  # Height above sea level in m
                components_db: Optional[ComponentsDatabase] = None) -> None:
        """Initialize the PV system.
        
        Args:
            config: Configuration of the PV array
            location: (latitude, longitude) tuple
            altitude: Height above sea level in meters
            components_db: Optional components database instance
        """
        # Initialize components database if not provided
        if components_db is None:
            components_db = ComponentsDatabase()
        
        # Load component specifications from database
        self.module_specs = PVModuleSpecifications.from_database(
            config.module_key, 
            components_db
        )
        self.inverter_specs = InverterSpecifications.from_database(
            config.inverter_key,
            components_db
        )
        
        self.config = config
        self.location = location
        self.altitude = altitude
        
        # Calculate total system capacity
        self.total_peak_power = self.module_specs.peak_power * self.config.modules_count
        self.total_area = self.module_specs.area * self.config.modules_count
        
        # Initialize pvlib location info if available
        if PVLIB_AVAILABLE:
            self.location_info = pvlib.location.Location(
                latitude=location[0], 
                longitude=location[1], 
                altitude=altitude
            )
        else:
            raise ImportError("pvlib is required for PV calculations but not available")

    def get_irradiance(self, 
                      timestamp: datetime,
                      weather_data: dict) -> tuple[float, float, float]:
        """Calculate irradiance on the tilted module surface using pvlib.
        
        Args:
            timestamp: Current timestamp
            weather_data: Dictionary with weather data (ghi, dni, dhi)
            
        Returns:
            Tuple of (poa_global, poa_direct, poa_diffuse) in W/m²
        """
        # Calculate solar position using pvlib
        solar_position = self.location_info.get_solarposition(timestamp)
        
        # Calculate irradiance on tilted surface using pvlib
        poa_irradiance = pvlib.irradiance.get_total_irradiance(
            surface_tilt=self.config.tilt,
            surface_azimuth=self.config.azimuth,
            solar_zenith=solar_position['zenith'].iloc[0] if hasattr(solar_position['zenith'], 'iloc') else solar_position['zenith'],
            solar_azimuth=solar_position['azimuth'].iloc[0] if hasattr(solar_position['azimuth'], 'iloc') else solar_position['azimuth'],
            dni=weather_data.get('dni', weather_data.get('ghi', 0) * 0.85),  # Fallback if DNI not available
            ghi=weather_data.get('ghi', 0),
            dhi=weather_data.get('dhi', weather_data.get('ghi', 0) * 0.15),  # Fallback if DHI not available
            albedo=self.config.albedo
        )
        
        return (poa_irradiance['poa_global'],
                poa_irradiance['poa_direct'],
                poa_irradiance['poa_diffuse'])

    def calculate_cell_temperature(self,
                                ambient_temp: float,
                                solar_irradiance: float,
                                wind_speed: float = 1.0) -> float:
        """Calculate cell temperature using pvlib models.
        
        Args:
            ambient_temp: Ambient temperature in °C
            solar_irradiance: Irradiance in W/m²
            wind_speed: Wind speed in m/s (Optional, default = 1.0 m/s)
            
        Returns:
            Cell temperature in °C
        """
        # Use pvlib's NOCT model
        cell_temp = pvlib.temperature.noct_sam(
            poa_global=solar_irradiance,
            temp_air=ambient_temp,
            wind_speed=wind_speed,
            noct=self.module_specs.noct,
            module_efficiency=self.module_specs.efficiency
        )
        return cell_temp
    
    def calculate_power_output(self,
                            timestamp: datetime,
                            weather_data: dict) -> tuple[float, float]:
        """Calculate power output of the PV system using pvlib.
        
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
        # Extract weather data
        ghi = weather_data.get('ghi', 0)
        dni = weather_data.get('dni', ghi * 0.85)  # Fallback estimate
        dhi = weather_data.get('dhi', ghi * 0.15)  # Fallback estimate
        temp_air = weather_data.get('temp_air', 25)
        wind_speed = weather_data.get('wind_speed', 1.0)
        
        # Calculate plane of array irradiance
        poa_global, poa_direct, poa_diffuse = self.get_irradiance(timestamp, {
            'ghi': ghi, 'dni': dni, 'dhi': dhi
        })
        
        # Calculate cell temperature
        cell_temp = self.calculate_cell_temperature(temp_air, poa_global, wind_speed)
        
        # Calculate DC power using pvlib photovoltaic model
        # Use simplified Single Diode Model
        photocurrent, saturation_current, resistance_series, resistance_shunt, nNsVth = (
            pvlib.pvsystem.calcparams_desoto(
                effective_irradiance=poa_global,
                temp_cell=cell_temp,
                alpha_sc=self.module_specs.temp_coefficient / 100 * self.module_specs.peak_power / 1000,  # A/°C
                a_ref=1.5,  # Diode ideality factor
                I_L_ref=8.0,  # Light current at reference conditions (A)
                I_o_ref=1e-10,  # Dark current at reference conditions (A)
                R_sh_ref=400,  # Shunt resistance at reference conditions (Ohm)
                R_s=0.4,  # Series resistance (Ohm)
                EgRef=1.121,  # Band gap energy at reference temperature (eV)
                dEgdT=-0.0002677  # Temperature coefficient of band gap (eV/°C)
            )
        )
        
        # Calculate I-V curve and find maximum power point using the newer recommended functions
        # Ersetze 'singlediode' mit separaten v_from_i & i_from_v Berechnungen
        # Erstelle ein Spannungsarray und berechne die entsprechenden Ströme
        v = np.linspace(0, 40, 100)  # Spannungsbereich von 0-40V mit 100 Punkten
        i = pvlib.pvsystem.i_from_v(
            v, photocurrent, saturation_current, resistance_series, 
            resistance_shunt, nNsVth
        )
        p = v * i  # Berechne Leistung
        
        # Finde MPP (Maximum Power Point)
        idx_max_p = np.argmax(p)
        dc_voltage, dc_current = v[idx_max_p], i[idx_max_p]
        
        # Simplified approach: Use temperature-corrected power
        temp_coefficient = self.module_specs.temp_coefficient / 100  # Convert from %/°C to 1/°C
        temp_factor = 1 + temp_coefficient * (cell_temp - 25)
        
        # DC power calculation
        dc_power_per_module = (self.module_specs.peak_power * 
                              (poa_global / 1000) *  # Irradiance factor
                              temp_factor *  # Temperature factor
                              0.95)  # Module mismatch and soiling losses
        
        dc_power_total = dc_power_per_module * self.config.modules_count / 1000  # Convert to kW
        
        # Calculate AC power using inverter efficiency
        # Use pvlib inverter model for more accuracy
        ac_power = pvlib.inverter.sandia(
            v_dc=dc_voltage if 'dc_voltage' in locals() else 400,  # Assume 400V DC
            p_dc=dc_power_total * 1000,  # Convert back to W for pvlib
            inverter={
                'Paco': self.inverter_specs.nominal_ac_power,
                'Pdco': self.inverter_specs.max_dc_power,
                'Vdco': 400,  # DC voltage at max power
                'Pso': self.inverter_specs.nominal_ac_power * 0.02,  # Standby power
                'C0': -0.000005,  # Curvature coefficient
                'C1': -0.000005,  # Curvature coefficient
                'C2': 0.0001,     # Curvature coefficient
                'C3': 0.005,      # Curvature coefficient
                'Pnt': 0.1        # Night tare loss
            }
        ) / 1000  # Convert back to kW
        
        # Fallback to simple efficiency calculation if Sandia model fails
        if np.isnan(ac_power) or ac_power < 0:
            ac_power = dc_power_total * self.inverter_specs.euro_efficiency
        
        # Ensure non-negative values
        dc_power_total = max(0, dc_power_total)
        ac_power = max(0, ac_power)
        
        return dc_power_total, ac_power
    
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
        temp_loss = 1 + (self.module_specs.temp_coefficient / 100) * (avg_temp - 25)
        pr = (1 - system_losses) * temp_loss
        
        return (self.total_peak_power / 1000) * yearly_radiation * pr

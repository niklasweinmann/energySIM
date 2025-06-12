"""
Zentrale Normenbibliothek für energyOS.
Enthält Konstanten und Berechnungsmethoden nach deutschen/europäischen Normen.
"""

from dataclasses import dataclass
from typing import Dict, Optional
import math

@dataclass
class EnEVRequirements:
    """Anforderungen nach Energieeinsparverordnung (EnEV)."""
    max_primary_energy_demand: float = 75.0  # kWh/(m²·a) Primärenergiebedarf
    max_transmission_heat_loss: float = 0.4  # W/(m²·K) Transmissionswärmeverlust
    min_room_temp: float = 20.0  # °C
    min_summer_heat_protection: float = 0.07  # Sonneneintragskennwert

@dataclass
class DIN4108:
    """Wärmeschutz im Hochbau - DIN 4108."""
    min_insulation_thickness: Dict[str, float] = None  # m
    max_u_values: Dict[str, float] = None
    min_air_exchange_rate: float = 0.5  # 1/h
    
    def __post_init__(self):
        self.max_u_values = {
            'exterior_wall': 0.24,  # W/(m²·K)
            'roof': 0.20,
            'floor': 0.30,
            'windows': 1.30,
            'doors': 1.80
        }
        self.min_insulation_thickness = {
            'exterior_wall': 0.14,  # m
            'roof': 0.18,
            'floor': 0.12
        }

@dataclass
class DIN1946:
    """Raumlufttechnik - DIN 1946-6."""
    min_air_flow_rates: Dict[str, float] = None
    max_air_velocity: float = 0.15  # m/s bei 20°C
    
    def __post_init__(self):
        self.min_air_flow_rates = {
            'living_room': 30,  # m³/h pro Person
            'bedroom': 20,
            'kitchen': 40,
            'bathroom': 40
        }

@dataclass
class VDI2067:
    """Wirtschaftlichkeit gebäudetechnischer Anlagen - VDI 2067."""
    calculation_period: int = 20  # Jahre
    interest_rate: float = 0.02  # 2%
    maintenance_factor: Dict[str, float] = None
    
    def __post_init__(self):
        self.maintenance_factor = {
            'heat_pump': 0.025,  # 2.5% der Investitionskosten
            'pv_system': 0.015,
            'solar_thermal': 0.02,
            'storage': 0.01
        }

@dataclass
class VDI6002:
    """Solare Trinkwassererwärmung - VDI 6002."""
    min_solar_coverage: float = 0.60  # 60% solarer Deckungsgrad
    max_stagnation_temp: float = 130.0  # °C
    min_storage_volume: float = 50.0  # L/m² Kollektorfläche

@dataclass
class DIN15316:
    """Heizungsanlagen in Gebäuden - DIN EN 15316."""
    distribution_losses: Dict[str, float] = None
    storage_losses: Dict[str, float] = None
    
    def __post_init__(self):
        self.distribution_losses = {
            'space_heating': 0.1,  # 10% Verteilungsverluste
            'dhw': 0.15
        }
        self.storage_losses = {
            'buffer': 0.15,  # kWh/(m³·d)
            'dhw': 0.2
        }

class NormCalculator:
    """Berechnungsmethoden nach Normen."""
    
    def __init__(self):
        self.enev = EnEVRequirements()
        self.din4108 = DIN4108()
        self.din1946 = DIN1946()
        self.vdi2067 = VDI2067()
        self.vdi6002 = VDI6002()
        self.din15316 = DIN15316()
    
    def calculate_u_value(self,
                        layer_thicknesses: list[float],
                        layer_conductivities: list[float],
                        rsi: float = 0.13,
                        rse: float = 0.04) -> float:
        """
        Berechnet U-Wert nach DIN EN ISO 6946.
        
        Args:
            layer_thicknesses: Schichtdicken in m
            layer_conductivities: Wärmeleitfähigkeiten in W/(m·K)
            rsi: Innerer Wärmeübergangswiderstand in (m²·K)/W
            rse: Äußerer Wärmeübergangswiderstand in (m²·K)/W
        
        Returns:
            U-Wert in W/(m²·K)
        """
        r_total = rsi + rse
        for d, lambda_ in zip(layer_thicknesses, layer_conductivities):
            r_total += d / lambda_
        return 1 / r_total
    
    def calculate_heat_load(self,
                         volume: float,
                         u_values: Dict[str, float],
                         areas: Dict[str, float],
                         air_exchange_rate: float,
                         inside_temp: float,
                         outside_temp: float) -> float:
        """
        Berechnet Heizlast nach DIN EN 12831.
        
        Args:
            volume: Gebäudevolumen in m³
            u_values: U-Werte der Bauteile in W/(m²·K)
            areas: Flächen der Bauteile in m²
            air_exchange_rate: Luftwechselrate in 1/h
            inside_temp: Innentemperatur in °C
            outside_temp: Außentemperatur in °C
            
        Returns:
            Heizlast in kW
        """
        # Transmissionswärmeverluste
        trans_loss = 0
        for component, u_value in u_values.items():
            area = areas[component]
            trans_loss += u_value * area * (inside_temp - outside_temp)
        
        # Lüftungswärmeverluste
        vent_loss = 0.34 * air_exchange_rate * volume * (inside_temp - outside_temp)
        
        total_loss = (trans_loss + vent_loss) / 1000  # Umrechnung in kW
        return total_loss
    
    def calculate_solar_gains(self,
                           window_areas: Dict[str, float],
                           g_values: Dict[str, float],
                           radiation: Dict[str, float],
                           shading_factors: Dict[str, float]) -> float:
        """
        Berechnet solare Wärmegewinne nach DIN EN ISO 13790.
        
        Args:
            window_areas: Fensterflächen nach Orientierung in m²
            g_values: g-Werte der Fenster
            radiation: Solare Einstrahlung nach Orientierung in W/m²
            shading_factors: Verschattungsfaktoren
            
        Returns:
            Solare Wärmegewinne in kW
        """
        solar_gains = 0
        for orientation in window_areas.keys():
            solar_gains += (window_areas[orientation] *
                          g_values[orientation] *
                          radiation[orientation] *
                          shading_factors[orientation])
        return solar_gains / 1000  # Umrechnung in kW
    
    def calculate_primary_energy_demand(self,
                                    final_energy: float,
                                    energy_source: str) -> float:
        """
        Berechnet Primärenergiebedarf nach DIN V 18599-1.
        
        Args:
            final_energy: Endenergiebedarf in kWh
            energy_source: Energieträger
            
        Returns:
            Primärenergiebedarf in kWh
        """
        primary_energy_factors = {
            'electricity': 1.8,
            'natural_gas': 1.1,
            'oil': 1.1,
            'wood_pellets': 0.2,
            'district_heating': 0.7
        }
        return final_energy * primary_energy_factors.get(energy_source, 1.0)

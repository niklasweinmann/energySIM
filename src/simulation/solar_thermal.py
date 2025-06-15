from dataclasses import dataclass
from typing import Dict, Optional, Tuple
import numpy as np
from src.core.standards import VDI6002, DIN15316

@dataclass
class SolarThermalSpecifications:
    """Technische Spezifikationen eines Solarthermie-Kollektors nach EN 12975."""
    area: float  # m² Aperturfläche
    optical_efficiency: float  # η0 optischer Wirkungsgrad
    heat_loss_coefficient_a1: float  # W/(m²·K) linearer Wärmeverlustkoeffizient
    heat_loss_coefficient_a2: float  # W/(m²·K²) quadratischer Wärmeverlustkoeffizient
    incident_angle_modifier: float  # IAM bei 50°
    specific_heat_capacity: float = 3.6  # kJ/(kg·K) Wärmekapazität Wärmeträger

@dataclass
class StorageSpecifications:
    """Spezifikationen des Solarthermie-Speichers nach DIN EN 12977-3."""
    volume: float  # m³
    height: float  # m
    insulation_thickness: float  # m
    insulation_conductivity: float  # W/(m·K)
    heat_loss_rate: float  # W/K Wärmeverlustkoeffizient
    stratification_efficiency: float  # Schichtungswirkungsgrad
    
class SolarThermalSystem:
    """Simulation einer Solarthermieanlage nach VDI 6002."""
    
    def __init__(self,
                collector_specs: SolarThermalSpecifications,
                storage_specs: StorageSpecifications,
                location: tuple[float, float],  # (latitude, longitude)
                tilt: float,  # Neigungswinkel in Grad
                azimuth: float):  # Azimutwinkel in Grad
        self.collector = collector_specs
        self.storage = storage_specs
        self.location = location
        self.tilt = tilt
        self.azimuth = azimuth
        
        # Normen
        self.vdi6002 = VDI6002()
        self.din15316 = DIN15316()
        
        # Betriebszustände
        self.collector_temp: float = 20.0
        self.storage_temps: list[float] = [45.0] * 10  # 10 Schichten
        self.flow_rate: float = 0.02  # kg/s pro m²
        
    def calculate_collector_efficiency(self,
                                   delta_t: float,  # K Temperaturdifferenz
                                   solar_irradiance: float  # W/m²
                                   ) -> float:
        """
        Berechnet den Kollektorwirkungsgrad nach EN 12975.
        
        Args:
            delta_t: Temperaturdifferenz (Kollektor - Umgebung) in K
            solar_irradiance: Solare Einstrahlung in W/m²
            
        Returns:
            Kollektorwirkungsgrad
        """
        if solar_irradiance < 1:
            return 0.0
            
        efficiency = (self.collector.optical_efficiency -
                     (self.collector.heat_loss_coefficient_a1 * delta_t +
                      self.collector.heat_loss_coefficient_a2 * delta_t**2) /
                     solar_irradiance)
        return max(0, efficiency)
    
    def calculate_thermal_power(self,
                             solar_irradiance: float,  # W/m²
                             ambient_temp: float,  # °C
                             flow_temp: float  # °C
                             ) -> tuple[float, float]:
        """
        Berechnet die thermische Leistung des Kollektorfeldes.
        
        Args:
            solar_irradiance: Solare Einstrahlung in W/m²
            ambient_temp: Umgebungstemperatur in °C
            flow_temp: Vorlauftemperatur in °C
            
        Returns:
            Tuple aus (thermische_Leistung in kW, Kollektortemperatur in °C)
        """
        # Stagnationsschutz nach VDI 6002
        if self.collector_temp >= self.vdi6002.max_stagnation_temp:
            # Bei Stagnation kein Durchfluss und keine Leistung
            max_temp = ambient_temp + solar_irradiance * self.collector.optical_efficiency / self.collector.heat_loss_coefficient_a1
            self.collector_temp = min(max_temp, self.vdi6002.max_stagnation_temp)
            return 0.0, self.collector_temp
        
        # Thermisches Gleichgewicht berechnen
        if self.flow_rate > 0:
            # Mit Durchfluss: Vorlauftemperatur + Temperaturhub
            delta_t = flow_temp - ambient_temp
            efficiency = self.calculate_collector_efficiency(delta_t, solar_irradiance)
            power = (efficiency * solar_irradiance * self.collector.area) / 1000  # kW
            
            # Temperaturanstieg durch thermische Leistung (begrenzt durch Verluste)
            max_temp_rise = solar_irradiance * self.collector.optical_efficiency / (
                self.collector.heat_loss_coefficient_a1 + 
                self.collector.heat_loss_coefficient_a2 * (flow_temp - ambient_temp)
            )
            temp_rise = min(
                power * 1000 / (self.flow_rate * self.collector.specific_heat_capacity),
                max_temp_rise
            )
            
            new_temp = flow_temp + temp_rise
            if new_temp > self.vdi6002.max_stagnation_temp:
                # Reduziere Leistung wenn maximale Temperatur überschritten
                power *= (self.vdi6002.max_stagnation_temp - flow_temp) / temp_rise
                new_temp = self.vdi6002.max_stagnation_temp
            
            self.collector_temp = new_temp
        else:
            # Ohne Durchfluss: Stagnationstemperatur
            max_temp = ambient_temp + solar_irradiance * self.collector.optical_efficiency / self.collector.heat_loss_coefficient_a1
            self.collector_temp = min(max_temp, self.vdi6002.max_stagnation_temp)
            power = 0.0
        
        return power, self.collector_temp
    
    def update_storage(self,
                     thermal_power: float,
                     dhw_demand: float,
                     time_step: float = 3600  # Zeitschritt in Sekunden
                     ) -> tuple[float, list[float]]:
        """
        Aktualisiert den Speicherzustand nach DIN EN 12977-3.
        
        Args:
            thermal_power: Thermische Leistung in kW
            dhw_demand: Warmwasserbedarf in kW
            time_step: Zeitschritt in Sekunden
            
        Returns:
            Tuple aus (nutzbare_Leistung in kW, Schichttemperaturen in °C)
        """
        # Wärmeverluste nach DIN 15316
        storage_losses = (self.storage.heat_loss_rate *
                        (np.mean(self.storage_temps) - 20.0) *  # 20°C Umgebungstemp.
                        time_step / 3600) / 1000  # kWh -> kW
        
        # Energiebilanz
        energy_in = thermal_power * time_step / 3600  # kWh
        energy_out = (dhw_demand + storage_losses) * time_step / 3600  # kWh
        
        # Temperaturschichtung
        volume_per_layer = self.storage.volume / len(self.storage_temps)
        energy_per_layer = energy_in / len(self.storage_temps)
        
        for i in range(len(self.storage_temps)):
            # Temperaturänderung durch Zu-/Abfuhr
            delta_t = (energy_per_layer - energy_out/len(self.storage_temps)) / (
                volume_per_layer * 1000 * 4.18  # Wasser: 4.18 kJ/(kg·K)
            )
            self.storage_temps[i] += delta_t
            
            # Minimale Temperatur nach DVGW W551
            self.storage_temps[i] = max(self.storage_temps[i], 60.0)
        
        return max(0, dhw_demand), self.storage_temps
    
    def calculate_solar_fraction(self,
                              total_demand: float,  # kWh
                              solar_contribution: float  # kWh
                              ) -> float:
        """
        Berechnet den solaren Deckungsgrad nach VDI 6002.
        
        Args:
            total_demand: Gesamtwärmebedarf in kWh
            solar_contribution: Solarer Beitrag in kWh
            
        Returns:
            Solarer Deckungsgrad
        """
        if total_demand <= 0:
            return 0.0
            
        solar_fraction = solar_contribution / total_demand
        return min(solar_fraction, 1.0)

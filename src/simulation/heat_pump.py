import numpy as np
from dataclasses import dataclass
from typing import Optional

@dataclass
class HeatPumpSpecifications:
    """Technische Spezifikationen einer Wärmepumpe nach VDI 4645."""
    nominal_heating_power: float  # kW
    cop_rating_points: dict  # {(outside_temp, flow_temp): cop}
    min_outside_temp: float  # °C
    max_flow_temp: float  # °C
    min_part_load_ratio: float  # Minimale Teillast (0-1)
    defrost_temp_threshold: float = 7.0  # °C, Temperatur unter der Abtauung nötig ist
    thermal_mass: float = 20.0  # kWh/K, Thermische Masse des Heizsystems
    
class HeatPump:
    """
    Simulation einer Wärmepumpe nach VDI 4645.
    Implementiert:
    - COP-Berechnung
    - Teillastverhalten
    - Abtauzyklen
    - Thermische Trägheit
    """
    
    def __init__(self, specs: HeatPumpSpecifications):
        self.specs = specs
        self.current_power: float = 0.0
        self.current_cop: float = 0.0
        self.current_flow_temp: float = 35.0
        self.is_defrosting: bool = False
        self.defrost_energy: float = 0.0
        self.runtime: float = 0.0
        
    def calculate_cop(self, outside_temp: float, flow_temp: float) -> float:
        """
        Berechnet den COP basierend auf Außen- und Vorlauftemperatur.
        Berücksichtigt Teillastverhalten und Abtauzyklen.
        
        Args:
            outside_temp: Außentemperatur in °C
            flow_temp: Vorlauftemperatur in °C
            
        Returns:
            Coefficient of Performance (COP)
        """
        # Prüfe Betriebsgrenzen
        if outside_temp < self.specs.min_outside_temp or flow_temp > self.specs.max_flow_temp:
            return 0.0
            
        # Interpolation zwischen den Rating-Punkten
        cops = []
        weights = []
        
        for (rated_outside, rated_flow), rated_cop in self.specs.cop_rating_points.items():
            distance = np.sqrt((outside_temp - rated_outside)**2 + 
                            (flow_temp - rated_flow)**2)
            if distance == 0:
                return rated_cop
            
            weight = 1 / distance
            weights.append(weight)
            cops.append(rated_cop)
            
        base_cop = np.average(cops, weights=weights)
        
        # Korrektur für Abtauung
        if outside_temp < self.specs.defrost_temp_threshold:
            defrost_factor = 1.0 - 0.1 * (self.specs.defrost_temp_threshold - outside_temp)
            base_cop *= max(0.5, defrost_factor)
            
        self.current_cop = base_cop
        return self.current_cop
    
    def get_power_output(self, 
                        outside_temp: float,
                        flow_temp: float,
                        demand: float,
                        time_step: float = 1.0  # Stunde
                        ) -> tuple[float, float]:
        """
        Berechnet die Wärmeleistung und den Stromverbrauch.
        
        Args:
            outside_temp: Außentemperatur in °C
            flow_temp: Vorlauftemperatur in °C
            demand: Angeforderter Wärmebedarf in kWh
            time_step: Zeitschritt in Stunden
            
        Returns:
            tuple: (Wärmeleistung in kWh, Stromverbrauch in kWh)
        """
        cop = self.calculate_cop(outside_temp, flow_temp)
        if cop == 0:
            return 0.0, 0.0
            
        # Maximale Leistung unter aktuellen Bedingungen
        max_power = self.specs.nominal_heating_power * (1 + (outside_temp - 7) * 0.03)
        
        # Minimale Leistung durch Teillastgrenze
        min_power = max_power * self.specs.min_part_load_ratio
        
        # Tatsächliche Leistung unter Berücksichtigung der Grenzen
        if demand / time_step < min_power:
            # Taktbetrieb
            runtime_fraction = demand / (min_power * time_step)
            heat_output = demand
            power_input = (heat_output / cop) * (1 + 0.1 * (1 - runtime_fraction))
        else:
            heat_output = min(demand, max_power * time_step)
            power_input = heat_output / cop
            
        # Abtauenergie berücksichtigen
        if outside_temp < self.specs.defrost_temp_threshold:
            defrost_energy = heat_output * 0.1  # 10% der Heizenergie für Abtauung
            heat_output -= defrost_energy
            self.defrost_energy += defrost_energy
            
        self.current_power = heat_output / time_step
        self.current_flow_temp = flow_temp
        self.runtime += time_step
        
        return heat_output, power_input
    
    def calculate_flow_temperature(self, 
                                 outside_temp: float,
                                 target_room_temp: float = 20.0
                                 ) -> float:
        """
        Berechnet die optimale Vorlauftemperatur nach Heizkurve.
        
        Args:
            outside_temp: Außentemperatur in °C
            target_room_temp: Gewünschte Raumtemperatur in °C
            
        Returns:
            Vorlauftemperatur in °C
        """
        # Heizkurve für Fußbodenheizung (35°C bei -15°C)
        base_temp = target_room_temp
        gradient = (35 - base_temp) / 35  # Steilheit der Heizkurve
        
        flow_temp = base_temp + gradient * (20 - outside_temp)
        return min(flow_temp, self.specs.max_flow_temp)
    
    def get_status(self) -> dict:
        """
        Gibt den aktuellen Betriebszustand zurück.
        
        Returns:
            Dictionary mit Betriebsdaten
        """
        return {
            'current_power': self.current_power,
            'current_cop': self.current_cop,
            'flow_temperature': self.current_flow_temp,
            'is_defrosting': self.is_defrosting,
            'defrost_energy': self.defrost_energy,
            'runtime': self.runtime
        }

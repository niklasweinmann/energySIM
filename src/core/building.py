from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
import numpy as np
from src.core.standards import DIN4108, NormCalculator

@dataclass
class Window:
    """Fensterspezifikationen nach DIN EN 673 und DIN EN 410."""
    area: float  # m²
    u_value: float  # W/(m²·K)
    g_value: float  # Gesamtenergiedurchlassgrad
    orientation: str  # N, NE, E, SE, S, SW, W, NW
    shading_factor: float  # Verschattungsfaktor Fs
    frame_factor: float  # Rahmenanteil

@dataclass
class Wall:
    """Wandaufbau nach DIN 4108."""
    area: float  # m²
    orientation: str
    layers: List[tuple[float, float]]  # Liste von (Dicke in m, Lambda in W/(m·K))
    
@dataclass
class Roof:
    """Dachaufbau nach DIN 4108."""
    area: float  # m²
    tilt: float  # Neigung in Grad
    layers: List[tuple[float, float]]  # Liste von (Dicke in m, Lambda in W/(m·K))

@dataclass
class Floor:
    """Bodenaufbau nach DIN 4108."""
    area: float  # m²
    layers: List[tuple[float, float]]  # Liste von (Dicke in m, Lambda in W/(m·K))
    ground_coupling: bool  # Boden an Erdreich grenzend

@dataclass
class BuildingProperties:
    """Gebäudeeigenschaften nach DIN 4108."""
    walls: List[Wall]
    windows: List[Window]
    roof: Roof
    floor: Floor
    volume: float  # m³
    infiltration_rate: float  # 1/h
    thermal_mass: float  # Wh/(m²·K)
    
class Building:
    """Gebäudemodell nach DIN 4108 und DIN EN ISO 13790."""
    
    def __init__(self, properties: BuildingProperties):
        self.properties = properties
        self.room_temperature = 20.0  # Starttemperatur
        self.previous_temperature = 20.0
        self.heat_demand_history = []
        
        # Berechne U-Werte für alle Bauteile
        self.u_values = {}
        self._calculate_u_values()
        
        # Wärmebrücken nach DIN 4108 Beiblatt 2
        self.thermal_bridges = 0.05  # W/(m²·K)
        
        # Berechne thermische Eigenschaften
        self.total_loss_coefficient = self._calculate_total_loss_coefficient()
        self.ventilation_loss_coefficient = self._calculate_ventilation_loss()
        self.effective_thermal_mass = properties.thermal_mass * self.get_total_area()
        
    def _calculate_u_values(self):
        """Berechne U-Werte für alle Bauteile nach DIN 4108."""
        # Wände
        for i, wall in enumerate(self.properties.walls):
            r_si = 0.13  # m²·K/W (Wärmeübergangswiderstand innen)
            r_se = 0.04  # m²·K/W (Wärmeübergangswiderstand außen)
            r_total = r_si + r_se
            
            # Addiere Wärmedurchgangswiderstände der Schichten
            for d, lambda_value in wall.layers:
                r_total += d / lambda_value
                
            self.u_values[f'wall_{i}'] = 1.0 / r_total
        
        # Fenster (direkt aus U-Wert)
        for i, window in enumerate(self.properties.windows):
            self.u_values[f'window_{i}'] = window.u_value
        
        # Dach
        r_si = 0.10  # m²·K/W (Wärmeübergangswiderstand innen, nach oben)
        r_se = 0.04  # m²·K/W (Wärmeübergangswiderstand außen)
        r_total = r_si + r_se
        
        for d, lambda_value in self.properties.roof.layers:
            r_total += d / lambda_value
        
        self.u_values['roof'] = 1.0 / r_total
        
        # Boden
        r_si = 0.17  # m²·K/W (Wärmeübergangswiderstand innen, nach unten)
        r_se = 0.04  # m²·K/W (Wärmeübergangswiderstand außen/Erdreich)
        r_total = r_si + r_se
        
        for d, lambda_value in self.properties.floor.layers:
            r_total += d / lambda_value
            
        if self.properties.floor.ground_coupling:
            r_total += 0.5  # Zusätzlicher Widerstand für Erdreich
            
        self.u_values['floor'] = 1.0 / r_total
    
    def _calculate_total_loss_coefficient(self) -> float:
        """Berechne den Gesamt-Wärmeverlustkoeffizienten in W/K."""
        total_loss = 0.0
        
        # Transmissionsverluste durch Wände
        for i, wall in enumerate(self.properties.walls):
            total_loss += wall.area * self.u_values[f'wall_{i}']
        
        # Transmissionsverluste durch Fenster
        for i, window in enumerate(self.properties.windows):
            total_loss += window.area * self.u_values[f'window_{i}']
        
        # Transmissionsverluste durch Dach
        total_loss += self.properties.roof.area * self.u_values['roof']
        
        # Transmissionsverluste durch Boden
        total_loss += self.properties.floor.area * self.u_values['floor']
        
        # Wärmebrücken nach DIN 4108 Beiblatt 2
        total_loss += self.get_total_area() * self.thermal_bridges
        
        return total_loss
    
    def _calculate_ventilation_loss(self) -> float:
        """Berechne den Lüftungswärmeverlustkoeffizienten in W/K."""
        rho_air = 1.2  # kg/m³
        c_p_air = 1005  # J/(kg·K)
        return self.properties.infiltration_rate * self.properties.volume * rho_air * c_p_air / 3600
    
    def get_total_area(self) -> float:
        """Berechne die Gesamtfläche der thermischen Hülle in m²."""
        total_area = (
            sum(wall.area for wall in self.properties.walls) +
            sum(window.area for window in self.properties.windows) +
            self.properties.roof.area +
            self.properties.floor.area
        )
        return total_area
    
    def calculate_heat_load(self, 
                          outside_temp: float,
                          solar_radiation: Dict[str, float],
                          inside_temp: float = 20.0
                          ) -> Tuple[float, float, float]:
        """
        Berechnet die Heizlast des Gebäudes.
        
        Args:
            outside_temp: Außentemperatur in °C
            solar_radiation: Solare Einstrahlung in W/m² nach Orientierung
            inside_temp: Innentemperatur in °C (Standard: 20°C)
            
        Returns:
            Tuple aus:
            - Transmissionswärmeverluste in W
            - Lüftungswärmeverluste in W
            - Solare Gewinne in W
        """
        # Transmissionsverluste (positiv wenn Wärme nach außen fließt)
        delta_t = inside_temp - outside_temp
        trans_loss = abs(self._calculate_total_loss_coefficient() * delta_t)
        
        # Lüftungsverluste (positiv wenn Wärme nach außen fließt)
        vent_loss = abs(self._calculate_ventilation_loss() * delta_t)
        
        # Solare Gewinne
        solar_gain = 0.0
        for window in self.properties.windows:
            if window.orientation in solar_radiation:
                solar_gain += (window.area * window.g_value * 
                             window.frame_factor * window.shading_factor * 
                             solar_radiation[window.orientation])
        
        return trans_loss, vent_loss, solar_gain
    
    def simulate_temperature(self,
                           outside_temp: float,
                           solar_radiation: Dict[str, float],
                           time_of_day: int,
                           time_step: float = 1.0) -> Tuple[float, float]:
        """
        Simuliere Raumtemperaturänderung über einen Zeitschritt.
        
        Args:
            outside_temp: Außentemperatur in °C
            solar_radiation: Solare Strahlung nach Orientierung in W/m²
            time_of_day: Stunde des Tages (0-23)
            time_step: Zeitschritt in Stunden
            
        Returns:
            Tuple von (Raumtemperatur in °C, Heizlast in kW)
        """
        # Wärmegewinne durch Fenster
        solar_gains = 0.0
        for window in self.properties.windows:
            if window.orientation in solar_radiation:
                solar_gains += (
                    window.area * 
                    window.g_value * 
                    window.frame_factor * 
                    window.shading_factor * 
                    solar_radiation[window.orientation]
                )
        
        # Interne Wärmegewinne (vereinfacht)
        if 7 <= time_of_day <= 22:  # Tagsüber
            internal_gains = 5.0 * self.get_total_area() / 100  # 5 W/m²
        else:  # Nachts
            internal_gains = 1.0 * self.get_total_area() / 100  # 1 W/m²
            
        # Wärmegewinne gesamt
        total_gains = solar_gains + internal_gains
        
        # Wärmeverluste
        transmission_losses = self.total_loss_coefficient * (self.room_temperature - outside_temp)
        ventilation_losses = self.ventilation_loss_coefficient * (self.room_temperature - outside_temp)
        total_losses = transmission_losses + ventilation_losses
        
        # Temperaturänderung (vereinfachtes RC-Modell)
        delta_q = total_gains - total_losses
        delta_t = delta_q * time_step * 3600 / self.effective_thermal_mass
        
        # Neue Raumtemperatur
        self.previous_temperature = self.room_temperature
        self.room_temperature += delta_t
        
        # Heizlast (wenn Temperatur unter Sollwert)
        target_temp = 20.0  # °C
        if self.room_temperature < target_temp:
            heating_power = (target_temp - self.room_temperature) * \
                          (self.total_loss_coefficient + self.ventilation_loss_coefficient)
            self.room_temperature = target_temp
        else:
            heating_power = 0.0
        
        return self.room_temperature, heating_power / 1000  # Konvertiere zu kW
    
    def calculate_dynamic_temperature(self,
                              current_temp: float,
                              heat_power: float,
                              losses: float,
                              solar_gains: float,
                              time_step: float) -> float:
        """
        Berechnet die dynamische Temperaturentwicklung für einen Zeitschritt.

        Args:
            current_temp: Aktuelle Raumtemperatur in °C
            heat_power: Heizleistung in kW
            losses: Wärmeverluste in kW
            solar_gains: Solare Gewinne in kW
            time_step: Zeitschritt in Sekunden

        Returns:
            Neue Raumtemperatur in °C
        """
        # Energiebilanz in kWh
        heat_energy = heat_power * time_step / 3600  # kW -> kWh
        loss_energy = losses * time_step / 3600
        solar_energy = solar_gains * time_step / 3600
        
        # Netto-Energiebilanz
        net_energy = heat_energy + solar_energy - loss_energy  # kWh
        
        # Temperaturänderung (Q = m*c*ΔT)
        temp_change = net_energy * 3600 / self.effective_thermal_mass  # kWh -> Wh
        
        return current_temp + temp_change

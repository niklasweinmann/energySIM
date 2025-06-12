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
        self._calculate_building_parameters()
    
    def _calculate_building_parameters(self):
        """Berechnet die grundlegenden Gebäudeparameter."""
        # U-Werte berechnen
        self.u_values = {
            'walls': [self._calculate_u_value(w.layers) for w in self.properties.walls],
            'roof': self._calculate_u_value(self.properties.roof.layers),
            'floor': self._calculate_u_value(self.properties.floor.layers)
        }
        
        # Transmissionswärmeverluste
        self.H_T = self._calculate_transmission_losses()
        
        # Lüftungswärmeverluste
        self.H_V = self._calculate_ventilation_losses()
        
        # Solare Gewinne
        self.effective_collection_area = self._calculate_effective_collection_area()
        
    def _calculate_u_value(self, layers: List[tuple[float, float]]) -> float:
        """
        Berechnet den U-Wert eines Bauteils nach DIN EN ISO 6946.
        
        Args:
            layers: Liste von (Dicke, Lambda)-Tupeln
            
        Returns:
            U-Wert in W/(m²·K)
        """
        R_si = 0.13  # Wärmeübergangswiderstand innen
        R_se = 0.04  # Wärmeübergangswiderstand außen
        
        # Wärmedurchlasswiderstände der Schichten
        R_layers = sum(d/l for d, l in layers)
        
        return 1 / (R_si + R_layers + R_se)
    
    def _calculate_transmission_losses(self) -> float:
        """
        Berechnet den spezifischen Transmissionswärmeverlust nach DIN EN ISO 13790.
        
        Returns:
            Spezifischer Transmissionswärmeverlust in W/K
        """
        H_T = 0.0
        
        # Wände
        for wall, u_value in zip(self.properties.walls, self.u_values['walls']):
            H_T += wall.area * u_value
        
        # Fenster
        for window in self.properties.windows:
            H_T += window.area * window.u_value
        
        # Dach
        H_T += self.properties.roof.area * self.u_values['roof']
        
        # Boden
        if self.properties.floor.ground_coupling:
            # Berücksichtigung des Erdreichs nach DIN EN ISO 13370
            H_T += self.properties.floor.area * self.u_values['floor'] * 0.6
        else:
            H_T += self.properties.floor.area * self.u_values['floor']
        
        return H_T
    
    def _calculate_ventilation_losses(self) -> float:
        """
        Berechnet den spezifischen Lüftungswärmeverlust nach DIN EN ISO 13790.
        
        Returns:
            Spezifischer Lüftungswärmeverlust in W/K
        """
        rho = 1.2  # Luftdichte in kg/m³
        c_p = 1005  # Spezifische Wärmekapazität der Luft in J/(kg·K)
        
        # Luftwechselrate in m³/h
        V_dot = self.properties.volume * self.properties.infiltration_rate
        
        return (rho * c_p * V_dot) / 3600  # Umrechnung in W/K
    
    def _calculate_effective_collection_area(self) -> Dict[str, float]:
        """
        Berechnet die effektive Sonnenkollektorfläche nach DIN EN ISO 13790.
        
        Returns:
            Dictionary mit effektiven Kollektorflächen pro Orientierung
        """
        A_sol = {}
        
        # Fenster
        for window in self.properties.windows:
            A_sol_window = (
                window.area *
                window.g_value *
                window.frame_factor *
                window.shading_factor
            )
            
            if window.orientation in A_sol:
                A_sol[window.orientation] += A_sol_window
            else:
                A_sol[window.orientation] = A_sol_window
                
        return A_sol
    
    def calculate_heating_demand(self, 
                               outdoor_temp: float,
                               solar_radiation: Dict[str, float],
                               indoor_temp: float = 20.0,
                               time_step: float = 1.0  # Stunde
                               ) -> float:
        """
        Berechnet den Heizwärmebedarf nach DIN EN ISO 13790.
        
        Args:
            outdoor_temp: Außentemperatur in °C
            solar_radiation: Solare Einstrahlung in W/m² pro Orientierung
            indoor_temp: Innentemperatur in °C
            time_step: Zeitschritt in Stunden
            
        Returns:
            Heizwärmebedarf in kWh
        """
        # Transmissions- und Lüftungsverluste
        Q_ht = (self.H_T + self.H_V) * (indoor_temp - outdoor_temp) * time_step
        
        # Solare Gewinne
        Q_sol = 0.0
        for orientation, area in self.effective_collection_area.items():
            if orientation in solar_radiation:
                Q_sol += area * solar_radiation[orientation] * time_step
        
        # Interne Gewinne (vereinfacht)
        Q_int = 5 * self.properties.volume / 100 * time_step  # 5 W/m² nach DIN V 18599
        
        # Ausnutzungsgrad der Wärmegewinne
        gains = Q_sol + Q_int
        eta = self._calculate_utilization_factor(Q_ht, gains)
        
        # Heizwärmebedarf
        Q_h = max(0, Q_ht - eta * gains) / 1000  # Umrechnung in kWh
        
        return Q_h
    
    def _calculate_utilization_factor(self, losses: float, gains: float) -> float:
        """
        Berechnet den Ausnutzungsgrad für Wärmegewinne nach DIN EN ISO 13790.
        
        Args:
            losses: Wärmeverluste in Wh
            gains: Wärmegewinne in Wh
            
        Returns:
            Ausnutzungsgrad (dimensionslos)
        """
        if losses <= 0:
            return 0.0
            
        gamma = gains / losses if losses > 0 else float('inf')
        
        # Zeitkonstante des Gebäudes
        tau = self.properties.thermal_mass * self.properties.volume / (self.H_T + self.H_V)
        
        # Parameter a nach DIN EN ISO 13790
        a = 1 + tau / 15
        
        if gamma == 1:
            return a / (a + 1)
        elif gamma > 0:
            return (1 - gamma**a) / (1 - gamma**(a + 1))
        else:
            return 1.0

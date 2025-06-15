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
        
    def _find_surrounding_points(self, outside_temp: float, flow_temp: float) -> tuple[tuple[float, float], float]:
        """
        Findet die umgebenden Temperaturpunkte für die Interpolation.
        
        Args:
            outside_temp: Außentemperatur in °C
            flow_temp: Vorlauftemperatur in °C
            
        Returns:
            Liste von Tupeln ((außentemp, vorlauftemp), cop)
        """
        outside_temps = sorted(set(t[0] for t in self.specs.cop_rating_points.keys()))
        flow_temps = sorted(set(t[1] for t in self.specs.cop_rating_points.keys()))
        
        # Finde die umgebenden Temperaturen
        lower_outside = max((t for t in outside_temps if t <= outside_temp), default=min(outside_temps))
        upper_outside = min((t for t in outside_temps if t >= outside_temp), default=max(outside_temps))
        lower_flow = max((t for t in flow_temps if t <= flow_temp), default=min(flow_temps))
        upper_flow = min((t for t in flow_temps if t >= flow_temp), default=max(flow_temps))
        
        points = []
        for out_temp in [lower_outside, upper_outside]:
            for flow_t in [lower_flow, upper_flow]:
                points.append(((out_temp, flow_t), self.specs.cop_rating_points[(out_temp, flow_t)]))
                
        return points
    
    def _interpolate_1d(self, x: float, x1: float, x2: float, y1: float, y2: float) -> float:
        """
        Führt eine lineare Interpolation zwischen zwei Punkten durch.
        
        Args:
            x: Der x-Wert, für den interpoliert werden soll
            x1: Der erste x-Wert
            x2: Der zweite x-Wert
            y1: Der erste y-Wert
            y2: Der zweite y-Wert
            
        Returns:
            Der interpolierte y-Wert
        """
        if x1 == x2:
            return y1
        ratio = (x - x1) / (x2 - x1)
        return y1 + ratio * (y2 - y1)
    
    def calculate_cop(self, outside_temp: float, flow_temp: float) -> float:
        """
        Berechnet den COP basierend auf Außen- und Vorlauftemperatur.
        Die COP-Werte aus der VDI 4645 beinhalten bereits die Abtaueffekte.
        
        Args:
            outside_temp: Außentemperatur in °C
            flow_temp: Vorlauftemperatur in °C
            
        Returns:
            Coefficient of Performance (COP)
        """
        # Prüfe Betriebsgrenzen
        if outside_temp < self.specs.min_outside_temp or flow_temp > self.specs.max_flow_temp:
            return 0.0
        
        # Stelle sicher, dass beide Temperaturen als float behandelt werden
        outside_temp_float = float(outside_temp)
        flow_temp_float = float(flow_temp)
        
        # Exakter Match - mit expliziter Float-Konvertierung
        # Suche nach einem passenden COP-Punkt mit Toleranz für Rundungsfehler
        for (out_t, fl_t), cop in self.specs.cop_rating_points.items():
            if abs(float(out_t) - outside_temp_float) < 0.01 and abs(float(fl_t) - flow_temp_float) < 0.01:
                return cop
        
        # Finde die verfügbaren Temperaturen und konvertiere zu float
        outside_temps = [float(t[0]) for t in self.specs.cop_rating_points.keys()]
        outside_temps = sorted(set(outside_temps))
        flow_temps = [float(t[1]) for t in self.specs.cop_rating_points.keys()]
        flow_temps = sorted(set(flow_temps))
        
        # Stelle sicher, dass outside_temp und flow_temp als float behandelt werden
        outside_temp_float = float(outside_temp)
        flow_temp_float = float(flow_temp)
        
        # Finde die umgebenden Außentemperaturen
        lower_outside = max((t for t in outside_temps if t <= outside_temp_float), default=min(outside_temps))
        upper_outside = min((t for t in outside_temps if t >= outside_temp_float), default=max(outside_temps))
        
        # Interpoliere zuerst für die untere Außentemperatur
        lower_outside_cops = []
        for flow_t in flow_temps:
            # Explizite Typkonvertierung für den Vergleich
            flow_t_float = float(flow_t)
            if flow_t_float in [float(t[1]) for t in self.specs.cop_rating_points.keys() if float(t[0]) == float(lower_outside)]:
                lower_outside_cops.append((flow_t_float, self.specs.cop_rating_points[(lower_outside, flow_t_float)]))
        
        lower_cop = self._interpolate_1d(
            flow_temp,
            lower_outside_cops[0][0],
            lower_outside_cops[-1][0],
            lower_outside_cops[0][1],
            lower_outside_cops[-1][1]
        )
        
        # Dann für die obere Außentemperatur
        upper_outside_cops = []
        for flow_t in flow_temps:
            # Explizite Typkonvertierung für den Vergleich
            flow_t_float = float(flow_t)
            if flow_t_float in [float(t[1]) for t in self.specs.cop_rating_points.keys() if float(t[0]) == float(upper_outside)]:
                upper_outside_cops.append((flow_t_float, self.specs.cop_rating_points[(upper_outside, flow_t_float)]))
        
        upper_cop = self._interpolate_1d(
            flow_temp,
            upper_outside_cops[0][0],
            upper_outside_cops[-1][0],
            upper_outside_cops[0][1],
            upper_outside_cops[-1][1]
        )
        
        # Schließlich zwischen den Außentemperaturen
        cop = self._interpolate_1d(
            outside_temp,
            lower_outside,
            upper_outside,
            lower_cop,
            upper_cop
        )
        
        self.current_cop = cop
        return cop
    
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

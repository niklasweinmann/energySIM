from typing import List, Optional, Tuple, Dict
import numpy as np
import tensorflow as tf
from tensorflow.keras import layers, models
import pandas as pd
from dataclasses import dataclass

@dataclass
class SystemState:
    """Aktueller Zustand des Energiesystems."""
    building_temp: float  # °C
    dhw_temp: float  # °C Warmwassertemperatur
    pv_power: float  # kW
    battery_soc: float  # % Batterieladezustand
    heat_storage_temp: float  # °C Pufferspeichertemperatur
    heat_demand: float  # kW
    dhw_demand: float  # kW Warmwasserbedarf

@dataclass
class OptimizationConstraints:
    """Betriebsgrenzen nach deutschen Normen."""
    min_room_temp: float = 20.0  # °C (EnEV)
    max_room_temp: float = 26.0  # °C (ASR A3.5)
    min_dhw_temp: float = 60.0   # °C (DVGW W551)
    max_flow_temp: float = 55.0  # °C (typisch für WP)
    min_storage_temp: float = 25.0  # °C
    max_storage_temp: float = 90.0  # °C (DIN 4753)
    
class EnergyFlowOptimizer:
    """Optimiert die Energieflüsse im System nach VDI 4655."""
    
    def __init__(self):
        self.model: Optional[models.Model] = None
        self.feature_columns: List[str] = [
            'outside_temp', 'solar_radiation', 'wind_speed',
            'building_temp', 'dhw_temp', 'pv_power',
            'battery_soc', 'heat_storage_temp'
        ]
        self.constraints = OptimizationConstraints()
        
    def build_model(self, input_shape: Tuple[int, int]):
        """
        Erweiterte Modellarchitektur für Energieflussoptimierung.
        
        Args:
            input_shape: Form der Eingabedaten (Zeitschritte, Features)
        """
        # Eingabeschicht
        inputs = layers.Input(shape=input_shape)
        
        # Encoder (Zeitreihenverarbeitung)
        x = layers.LSTM(128, return_sequences=True)(inputs)
        x = layers.LSTM(64)(x)
        
        # Verzweigung für verschiedene Optimierungsziele
        heat_pump_control = layers.Dense(32, activation='relu')(x)
        heat_pump_control = layers.Dense(1, activation='sigmoid', name='heat_pump')(heat_pump_control)
        
        storage_control = layers.Dense(32, activation='relu')(x)
        storage_control = layers.Dense(1, activation='sigmoid', name='storage')(storage_control)
        
        pv_battery_control = layers.Dense(32, activation='relu')(x)
        pv_battery_control = layers.Dense(1, activation='sigmoid', name='pv_battery')(pv_battery_control)
        
        # Kombiniertes Modell
        self.model = models.Model(
            inputs=inputs,
            outputs=[heat_pump_control, storage_control, pv_battery_control]
        )
        
        # Multi-Objective Loss
        self.model.compile(
            optimizer='adam',
            loss={
                'heat_pump': 'mse',
                'storage': 'mse',
                'pv_battery': 'mse'
            },
            loss_weights={
                'heat_pump': 1.0,
                'storage': 0.8,
                'pv_battery': 0.6
            },
            metrics=['mae']
        )
    
    def optimize_energy_flows(self, 
                            state: SystemState,
                            weather_forecast: pd.DataFrame,
                            electricity_prices: pd.DataFrame) -> Dict[str, float]:
        """
        Optimiert die Energieflüsse unter Berücksichtigung von VDI 4655.
        
        Args:
            state: Aktueller Systemzustand
            weather_forecast: Wettervorhersage für den Optimierungshorizont
            electricity_prices: Strompreise für den Optimierungshorizont
            
        Returns:
            Dict mit Steuerungssignalen für alle Komponenten
        """
        # Eingabedaten vorbereiten
        input_data = self._prepare_optimization_input(state, weather_forecast)
        
        # Vorhersage der optimalen Steuerungssignale
        heat_pump, storage, pv_battery = self.model.predict(input_data)
        
        # Anwendung der Betriebsgrenzen (nach deutschen Normen)
        controls = self._apply_operational_constraints(
            heat_pump[0], storage[0], pv_battery[0], state
        )
        
        return controls
    
    def _prepare_optimization_input(self,
                                 state: SystemState,
                                 weather_forecast: pd.DataFrame) -> np.ndarray:
        """Bereitet Daten für die Optimierung vor."""
        # Kombiniere Zustandsdaten mit Wettervorhersage
        data = []
        # Begrenze auf genau 24h
        for _, weather in weather_forecast.head(24).iterrows():
            features = [
                weather['temperature'],
                weather['solar_radiation'],
                weather['wind_speed'],
                state.building_temp,
                state.dhw_temp,
                state.pv_power,
                state.battery_soc,
                state.heat_storage_temp
            ]
            data.append(features)
        
        # Stelle sicher, dass genau 24 Zeitschritte vorhanden sind
        if len(data) < 24:
            # Fülle fehlende Daten mit dem letzten bekannten Wert
            last_data = data[-1]
            while len(data) < 24:
                data.append(last_data[:])
        elif len(data) > 24:
            # Kürze auf 24 Stunden
            data = data[:24]
        
        return np.array([data])  # Shape: (1, 24, 8)
    
    def _apply_operational_constraints(self,
                                    heat_pump: float,
                                    storage: float,
                                    pv_battery: float,
                                    state: SystemState) -> Dict[str, float]:
        """Wendet Betriebsgrenzen nach deutschen Normen an."""
        controls = {}
        
        # Wärmepumpensteuerung (VDI 4645)
        if state.building_temp < self.constraints.min_room_temp:
            controls['heat_pump'] = 1.0  # Maximale Heizleistung
        elif state.building_temp > self.constraints.max_room_temp:
            controls['heat_pump'] = 0.0  # Heizung aus
        else:
            controls['heat_pump'] = heat_pump
        
        # Warmwasserspeicher (DVGW W551, DIN 4753)
        if state.dhw_temp < self.constraints.min_dhw_temp:
            controls['dhw_heating'] = 1.0
        else:
            controls['dhw_heating'] = storage
        
        # PV-Batterie-Steuerung
        controls['battery_charging'] = pv_battery if state.battery_soc < 100 else 0.0
        
        return controls
    
    def calculate_cop_based_operation(self,
                                   outside_temp: float,
                                   flow_temp: float,
                                   electricity_price: float) -> bool:
        """
        Berechnet die Wirtschaftlichkeit des WP-Betriebs nach VDI 4645.
        
        Args:
            outside_temp: Außentemperatur in °C
            flow_temp: Vorlauftemperatur in °C
            electricity_price: Strompreis in €/kWh
            
        Returns:
            True wenn Betrieb wirtschaftlich sinnvoll
        """
        # JAZ-Berechnung nach VDI 4645 (korrigiert)
        # Carnot-COP als theoretisches Maximum
        t_hot = 273.15 + flow_temp  # Kelvin
        t_cold = 273.15 + outside_temp  # Kelvin
        carnot_cop = t_hot / (t_hot - t_cold)
        
        # Realer COP mit typischem Gütegrad von 45-55%
        real_cop = carnot_cop * 0.50  # Korrigiert: 50% Gütegrad
        
        # Mindest-COP nach VDI 4645 beachten
        min_cop = 3.0  # A-7/W35
        real_cop = max(real_cop, min_cop)
        
        # Wirtschaftlichkeitsberechnung
        operating_cost = electricity_price / real_cop
        
        # Grenzwert für wirtschaftlichen Betrieb (beispielhaft)
        return operating_cost < 0.15  # €/kWh Wärme

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from src.models.energy_optimizer import EnergyFlowOptimizer, SystemState
from src.data_handlers.weather import WeatherDataHandler

def test_energy_optimization():
    # System-Optimierer erstellen
    optimizer = EnergyFlowOptimizer()
    
    # Systemzustand definieren
    state = SystemState(
        building_temp=19.0,  # °C - unter Mindesttemperatur
        dhw_temp=55.0,      # °C - unter Mindesttemperatur nach DVGW W551
        pv_power=5.0,       # kW
        battery_soc=30.0,   # %
        heat_storage_temp=40.0,  # °C
        heat_demand=10.0,   # kW
        dhw_demand=2.0      # kW
    )
    
    # Wetterdaten laden
    weather = WeatherDataHandler()
    start_date = datetime.now()
    end_date = start_date + timedelta(days=1)
    weather_forecast = weather.get_historical_data(
        location=(52.52, 13.405),  # Berlin
        start_date=start_date,
        end_date=end_date
    )
    
    # Beispiel-Strompreise (variable Tarife)
    electricity_prices = pd.DataFrame({
        'timestamp': weather_forecast['timestamp'],
        'price': 0.30 + 0.10 * np.sin(np.pi * pd.to_datetime(weather_forecast['timestamp']).dt.hour / 12)  # Tag/Nacht-Tarif
    })
    
    # Optimierer trainieren
    optimizer.build_model(input_shape=(24, 8))  # 24 Stunden, 8 Features
    
    # Optimierung durchführen
    controls = optimizer.optimize_energy_flows(
        state=state,
        weather_forecast=weather_forecast,
        electricity_prices=electricity_prices
    )
    
    # Überprüfungen
    assert 'heat_pump' in controls
    assert 'dhw_heating' in controls
    assert 'battery_charging' in controls
    
    # Prüfen der Normenkonformität
    assert controls['heat_pump'] == 1.0  # Sollte maximal heizen, da unter Mindesttemperatur
    assert controls['dhw_heating'] > 0.0  # Sollte heizen, da unter DVGW W551 Mindesttemperatur
    
    # COP-basierte Betriebsoptimierung testen
    outside_temp = 5.0  # °C
    flow_temp = 35.0   # °C
    electricity_price = 0.30  # €/kWh
    
    operation_recommended = optimizer.calculate_cop_based_operation(
        outside_temp=outside_temp,
        flow_temp=flow_temp,
        electricity_price=electricity_price
    )
    
    print("\nOptimierungsergebnisse:")
    print(f"Wärmepumpensteuerung: {controls['heat_pump']:.2f}")
    print(f"Warmwassererwärmung: {controls['dhw_heating']:.2f}")
    
    # Handle numpy array case for battery_charging
    battery_value = controls['battery_charging']
    if hasattr(battery_value, '__len__') and len(battery_value) > 0:
        battery_value = battery_value[0]  # Take first element if it's an array
    print(f"Batterieladung: {battery_value:.2f}")
    print(f"WP-Betrieb wirtschaftlich: {operation_recommended}")

if __name__ == "__main__":
    test_energy_optimization()

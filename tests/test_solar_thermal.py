import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from src.simulation.solar_thermal import (
    SolarThermalSystem,
    SolarThermalSpecifications,
    StorageSpecifications
)
from src.data_handlers.weather import WeatherDataHandler

def test_solar_thermal_system():
    # Solarthermie-System erstellen (Beispiel: Vakuumröhrenkollektor)
    collector_specs = SolarThermalSpecifications(
        area=10.0,  # m²
        optical_efficiency=0.75,
        heat_loss_coefficient_a1=1.8,  # W/(m²·K)
        heat_loss_coefficient_a2=0.008,  # W/(m²·K²)
        incident_angle_modifier=0.94
    )
    
    storage_specs = StorageSpecifications(
        volume=0.75,  # m³ (750 Liter)
        height=1.8,  # m
        insulation_thickness=0.1,  # m
        insulation_conductivity=0.04,  # W/(m·K)
        heat_loss_rate=2.5,  # W/K
        stratification_efficiency=0.85
    )
    
    location = (52.52, 13.405)  # Berlin
    tilt = 45  # 45° Neigung
    azimuth = 180  # Südausrichtung
    
    solar_system = SolarThermalSystem(
        collector_specs=collector_specs,
        storage_specs=storage_specs,
        location=location,
        tilt=tilt,
        azimuth=azimuth
    )
    
    # Wetterdaten laden
    weather = WeatherDataHandler()
    start_date = datetime.now()
    end_date = start_date + timedelta(days=1)
    weather_data = weather.get_historical_data(
        location=location,
        start_date=start_date,
        end_date=end_date
    )
    
    # Tagesverlauf simulieren
    thermal_powers = []
    collector_temps = []
    storage_temps_avg = []
    solar_fractions = []
    
    total_demand = 0
    total_solar = 0
    
    for _, row in weather_data.iterrows():
        # Standardlast für Warmwasser nach VDI 6002
        timestamp = pd.to_datetime(row['timestamp'])
        hour = timestamp.hour
        if 6 <= hour <= 9:  # Morgenpeak
            dhw_demand = 3.0  # kW
        elif 18 <= hour <= 22:  # Abendpeak
            dhw_demand = 2.0  # kW
        else:
            dhw_demand = 0.5  # kW
            
        # Thermische Leistung berechnen
        power, temp = solar_system.calculate_thermal_power(
            solar_irradiance=row['solar_radiation'],
            ambient_temp=row['temperature'],
            flow_temp=60.0  # Vorlauftemperatur für Warmwasser
        )
        
        # Speicher aktualisieren
        useful_power, storage_temps = solar_system.update_storage(
            thermal_power=power,
            dhw_demand=dhw_demand
        )
        
        thermal_powers.append(power)
        collector_temps.append(temp)
        storage_temps_avg.append(np.mean(storage_temps))
        
        # Solare Deckung berechnen
        total_demand += dhw_demand
        total_solar += min(power, dhw_demand)
        current_fraction = solar_system.calculate_solar_fraction(
            total_demand, total_solar
        )
        solar_fractions.append(current_fraction)
    
    # Überprüfungen
    assert len(thermal_powers) == len(weather_data)
    assert all(power >= 0 for power in thermal_powers)
    assert all(60 <= temp <= 130 for temp in collector_temps)  # VDI 6002
    assert all(60 <= temp <= 90 for temp in storage_temps_avg)  # DVGW W551
    assert all(0 <= f <= 1 for f in solar_fractions)
    
    # Ergebnisse ausgeben
    print("\nSolarthermie-Simulationsergebnisse:")
    print(f"Maximale thermische Leistung: {max(thermal_powers):.2f} kW")
    print(f"Durchschnittliche Speichertemperatur: {np.mean(storage_temps_avg):.1f} °C")
    print(f"Solarer Deckungsgrad: {solar_fractions[-1]*100:.1f}%")
    print(f"Maximale Kollektortemperatur: {max(collector_temps):.1f} °C")

if __name__ == "__main__":
    test_solar_thermal_system()

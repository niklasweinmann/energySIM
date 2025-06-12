import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from datetime import datetime, timedelta
import numpy as np
from src.core.building import Building, BuildingProperties
from src.simulation.heat_pump import HeatPump, HeatPumpSpecifications
from src.data_handlers.weather import WeatherDataHandler

def test_basic_simulation():
    # Gebäude erstellen
    building_props = BuildingProperties(
        area=200,
        volume=600,
        u_values={"walls": 0.24, "roof": 0.2, "floor": 0.3, "windows": 1.1},
        thermal_mass=165,
        infiltration_rate=0.5
    )
    building = Building(building_props)
    
    # Wärmepumpe erstellen
    hp_specs = HeatPumpSpecifications(
        nominal_heating_power=12,
        cop_rating_points={
            (-7, 35): 2.5,
            (2, 35): 3.5,
            (7, 35): 4.2,
            (20, 35): 5.0
        },
        min_outside_temp=-20,
        max_flow_temp=60
    )
    heat_pump = HeatPump(hp_specs)
    
    # Wetterdaten laden
    weather = WeatherDataHandler()
    start_date = datetime.now()
    end_date = start_date + timedelta(days=1)
    weather_data = weather.get_historical_data(
        location=(52.52, 13.405),  # Berlin
        start_date=start_date,
        end_date=end_date
    )
    
    # Simulation für 24 Stunden
    heat_demands = []
    heat_pump_powers = []
    cops = []
    
    for _, row in weather_data.iterrows():
        # Heizlast berechnen
        heat_demand = building.calculate_heat_load(
            outside_temp=row['temperature'],
            inside_temp=20.0
        )
        heat_demands.append(heat_demand)
        
        # Wärmepumpenleistung berechnen
        thermal_power, electrical_power = heat_pump.get_power_output(
            outside_temp=row['temperature'],
            flow_temp=35,  # Konstante Vorlauftemperatur für den Test
            demand=heat_demand
        )
        heat_pump_powers.append(thermal_power)
        cops.append(heat_pump.current_cop)
    
    # Einfache Überprüfungen
    assert len(heat_demands) == len(weather_data)
    assert all(demand >= 0 for demand in heat_demands)
    assert all(power >= 0 for power in heat_pump_powers)
    assert all(cop > 0 for cop in cops)
    
    print(f"Durchschnittliche Heizlast: {np.mean(heat_demands):.2f} kW")
    print(f"Durchschnittlicher COP: {np.mean(cops):.2f}")
    print(f"Maximale Heizlast: {max(heat_demands):.2f} kW")

if __name__ == "__main__":
    test_basic_simulation()

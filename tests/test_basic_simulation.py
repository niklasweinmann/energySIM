import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from datetime import datetime, timedelta
import numpy as np
from src.core.building import Building, BuildingProperties, Wall, Window, Roof, Floor
from src.simulation.heat_pump import HeatPump, HeatPumpSpecifications
from src.data_handlers.weather import WeatherDataHandler
from src.data_handlers.weather import WeatherDataHandler

def test_basic_simulation():
    # Gebäude erstellen
    # Erstelle vereinfachte Gebäudekomponenten
    walls = [Wall(area=50, orientation='N', layers=[(0.2, 0.035)]),  # Beispielwand
            Wall(area=50, orientation='S', layers=[(0.2, 0.035)])]
    windows = [Window(area=8, u_value=1.1, g_value=0.6, orientation='S',
                     shading_factor=0.7, frame_factor=0.7)]
    roof = Roof(area=100, tilt=45, layers=[(0.25, 0.035)])
    floor = Floor(area=100, layers=[(0.2, 0.035)], ground_coupling=True)
    
    building_props = BuildingProperties(
        walls=walls,
        windows=windows,
        roof=roof,
        floor=floor,
        volume=600,
        infiltration_rate=0.5,
        thermal_mass=165
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
        min_outside_temp=-20,            max_flow_temp=60,
            min_part_load_ratio=0.3
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
        trans_loss, vent_loss, solar_gain = building.calculate_heat_load(
            outside_temp=row['temperature'],
            solar_radiation={
                'N': row['solar_radiation'] * 0.3,  # 30% diffuse
                'S': row['solar_radiation'] * 1.0,  # Direkt + diffus
                'E': row['solar_radiation'] * 0.7,  # Morgens
                'W': row['solar_radiation'] * 0.7   # Abends
            },
            inside_temp=20.0
        )
        # Gesamtheizlast = Verluste - Gewinne (in kW)
        heat_demand = float(max(0, trans_loss + vent_loss - solar_gain))
        heat_demands.append(heat_demand)
        
        # Wärmepumpenleistung berechnen (Energiebedarf = Leistung * Zeit)
        thermal_power, electrical_power = heat_pump.get_power_output(
            outside_temp=row['temperature'],
            flow_temp=35,  # Konstante Vorlauftemperatur für den Test
            demand=heat_demand  # Da time_step=1.0 (Standard), ist der Energiebedarf gleich der Leistung
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

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from datetime import datetime, timedelta
import numpy as np
from src.core.building import (
    Building,
    BuildingProperties,
    Wall,
    Window,
    Roof,
    Floor
)
from src.data_handlers.weather import WeatherDataHandler

def test_building_physics():
    # Gebäudeparameter nach DIN 4108 (Beispiel: Einfamilienhaus EnEV-Standard)
    walls = [
        Wall(
            area=150.0,  # m²
            orientation='S',
            layers=[
                (0.015, 0.870),  # Innenputz (d=15mm, λ=0.87)
                (0.175, 0.800),  # Kalksandstein (d=175mm, λ=0.80)
                (0.160, 0.035),  # Dämmung WLG 035
                (0.015, 0.870)   # Außenputz
            ]
        ),
        Wall(
            area=150.0,
            orientation='N',
            layers=[
                (0.015, 0.870),
                (0.175, 0.800),
                (0.160, 0.035),
                (0.015, 0.870)
            ]
        )
    ]
    
    windows = [
        Window(
            area=16.0,  # m²
            u_value=0.95,  # Dreifachverglasung
            g_value=0.5,
            orientation='S',
            shading_factor=0.7,
            frame_factor=0.7
        ),
        Window(
            area=8.0,
            u_value=0.95,
            g_value=0.5,
            orientation='N',
            shading_factor=0.9,  # weniger Verschattung nach Norden
            frame_factor=0.7
        )
    ]
    
    roof = Roof(
        area=100.0,
        tilt=45.0,
        layers=[
            (0.0125, 0.130),  # Gipskarton
            (0.220, 0.035),   # Dämmung zwischen Sparren
            (0.100, 0.035),   # Aufdachdämmung
            (0.02, 1.000)     # Ziegel + Unterspannbahn
        ]
    )
    
    floor = Floor(
        area=100.0,
        layers=[
            (0.015, 1.400),   # Fliesen
            (0.060, 1.330),   # Estrich
            (0.030, 0.040),   # Trittschalldämmung
            (0.120, 0.035),   # Wärmedämmung
            (0.250, 2.300)    # Stahlbeton
        ],
        ground_coupling=True
    )
    
    building_props = BuildingProperties(
        walls=walls,
        windows=windows,
        roof=roof,
        floor=floor,
        volume=500.0,  # m³
        infiltration_rate=0.6,  # 1/h (EnEV-Standard)
        thermal_mass=165.0  # Wh/(m²·K) (Massivbau)
    )
    
    building = Building(building_props)
    
    # Test 1: U-Werte nach DIN 4108
    assert all(u <= 0.24 for u in [building.u_values[f'wall_{i}'] for i in range(len(walls))])
    assert all(u <= 1.30 for u in [building.u_values[f'window_{i}'] for i in range(len(windows))])
    assert building.u_values['roof'] <= 0.20
    assert building.u_values['floor'] <= 0.30
    
    # Test 2: Wärmebrücken nach DIN 4108 Beiblatt 2
    assert building.thermal_bridges == 0.05  # Niedrigenergiehaus-Standard
    
    # Test 3: Heizlastberechnung für verschiedene Bedingungen
    # Testszenario 1: Winterfall (-10°C, geringe Solarstrahlung)
    winter_radiation = {
        'N': 20.0,  # W/m²
        'S': 100.0,
        'E': 50.0,
        'W': 50.0
    }
    trans_loss, vent_loss, solar_gain = building.calculate_heat_load(
        outside_temp=-10.0,
        solar_radiation=winter_radiation
    )
    # Plausibilitätsprüfungen Winter
    assert trans_loss >= 0
    assert vent_loss >= 0
    assert solar_gain >= 0
    assert trans_loss + vent_loss > solar_gain  # Im Winter müssen die Verluste größer sein
    
    # Testszenario 2: Sommerfall (30°C, hohe Solarstrahlung)
    summer_radiation = {
        'N': 100.0,  # W/m²
        'S': 800.0,
        'E': 500.0,
        'W': 500.0
    }
    trans_loss, vent_loss, solar_gain = building.calculate_heat_load(
        outside_temp=30.0,
        solar_radiation=summer_radiation
    )
    # Plausibilitätsprüfungen Sommer
    assert trans_loss >= 0
    assert vent_loss >= 0
    assert solar_gain >= 0
    assert solar_gain > trans_loss + vent_loss  # Im Sommer müssen die solaren Gewinne größer sein
    
    # Test 4: Dynamische Temperaturentwicklung
    current_temp = 20.0
    heat_power = 10.0  # kW
    losses = 8.0      # kW
    solar_gains = 2.0 # kW
    time_step = 3600  # 1 Stunde
    
    new_temp = building.calculate_dynamic_temperature(
        current_temp=current_temp,
        heat_power=heat_power,
        losses=losses,
        solar_gains=solar_gains,
        time_step=time_step
    )
    
    # Temperatur sollte bei Überheizung steigen
    assert new_temp > current_temp
    
    print("\nGebäude-Simulationsergebnisse:")
    print(f"U-Wert Südwand: {building.u_values['wall_0']:.3f} W/(m²·K)")
    print(f"U-Wert Fenster: {building.u_values['window_0']:.3f} W/(m²·K)")
    print(f"U-Wert Dach: {building.u_values['roof']:.3f} W/(m²·K)")
    print(f"Wärmebrückenzuschlag: {building.thermal_bridges:.3f} W/(m²·K)")
    print(f"Effektive thermische Masse: {building.effective_thermal_mass:.0f} Wh/K")
    print(f"Mittlere Heizlast: {np.mean(building.heat_demand_history):.1f} kW")

if __name__ == "__main__":
    test_building_physics()

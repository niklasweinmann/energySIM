"""
Test für die dynamische Gebäudesimulation
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime
import matplotlib.pyplot as plt
import numpy as np
from src.core.building import Building, BuildingProperties, Wall, Window, Roof, Floor
from src.data_handlers.weather import WeatherDataHandler

def create_test_building() -> Building:
    """Erstelle ein Testgebäude."""
    # Wandaufbau (U-Wert ca. 0.2 W/m²K)
    wall_layers = [
        (0.015, 0.870),  # Innenputz
        (0.175, 0.035),  # Dämmung
        (0.240, 0.790),  # Mauerwerk
        (0.020, 0.870)   # Außenputz
    ]
    
    # Wände
    walls = [
        Wall(area=30.0, orientation='N', layers=wall_layers),
        Wall(area=30.0, orientation='S', layers=wall_layers),
        Wall(area=20.0, orientation='E', layers=wall_layers),
        Wall(area=20.0, orientation='W', layers=wall_layers)
    ]
    
    # Fenster
    windows = [
        Window(area=5.0, u_value=1.1, g_value=0.6, orientation='S',
               shading_factor=0.9, frame_factor=0.3),
        Window(area=3.0, u_value=1.1, g_value=0.6, orientation='N',
               shading_factor=0.9, frame_factor=0.3),
        Window(area=2.0, u_value=1.1, g_value=0.6, orientation='E',
               shading_factor=0.9, frame_factor=0.3),
        Window(area=2.0, u_value=1.1, g_value=0.6, orientation='W',
               shading_factor=0.9, frame_factor=0.3)
    ]
    
    # Dach (U-Wert ca. 0.15 W/m²K)
    roof = Roof(
        area=100.0,
        tilt=45.0,
        layers=[
            (0.015, 0.870),  # Innenverkleidung
            (0.300, 0.035),  # Dämmung
            (0.020, 0.230)   # Dachziegel
        ]
    )
    
    # Boden (U-Wert ca. 0.25 W/m²K)
    floor = Floor(
        area=100.0,
        layers=[
            (0.015, 1.000),  # Bodenbelag
            (0.060, 1.330),  # Estrich
            (0.140, 0.035),  # Dämmung
            (0.200, 2.300)   # Bodenplatte
        ],
        ground_coupling=True
    )
    
    # Gebäudeeigenschaften
    properties = BuildingProperties(
        walls=walls,
        windows=windows,
        roof=roof,
        floor=floor,
        volume=300.0,  # m³
        infiltration_rate=0.5,  # 1/h
        thermal_mass=60.0  # Wh/(m²·K)
    )
    
    return Building(properties)

def test_building_simulation():
    """Teste die dynamische Gebäudesimulation."""
    
    # Erstelle Testgebäude
    building = create_test_building()
    
    # Hole Wetterdaten
    weather = WeatherDataHandler()
    location = (52.52, 13.4)  # Berlin
    start_date = datetime(2025, 6, 13)
    end_date = datetime(2025, 6, 14)  # Ein Tag später für 24 Stunden
    weather_data = weather.get_historical_data(location, start_date, end_date)
    
    # Simulationsarrays
    hours = np.arange(24)
    temperatures = np.zeros(24)
    heating_loads = np.zeros(24)
    
    # Simuliere einen Tag
    for i in hours:
        # Konvertiere Globalstrahlung in Orientierungen (vereinfacht)
        if i < len(weather_data):
            ghi = weather_data.iloc[i]['solar_radiation']
        else:
            ghi = 0  # Nachtstunden ohne Strahlung
            
        solar_radiation = {
            'N': ghi * 0.2,   # 20% diffuse Strahlung
            'E': ghi * 0.5,   # Morgens
            'S': ghi * 0.8,   # Mittags
            'W': ghi * 0.5    # Abends
        }
        
        # Simuliere Zeitschritt
        temp, heat = building.simulate_temperature(
            outside_temp=weather_data['temperature'].iloc[i],
            solar_radiation=solar_radiation,
            time_of_day=i
        )
        
        temperatures[i] = temp
        heating_loads[i] = heat
    
    # Plotte Ergebnisse
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))
    fig.suptitle('Gebäudesimulation über 24 Stunden')
    
    # Temperaturplot
    ax1.plot(hours, temperatures, 'r-', label='Raumtemperatur')
    ax1.plot(hours, weather_data['temperature'], 'b-', label='Außentemperatur')
    ax1.set_xlabel('Stunde')
    ax1.set_ylabel('Temperatur (°C)')
    ax1.legend()
    ax1.grid(True)
    
    # Heizlastplot
    ax2.plot(hours, heating_loads, 'r-', label='Heizlast')
    ax2_twin = ax2.twinx()
    ax2_twin.plot(hours, weather_data['solar_radiation'], 'y-', label='Solare Einstrahlung', alpha=0.5)
    
    ax2.set_xlabel('Stunde')
    ax2.set_ylabel('Heizlast (kW)', color='r')
    ax2_twin.set_ylabel('Solare Einstrahlung (W/m²)', color='y')
    ax2.legend(loc='upper left')
    ax2_twin.legend(loc='upper right')
    ax2.grid(True)
    
    plt.tight_layout()
    plt.savefig('output/building_simulation.png')
    print("\nPlot saved as 'output/building_simulation.png'")

if __name__ == '__main__':
    test_building_simulation()

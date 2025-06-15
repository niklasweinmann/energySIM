"""
Test für die Integration von Wettermodellierung und Gebäudesimulation
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from src.core.building import Building, BuildingProperties, Wall, Window, Roof, Floor
from src.data_handlers.weather import WeatherDataHandler

def test_weather_building_integration():
    """Teste die Integration von Wettermodellierung und Gebäudesimulation."""
    
    # Testgebäude erstellen (EnEV-Standard)
    walls = [
        Wall(area=150.0, orientation='S', layers=[
            (0.015, 0.870),  # Innenputz
            (0.175, 0.800),  # Kalksandstein
            (0.160, 0.035),  # Dämmung WLG 035
            (0.015, 0.870)   # Außenputz
        ]),
        Wall(area=150.0, orientation='N', layers=[
            (0.015, 0.870),
            (0.175, 0.800),
            (0.160, 0.035),
            (0.015, 0.870)
        ])
    ]
    
    windows = [
        Window(area=16.0, u_value=0.95, g_value=0.5, orientation='S',
              shading_factor=0.7, frame_factor=0.7),
        Window(area=8.0, u_value=0.95, g_value=0.5, orientation='N',
              shading_factor=0.9, frame_factor=0.7)
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
        volume=500.0,
        infiltration_rate=0.6,
        thermal_mass=165.0
    )
    
    building = Building(building_props)
    
    # Wetterdaten für einen Referenztag laden
    weather = WeatherDataHandler()
    location = (52.52, 13.4)  # Berlin
    date = datetime(2025, 6, 13)  # Sommertag
    weather_data = weather.get_historical_data(location, date, date)
    
    # Arrays für Simulationsergebnisse
    hours = np.arange(24)
    temperatures = np.zeros(24)
    heating_loads = np.zeros(24)
    solar_gains = np.zeros(24)
    transmission_losses = np.zeros(24)
    ventilation_losses = np.zeros(24)
    
    # Validiere und interpoliere Wetterdaten auf Stundenbasis
    hourly_index = pd.date_range(date, date + timedelta(days=1), freq='H', inclusive='left')
    weather_data = weather_data.reindex(hourly_index).interpolate()
    
    # Gebäudeverhalten über 24 Stunden simulieren
    for i in hours:
        # Solare Einstrahlung nach Orientierung verteilen
        ghi = weather_data.iloc[i]['solar_radiation']
        solar_radiation = {
            'N': ghi * 0.3,   # Diffuse Strahlung
            'S': ghi * 1.0,   # Direkte + diffuse Strahlung
            'E': ghi * 0.7,   # Morgens stärker
            'W': ghi * 0.7    # Abends stärker
        }
        
        # Raumtemperatur und Heizlast simulieren
        temp, heat = building.simulate_temperature(
            outside_temp=weather_data.iloc[i]['temperature'],
            solar_radiation=solar_radiation,
            time_of_day=i
        )
        
        temperatures[i] = temp
        heating_loads[i] = heat
        solar_gains[i] = sum(solar_radiation.values())
        transmission_losses[i] = building.total_loss_coefficient * \
            (temp - weather_data.iloc[i]['temperature'])
        ventilation_losses[i] = building.ventilation_loss_coefficient * \
            (temp - weather_data.iloc[i]['temperature'])
    
    # Validierung der Ergebnisse
    assert all(temp >= 18 and temp <= 26 for temp in temperatures), \
        "Raumtemperaturen außerhalb des Komfortbereichs"
    assert all(load >= 0 for load in heating_loads), \
        "Negative Heizlasten aufgetreten"
    assert all(gain >= 0 for gain in solar_gains), \
        "Negative solare Gewinne aufgetreten"
    
    # Plotte Ergebnisse
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))
    fig.suptitle('Integration von Wettermodellierung und Gebäudesimulation')
    
    # Plot 1: Temperaturen
    ax1.plot(hours, temperatures, 'r-', label='Raumtemperatur')
    ax1.plot(hours, weather_data['temperature'], 'b-', label='Außentemperatur')
    ax1.set_xlabel('Stunde')
    ax1.set_ylabel('Temperatur (°C)')
    ax1.legend()
    ax1.grid(True)
    
    # Plot 2: Heizlast
    ax2.plot(hours, heating_loads, 'r-', label='Heizlast')
    ax2_twin = ax2.twinx()
    ax2_twin.plot(hours, weather_data['solar_radiation'], 'y-', 
                 label='Solare Einstrahlung', alpha=0.5)
    ax2.set_xlabel('Stunde')
    ax2.set_ylabel('Heizlast (kW)', color='r')
    ax2_twin.set_ylabel('Solare Einstrahlung (W/m²)', color='y')
    ax2.legend(loc='upper left')
    ax2_twin.legend(loc='upper right')
    ax2.grid(True)
    
    # Plot 3: Energiebilanz
    ax3.plot(hours, solar_gains, 'y-', label='Solare Gewinne')
    ax3.plot(hours, -transmission_losses, 'b-', label='Transmissionsverluste')
    ax3.plot(hours, -ventilation_losses, 'g-', label='Lüftungsverluste')
    ax3.plot(hours, heating_loads * 1000, 'r-', label='Heizleistung')  # kW zu W
    ax3.set_xlabel('Stunde')
    ax3.set_ylabel('Wärmestrom (W)')
    ax3.legend()
    ax3.grid(True)
    
    # Plot 4: Wind und Luftfeuchte
    ax4.plot(hours, weather_data['wind_speed'], 'g-', label='Windgeschwindigkeit')
    ax4_twin = ax4.twinx()
    ax4_twin.plot(hours, weather_data['humidity'], 'b-', 
                 label='Relative Luftfeuchte', alpha=0.5)
    ax4.set_xlabel('Stunde')
    ax4.set_ylabel('Windgeschwindigkeit (m/s)', color='g')
    ax4_twin.set_ylabel('Relative Luftfeuchte (%)', color='b')
    ax4.legend(loc='upper left')
    ax4_twin.legend(loc='upper right')
    ax4.grid(True)
    
    plt.tight_layout()
    plt.savefig('output/weather_building_integration.png')
    print("\nPlot saved as 'output/weather_building_integration.png'")
    
    # Zusammenfassung der Ergebnisse ausgeben
    print("\nSimulationsergebnisse:")
    print(f"Mittlere Raumtemperatur: {np.mean(temperatures):.1f} °C")
    print(f"Maximale Raumtemperatur: {np.max(temperatures):.1f} °C")
    print(f"Minimale Raumtemperatur: {np.min(temperatures):.1f} °C")
    print(f"Mittlere Heizlast: {np.mean(heating_loads):.2f} kW")
    print(f"Maximale Heizlast: {np.max(heating_loads):.2f} kW")
    print(f"Mittlere solare Gewinne: {np.mean(solar_gains):.0f} W")
    print(f"Mittlere Transmissionsverluste: {np.mean(transmission_losses):.0f} W")
    print(f"Mittlere Lüftungsverluste: {np.mean(ventilation_losses):.0f} W")

if __name__ == '__main__':
    test_weather_building_integration()

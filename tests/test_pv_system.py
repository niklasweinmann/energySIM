import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from src.simulation.pv_system import PVSystem, PVModuleSpecifications, PVArrayConfiguration
from src.data_handlers.weather import WeatherDataHandler

def test_pv_system():
    # PV-System erstellen mit korrekter Parameterreihenfolge
    config = PVArrayConfiguration(
        modules_count=20,  # 20 Module
        tilt=30,  # 30° Neigung
        azimuth=180,  # Südausrichtung
        albedo=0.2,
        module_key="SunPower_MAX6_440",  # Verwende ein Modul aus der Datenbank
        inverter_key="SMA_Sunny_Tripower_10"  # Verwende einen Inverter aus der Datenbank
    )
    
    location = (52.52, 13.405)  # Berlin
    altitude = 34.0  # Berlin Höhe
    
    pv_system = PVSystem(config, location, altitude)
    
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
    dc_powers = []
    ac_powers = []
    
    for idx, row in weather_data.iterrows():
        # Erstelle das weather_data Dictionary im erwarteten Format
        weather_dict = {
            'ghi': row['solar_radiation'],
            'dni': row['solar_radiation'] * 0.85,  # Vereinfachte Annahme
            'dhi': row['solar_radiation'] * 0.15,  # Vereinfachte Annahme  
            'temp_air': row['temperature'],
            'wind_speed': row.get('wind_speed', 1.0)
        }
        
        # Verwende row['timestamp'] als datetime
        timestamp = pd.to_datetime(row['timestamp'])
        
        dc_power, ac_power = pv_system.calculate_power_output(
            timestamp=timestamp,
            weather_data=weather_dict
        )
        dc_powers.append(dc_power)
        ac_powers.append(ac_power)
    
    # Überprüfungen
    assert len(dc_powers) == len(weather_data)
    assert all(dc >= 0 for dc in dc_powers)
    assert all(ac >= 0 for ac in ac_powers)
    assert all(dc >= ac for dc, ac in zip(dc_powers, ac_powers))
    
    # Jahresertrag schätzen
    yearly_yield = pv_system.estimate_yearly_yield(
        yearly_radiation=1000,  # 1000 kWh/m²/Jahr (typisch für Deutschland)
        avg_temp=10.0  # 10°C Durchschnittstemperatur
    )
    
    print(f"Installierte Leistung: {pv_system.total_peak_power/1000:.2f} kWp")
    print(f"Maximale AC-Leistung: {max(ac_powers):.2f} kW")
    print(f"Geschätzter Jahresertrag: {yearly_yield:.0f} kWh")

if __name__ == "__main__":
    test_pv_system()

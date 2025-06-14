"""
Test-Skript für die DWD-Wetter-Integration
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.data_handlers.weather import WeatherDataHandler
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import pandas as pd

def test_dwd_integration():
    """Teste die DWD-Wetter-Integration."""
    
    # Initialize weather handler
    weather = WeatherDataHandler(use_dwd=True)
    
    # Set location (Berlin)
    location = (52.52, 13.4)
    print(f"\nTesting weather data for Berlin {location}")
    
    # Get data for current date and several days
    start_date = datetime(2025, 6, 10)  # 4 Tage Daten
    end_date = datetime(2025, 6, 13)
    print(f"\nFetching weather data from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
    
    try:
        data = weather.get_historical_data(
            location=location,
            start_date=start_date,
            end_date=end_date
        )
        
        print("\nData columns available:", data.columns.tolist())
        print(f"\nLoaded {len(data)} data points")
        print("\nFirst few rows of data:")
        print(data.head())
        
        # Plot the data
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))
        fig.suptitle(f'Weather Data for Berlin ({start_date.strftime("%Y-%m-%d")} to {end_date.strftime("%Y-%m-%d")})')
        
        # Temperature plot
        ax1.plot(data['timestamp'].dt.hour, data['temperature'], 'r-', label='Temperature')
        ax1_twin = ax1.twinx()
        ax1_twin.plot(data['timestamp'].dt.hour, data['humidity'], 'b--', label='Humidity')
        
        ax1.set_xlabel('Hour')
        ax1.set_ylabel('Temperature (°C)', color='r')
        ax1_twin.set_ylabel('Humidity (%)', color='b')
        ax1.grid(True)
        
        # Solar radiation plot
        ax2.plot(data['timestamp'].dt.hour, data['solar_radiation'], 'y-', label='Solar Radiation')
        ax2_twin = ax2.twinx()
        ax2_twin.plot(data['timestamp'].dt.hour, data['wind_speed'], 'g--', label='Wind Speed')
        
        ax2.set_xlabel('Hour')
        ax2.set_ylabel('Solar Radiation (W/m²)', color='y')
        ax2_twin.set_ylabel('Wind Speed (m/s)', color='g')
        ax2.grid(True)
        
        # Add legends
        ax1.legend(loc='upper left')
        ax1_twin.legend(loc='upper right')
        ax2.legend(loc='upper left')
        ax2_twin.legend(loc='upper right')
        
        plt.tight_layout()
        plt.savefig('output/dwd_weather_test.png')
        print("\nPlot saved as 'output/dwd_weather_test.png'")
        
    except Exception as e:
        print(f"\nError testing DWD integration: {str(e)}")
        raise

if __name__ == '__main__':
    test_dwd_integration()

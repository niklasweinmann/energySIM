"""
EnergyOS - Main program for building energy system simulation
"""

import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
import json
from typing import Dict, Any, Optional, Tuple, List, Union
import importlib.util
import logging

# Logger konfigurieren
logger = logging.getLogger(__name__)

# Importe basierend auf dem Ausführungskontext
try:
    if __name__ == "__main__":
        # Wenn direkt ausgeführt
        from simulation.heat_pump import HeatPump, HeatPumpSpecifications
        from simulation.pv_system import PVSystem, PVArrayConfiguration
        from data_handlers.components import ComponentsDatabase
        from data_handlers.weather import WeatherDataHandler
        from core.building import Building, BuildingProperties
    else:
        # Wenn als Modul importiert
        from .simulation.heat_pump import HeatPump, HeatPumpSpecifications
        from .simulation.pv_system import PVSystem, PVArrayConfiguration
        from .data_handlers.components import ComponentsDatabase
        from .data_handlers.weather import WeatherDataHandler
        from .core.building import Building, BuildingProperties
except ImportError:
    # Fallback für absolute Importe
    from src.simulation.heat_pump import HeatPump, HeatPumpSpecifications
    from src.simulation.pv_system import PVSystem, PVArrayConfiguration
    from src.data_handlers.components import ComponentsDatabase
    from src.data_handlers.weather import WeatherDataHandler
    from src.core.building import Building, BuildingProperties

def init_heat_pump() -> HeatPump:
    """Initialize heat pump with default parameters."""
    # Initialize components database
    db = ComponentsDatabase()
    heat_pump_data = db.get_heat_pump("Viessmann_Vitocal_200S")
    
    # COP Datenpunkte konvertieren von A7W35 Format zu (7.0, 35.0) Tupel
    cop_rating_points = {}
    for key, cop in heat_pump_data.cop_data.items():
        # Format A7W35 aufteilen und konvertieren
        if key.startswith('A') and 'W' in key:
            try:
                outside_temp = float(key.split('A')[1].split('W')[0])
                flow_temp = float(key.split('W')[1])
                cop_rating_points[(float(outside_temp), float(flow_temp))] = float(cop)
            except (ValueError, IndexError) as e:
                logger.error(f"Fehler bei der Konvertierung des COP-Schlüssels {key}: {e}")
    
    specs = HeatPumpSpecifications(
        nominal_heating_power=heat_pump_data.nominal_heating_power / 1000,  # Convert W to kW
        cop_rating_points=cop_rating_points,
        min_outside_temp=heat_pump_data.min_outdoor_temp,
        max_flow_temp=heat_pump_data.max_flow_temp,
        min_part_load_ratio=0.3,
        defrost_temp_threshold=7.0,
        thermal_mass=20.0,
    )
    return HeatPump(specs)

def init_pv_system() -> PVSystem:
    """Initialize PV system with default parameters using component database."""
    array_config = PVArrayConfiguration(
        modules_count=25,  # 25 modules for ~10 kWp
        tilt=30,  # 30° tilt
        azimuth=180,  # South orientation
        albedo=0.2,  # Default ground reflection
        module_key="SunPower_MAX6_440",  # High-efficiency module
        inverter_key="SMA_Sunny_Tripower_10"  # 10 kW inverter
    )
    
    return PVSystem(
        config=array_config,
        location=(52.52, 13.4),  # Berlin
        altitude=34.0  # Height above sea level in Berlin
    )

def run_simulation(
    latitude: float = 52.52,
    longitude: float = 13.41,
    building_type: str = "single_family",
    heated_area: float = 150,
    building_year: int = 2015,
    building_standard: Optional[str] = None,
    heatpump_type: str = "air_water",
    heatpump_power: float = 9.0,
    storage_volume: float = 300,
    heating_system: str = "floor_heating",
    pv_peak_power: float = 10.0,
    pv_orientation: float = 0.0,
    pv_tilt: float = 30.0,
    start_date: str = "2025-01-01",
    end_date: str = "2025-01-07",
    time_step_minutes: int = 60,
    save_output: bool = False,
    output_file: Optional[str] = None,
    create_plot: bool = False
) -> Dict[str, Any]:
    """
    Führt eine Energiesystemsimulation mit den angegebenen Parametern durch.
    
    Args:
        latitude: Breitengrad des Gebäudestandorts
        longitude: Längengrad des Gebäudestandorts
        building_type: Gebäudetyp ('single_family', 'multi_family', 'apartment')
        heated_area: Beheizte Fläche in m²
        building_year: Baujahr des Gebäudes
        building_standard: Optional, Baustandard ('EnEV2014', 'EnEV2016', 'GEG2020', 'KfW55', 'KfW40', 'KfW40plus')
        heatpump_type: Wärmepumpentyp ('air_water', 'brine_water', 'water_water')
        heatpump_power: Nennleistung der Wärmepumpe in kW
        storage_volume: Speichervolumen in Liter
        heating_system: Heizungssystem ('radiator', 'floor_heating')
        pv_peak_power: Spitzenleistung der PV-Anlage in kWp
        pv_orientation: Ausrichtung der Module in Grad (0=Süd, -90=Ost, 90=West)
        pv_tilt: Neigung der Module in Grad (0=horizontal, 90=vertikal)
        start_date: Startdatum der Simulation (Format: 'YYYY-MM-DD')
        end_date: Enddatum der Simulation (Format: 'YYYY-MM-DD')
        time_step_minutes: Zeitschritt in Minuten (Standard: 60)
        save_output: Wenn True, werden detaillierte Simulationsergebnisse in einer Datei gespeichert
        output_file: Optionaler Pfad für die Ausgabedatei (Standard: 'simulation_results_{Datum}.csv')
        create_plot: Wenn True, wird ein Plot der Simulationsergebnisse erstellt (nur für kurze Zeiträume sinnvoll)
        
    Returns:
        Dictionary mit Simulationsergebnissen:
        - energy_demand: Energiebedarf in kWh
        - energy_production: Energieproduktion in kWh
        - self_consumption: Eigenverbrauch in kWh
        - costs: Kosten in Euro
        - emissions: CO2-Emissionen in kg
        - renewable_share: Anteil erneuerbarer Energien (0-1)
        - temperatures: Zeitreihe der Temperaturen
        - power_flows: Zeitreihe der Energieflüsse
    """
    # Konvertiere Zeitschritt von Minuten in Stunden
    time_step_hours = time_step_minutes / 60.0
    
    # Initialisiere Systeme
    heat_pump = init_heat_pump()
    
    # PV-System mit angepassten Parametern
    modules_count = round(pv_peak_power / 0.4)  # Annahme: ~400Wp pro Modul
    array_config = PVArrayConfiguration(
        modules_count=modules_count,
        tilt=pv_tilt,
        azimuth=180 + pv_orientation,  # Umrechnung: 0=Süd, 180=Nord (intern)
        albedo=0.2,
        module_key="SunPower_MAX6_440",
        inverter_key="SMA_Sunny_Tripower_10" if pv_peak_power <= 10 else "SMA_Sunny_Tripower_15"
    )
    
    pv_system = PVSystem(
        config=array_config,
        location=(latitude, longitude),
        altitude=34.0  # Standardwert, könnte anhand der Koordinaten genauer bestimmt werden
    )
    
    # Wetterdaten
    weather = WeatherDataHandler()
    location = (latitude, longitude)
    
    # Parse dates
    start = datetime.strptime(start_date, '%Y-%m-%d')
    end = datetime.strptime(end_date, '%Y-%m-%d')
    
    # Bestimme Anzahl der Zeitschritte
    simulation_duration = (end - start).days + 1
    steps_per_day = 24 * 60 / time_step_minutes
    total_steps = int(simulation_duration * steps_per_day)
    
    # Erstelle Zeitpunkte für die Simulation
    timestamps = [start + timedelta(minutes=i*time_step_minutes) for i in range(total_steps)]
    
    # Ergebnisarrays initialisieren
    outside_temps = []
    solar_radiations = []
    heat_demands = []
    heat_outputs = []
    power_inputs = []
    pv_dc_outputs = []
    pv_ac_outputs = []
    cop_values = []
    flow_temps = []
    # Liste der tatsächlich verwendeten Zeitpunkte
    used_timestamps = []
    
    # Pro Tag simulieren
    current_date = start
    while current_date <= end:
        # Hole Wetterdaten für den aktuellen Tag
        next_day = current_date + timedelta(days=1)
        weather_data = weather.get_historical_data(location, current_date, next_day)
        
        # Debug-Ausgabe zum Verstehen der Struktur der Wetterdaten
        print(f"\nWetterdaten für {current_date.strftime('%Y-%m-%d')}:")
        print(f"Shape: {weather_data.shape}, Columns: {weather_data.columns}")
        print(f"Anzahl der Zeitpunkte: {len(weather_data)}")
        
        # Interpoliere Wetterdaten auf Zeitschritte
        # Verwende die tatsächlichen Stunden aus den Wetterdaten anstatt eine feste Liste
        if 'timestamp' in weather_data.columns:
            # Verwende die Stunden direkt aus den timestamp-Daten
            data_hours = pd.to_datetime(weather_data['timestamp']).dt.hour.values + pd.to_datetime(weather_data['timestamp']).dt.minute.values / 60.0
        else:
            # Fallback: Nehme an, dass Daten stündlich von 0-23 Uhr vorliegen
            data_hours = np.arange(len(weather_data)) % 24
            
        # Debug-Ausgabe für die Stunden
        print(f"Stunden in den Wetterdaten: {data_hours}")
        
        minutes_in_day = np.arange(0, 24*60, time_step_minutes)
        hours_as_float = minutes_in_day / 60.0
        
        # Stelle sicher, dass die Daten die richtige Größe haben, bevor wir interpolieren
        if len(data_hours) != len(weather_data['temperature']):
            print(f"WARNUNG: Stunden ({len(data_hours)}) und Temperaturdaten ({len(weather_data['temperature'])}) haben unterschiedliche Längen!")
            # Verwende nur so viele Datenpunkte, wie in beiden Arrays vorhanden sind
            min_len = min(len(data_hours), len(weather_data['temperature']))
            data_hours = data_hours[:min_len]
            weather_data = weather_data.iloc[:min_len]
        
        # Debug-Ausgabe vor der Interpolation
        print(f"Interpoliere von {len(data_hours)} Wetterdaten-Punkten auf {len(hours_as_float)} Zeitschritte")
        
        # Interpoliere Temperaturen
        temp_interpolation = np.interp(
            hours_as_float, 
            data_hours, 
            weather_data['temperature']
        )
        
        # Interpoliere Solarstrahlung
        radiation_interpolation = np.interp(
            hours_as_float, 
            data_hours, 
            weather_data['solar_radiation']
        )
        
        # Interpoliere Windgeschwindigkeit
        wind_interpolation = np.interp(
            hours_as_float, 
            data_hours, 
            weather_data['wind_speed']
        )
        
        # Simplifizierten Wärmebedarf basierend auf Außentemperatur berechnen
        # In der Realität würde hier ein detailliertes Gebäudemodell verwendet
        heat_demand_daily = []
        for temp in temp_interpolation:
            # Einfaches Modell: Heizgrenztemperatur 15°C, darunter linear steigender Bedarf
            if temp < 15:
                demand = max(0, (15 - temp) * heated_area * 0.03)  # ~3W/m² pro Kelvin
            else:
                demand = 0
            heat_demand_daily.append(demand)
        
        # Simuliere für jeden Zeitschritt des Tages
        for i, minute in enumerate(minutes_in_day):
            hour_decimal = minute / 60.0
            hour = int(hour_decimal)
            minute_of_hour = int((hour_decimal - hour) * 60)
            
            timestamp = current_date.replace(hour=hour, minute=minute_of_hour)
            if timestamp > end:
                break
            
            outside_temp = temp_interpolation[i]
            solar_radiation = radiation_interpolation[i]
            wind_speed = wind_interpolation[i]
            heat_demand = heat_demand_daily[i] * time_step_hours  # kWh für diesen Zeitschritt
            
            # Heat pump simulation
            flow_temp = heat_pump.calculate_flow_temperature(outside_temp)
            cop = heat_pump.calculate_cop(outside_temp, flow_temp)
            heat_output, power_input = heat_pump.get_power_output(
                outside_temp=outside_temp,
                flow_temp=flow_temp,
                demand=heat_demand,
                time_step=time_step_hours
            )
            
            # PV simulation
            current_weather = {
                'ghi': solar_radiation,
                'dni': solar_radiation * 0.85,  # Vereinfachte DNI
                'dhi': solar_radiation * 0.15,  # Vereinfachte DHI
                'temp_air': outside_temp,
                'wind_speed': wind_speed
            }
            
            dc_power, ac_power = pv_system.calculate_power_output(
                timestamp, current_weather
            )
            
            # Werte speichern
            outside_temps.append(outside_temp)
            solar_radiations.append(solar_radiation)
            heat_demands.append(heat_demand)
            heat_outputs.append(heat_output)
            power_inputs.append(power_input)
            pv_dc_outputs.append(float(dc_power) if dc_power is not None else 0)
            pv_ac_outputs.append(float(ac_power) if ac_power is not None else 0)
            cop_values.append(cop)
            flow_temps.append(flow_temp)
            used_timestamps.append(timestamp)
        
        current_date += timedelta(days=1)
    
    # Ergebnisse zusammenfassen
    total_heat_demand = sum(heat_demands)
    total_heat_output = sum(heat_outputs)
    total_power_input = sum(power_inputs)
    total_pv_production = sum(pv_ac_outputs)
    
    # Einfache Berechnung des Eigenverbrauchs (könnte detaillierter sein)
    self_consumption = 0
    grid_feed = 0
    grid_draw = 0
    
    for pv, hp in zip(pv_ac_outputs, power_inputs):
        if pv >= hp:
            self_consumption += hp
            grid_feed += (pv - hp)
        else:
            self_consumption += pv
            grid_draw += (hp - pv)
    
    # Energiebilanz
    energy_results = {
        "heat_demand_kWh": total_heat_demand,
        "heat_output_kWh": total_heat_output,
        "cop_average": total_heat_output / total_power_input if total_power_input > 0 else 0,
        "electricity_consumption_kWh": total_power_input,
        "pv_production_kWh": total_pv_production,
        "self_consumption_kWh": self_consumption,
        "grid_feed_kWh": grid_feed,
        "grid_draw_kWh": grid_draw,
        "self_sufficiency": self_consumption / total_power_input if total_power_input > 0 else 0,
        "renewable_share": (total_pv_production / total_power_input) if total_power_input > 0 else 0
    }
    
    # Wirtschaftsberechnung (vereinfacht)
    electricity_price = 0.32  # €/kWh
    feed_in_tariff = 0.08  # €/kWh
    
    costs = {
        "electricity_costs": grid_draw * electricity_price,
        "feed_in_revenue": grid_feed * feed_in_tariff,
        "net_energy_costs": grid_draw * electricity_price - grid_feed * feed_in_tariff
    }
    
    # Emissionen (vereinfacht)
    grid_emission_factor = 0.388  # kg CO2/kWh
    emissions = {
        "total_emissions": grid_draw * grid_emission_factor,
        "emissions_saved": grid_feed * grid_emission_factor,
        "net_emissions": (grid_draw - grid_feed) * grid_emission_factor
    }
    
    # Wenn ein Plot erstellt werden soll
    if create_plot:
        # Erstelle einen Plot für einen Tag oder die gesamte Zeitreihe (je nach Länge)
        if len(timestamps) <= 96:  # Max. 4 Tage für detaillierten Plot
            # Konvertiere zu stündlichen Werten für die Visualisierung, falls längere Zeiträume
            plot_indices = np.linspace(0, len(timestamps)-1, min(len(timestamps), 24)).astype(int)
            
            # Erstelle Plot
            fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))
            fig.suptitle('Building Energy System Simulation')
            
            # Zeitachse für Plots
            hours = [i * time_step_hours for i in range(len(plot_indices))]
            
            # Plot 1: Temperaturen
            ax1.plot(hours, [outside_temps[i] for i in plot_indices], 'b-', label='Outside Temperature')
            ax1.plot(hours, [flow_temps[i] for i in plot_indices], 'r-', label='Flow Temperature')
            ax1.set_xlabel('Hour')
            ax1.set_ylabel('Temperature (°C)')
            ax1.legend()
            ax1.grid(True)
            
            # Plot 2: COP und PV-Leistung
            ax2.plot(hours, [cop_values[i] for i in plot_indices], 'g-', label='Heat Pump COP')
            ax2.plot(hours, [pv_ac_outputs[i] for i in plot_indices], 'y-', label='PV Power (AC)')
            ax2.set_xlabel('Hour')
            ax2.set_ylabel('COP / Power (kW)')
            ax2.legend()
            ax2.grid(True)
            
            # Plot 3: Wärmepumpenleistung
            ax3.plot(hours, [heat_outputs[i] for i in plot_indices], 'r-', label='Heat Output')
            ax3.plot(hours, [power_inputs[i] for i in plot_indices], 'b-', label='Power Input')
            ax3.plot(hours, [heat_demands[i] for i in plot_indices], 'k--', label='Heat Demand')
            ax3.set_xlabel('Hour')
            ax3.set_ylabel('Power (kW)')
            ax3.legend()
            ax3.grid(True)
            
            # Plot 4: Solarstrahlung
            ax4.plot(hours, [solar_radiations[i] for i in plot_indices], 'y-', label='Global Radiation')
            ax4.set_xlabel('Hour')
            ax4.set_ylabel('Irradiance (W/m²)')
            ax4.legend()
            ax4.grid(True)
            
            # Speichere Plot
            output_dir = Path(__file__).parent.parent / 'output'
            output_dir.mkdir(exist_ok=True)
            
            plot_filename = output_dir / f'simulation_plot_{start_date}_to_{end_date}.png'
            plt.savefig(plot_filename)
            plt.close()
            print(f"Simulationsplot gespeichert unter: {plot_filename}")
        else:
            # Erstelle zusammengefassten Tagesplot für längere Simulationen
            # Tägliche Aggregation
            daily_data = pd.DataFrame({
                'timestamp': timestamps,
                'heat_demand': heat_demands,
                'heat_output': heat_outputs,
                'power_input': power_inputs,
                'pv_output': pv_ac_outputs,
                'temperature': outside_temps
            })
            daily_data['date'] = pd.to_datetime(daily_data['timestamp']).dt.date
            daily_agg = daily_data.groupby('date').agg({
                'heat_demand': 'sum',
                'heat_output': 'sum',
                'power_input': 'sum',
                'pv_output': 'sum',
                'temperature': 'mean'
            })
            
            # Plot der täglichen Werte
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))
            fig.suptitle('Daily Energy Balance')
            
            # Plot 1: Energie
            dates = daily_agg.index
            ax1.bar(dates, daily_agg['heat_demand'], label='Heat Demand', alpha=0.7)
            ax1.bar(dates, daily_agg['heat_output'], label='Heat Output', alpha=0.7)
            ax1.plot(dates, daily_agg['pv_output'], 'y-', label='PV Production', linewidth=2)
            ax1.set_xlabel('Date')
            ax1.set_ylabel('Energy (kWh)')
            ax1.legend()
            ax1.grid(True)
            
            # Plot 2: Temperatur und Leistung
            ax2.plot(dates, daily_agg['temperature'], 'b-', label='Average Temperature')
            ax2.set_xlabel('Date')
            ax2.set_ylabel('Temperature (°C)')
            ax2.legend(loc='upper left')
            ax2.grid(True)
            
            # Zweite Y-Achse für Effizienz
            ax3 = ax2.twinx()
            efficiency = daily_agg['heat_output'] / daily_agg['power_input']
            efficiency = efficiency.replace([np.inf, -np.inf, np.nan], 0)
            ax3.plot(dates, efficiency, 'g-', label='COP')
            ax3.set_ylabel('COP')
            ax3.legend(loc='upper right')
            
            # Speichere Plot
            output_dir = Path(__file__).parent.parent / 'output'
            output_dir.mkdir(exist_ok=True)
            
            plot_filename = output_dir / f'daily_energy_balance_{start_date}_to_{end_date}.png'
            plt.savefig(plot_filename)
            plt.close()
            print(f"Tägliche Energiebilanz gespeichert unter: {plot_filename}")
    
    # Wenn gewünscht, speichere detaillierte Zeitreihen in CSV
    if save_output:
        if not output_file:
            output_dir = Path(__file__).parent.parent / 'output'
            output_dir.mkdir(exist_ok=True)
            current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = output_dir / f'simulation_results_{current_time}.csv'
        else:
            output_file = Path(output_file)
            output_file.parent.mkdir(exist_ok=True, parents=True)
        
        # Erstelle DataFrame mit Zeitreihen
        df_results = pd.DataFrame({
            'timestamp': used_timestamps,  # Verwende die tatsächlich verwendeten Zeitstempel
            'outside_temperature': outside_temps,
            'flow_temperature': flow_temps,
            'solar_radiation': solar_radiations,
            'heat_demand': heat_demands,
            'heat_output': heat_outputs,
            'cop': cop_values,
            'power_input': power_inputs,
            'pv_dc_output': pv_dc_outputs,
            'pv_ac_output': pv_ac_outputs,
        })
        
        # Speichere CSV
        df_results.to_csv(output_file, index=False)
        print(f"Detaillierte Simulationsergebnisse gespeichert unter: {output_file}")
    
    # Rückgabewerte
    return {
        "energy_demand": energy_results,
        "costs": costs,
        "emissions": emissions,
        "time_series_summary": {
            "outside_temp_avg": sum(outside_temps) / len(outside_temps),
            "outside_temp_min": min(outside_temps),
            "outside_temp_max": max(outside_temps),
            "cop_avg": sum(cop_values) / len(cop_values),
            "pv_peak_output": max(pv_ac_outputs),
        },
        "output_file": str(output_file) if save_output else None
    }

def simulate_day():
    """Run a daily simulation of the energy system."""
    
    # Initialize systems
    heat_pump = init_heat_pump()
    pv_system = init_pv_system()
    weather = WeatherDataHandler()
    location = (52.52, 13.4)  # Berlin
    
    # Get weather data for simulation day
    simulation_date = datetime(2025, 6, 13)  # Current date
    next_day = simulation_date + timedelta(days=1)
    weather_data = weather.get_historical_data(location, simulation_date, next_day)
    
    # Prepare arrays
    hours = np.arange(24)
    outside_temps = weather_data['temperature'].values
    heat_demand = 6 + 4 * np.cos(2 * np.pi * (hours - 2) / 24)  # kW
    
    # Result arrays
    heat_output = np.zeros(24)
    power_input = np.zeros(24)
    pv_dc_output = np.zeros(24)
    pv_ac_output = np.zeros(24)
    cop_values = np.zeros(24)
    flow_temps = np.zeros(24)
    
    # Run simulation for each timestep
    for i, hour in enumerate(hours):
        # Heat pump simulation
        flow_temps[i] = heat_pump.calculate_flow_temperature(outside_temps[i])
        cop_values[i] = heat_pump.calculate_cop(outside_temps[i], flow_temps[i])
        heat_output[i], power_input[i] = heat_pump.get_power_output(
            outside_temp=outside_temps[i],
            flow_temp=flow_temps[i],
            demand=heat_demand[i],
            time_step=1.0
        )
        
        # Prepare weather data for PV simulation
        current_datetime = simulation_date.replace(hour=hour)
        current_weather = {
            'ghi': weather_data['solar_radiation'].iloc[i],
            'dni': weather_data['solar_radiation'].iloc[i] * 0.85,  # Simplified DNI
            'dhi': weather_data['solar_radiation'].iloc[i] * 0.15,  # Simplified DHI
            'temp_air': outside_temps[i],
            'wind_speed': weather_data['wind_speed'].iloc[i]
        }
        
        # PV simulation
        dc_power, ac_power = pv_system.calculate_power_output(
            current_datetime,
            current_weather
        )
        pv_dc_output[i] = float(dc_power) if dc_power is not None else 0
        pv_ac_output[i] = float(ac_power) if ac_power is not None else 0
    
    # Plot results
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))
    fig.suptitle('Building Energy System Simulation over 24 Hours')
    
    # Plot 1: Temperatures
    ax1.plot(hours, outside_temps, 'b-', label='Outside Temperature')
    ax1.plot(hours, flow_temps, 'r-', label='Flow Temperature')
    ax1.set_xlabel('Hour')
    ax1.set_ylabel('Temperature (°C)')
    ax1.legend()
    ax1.grid(True)
    
    # Plot 2: COP and PV Power
    ax2.plot(hours, cop_values, 'g-', label='Heat Pump COP')
    ax2.plot(hours, pv_ac_output, 'y-', label='PV Power (AC)')
    ax2.set_xlabel('Hour')
    ax2.set_ylabel('COP / Power (kW)')
    ax2.legend()
    ax2.grid(True)
    
    # Plot 3: Heat Pump Power
    ax3.plot(hours, heat_output, 'r-', label='Heat Output')
    ax3.plot(hours, power_input, 'b-', label='Power Input')
    ax3.plot(hours, heat_demand, 'k--', label='Heat Demand')
    ax3.set_xlabel('Hour')
    ax3.set_ylabel('Power (kW)')
    ax3.legend()
    ax3.grid(True)
    
    # Plot 4: Solar Radiation
    ax4.plot(hours, weather_data['solar_radiation'], 'y-', label='Global Radiation')
    ax4.set_xlabel('Hour')
    ax4.set_ylabel('Irradiance (W/m²)')
    ax4.legend()
    ax4.grid(True)
    
    # Save plot
    output_dir = Path(__file__).parent.parent / 'output'
    output_dir.mkdir(exist_ok=True)
    plt.savefig(output_dir / 'energy_system_simulation.png')
    plt.close()

if __name__ == '__main__':
    # Beispiel für eine Simulation
    results = run_simulation(
        latitude=52.52,
        longitude=13.41,
        building_type="single_family",
        heated_area=150,
        building_year=2015,
        heatpump_power=9,
        pv_peak_power=10,
        start_date="2025-06-10",
        end_date="2025-06-15",
        time_step_minutes=60,  # 1-Stunden-Zeitschritte
        save_output=True,
        create_plot=True
    )
    
    print("Simulationsergebnisse:")
    print(json.dumps(results, indent=2))

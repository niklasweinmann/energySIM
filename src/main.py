"""
EnergyOS - Main program for building energy system simulation
"""

import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from datetime import datetime

from simulation.heat_pump import HeatPump, HeatPumpSpecifications
from simulation.pv_system import PVSystem, PVModuleSpecifications, PVArrayConfiguration

def init_heat_pump() -> HeatPump:
    """Initialize heat pump with default parameters."""
    specs = HeatPumpSpecifications(
        nominal_heating_power=10.0,  # 10 kW
        cop_rating_points={
            (-7, 35): 2.70, (-7, 45): 2.20,
            (2, 35): 3.40, (2, 45): 2.70,
            (7, 35): 4.00, (7, 45): 3.20,
            (10, 35): 4.40, (10, 45): 3.50,
        },
        min_outside_temp=-20.0,
        max_flow_temp=60.0,
        min_part_load_ratio=0.3,
        defrost_temp_threshold=7.0,
        thermal_mass=20.0,
    )
    return HeatPump(specs)

def init_pv_system() -> PVSystem:
    """Initialize PV system with default parameters."""
    module_specs = PVModuleSpecifications(
        peak_power=400.0,  # Wp per module
        area=1.75,  # m² per module
        efficiency_stc=20.0,  # 20% efficiency
        temp_coefficient=-0.35,  # -0.35%/K
        noct=45.0  # °C
    )
    
    array_config = PVArrayConfiguration(
        modules_count=25,  # 25 modules for ~10 kWp
        tilt=30,  # 30° tilt
        azimuth=180,  # South orientation
        albedo=0.2  # Default ground reflection
    )
    
    return PVSystem(
        module_specs=module_specs,
        config=array_config,
        location=(52.52, 13.4),  # Berlin
        altitude=34.0  # Height above sea level in Berlin
    )

def simulate_day():
    """Run a daily simulation of the energy system."""
    
    # Initialize systems
    heat_pump = init_heat_pump()
    pv_system = init_pv_system()
    
    # Simulation setup
    hours = np.arange(24)
    outside_temps = 5 + 5 * np.sin(2 * np.pi * (hours - 14) / 24)  # Min: 0°C, Max: 10°C
    heat_demand = 6 + 4 * np.cos(2 * np.pi * (hours - 2) / 24)  # kW
    
    # Result arrays
    heat_output = np.zeros(24)
    power_input = np.zeros(24)
    pv_dc_output = np.zeros(24)
    pv_ac_output = np.zeros(24)
    cop_values = np.zeros(24)
    flow_temps = np.zeros(24)
    
    # Simplified radiation profile
    max_ghi = 800  # W/m²
    max_dni = 600  # W/m²
    max_dhi = 200  # W/m²
    
    # Initialize weather data arrays
    ghi = np.zeros(24)
    dni = np.zeros(24)
    dhi = np.zeros(24)
    
    # Create simplified daily radiation profile
    for i in range(24):
        if 6 <= i <= 18:  # Daylight between 6 and 18
            sun_height = np.sin(np.pi * (i - 6) / 12)
            ghi[i] = max_ghi * sun_height
            dni[i] = max_dni * sun_height
            dhi[i] = max_dhi * sun_height
    
    # Wind speed (simplified constant)
    wind_speed = 2.0  # m/s
    
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
        
        # PV simulation for current date (June 13, 2025)
        current_datetime = datetime(2025, 6, 13, hour)
        weather_data = {
            'ghi': ghi[i],
            'dni': dni[i],
            'dhi': dhi[i],
            'temp_air': outside_temps[i],
            'wind_speed': wind_speed
        }
        
        dc_power, ac_power = pv_system.calculate_power_output(
            current_datetime,
            weather_data
        )
        pv_dc_output[i] = float(dc_power.iloc[0])
        pv_ac_output[i] = float(ac_power.iloc[0])
    
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
    
    # Plot 4: Radiation
    ax4.plot(hours, ghi, 'y-', label='Global Horizontal')
    ax4.plot(hours, dni, 'r-', label='Direct Normal')
    ax4.plot(hours, dhi, 'b-', label='Diffuse Horizontal')
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
    simulate_day()

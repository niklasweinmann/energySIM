"""
EnergyOS - Hauptprogramm für die Gebäude-Energiesystem-Simulation
"""

from simulation.heat_pump import HeatPump, HeatPumpSpecifications
from simulation.pv_system import PVSystem, PVModuleSpecifications, PVArrayConfiguration
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from datetime import datetime

def run_simple_simulation():
    """Führt eine einfache Simulation einer Wärmepumpe und PV-Anlage über einen Tag durch."""
    
    # Wärmepumpen-Setup
    cop_rating_points = {
        (-7, 35): 2.70,
        (-7, 45): 2.20,
        (2, 35): 3.40,
        (2, 45): 2.70,
        (7, 35): 4.00,
        (7, 45): 3.20,
        (10, 35): 4.40,
        (10, 45): 3.50,
    }
    
    heat_pump_specs = HeatPumpSpecifications(
        nominal_heating_power=10.0,  # 10 kW
        cop_rating_points=cop_rating_points,
        min_outside_temp=-20.0,
        max_flow_temp=60.0,
        min_part_load_ratio=0.3,
        defrost_temp_threshold=7.0,
        thermal_mass=20.0,
    )
    
    heat_pump = HeatPump(heat_pump_specs)
    
    # PV-System-Setup
    pv_specs = PVModuleSpecifications(
        peak_power=400.0,  # Wp pro Modul
        area=1.75,  # m² pro Modul
        efficiency_stc=20.0,  # 20% Wirkungsgrad
        temp_coefficient=-0.35,  # -0.35%/K
    )
    
    pv_config = PVArrayConfiguration(
        modules_count=25,  # 25 Module für ca. 10 kWp
        tilt=30,  # 30° Neigung
        azimuth=180,  # Süd-Ausrichtung
    )
    
    pv_system = PVSystem(
        module_specs=pv_specs,
        config=pv_config,
        location=(52.52, 13.4),  # Berlin
        altitude=34.0  # Höhe über NN in Berlin
    )
    
    # Wärmepumpen-Spezifikationen (Beispiel einer 10kW Luft-Wasser-Wärmepumpe)
    cop_rating_points = {
        (-7, 35): 2.70,
        (-7, 45): 2.20,
        (2, 35): 3.40,
        (2, 45): 2.70,
        (7, 35): 4.00,
        (7, 45): 3.20,
        (10, 35): 4.40,
        (10, 45): 3.50,
    }
    
    specs = HeatPumpSpecifications(
        nominal_heating_power=10.0,  # 10 kW
        cop_rating_points=cop_rating_points,
        min_outside_temp=-20.0,
        max_flow_temp=60.0,
        min_part_load_ratio=0.3,
        defrost_temp_threshold=7.0,
        thermal_mass=20.0,
    )
    
    heat_pump = HeatPump(specs)
    
    # PV-System-Setup
    pv_specs = PVModuleSpecifications(
        peak_power=400.0,  # Wp pro Modul
        area=1.75,  # m² pro Modul
        efficiency_stc=20.0,  # 20% Wirkungsgrad
        temp_coefficient=-0.35,  # -0.35%/K
        noct=45.0,  # Nominal Operating Cell Temperature
    )
    
    pv_config = PVArrayConfiguration(
        modules_count=25,  # 25 Module für ca. 10 kWp
        tilt=30,  # 30° Neigung
        azimuth=180,  # Süd-Ausrichtung
        albedo=0.2  # Standard-Bodenreflexion
    )
    
    pv_system = PVSystem(
        module_specs=pv_specs,
        config=pv_config,
        location=(52.52, 13.4),  # Berlin
        altitude=34.0  # Höhe über NN in Berlin
    )
    
    # Simulation durchführen
    hours = np.arange(24)
    outside_temps = 5 + 5 * np.sin(2 * np.pi * (hours - 14) / 24)  # Min: 0°C, Max: 10°C
    heat_demand = 6 + 4 * np.cos(2 * np.pi * (hours - 2) / 24)  # kW
    
    # Arrays für die Ergebnisse
    heat_output = np.zeros(24)
    power_input = np.zeros(24)
    pv_output = np.zeros(24)
    cop_values = np.zeros(24)
    flow_temps = np.zeros(24)
    
    # Beispiel-Strahlungsverlauf (vereinfacht)
    max_irradiance = 800  # W/m²
    irradiance = np.zeros(24)
    for i in range(24):
        if 6 <= i <= 18:  # Tageslicht zwischen 6 und 18 Uhr
            irradiance[i] = max_irradiance * np.sin(np.pi * (i - 6) / 12)
    
    # Führe die Simulation für jeden Zeitschritt durch
    for i, hour in enumerate(hours):
        # Wärmepumpen-Simulation
        flow_temps[i] = heat_pump.calculate_flow_temperature(outside_temps[i])
        cop_values[i] = heat_pump.calculate_cop(outside_temps[i], flow_temps[i])
        heat_output[i], power_input[i] = heat_pump.get_power_output(
            outside_temp=outside_temps[i],
            flow_temp=flow_temps[i],
            demand=heat_demand[i],
            time_step=1.0
        )
        
        # PV-Simulation für das aktuelle Datum (13. Juni 2025)
        current_datetime = datetime(2025, 6, 13, hour)
        pv_output[i] = pv_system.calculate_power_output(
            current_datetime,
            irradiance[i],
            outside_temps[i]
        )
    
    # Plotte die Ergebnisse
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))
    fig.suptitle('Gebäude-Energiesystem-Simulation über 24 Stunden')
    
    # Plot 1: Temperaturen
    ax1.plot(hours, outside_temps, 'b-', label='Außentemperatur')
    ax1.plot(hours, flow_temps, 'r-', label='Vorlauftemperatur')
    ax1.set_xlabel('Stunde')
    ax1.set_ylabel('Temperatur (°C)')
    ax1.legend()
    ax1.grid(True)
    
    # Plot 2: COP und PV-Leistung
    ax2.plot(hours, cop_values, 'g-', label='COP')
    ax2_twin = ax2.twinx()
    ax2_twin.plot(hours, pv_output, 'y-', label='PV-Leistung')
    ax2.set_xlabel('Stunde')
    ax2.set_ylabel('COP')
    ax2_twin.set_ylabel('PV-Leistung (kW)')
    lines1, labels1 = ax2.get_legend_handles_labels()
    lines2, labels2 = ax2_twin.get_legend_handles_labels()
    ax2.legend(lines1 + lines2, labels1 + labels2)
    ax2.grid(True)
    
    # Plot 3: Wärmeleistung
    ax3.plot(hours, heat_demand, 'b-', label='Bedarf')
    ax3.plot(hours, heat_output, 'r-', label='Erzeugung')
    ax3.set_xlabel('Stunde')
    ax3.set_ylabel('Wärmeleistung (kW)')
    ax3.legend()
    ax3.grid(True)
    
    # Plot 4: Energiebilanz
    ax4.plot(hours, power_input, 'r-', label='WP Verbrauch')
    ax4.plot(hours, pv_output, 'g-', label='PV Erzeugung')
    ax4.plot(hours, pv_output - power_input, 'b-', label='Netto')
    ax4.set_xlabel('Stunde')
    ax4.set_ylabel('Elektrische Leistung (kW)')
    ax4.legend()
    ax4.grid(True)
    
    # Erstelle Ausgabeverzeichnis falls nicht vorhanden
    output_dir = Path('output')
    output_dir.mkdir(exist_ok=True)
    
    # Speichere die Grafik
    plt.savefig(output_dir / 'energy_system_simulation.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    # Berechne und gebe Kennzahlen aus
    total_heat = heat_output.sum()
    total_power_consumed = power_input.sum()
    total_pv_generated = pv_output.sum()
    net_power = total_pv_generated - total_power_consumed
    average_cop = total_heat / total_power_consumed if total_power_consumed > 0 else 0
    
    print("\nSimulationsergebnisse:")
    print(f"Gesamtwärmeerzeugung: {total_heat:.1f} kWh")
    print(f"Wärmepumpen-Stromverbrauch: {total_power_consumed:.1f} kWh")
    print(f"PV-Stromerzeugung: {total_pv_generated:.1f} kWh")
    print(f"Netto-Strombilanz: {net_power:.1f} kWh")
    print(f"Durchschnittlicher COP: {average_cop:.2f}")
    print(f"Autarkiegrad: {min(100 * total_pv_generated / total_power_consumed, 100):.1f}%")
    
if __name__ == "__main__":
    run_simple_simulation()

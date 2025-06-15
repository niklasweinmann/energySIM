"""
Systemintegrationstest für energyOS.
Testet alle Komponenten unabhängig und im Zusammenspiel.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, timedelta
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from src.core.building import Building, BuildingProperties, Wall, Window, Roof, Floor
from src.simulation.heat_pump import HeatPump, HeatPumpSpecifications
from src.simulation.pv_system import PVSystem, PVModuleSpecifications, PVArrayConfiguration
from src.simulation.solar_thermal import SolarThermalSystem, SolarThermalSpecifications, StorageSpecifications
from src.data_handlers.weather import WeatherDataHandler
from src.data_handlers.components import ComponentsDatabase
from src.models.energy_optimizer import EnergyFlowOptimizer

class SystemTest:
    """Testklasse für Systemintegration"""
    
    def __init__(self):
        """Initialisiere Testumgebung"""
        self.weather = WeatherDataHandler()
        self.components = ComponentsDatabase()
        self.location = (52.52, 13.4)  # Berlin
        self.simulation_date = datetime(2025, 6, 13)
        
    def setup_building(self):
        """Erstelle und teste Gebäudemodell"""
        print("\nTeste Gebäudemodell...")
        
        # Gebäudeparameter nach EnEV
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
                (0.02, 1.000)     # Ziegel
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
        
        self.building = Building(building_props)
        print("✓ Gebäudemodell erstellt")
        
        # Teste U-Werte
        assert all(u <= 0.24 for u in [self.building.u_values[f'wall_{i}'] 
                                     for i in range(len(walls))])
        assert all(u <= 1.30 for u in [self.building.u_values[f'window_{i}'] 
                                     for i in range(len(windows))])
        assert self.building.u_values['roof'] <= 0.20
        assert self.building.u_values['floor'] <= 0.30
        print("✓ U-Werte validiert")
        
        return self.building
        
    def setup_heat_pump(self):
        """Erstelle und teste Wärmepumpe"""
        print("\nTeste Wärmepumpe...")
        
        hp_specs = HeatPumpSpecifications(
            nominal_heating_power=12.0,  # kW
            cop_rating_points={
                (-7, 35): 2.5,
                (2, 35): 3.5,
                (7, 35): 4.2,
                (20, 35): 5.0
            },
            min_outside_temp=-20,
            max_flow_temp=60
        )
        
        self.heat_pump = HeatPump(hp_specs)
        print("✓ Wärmepumpe erstellt")
        
        # Teste COP-Berechnung
        test_conditions = [(-7, 35), (2, 35), (7, 35), (20, 35)]
        for outside_temp, flow_temp in test_conditions:
            cop = self.heat_pump.calculate_cop(outside_temp, flow_temp)
            assert 1.5 <= cop <= 6.0, f"COP {cop} außerhalb plausibler Grenzen"
        print("✓ COP-Berechnung validiert")
        
        return self.heat_pump
        
    def setup_pv_system(self):
        """Erstelle und teste PV-System"""
        print("\nTeste PV-System...")
        
        module_specs = PVModuleSpecifications(
            peak_power=380,  # Wp
            area=1.95,      # m²
            efficiency_stc=0.195,
            temp_coefficient=-0.35,
            noct=45.0
        )
        
        array_config = PVArrayConfiguration(
            modules_count=20,
            tilt=30,
            azimuth=180,  # Süd
            albedo=0.2
        )
        
        self.pv_system = PVSystem(
            module_specs=module_specs,
            config=array_config,
            location=self.location,
            altitude=34.0  # Berlin
        )
        print("✓ PV-System erstellt")
        
        # Teste Leistungsberechnung
        test_conditions = [
            (1000, 25, 1.5),  # STC-ähnliche Bedingungen
            (200, 15, 3.0),   # Bewölkt
            (0, 10, 2.0)      # Nachts
        ]
        for irradiance, temp, wind in test_conditions:
            dc_power, ac_power = self.pv_system.calculate_power_output(
                solar_irradiance=irradiance,
                ambient_temp=temp,
                wind_speed=wind,
                timestamp=self.simulation_date
            )
            assert dc_power >= 0, "Negative DC-Leistung"
            assert ac_power >= 0, "Negative AC-Leistung"
            assert ac_power <= dc_power, "AC-Leistung größer als DC-Leistung"
        print("✓ PV-Leistungsberechnung validiert")
        
        return self.pv_system
        
    def setup_solar_thermal(self):
        """Erstelle und teste Solarthermie-System"""
        print("\nTeste Solarthermie-System...")
        
        collector_specs = SolarThermalSpecifications(
            area=10.0,
            optical_efficiency=0.75,
            heat_loss_coefficient_a1=1.8,
            heat_loss_coefficient_a2=0.008,
            incident_angle_modifier=0.94
        )
        
        storage_specs = StorageSpecifications(
            volume=0.75,
            height=1.8,
            insulation_thickness=0.1,
            insulation_conductivity=0.04,
            heat_loss_rate=2.5,
            stratification_efficiency=0.85
        )
        
        self.solar_thermal = SolarThermalSystem(
            collector_specs=collector_specs,
            storage_specs=storage_specs,
            location=self.location,
            tilt=45,
            azimuth=180
        )
        print("✓ Solarthermie-System erstellt")
        
        # Teste thermische Leistung
        test_conditions = [
            (1000, 25, 60),  # Hohe Einstrahlung
            (200, 15, 50),   # Bewölkt
            (0, 10, 40)      # Nachts
        ]
        for irradiance, ambient_temp, flow_temp in test_conditions:
            power, temp = self.solar_thermal.calculate_thermal_power(
                solar_irradiance=irradiance,
                ambient_temp=ambient_temp,
                flow_temp=flow_temp
            )
            assert power >= 0, "Negative thermische Leistung"
            assert 0 <= temp <= 150, "Unplausible Kollektortemperatur"
        print("✓ Thermische Leistungsberechnung validiert")
        
        return self.solar_thermal
        
    def run_system_simulation(self):
        """Führe Gesamtsystemsimulation durch"""
        print("\nStarte Gesamtsystemsimulation...")
        
        # Hole Wetterdaten
        weather_data = self.weather.get_historical_data(
            location=self.location,
            start_date=self.simulation_date,
            end_date=self.simulation_date
        )
        print("✓ Wetterdaten geladen")
        
        # Initialisiere Ergebnisarrays
        hours = np.arange(24)
        results = {
            'temperature_room': np.zeros(24),
            'temperature_outside': weather_data['temperature'].values,
            'heating_load': np.zeros(24),
            'heat_pump_thermal': np.zeros(24),
            'heat_pump_electrical': np.zeros(24),
            'heat_pump_cop': np.zeros(24),
            'pv_power': np.zeros(24),
            'solar_thermal_power': np.zeros(24),
            'solar_radiation': weather_data['solar_radiation'].values,
            'wind_speed': weather_data['wind_speed'].values
        }
        
        # Führe Stundensimulation durch
        for hour in hours:
            # 1. Gebäudesimulation
            solar_radiation = {
                'N': results['solar_radiation'][hour] * 0.3,
                'S': results['solar_radiation'][hour] * 1.0,
                'E': results['solar_radiation'][hour] * 0.7,
                'W': results['solar_radiation'][hour] * 0.7
            }
            
            temp, heat_load = self.building.simulate_temperature(
                outside_temp=results['temperature_outside'][hour],
                solar_radiation=solar_radiation,
                time_of_day=hour
            )
            results['temperature_room'][hour] = temp
            results['heating_load'][hour] = heat_load
            
            # 2. Wärmepumpensimulation
            flow_temp = 35.0  # Konstante Vorlauftemperatur für Flächenheizung
            cop = self.heat_pump.calculate_cop(
                results['temperature_outside'][hour], 
                flow_temp
            )
            thermal_power, electrical_power = self.heat_pump.get_power_output(
                outside_temp=results['temperature_outside'][hour],
                flow_temp=flow_temp,
                demand=heat_load
            )
            results['heat_pump_thermal'][hour] = thermal_power
            results['heat_pump_electrical'][hour] = electrical_power
            results['heat_pump_cop'][hour] = cop
            
            # 3. PV-Simulation
            dc_power, ac_power = self.pv_system.calculate_power_output(
                solar_irradiance=results['solar_radiation'][hour],
                ambient_temp=results['temperature_outside'][hour],
                wind_speed=results['wind_speed'][hour],
                timestamp=self.simulation_date.replace(hour=hour)
            )
            results['pv_power'][hour] = ac_power
            
            # 4. Solarthermie-Simulation
            solar_power, _ = self.solar_thermal.calculate_thermal_power(
                solar_irradiance=results['solar_radiation'][hour],
                ambient_temp=results['temperature_outside'][hour],
                flow_temp=60.0  # Warmwasser-Vorlauftemperatur
            )
            results['solar_thermal_power'][hour] = solar_power
        
        print("✓ Stundensimulation abgeschlossen")
        
        # Plotte Ergebnisse
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))
        fig.suptitle('Gesamtsystemsimulation energyOS')
        
        # Plot 1: Temperaturen
        ax1.plot(hours, results['temperature_room'], 'r-', label='Raumtemperatur')
        ax1.plot(hours, results['temperature_outside'], 'b-', label='Außentemperatur')
        ax1.set_xlabel('Stunde')
        ax1.set_ylabel('Temperatur (°C)')
        ax1.legend()
        ax1.grid(True)
        
        # Plot 2: Wärmepumpe
        ax2.plot(hours, results['heating_load'], 'r-', label='Heizlast')
        ax2.plot(hours, results['heat_pump_thermal'], 'b-', label='WP thermisch')
        ax2_twin = ax2.twinx()
        ax2_twin.plot(hours, results['heat_pump_cop'], 'g--', label='COP')
        ax2.set_xlabel('Stunde')
        ax2.set_ylabel('Leistung (kW)')
        ax2_twin.set_ylabel('COP')
        ax2.legend(loc='upper left')
        ax2_twin.legend(loc='upper right')
        ax2.grid(True)
        
        # Plot 3: Stromerzeugung und -verbrauch
        ax3.plot(hours, results['pv_power'], 'y-', label='PV-Leistung')
        ax3.plot(hours, results['heat_pump_electrical'], 'r-', label='WP elektrisch')
        ax3.plot(hours, results['pv_power'] - results['heat_pump_electrical'], 
                'g--', label='Bilanz')
        ax3.set_xlabel('Stunde')
        ax3.set_ylabel('Elektrische Leistung (kW)')
        ax3.legend()
        ax3.grid(True)
        
        # Plot 4: Solar
        ax4.plot(hours, results['solar_radiation'], 'y-', label='Globalstrahlung')
        ax4.plot(hours, results['solar_thermal_power'], 'r-', label='Solarthermie')
        ax4_twin = ax4.twinx()
        ax4_twin.plot(hours, results['wind_speed'], 'b--', label='Windgeschwindigkeit')
        ax4.set_xlabel('Stunde')
        ax4.set_ylabel('Strahlung (W/m²) / Leistung (W)')
        ax4_twin.set_ylabel('Windgeschwindigkeit (m/s)')
        ax4.legend(loc='upper left')
        ax4_twin.legend(loc='upper right')
        ax4.grid(True)
        
        plt.tight_layout()
        plt.savefig('output/system_simulation.png')
        print("✓ Simulationsergebnisse gespeichert in 'output/system_simulation.png'")
        
        # Analysiere Ergebnisse
        analysis = {
            'Mittlere Raumtemperatur': f"{np.mean(results['temperature_room']):.1f} °C",
            'Maximale Raumtemperatur': f"{np.max(results['temperature_room']):.1f} °C",
            'Minimale Raumtemperatur': f"{np.min(results['temperature_room']):.1f} °C",
            'Mittlere Heizlast': f"{np.mean(results['heating_load']):.2f} kW",
            'Maximale Heizlast': f"{np.max(results['heating_load']):.2f} kW",
            'Mittlerer COP': f"{np.mean(results['heat_pump_cop']):.2f}",
            'PV-Energieertrag': f"{np.sum(results['pv_power']):.1f} kWh",
            'WP-Stromverbrauch': f"{np.sum(results['heat_pump_electrical']):.1f} kWh",
            'Eigenverbrauchsquote': f"{np.sum(np.minimum(results['pv_power'], results['heat_pump_electrical'])) / np.sum(results['pv_power']) * 100:.1f} %",
            'Solar thermischer Ertrag': f"{np.sum(results['solar_thermal_power'])/1000:.1f} kWh"
        }
        
        print("\nSimulationsergebnisse:")
        for key, value in analysis.items():
            print(f"{key}: {value}")
        
        return results, analysis

def main():
    """Hauptfunktion für Systemtest"""
    system_test = SystemTest()
    
    try:
        # Komponenten einzeln testen
        system_test.setup_building()
        system_test.setup_heat_pump()
        system_test.setup_pv_system()
        system_test.setup_solar_thermal()
        
        # Gesamtsystem simulieren
        results, analysis = system_test.run_system_simulation()
        
        print("\nSystemtest erfolgreich abgeschlossen!")
        return 0
        
    except Exception as e:
        print(f"\nFehler im Systemtest: {str(e)}")
        return 1

if __name__ == '__main__':
    sys.exit(main())

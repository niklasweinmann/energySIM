"""
Zentrale Normenbibliothek für energyOS.
Enthält Konstanten und Berechnungsmethoden nach deutschen/europäischen Normen.
"""

from dataclasses import dataclass
from typing import Dict, Optional
import math

@dataclass
class GEGRequirements:
    """Anforderungen nach Gebäudeenergiegesetz (GEG 2020/2023)."""
    max_primary_energy_demand: float = 55.0  # kWh/(m²·a) Primärenergiebedarf (verschärft seit 2023)
    max_transmission_heat_loss: float = 0.35  # W/(m²·K) Transmissionswärmeverlust (verschärft)
    min_room_temp: float = 20.0  # °C
    min_summer_heat_protection: float = 0.07  # Sonneneintragskennwert
    renewable_energy_share: float = 0.65  # 65% erneuerbare Energien ab 2024

@dataclass
class DIN4108:
    """Wärmeschutz im Hochbau - DIN 4108."""
    min_insulation_thickness: Dict[str, float] = None  # m
    max_u_values: Dict[str, float] = None
    min_air_exchange_rate: float = 0.5  # 1/h
    
    def __post_init__(self):
        self.max_u_values = {
            'exterior_wall': 0.20,  # W/(m²·K) - verschärft für GEG 2023
            'roof': 0.16,           # W/(m²·K) - verschärft
            'floor': 0.25,          # W/(m²·K) - verschärft  
            'windows': 1.0,         # W/(m²·K) - verschärft (Dreifachverglasung Standard)
            'doors': 1.2            # W/(m²·K) - verschärft
        }
        self.min_insulation_thickness = {
            'exterior_wall': 0.16,  # m - angepasst an neue U-Werte
            'roof': 0.20,           # m - angepasst
            'floor': 0.14           # m - angepasst
        }

@dataclass
class DIN1946:
    """Raumlufttechnik - DIN 1946-6:2019."""
    min_air_flow_rates: Dict[str, float] = None
    max_air_velocity: float = 0.15  # m/s bei 20°C
    min_air_exchange_rate: float = 0.4  # 1/h (reduziert durch bessere Dichtheit)
    max_air_exchange_rate: float = 0.6  # 1/h bei natürlicher Lüftung
    
    def __post_init__(self):
        self.min_air_flow_rates = {
            'living_room': 30,  # m³/h pro Person
            'bedroom': 25,      # m³/h pro Person (erhöht für bessere Schlafqualität)
            'kitchen': 60,      # m³/h (erhöht wegen Kochaktivitäten)
            'bathroom': 40,     # m³/h
            'wc': 20,          # m³/h (separates WC)
            'office': 30       # m³/h pro Person (Homeoffice)
        }

@dataclass
class VDI2067:
    """Wirtschaftlichkeit gebäudetechnischer Anlagen - VDI 2067 Blatt 1 (2022)."""
    calculation_period: int = 20  # Jahre
    interest_rate: float = 0.04  # 4% (aktualisiert 2025 - gestiegenes Zinsniveau)
    maintenance_factor: Dict[str, float] = None
    price_increase_rates: Dict[str, float] = None  # Jährliche Preissteigerungsraten
    
    def __post_init__(self):
        self.maintenance_factor = {
            'heat_pump': 0.02,      # 2% der Investitionskosten (reduziert durch Zuverlässigkeit)
            'pv_system': 0.01,      # 1% (reduziert durch weniger Wartung)
            'solar_thermal': 0.015, # 1.5% (reduziert)
            'storage': 0.008,       # 0.8% (reduziert)
            'ventilation': 0.025,   # 2.5% (neue Kategorie)
            'smart_home': 0.05      # 5% (neue Kategorie für Gebäudeautomation)
        }
        self.price_increase_rates = {
            'electricity': 0.025,   # 2.5% jährlich (aktualisiert 2025)
            'gas': 0.03,           # 3% jährlich (aktualisiert 2025)  
            'district_heating': 0.025, # 2.5% jährlich (aktualisiert 2025)
            'maintenance': 0.02     # 2% jährlich
        }

@dataclass
class VDI4655:
    """Referenzlastprofile von Ein- und Mehrfamilienhäusern für Anwendung der KWK - VDI 4655 (2019)."""
    dhw_profile_types: Dict[str, str] = None
    heating_profile_types: Dict[str, str] = None
    electricity_profile_types: Dict[str, str] = None
    
    def __post_init__(self):
        self.dhw_profile_types = {
            'single_family': 'M-XS',   # Einfamilienhaus
            'multi_family': 'M-S',     # Mehrfamilienhaus
            'apartment': 'M-XS'        # Wohnung
        }
        self.heating_profile_types = {
            'single_family': 'EFH',    # Einfamilienhaus
            'multi_family': 'MFH',     # Mehrfamilienhaus  
            'apartment': 'MFH'         # Wohnung
        }
        self.electricity_profile_types = {
            'household_standard': 'H0',  # Standard Haushalt
            'business': 'G0'            # Gewerbe
        }

@dataclass  
class VDI4645:
    """Planung und Dimensionierung von Wärmepumpenanlagen - VDI 4645 (2018/2021)."""
    min_cop_heating: float = 3.0       # Mindest-COP bei A-7/W35
    min_scop_heating: float = 3.5      # Mindest-SCOP (saisonal)
    max_flow_temp: float = 55.0        # °C Maximaltemperatur  
    min_outside_temp: float = -20.0    # °C Mindest-Außentemperatur
    defrost_factor: float = 0.9        # Faktor für Abtauverluste
    part_load_factors: Dict[str, float] = None
    
    def __post_init__(self):
        self.part_load_factors = {
            'inverter': 0.25,          # Mindest-Teillast Inverter-WP
            'on_off': 0.5             # Mindest-Teillast On/Off-WP  
        }

@dataclass
class VDI6002:
    """Solare Trinkwassererwärmung - VDI 6002 Blatt 1 (2021)."""
    min_solar_coverage: float = 0.60  # 60% solarer Deckungsgrad
    max_stagnation_temp: float = 120.0  # °C (reduziert für moderne Kollektoren)
    min_storage_volume: float = 50.0  # L/m² Kollektorfläche
    max_storage_volume: float = 100.0  # L/m² Kollektorfläche (neue Obergrenze)
    min_collector_tilt: float = 20.0  # Grad Mindestneigung
    max_collector_tilt: float = 70.0  # Grad Maximalneigung

@dataclass
class DIN15316:
    """Heizungsanlagen in Gebäuden - DIN EN 15316 (2017)."""
    distribution_losses: Dict[str, float] = None
    storage_losses: Dict[str, float] = None
    generation_losses: Dict[str, float] = None  # Neue Kategorie
    
    def __post_init__(self):
        self.distribution_losses = {
            'space_heating': 0.08,  # 8% Verteilungsverluste (reduziert durch bessere Dämmung)
            'dhw': 0.12,           # 12% (reduziert)
            'radiant_heating': 0.05, # 5% Flächenheizung
            'radiator_heating': 0.10 # 10% Radiatorheizung
        }
        self.storage_losses = {
            'buffer': 0.12,        # kWh/(m³·d) (reduziert durch bessere Dämmung)
            'dhw': 0.15,          # kWh/(m³·d) 
            'combi_storage': 0.13  # kWh/(m³·d) Kombispeicher
        }
        self.generation_losses = {
            'heat_pump': 0.02,     # 2% Erzeugungsverluste
            'gas_boiler': 0.05,    # 5% 
            'solar_thermal': 0.01  # 1%
        }

@dataclass
class DVGW_W551:
    """Trinkwassererwärmung und Trinkwasserleitungsanlagen - DVGW W551 (2019)."""
    min_dhw_temp: float = 60.0        # °C Mindesttemperatur im Speicher
    min_circulation_temp: float = 55.0 # °C Mindesttemperatur Zirkulation
    max_legionella_temp: float = 70.0  # °C Temperatur gegen Legionellen
    thermal_disinfection_temp: float = 70.0  # °C thermische Desinfektion
    thermal_disinfection_duration: float = 10.0  # Minuten bei 70°C
    max_stagnation_time: float = 3.0   # Sekunden bis Warmwasser (72h Regel)

@dataclass
class DIN4753:
    """Heizungsspeicher - DIN 4753-1:2018."""
    max_operating_temp: float = 95.0  # °C
    max_storage_pressure: float = 3.0  # bar
    min_insulation_thickness: float = 0.05  # m
    heat_loss_classification: Dict[str, float] = None  # W/K nach Speichergröße
    
    def __post_init__(self):
        self.heat_loss_classification = {
            'small': 1.5,   # ≤ 300L: max 1.5 W/K
            'medium': 2.0,  # 301-500L: max 2.0 W/K
            'large': 3.0    # > 500L: max 3.0 W/K
        }

@dataclass
class DIN12831:
    """Heizungsanlagen in Gebäuden - DIN EN 12831-1:2017."""
    design_temperatures: Dict[str, float] = None  # °C Norm-Innentemperaturen
    intermittent_heating_factor: float = 1.24  # Aufheizzuschlag
    thermal_bridge_supplement: float = 0.10  # Wärmebrücken-Zuschlag vereinfacht
    
    def __post_init__(self):
        self.design_temperatures = {
            'living_room': 20.0,
            'bedroom': 20.0,
            'bathroom': 24.0,
            'kitchen': 20.0,
            'hallway': 15.0,
            'office': 20.0
        }

@dataclass 
class DIN18599:
    """Energetische Bewertung von Gebäuden - DIN V 18599 (2018/2023)."""
    primary_energy_factors: Dict[str, float] = None
    co2_emission_factors: Dict[str, float] = None  # kg CO2/kWh
    
    def __post_init__(self):
        # Aktualisierte Faktoren nach GEG 2023
        self.primary_energy_factors = {
            'electricity_grid': 1.7,      # Aktualisiert nach GEG 2023 (war 1.8)
            'natural_gas': 1.1,
            'oil': 1.1,
            'district_heating_fossil': 0.7,
            'district_heating_renewable': 0.1,
            'biomass': 0.2,
            'solar_thermal': 0.0,
            'geothermal': 0.0
        }
        self.co2_emission_factors = {
            'electricity_grid': 0.388,  # Aktualisiert auf Wert 2023 laut UBA
            'natural_gas': 0.201,
            'oil': 0.266,
            'district_heating': 0.153,
            'biomass': 0.025
        }

@dataclass
class DIN748:
    """Kältemittel-Rohrleitungen - DIN EN 378:2017."""
    max_refrigerant_velocity: Dict[str, float] = None  # m/s
    min_pipe_insulation: float = 0.019  # m (19mm Standard)
    safety_factors: Dict[str, float] = None
    
    def __post_init__(self):
        self.max_refrigerant_velocity = {
            'suction_line': 20.0,
            'liquid_line': 3.5,
            'hot_gas_line': 25.0
        }
        self.safety_factors = {
            'A1_refrigerants': 1.0,  # R32, R410A etc.
            'A2L_refrigerants': 1.2, # R454B, R290 etc.
            'A3_refrigerants': 1.5   # R290 (Propan)
        }

@dataclass
class DIN18710:
    """Normen-Klimadaten - DIN 4710:2003."""
    design_temperatures: Dict[str, Dict[str, float]] = None  # °C nach Klimazone
    heating_days_threshold: float = 15.0  # °C Heizgrenztemperatur
    
    def __post_init__(self):
        # Deutsche Klimazonen (vereinfacht)
        self.design_temperatures = {
            'zone_1': {'winter': -10.0, 'summer': 32.0},  # Norddeutschland
            'zone_2': {'winter': -12.0, 'summer': 32.0},  # Mitteldeutschland
            'zone_3': {'winter': -14.0, 'summer': 32.0},  # Süddeutschland
            'zone_4': {'winter': -16.0, 'summer': 32.0}   # Alpenvorland
        }

@dataclass
class DIN60364:
    """Errichten von Niederspannungsanlagen - DIN VDE 0100:2018."""
    max_string_voltage: float = 1500.0  # V DC für PV-Anlagen
    min_insulation_resistance: float = 0.5  # MΩ/kW
    max_earth_fault_current: float = 30.0  # mA
    overcurrent_protection_factor: float = 1.25
    
@dataclass
class DIN62446:
    """Photovoltaik-Anlagen - DIN EN 62446-1:2016."""
    max_power_tolerance: float = 0.05  # ±5% Leistungstoleranz
    min_irradiance_measurement: float = 700.0  # W/m² für Leistungsmessung
    max_temperature_coefficient: float = -0.004  # %/K
    insulation_test_voltage: float = 1000.0  # V
    
@dataclass
class F_GAS_VO:
    """F-Gase-Verordnung EU 517/2014."""
    gwp_limits: Dict[str, float] = None  # GWP-Grenzwerte
    phase_out_schedule: Dict[int, float] = None  # Ausstiegszeitplan
    
    def __post_init__(self):
        self.gwp_limits = {
            'split_ac_new': 750,       # ab 2025
            'heat_pump_new': 150,      # ab 2027 (beschlossene Regelung)
            'chiller_new': 675         # ab 2024
        }
        self.phase_out_schedule = {
            2024: 0.79,  # 79% des Baseline-Verbrauchs
            2027: 0.50,  # 50% (aktualisiert)
            2030: 0.27,  # 27% (aktualisiert)
            2034: 0.15   # 15%
        }

@dataclass
class VDI4640:
    """Thermische Nutzung des Untergrunds - VDI 4640 (2019)."""
    min_probe_spacing: float = 6.0  # m Mindestabstand Erdsonden
    max_extraction_power: float = 50.0  # W/m spezifische Entzugsleistung
    undisturbed_ground_temp: float = 10.0  # °C (Deutschland, 10m Tiefe)
    
@dataclass
class VDI3805:
    """Produktdatenaustausch in der TGA - VDI 3805:2020."""
    energy_efficiency_classes: Dict[str, str] = None
    
    def __post_init__(self):
        self.energy_efficiency_classes = {
            'A+++': 'sehr_hoch',
            'A++': 'hoch', 
            'A+': 'gut',
            'A': 'standard'
        }

@dataclass
class ASR_A35:
    """Raumtemperatur - ASR A3.5:2010."""
    min_workplace_temp: float = 20.0  # °C
    max_workplace_temp: float = 26.0  # °C
    optimal_humidity_range: tuple = (40.0, 70.0)  # % rel. Feuchte

@dataclass
class DIN_SPEC_4701:
    """Gebäudeautomation - DIN SPEC 4701-10/11:2018."""
    efficiency_factors: Dict[str, float] = None  # Effizienzfaktoren Regelung
    
    def __post_init__(self):
        self.efficiency_factors = {
            'room_control': 0.95,      # Raumregelung
            'weather_compensation': 0.92, # Witterungsführung
            'optimized_start': 0.94,   # Optimaler Start
            'presence_control': 0.88   # Präsenzsteuerung
        }

class NormCalculator:
    """Berechnungsmethoden nach Normen."""
    
    def __init__(self):
        self.geg = GEGRequirements()
        self.din4108 = DIN4108()
        self.din1946 = DIN1946()
        self.vdi2067 = VDI2067()
        self.vdi4655 = VDI4655()
        self.vdi4645 = VDI4645()
        self.vdi6002 = VDI6002()
        self.din15316 = DIN15316()
        self.dvgw_w551 = DVGW_W551()
        # Neue Normen
        self.din4753 = DIN4753()
        self.din12831 = DIN12831()
        self.din18599 = DIN18599()
        self.din748 = DIN748()
        self.din18710 = DIN18710()
        self.din60364 = DIN60364()
        self.din62446 = DIN62446()
        self.f_gas_vo = F_GAS_VO()
        self.vdi4640 = VDI4640()
        self.vdi3805 = VDI3805()
        self.asr_a35 = ASR_A35()
        self.din_spec_4701 = DIN_SPEC_4701()
        self.din4753 = DIN4753()
        self.din12831 = DIN12831()
        self.din18599 = DIN18599()
        self.din748 = DIN748()
        self.din18710 = DIN18710()
        self.din60364 = DIN60364()
        self.din62446 = DIN62446()
        self.f_gas_vo = F_GAS_VO()
        self.vdi4640 = VDI4640()
        self.vdi3805 = VDI3805()
        self.asr_a35 = ASR_A35()
        self.din_spec_4701 = DIN_SPEC_4701()
    
    def calculate_u_value(self,
                        layer_thicknesses: list[float],
                        layer_conductivities: list[float],
                        rsi: float = 0.13,
                        rse: float = 0.04) -> float:
        """
        Berechnet U-Wert nach DIN EN ISO 6946.
        
        Args:
            layer_thicknesses: Schichtdicken in m
            layer_conductivities: Wärmeleitfähigkeiten in W/(m·K)
            rsi: Innerer Wärmeübergangswiderstand in (m²·K)/W
            rse: Äußerer Wärmeübergangswiderstand in (m²·K)/W
        
        Returns:
            U-Wert in W/(m²·K)
        """
        r_total = rsi + rse
        for d, lambda_ in zip(layer_thicknesses, layer_conductivities):
            r_total += d / lambda_
        return 1 / r_total
    
    def calculate_heat_load(self,
                         volume: float,
                         u_values: Dict[str, float],
                         areas: Dict[str, float],
                         air_exchange_rate: float,
                         inside_temp: float,
                         outside_temp: float,
                         thermal_bridges: float = 0.10) -> float:
        """
        Berechnet Heizlast nach DIN EN 12831-1:2017.
        
        Args:
            volume: Gebäudevolumen in m³
            u_values: U-Werte der Bauteile in W/(m²·K)
            areas: Flächen der Bauteile in m²
            air_exchange_rate: Luftwechselrate in 1/h
            inside_temp: Innentemperatur in °C
            outside_temp: Außentemperatur in °C
            thermal_bridges: Wärmebrückenzuschlag in W/(m²·K)
            
        Returns:
            Heizlast in kW
        """
        temp_diff = inside_temp - outside_temp
        
        # Transmissionswärmeverluste mit Wärmebrücken
        trans_loss = 0
        total_area = 0
        for component, u_value in u_values.items():
            if component in areas:
                area = areas[component]
                trans_loss += u_value * area * temp_diff
                total_area += area
        
        # Wärmebrückenzuschlag nach DIN 4108 Beiblatt 2
        thermal_bridge_loss = thermal_bridges * total_area * temp_diff
        
        # Lüftungswärmeverluste (0.34 = spez. Wärmekapazität Luft)
        vent_loss = 0.34 * air_exchange_rate * volume * temp_diff
        
        # Aufheizzuschlag nach DIN EN 12831 (korrigiert)
        # 10% ist zu niedrig, korrekt nach DIN 12831: 24% (1.24)
        intermittent_heating_factor = 1.24  # 24% Zuschlag nach DIN 12831
        
        total_loss = (trans_loss + thermal_bridge_loss + vent_loss) * intermittent_heating_factor / 1000
        return max(0, total_loss)  # kW
    
    def calculate_solar_gains(self,
                           window_areas: Dict[str, float],
                           g_values: Dict[str, float],
                           radiation: Dict[str, float],
                           shading_factors: Dict[str, float]) -> float:
        """
        Berechnet solare Wärmegewinne nach DIN EN ISO 13790.
        
        Args:
            window_areas: Fensterflächen nach Orientierung in m²
            g_values: g-Werte der Fenster
            radiation: Solare Einstrahlung nach Orientierung in W/m²
            shading_factors: Verschattungsfaktoren
            
        Returns:
            Solare Wärmegewinne in kW
        """
        solar_gains = 0
        for orientation in window_areas.keys():
            solar_gains += (window_areas[orientation] *
                          g_values[orientation] *
                          radiation[orientation] *
                          shading_factors[orientation])
        return solar_gains / 1000  # Umrechnung in kW
    
    def calculate_primary_energy_demand(self,
                                    final_energy: float,
                                    energy_source: str) -> float:
        """
        Berechnet Primärenergiebedarf nach DIN V 18599-1 (2018/2023).
        
        Args:
            final_energy: Endenergiebedarf in kWh
            energy_source: Energieträger
            
        Returns:
            Primärenergiebedarf in kWh
        """
        # Aktualisierte Primärenergiefaktoren nach DIN V 18599-1:2018 und GEG 2023
        primary_energy_factors = {
            'electricity': 1.8,      # Deutschland-Mix (leicht gesunken durch EE-Ausbau)
            'electricity_green': 0.0, # Grünstrom/Eigenverbrauch PV
            'natural_gas': 1.1,
            'oil': 1.1,
            'wood_pellets': 0.2,
            'district_heating': 0.7,  # Abhängig von lokaler Erzeugung
            'heat_pump_electricity': 1.8,  # Wärmepumpe mit Netzstrom
            'biogas': 0.5,           # Neu: Biogas
            'hydrogen': 2.5,         # Neu: Wasserstoff (grün)
            'ambient_heat': 0.0      # Umweltwärme (Wärmepumpe)
        }
        return final_energy * primary_energy_factors.get(energy_source, 1.0)
    
    def calculate_renewable_energy_share(self,
                                       renewable_energy: float,
                                       total_energy: float) -> float:
        """
        Berechnet den Anteil erneuerbarer Energien nach GEG.
        
        Args:
            renewable_energy: Erneuerbare Energie in kWh
            total_energy: Gesamtenergiebedarf in kWh
            
        Returns:
            Anteil erneuerbarer Energien (0-1)
        """
        if total_energy <= 0:
            return 0.0
        return min(renewable_energy / total_energy, 1.0)
    
    def calculate_seasonal_cop(self,
                             monthly_cops: list[float],
                             monthly_heating_demands: list[float]) -> float:
        """
        Berechnet die saisonale Leistungszahl (SCOP) nach VDI 4645.
        
        Args:
            monthly_cops: Monatliche COP-Werte
            monthly_heating_demands: Monatliche Heizbedarfe in kWh
            
        Returns:
            Saisonale Leistungszahl (SCOP)
        """
        if len(monthly_cops) != len(monthly_heating_demands):
            raise ValueError("Anzahl COP-Werte und Heizbedarfe müssen übereinstimmen")
        
        total_heating = sum(monthly_heating_demands)
        if total_heating <= 0:
            return 0.0
            
        weighted_cop = sum(cop * demand for cop, demand in zip(monthly_cops, monthly_heating_demands))
        return weighted_cop / total_heating
    
    def calculate_co2_emissions(self,
                              final_energy: float,
                              energy_source: str) -> float:
        """
        Berechnet CO2-Emissionen nach aktuellen Emissionsfaktoren.
        
        Args:
            final_energy: Endenergiebedarf in kWh
            energy_source: Energieträger
            
        Returns:
            CO2-Emissionen in kg
        """
        # CO2-Emissionsfaktoren in kg/kWh (Stand 2023)
        emission_factors = {
            'electricity': 0.434,     # Deutschland-Mix 2023
            'electricity_green': 0.0, # Grünstrom
            'natural_gas': 0.201,
            'oil': 0.266,
            'wood_pellets': 0.025,
            'district_heating': 0.153,
            'biogas': 0.110,
            'hydrogen': 0.0,          # Grüner Wasserstoff
            'ambient_heat': 0.0       # Umweltwärme
        }
        return final_energy * emission_factors.get(energy_source, 0.5)  # Default: mittlerer Wert
    
    def calculate_heating_load_din12831(self,
                                      design_temp_inside: float,
                                      design_temp_outside: float,
                                      u_values: Dict[str, float],
                                      areas: Dict[str, float],
                                      volume: float,
                                      air_exchange_rate: float,
                                      room_type: str = 'living_room') -> float:
        """
        Berechnet Heizlast nach DIN EN 12831-1:2017 (genauer als die bestehende Methode).
        
        Args:
            design_temp_inside: Norm-Innentemperatur nach DIN 12831
            design_temp_outside: Norm-Außentemperatur nach DIN 4710  
            u_values: U-Werte der Bauteile
            areas: Flächen der Bauteile
            volume: Raumvolumen
            air_exchange_rate: Luftwechselrate
            room_type: Raumtyp für Norm-Innentemperatur
            
        Returns:
            Heizlast in kW
        """
        # Verwende Norm-Innentemperatur falls nicht angegeben
        if room_type in self.din12831.design_temperatures:
            design_temp_inside = self.din12831.design_temperatures[room_type]
        
        # Basis-Heizlast
        base_load = self.calculate_heat_load(
            volume, u_values, areas, air_exchange_rate,
            design_temp_inside, design_temp_outside,
            self.din12831.thermal_bridge_supplement
        )
        
        # Aufheizzuschlag nach DIN 12831
        return base_load * self.din12831.intermittent_heating_factor
    
    def calculate_storage_losses_din4753(self,
                                       storage_volume: float,  # L
                                       storage_temp: float,    # °C
                                       ambient_temp: float = 20.0) -> float:
        """
        Berechnet Speicherverluste nach DIN 4753-1.
        
        Args:
            storage_volume: Speichervolumen in L
            storage_temp: Speichertemperatur in °C
            ambient_temp: Umgebungstemperatur in °C
            
        Returns:
            Wärmeverluste in W
        """
        # Klassifizierung nach Speichergröße
        if storage_volume <= 300:
            max_loss_coefficient = self.din4753.heat_loss_classification['small']
        elif storage_volume <= 500:
            max_loss_coefficient = self.din4753.heat_loss_classification['medium']
        else:
            max_loss_coefficient = self.din4753.heat_loss_classification['large']
        
        return max_loss_coefficient * (storage_temp - ambient_temp)
    
    def calculate_pv_safety_requirements_din60364(self,
                                                 pv_power: float,  # kW
                                                 string_voltage: float,  # V
                                                 ambient_temp: float = 25.0) -> Dict[str, float]:
        """
        Berechnet Sicherheitsanforderungen für PV-Anlagen nach DIN VDE 0100.
        
        Args:
            pv_power: PV-Leistung in kW
            string_voltage: String-Spannung in V
            ambient_temp: Umgebungstemperatur in °C
            
        Returns:
            Dict mit Sicherheitsparametern
        """
        results = {}
        
        # Überstromschutz
        results['overcurrent_protection'] = pv_power * 1000 / string_voltage * self.din60364.overcurrent_protection_factor
        
        # Isolationswiderstand
        results['min_insulation_resistance'] = self.din60364.min_insulation_resistance * pv_power
        
        # Maximale String-Spannung prüfen
        results['string_voltage_ok'] = string_voltage <= self.din60364.max_string_voltage
        
        return results
    
    def calculate_refrigerant_requirements_fgas(self,
                                              refrigerant_type: str,
                                              gwp_value: float,
                                              system_type: str) -> Dict[str, bool]:
        """
        Prüft F-Gase-Verordnung Anforderungen.
        
        Args:
            refrigerant_type: Kältemittel-Typ (R32, R290, etc.)
            gwp_value: GWP-Wert des Kältemittels
            system_type: Anlagentyp
            
        Returns:
            Dict mit Compliance-Status
        """
        results = {}
        
        if system_type in self.f_gas_vo.gwp_limits:
            results['gwp_compliant'] = gwp_value <= self.f_gas_vo.gwp_limits[system_type]
        else:
            results['gwp_compliant'] = True
        
        # Natürliche Kältemittel bevorzugt
        natural_refrigerants = ['R290', 'R717', 'R744']
        results['natural_refrigerant'] = refrigerant_type in natural_refrigerants
        
        return results
    
    def calculate_ground_source_capacity_vdi4640(self,
                                                ground_type: str,
                                                probe_length: float,  # m
                                                number_of_probes: int) -> float:
        """
        Berechnet Erdwärme-Kapazität nach VDI 4640.
        
        Args:
            ground_type: Bodentyp
            probe_length: Sondenlänge in m
            number_of_probes: Anzahl Sonden
            
        Returns:
            Entzugsleistung in kW
        """
        # Spezifische Entzugsleistungen nach Bodentyp (W/m)
        extraction_powers = {
            'clay_wet': 65,
            'clay_dry': 35,
            'sand_wet': 80,
            'sand_dry': 40,
            'gravel_wet': 100,
            'gravel_dry': 60,
            'bedrock_hard': 70,
            'bedrock_soft': 45
        }
        
        specific_power = extraction_powers.get(ground_type, 50)  # Default
        return specific_power * probe_length * number_of_probes / 1000  # kW
    
    def calculate_building_automation_efficiency_din4701(self,
                                                       control_systems: list[str]) -> float:
        """
        Berechnet Effizienzfaktor für Gebäudeautomation nach DIN SPEC 4701.
        
        Args:
            control_systems: Liste der Regelsysteme
            
        Returns:
            Gesamteffizienzfaktor
        """
        total_efficiency = 1.0
        
        for system in control_systems:
            if system in self.din_spec_4701.efficiency_factors:
                total_efficiency *= self.din_spec_4701.efficiency_factors[system]
        
        return total_efficiency
    
    def validate_building_compliance_geg(self,
                                       building_area: float,  # m²
                                       primary_energy_demand: float,  # kWh/(m²·a)
                                       transmission_loss: float,  # W/(m²·K)
                                       renewable_share: float) -> Dict[str, bool]:
        """
        Überprüft GEG-Konformität eines Gebäudes.
        
        Args:
            building_area: Gebäudefläche in m²
            primary_energy_demand: Primärenergiebedarf in kWh/(m²·a)
            transmission_loss: Transmissionswärmeverlust in W/(m²·K)
            renewable_share: Anteil erneuerbarer Energien (0-1)
            
        Returns:
            Dict mit Compliance-Status
        """
        results = {}
        
        # GEG 2023 Anforderungen
        results['primary_energy_ok'] = primary_energy_demand <= self.geg.max_primary_energy_demand
        results['transmission_loss_ok'] = transmission_loss <= self.geg.max_transmission_heat_loss
        results['renewable_share_ok'] = renewable_share >= self.geg.renewable_energy_share
        
        results['geg_compliant'] = all(results.values())
        
        return results

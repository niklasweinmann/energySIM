"""
Erweiterte 3D-Gebäudeoperationen für energyOS
Zusätzliche Funktionen für komplexere Gebäudebearbeitung
"""

import numpy as np
from typing import Dict, List, Tuple, Optional
from src.core.building import Building, BuildingProperties, Wall, Window, Roof, Floor

class Building3DEnhanced:
    """Erweiterte 3D-Gebäudefunktionalität"""
    
    def __init__(self):
        self.building_history = []  # Für Undo/Redo
        self.current_state = 0
        
    def add_solar_panels(self, building_data: Dict, panel_config: Dict) -> Dict:
        """Fügt Solarpanels auf dem Dach hinzu"""
        
        roof_data = building_data['geometry']['roof']
        roof_area = roof_data['area']
        roof_tilt = roof_data['tilt']
        
        # Berechne Panel-Layout
        panel_width = panel_config.get('width', 1.65)  # Standard-Panel 1.65m
        panel_height = panel_config.get('height', 1.0)  # Standard-Panel 1.0m
        panel_power = panel_config.get('power', 300)    # 300W Standard
        
        # Verfügbare Dachfläche (80% für Montage und Wartung)
        usable_area = roof_area * 0.8
        panel_area = panel_width * panel_height
        max_panels = int(usable_area / panel_area)
        
        # Panel-Positionen berechnen
        panels_per_row = int(roof_data['width'] / panel_width)
        panel_rows = max_panels // panels_per_row
        
        panels = []
        for row in range(panel_rows):
            for col in range(panels_per_row):
                panels.append({
                    'id': f'panel_{row}_{col}',
                    'position': {
                        'x': col * panel_width + panel_width/2,
                        'y': roof_data['depth'] - row * panel_height - panel_height/2,
                        'z': 0.05  # Leicht über dem Dach
                    },
                    'dimensions': {
                        'width': panel_width,
                        'height': panel_height,
                        'thickness': 0.04
                    },
                    'power': panel_power,
                    'tilt': roof_tilt,
                    'orientation': 'S'  # Annahme: Süd-orientiertes Dach
                })
        
        # Füge zu Gebäudedaten hinzu
        building_data['geometry']['solar_panels'] = panels
        building_data['energy_data']['pv_installed_power'] = len(panels) * panel_power / 1000  # kWp
        
        return building_data
    
    def optimize_window_placement(self, building_data: Dict) -> Dict:
        """Optimiert Fensterplatzierung für maximale Energieeffizienz"""
        
        walls = building_data['geometry']['walls']
        optimized_windows = []
        
        for wall in walls:
            orientation = wall['orientation']
            wall_area = wall['area']
            
            # Optimale Fensterfläche je nach Orientierung
            optimal_ratios = {
                'S': 0.4,   # Süden: 40% Fensteranteil
                'E': 0.25,  # Osten: 25%
                'W': 0.25,  # Westen: 25%
                'N': 0.15   # Norden: 15%
            }
            
            target_window_area = wall_area * optimal_ratios.get(orientation, 0.2)
            
            # Standardfenstergröße
            window_width = 1.5
            window_height = 1.4
            window_area = window_width * window_height
            
            # Anzahl Fenster
            num_windows = max(1, int(target_window_area / window_area))
            
            for i in range(num_windows):
                window_id = f"window_{orientation}_{i}"
                
                # Position entlang der Wand
                spacing = wall['width'] / (num_windows + 1)
                x_offset = spacing * (i + 1) - wall['width'] / 2
                
                optimized_windows.append({
                    'id': window_id,
                    'area': window_area,
                    'orientation': orientation,
                    'u_value': 0.8,  # Moderne Dreifachverglasung
                    'g_value': 0.6,
                    'position': {
                        'x': wall['position']['x'] + x_offset,
                        'y': 1.2,  # Fensterbank-Höhe
                        'z': wall['position']['z'],
                        'rotation': wall['position']['rotation']
                    },
                    'width': window_width,
                    'height': window_height
                })
        
        building_data['geometry']['windows'] = optimized_windows
        return building_data
    
    def calculate_thermal_bridges(self, building_data: Dict) -> Dict:
        """Berechnet Wärmebrücken-Verluste"""
        
        geometry = building_data['geometry']
        
        # Wärmebrücken-Längen
        corner_length = geometry['dimensions']['height'] * 4  # Ecken
        roof_perimeter = 2 * (geometry['dimensions']['width'] + geometry['dimensions']['depth'])
        floor_perimeter = roof_perimeter
        window_perimeter = sum(2 * (w['width'] + w['height']) for w in geometry['windows'])
        
        # Wärmebrücken-Koeffizienten (W/mK)
        psi_values = {
            'corner': 0.05,
            'roof_wall': 0.15,
            'floor_wall': 0.20,
            'window': 0.10
        }
        
        # Wärmebrücken-Verluste
        thermal_bridge_losses = (
            corner_length * psi_values['corner'] +
            roof_perimeter * psi_values['roof_wall'] +
            floor_perimeter * psi_values['floor_wall'] +
            window_perimeter * psi_values['window']
        )
        
        building_data['energy_data']['thermal_bridge_coefficient'] = thermal_bridge_losses
        
        return building_data
    
    def analyze_shading(self, building_data: Dict, environment: Dict) -> Dict:
        """Analysiert Verschattung durch Umgebung"""
        
        # Vereinfachte Verschattungsanalyse
        shading_factors = {}
        
        # Umgebungsobjekte (Bäume, Nachbargebäude, etc.)
        obstacles = environment.get('obstacles', [])
        
        for window in building_data['geometry']['windows']:
            orientation = window['orientation']
            
            # Standard-Verschattungsfaktor
            base_shading = 0.9
            
            # Reduziere Verschattung basierend auf Hindernissen
            for obstacle in obstacles:
                if obstacle['type'] == 'building':
                    # Vereinfachte Verschattungsberechnung
                    distance = obstacle.get('distance', 20)  # m
                    height = obstacle.get('height', 10)      # m
                    
                    # Verschattungswinkel
                    shading_angle = np.arctan(height / distance)
                    
                    if shading_angle > np.radians(30):  # Signifikante Verschattung
                        if orientation in ['S', 'SE', 'SW']:
                            base_shading *= 0.7
                        elif orientation in ['E', 'W']:
                            base_shading *= 0.8
            
            shading_factors[window['id']] = base_shading
            window['shading_factor'] = base_shading
        
        building_data['analysis'] = building_data.get('analysis', {})
        building_data['analysis']['shading_factors'] = shading_factors
        
        return building_data
    
    def generate_energy_certificate(self, building_data: Dict, simulation_results: Dict) -> Dict:
        """Generiert einen Energieausweis"""
        
        # Gebäudedaten
        floor_area = building_data['geometry']['floor']['area']
        building_volume = building_data['properties']['building_volume']
        
        # Energiekennwerte aus Simulation
        annual_heat_demand = simulation_results.get('heat_demand_kWh', 0) * 52  # Woche -> Jahr
        annual_electricity = simulation_results.get('electricity_consumption_kWh', 0) * 52
        
        # Spezifische Kennwerte
        specific_heat_demand = annual_heat_demand / floor_area  # kWh/(m²a)
        specific_electricity = annual_electricity / floor_area   # kWh/(m²a)
        
        # Energieeffizienzklasse bestimmen
        efficiency_classes = [
            ('A+', 30),   # < 30 kWh/(m²a)
            ('A', 50),    # < 50 kWh/(m²a)
            ('B', 75),    # < 75 kWh/(m²a)
            ('C', 100),   # < 100 kWh/(m²a)
            ('D', 130),   # < 130 kWh/(m²a)
            ('E', 160),   # < 160 kWh/(m²a)
            ('F', 200),   # < 200 kWh/(m²a)
            ('G', 250),   # < 250 kWh/(m²a)
            ('H', float('inf'))
        ]
        
        efficiency_class = 'H'
        for class_name, threshold in efficiency_classes:
            if specific_heat_demand < threshold:
                efficiency_class = class_name
                break
        
        # CO2-Emissionen (vereinfacht)
        co2_factor_heat = 0.25  # kg CO2/kWh (Wärmepumpe mit Strommix)
        co2_factor_electricity = 0.4  # kg CO2/kWh (deutscher Strommix)
        
        annual_co2 = (annual_heat_demand * co2_factor_heat + 
                     annual_electricity * co2_factor_electricity)
        
        certificate = {
            'building_id': building_data.get('id', 'unknown'),
            'issue_date': '2025-06-16',
            'valid_until': '2035-06-16',
            'floor_area_m2': floor_area,
            'building_volume_m3': building_volume,
            'energy_demand': {
                'heating_kwh_per_m2_year': specific_heat_demand,
                'electricity_kwh_per_m2_year': specific_electricity,
                'total_kwh_per_m2_year': specific_heat_demand + specific_electricity
            },
            'efficiency_class': efficiency_class,
            'co2_emissions_kg_per_year': annual_co2,
            'renewable_energy_share': simulation_results.get('renewable_share', 0),
            'recommendations': self._generate_recommendations(building_data, specific_heat_demand)
        }
        
        return certificate
    
    def _generate_recommendations(self, building_data: Dict, heat_demand: float) -> List[str]:
        """Generiert Verbesserungsempfehlungen"""
        
        recommendations = []
        
        # Wärmedämmung
        if heat_demand > 100:
            recommendations.append("Verbesserung der Wärmedämmung von Wänden und Dach")
        
        # Fenster
        windows = building_data['geometry']['windows']
        avg_u_value = np.mean([w.get('u_value', 1.4) for w in windows])
        if avg_u_value > 1.0:
            recommendations.append("Austausch der Fenster gegen Dreifachverglasung")
        
        # Heizsystem
        cop = building_data.get('energy_data', {}).get('cop_average', 3.0)
        if cop < 3.5:
            recommendations.append("Optimierung oder Austausch des Heizsystems")
        
        # Erneuerbare Energien
        pv_power = building_data.get('energy_data', {}).get('pv_installed_power', 0)
        if pv_power == 0:
            recommendations.append("Installation einer Photovoltaikanlage")
        
        # Lüftung
        infiltration = building_data.get('energy_data', {}).get('infiltration_rate', 0.6)
        if infiltration > 0.4:
            recommendations.append("Verbesserung der Luftdichtheit")
        
        return recommendations

class BuildingValidator:
    """Validiert Gebäudedaten nach deutschen Normen"""
    
    @staticmethod
    def validate_u_values(building_data: Dict) -> Dict[str, List[str]]:
        """Validiert U-Werte nach GEG 2023"""
        
        errors = []
        warnings = []
        
        # GEG-Grenzwerte
        limits = {
            'wall': 0.24,      # W/(m²K)
            'roof': 0.20,      # W/(m²K)
            'floor': 0.30,     # W/(m²K)
            'window': 1.30     # W/(m²K)
        }
        
        # Prüfe Wände
        for wall in building_data['geometry']['walls']:
            u_value = wall.get('u_value', 999)
            if u_value > limits['wall']:
                errors.append(f"Wand {wall['id']}: U-Wert {u_value:.3f} überschreitet GEG-Grenzwert {limits['wall']}")
        
        # Prüfe Fenster
        for window in building_data['geometry']['windows']:
            u_value = window.get('u_value', 999)
            if u_value > limits['window']:
                errors.append(f"Fenster {window['id']}: U-Wert {u_value:.3f} überschreitet GEG-Grenzwert {limits['window']}")
        
        # Prüfe Dach
        roof_u_value = building_data['geometry']['roof'].get('u_value', 999)
        if roof_u_value > limits['roof']:
            errors.append(f"Dach: U-Wert {roof_u_value:.3f} überschreitet GEG-Grenzwert {limits['roof']}")
        
        return {
            'errors': errors,
            'warnings': warnings,
            'compliant': len(errors) == 0
        }
    
    @staticmethod
    def validate_geometry(building_data: Dict) -> Dict[str, List[str]]:
        """Validiert Gebäudegeometrie"""
        
        errors = []
        warnings = []
        
        dimensions = building_data['geometry']['dimensions']
        
        # Mindestabmessungen
        if dimensions['width'] < 3.0:
            errors.append("Gebäudebreite unter 3m ist unüblich")
        if dimensions['depth'] < 3.0:
            errors.append("Gebäudetiefe unter 3m ist unüblich")
        if dimensions['height'] < 2.4:
            errors.append("Raumhöhe unter 2.4m unterschreitet Mindestanforderungen")
        
        # Verhältnisse
        aspect_ratio = max(dimensions['width'], dimensions['depth']) / min(dimensions['width'], dimensions['depth'])
        if aspect_ratio > 4:
            warnings.append("Gebäude ist sehr langgestreckt (Verhältnis > 4:1)")
        
        # Fensterflächenanteil
        total_window_area = sum(w['area'] for w in building_data['geometry']['windows'])
        total_wall_area = sum(w['area'] for w in building_data['geometry']['walls'])
        
        if total_wall_area > 0:
            window_ratio = total_window_area / total_wall_area
            if window_ratio > 0.5:
                warnings.append(f"Fensterflächenanteil sehr hoch: {window_ratio:.1%}")
            elif window_ratio < 0.1:
                warnings.append(f"Fensterflächenanteil sehr niedrig: {window_ratio:.1%}")
        
        return {
            'errors': errors,
            'warnings': warnings,
            'valid': len(errors) == 0
        }

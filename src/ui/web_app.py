"""
Erweiterte 3D-Gebäudemodellierung für energyOS
============================================

Erweiterte Web-App für detaillierte Gebäudemodellierung mit allen Bauteilen,
U-Werten und Heizkörpern nach deutschen Normen.
"""

from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import sys
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
import numpy as np

# Importiere energyOS Module
sys.path.append(str(Path(__file__).parent.parent))
from core.building import Building, BuildingProperties, Wall, Window, Roof, Floor
from core.detailed_building_components import (
    DetailedBuildingManager, DetailedWall, DetailedWindow, DetailedDoor,
    DetailedRoof, DetailedFloor, HeatingElement, ThermalBridge, ShadingElement,
    Material, Layer, Position3D, ComponentType
)
from main import run_simulation

# Flask-App initialisieren
STATIC_DIR = Path(__file__).parent / "static"
TEMPLATES_DIR = Path(__file__).parent / "templates"

app = Flask(__name__, 
            template_folder=str(TEMPLATES_DIR),
            static_folder=str(STATIC_DIR),
            static_url_path='/static')
CORS(app)

# Globale Instanz für erweiterte 3D-Verwaltung
building_manager = None

def create_building_manager():
    """Erstellt Building Manager Instanz"""
    global building_manager
    if building_manager is None:
        building_manager = Building3DManager()
    return building_manager

class Building3DManager:
    """Erweiterte 3D-Gebäudeverwaltung mit detaillierter Modellierung"""
    
    def __init__(self):
        self.building_manager = DetailedBuildingManager()
        self.current_building_id = None
        self.simulation_results = {}
        
        # Lade Standard-Gebäude
        self._create_default_building()
    
    def _create_default_building(self):
        """Erstellt Standard-Gebäude mit allen Komponenten"""
        # Standard-Außenwände
        wall_layers = [
            Layer(self.building_manager.standard_materials["plaster_internal"], 0.015),
            Layer(self.building_manager.standard_materials["brick"], 0.175),
            Layer(self.building_manager.standard_materials["insulation_eps"], 0.14),
            Layer(self.building_manager.standard_materials["plaster_external"], 0.02)
        ]
        
        # Süd-Wand
        south_wall = DetailedWall(
            name="Südwand",
            area=30.0,
            height=2.5,
            orientation="S",
            layers=wall_layers,
            position=Position3D(0, 0, 0, 0, 0, 0),
            is_external=True
        )
        
        # Nord-Wand
        north_wall = DetailedWall(
            name="Nordwand",
            area=30.0,
            height=2.5,
            orientation="N",
            layers=wall_layers,
            position=Position3D(0, 0, 12, 0, 0, 180),
            is_external=True
        )
        
        # Ost-Wand
        east_wall = DetailedWall(
            name="Ostwand",
            area=20.0,
            height=2.5,
            orientation="E",
            layers=wall_layers,
            position=Position3D(12, 0, 6, 0, 0, 90),
            is_external=True
        )
        
        # West-Wand
        west_wall = DetailedWall(
            name="Westwand",
            area=20.0,
            height=2.5,
            orientation="W",
            layers=wall_layers,
            position=Position3D(0, 0, 6, 0, 0, 270),
            is_external=True
        )
        
        # Fenster
        south_window = DetailedWindow(
            name="Südfenster",
            area=8.0,
            width=2.0,
            height=1.5,
            orientation="S",
            position=Position3D(6, 1.0, 0),
            u_value=1.1,
            g_value=0.6,
            glazing_type="3-fach"
        )
        
        east_window = DetailedWindow(
            name="Ostfenster",
            area=4.0,
            width=1.2,
            height=1.5,
            orientation="E",
            position=Position3D(12, 1.0, 4),
            u_value=1.1,
            g_value=0.6,
            glazing_type="3-fach"
        )
        
        # Haustür
        main_door = DetailedDoor(
            name="Haustür",
            area=2.1,
            width=1.0,
            height=2.1,
            orientation="S",
            position=Position3D(2, 0, 0),
            u_value=1.8,
            door_type="external",
            material="wood",
            is_main_entrance=True
        )
        
        # Dach
        roof_layers = [
            Layer(self.building_manager.standard_materials["plaster_internal"], 0.015),
            Layer(self.building_manager.standard_materials["wood_construction"], 0.04),
            Layer(self.building_manager.standard_materials["insulation_mineral"], 0.20),
            Layer(self.building_manager.standard_materials["wood_construction"], 0.025)
        ]
        
        roof = DetailedRoof(
            name="Satteldach",
            area=120.0,
            tilt=35.0,
            orientation="S",
            layers=roof_layers,
            position=Position3D(6, 3.0, 6),
            roof_type="satteldach",
            pv_suitable=True,
            pv_area_available=80.0
        )
        
        # Bodenplatte
        floor_layers = [
            Layer(self.building_manager.standard_materials["screed"], 0.06),
            Layer(self.building_manager.standard_materials["insulation_eps"], 0.14),
            Layer(self.building_manager.standard_materials["concrete"], 0.20)
        ]
        
        floor = DetailedFloor(
            name="Bodenplatte",
            area=100.0,
            layers=floor_layers,
            position=Position3D(6, 0, 6),
            floor_type="bodenplatte",
            ground_coupling=True
        )
        
        # Heizkörper
        radiator_living = HeatingElement(
            name="HK Wohnzimmer",
            position=Position3D(1, 0.1, 1),
            radiator_type="panel",
            heating_power=2000.0,
            width=1.0,
            height=0.6,
            supply_temp=55.0,
            return_temp=45.0,
            has_thermostatic_valve=True
        )
        
        radiator_bedroom = HeatingElement(
            name="HK Schlafzimmer",
            position=Position3D(10, 0.1, 10),
            radiator_type="panel",
            heating_power=1500.0,
            width=0.8,
            height=0.6,
            supply_temp=55.0,
            return_temp=45.0,
            has_thermostatic_valve=True
        )
        
        # Wärmebrücken
        corner_bridge = ThermalBridge(
            name="Gebäudeecke",
            bridge_type="corner",
            position=Position3D(0, 0, 0),
            psi_value=0.05,
            length=2.5
        )
        
        # Verschattung
        overhang = ShadingElement(
            name="Dachüberstand",
            position=Position3D(6, 2.8, -0.5),
            shading_type="overhang",
            width=2.0,
            height=0.5,
            depth=0.8,
            shading_factor=0.3
        )
        
        # Komponenten hinzufügen
        self.building_manager.add_component(south_wall)
        self.building_manager.add_component(north_wall)
        self.building_manager.add_component(east_wall)
        self.building_manager.add_component(west_wall)
        self.building_manager.add_component(south_window)
        self.building_manager.add_component(east_window)
        self.building_manager.add_component(main_door)
        self.building_manager.add_component(roof)
        self.building_manager.add_component(floor)
        self.building_manager.add_component(radiator_living)
        self.building_manager.add_component(radiator_bedroom)
        self.building_manager.add_component(corner_bridge)
        self.building_manager.add_component(overhang)
    
    def get_building_3d_data(self) -> Dict[str, Any]:
        """Erweiterte Gebäudedaten für 3D-Darstellung"""
        try:
            # Basis-3D-Daten vom Manager holen
            base_data = self.building_manager.get_building_3d_data()
            
            # Erweiterte Berechnungen hinzufügen
            heat_losses = self.building_manager.calculate_total_heat_loss()
            
            # Gebäudedimensionen berechnen
            dimensions = self._calculate_building_dimensions()
            
            # Energie-Daten zusammenstellen
            energy_data = {
                "total_heat_loss": heat_losses.get("total_transmission", 0),
                "heat_losses": heat_losses,
                "total_heated_area": dimensions.get("floor_area", 100),
                "envelope_area": dimensions.get("envelope_area", 200),
                "u_values_summary": self._calculate_u_value_summary()
            }
            
            # Erweiterte Daten hinzufügen
            base_data.update({
                "dimensions": dimensions,
                "energy_data": energy_data,
                "success": True
            })
            
            return base_data
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _calculate_building_dimensions(self) -> Dict[str, float]:
        """Berechnet Gebäudedimensionen"""
        walls = self.building_manager.get_components_by_type(ComponentType.WALL)
        floors = self.building_manager.get_components_by_type(ComponentType.FLOOR)
        
        # Vereinfachte Berechnung - kann erweitert werden
        floor_area = floors[0].area if floors else 100.0
        envelope_area = sum(wall.area for wall in walls) + (floors[0].area if floors else 0)
        
        # Geschätzte Dimensionen
        width = 12.0
        depth = 8.0
        height = 2.5
        
        if floors:
            width = (floor_area / 8.0) ** 0.5 * 8.0 ** 0.5
            depth = floor_area / width
        
        return {
            "width": width,
            "depth": depth,
            "height": height,
            "floor_area": floor_area,
            "envelope_area": envelope_area,
            "volume": floor_area * height
        }
    
    def _calculate_u_value_summary(self) -> Dict[str, float]:
        """Berechnet U-Wert-Zusammenfassung"""
        walls = self.building_manager.get_components_by_type(ComponentType.WALL)
        windows = self.building_manager.get_components_by_type(ComponentType.WINDOW)
        doors = self.building_manager.get_components_by_type(ComponentType.DOOR)
        
        def weighted_average(components, area_attr='area', u_attr='u_value'):
            total_area = 0
            weighted_sum = 0
            for comp in components:
                area = getattr(comp, area_attr, 0)
                u_value = getattr(comp, u_attr, None)
                if u_value is None and hasattr(comp, 'calculate_u_value'):
                    u_value = comp.calculate_u_value()
                if u_value and area > 0:
                    total_area += area
                    weighted_sum += u_value * area
            return weighted_sum / total_area if total_area > 0 else 0
        
        return {
            "walls_avg": weighted_average(walls),
            "windows_avg": weighted_average(windows),
            "doors_avg": weighted_average(doors),
            "avg": weighted_average(walls + windows + doors)
        }
    
    def add_component(self, component_type: str, component_data: Dict[str, Any]) -> str:
        """Fügt neue Komponente hinzu"""
        try:
            if component_type == "wall":
                component = self._create_wall_from_data(component_data)
            elif component_type == "window":
                component = self._create_window_from_data(component_data)
            elif component_type == "door":
                component = self._create_door_from_data(component_data)
            elif component_type == "radiator":
                component = self._create_radiator_from_data(component_data)
            else:
                raise ValueError(f"Unbekannter Komponententyp: {component_type}")
            
            return self.building_manager.add_component(component)
        
        except Exception as e:
            raise ValueError(f"Fehler beim Erstellen der Komponente: {str(e)}")
    
    def _create_wall_from_data(self, data: Dict[str, Any]) -> DetailedWall:
        """Erstellt Wand aus Daten"""
        # Standard-Materialien verwenden
        layers = []
        for layer_data in data.get("layers", []):
            material_name = layer_data.get("material", "brick")
            thickness = layer_data.get("thickness", 0.1)
            
            if material_name in self.building_manager.standard_materials:
                material = self.building_manager.standard_materials[material_name]
                layers.append(Layer(material, thickness))
        
        # Falls keine Schichten angegeben, Standard-Aufbau verwenden
        if not layers:
            layers = self.building_manager.standard_constructions["external_wall_geg"]
        
        position = Position3D(
            x=data.get("position", {}).get("x", 0),
            y=data.get("position", {}).get("y", 0),
            z=data.get("position", {}).get("z", 0),
            rotation_z=data.get("position", {}).get("rotation", 0)
        )
        
        wall = DetailedWall(
            name=data.get("name", "Neue Wand"),
            area=data.get("area", 20.0),
            height=data.get("height", 2.5),
            orientation=data.get("orientation", "S"),
            layers=layers,
            position=position,
            is_external=data.get("is_external", True),
            is_load_bearing=data.get("is_load_bearing", False)
        )
        
        return wall
    
    def _create_window_from_data(self, data: Dict[str, Any]) -> DetailedWindow:
        """Erstellt Fenster aus Daten"""
        position = Position3D(
            x=data.get("position", {}).get("x", 0),
            y=data.get("position", {}).get("y", 1.0),
            z=data.get("position", {}).get("z", 0)
        )
        
        window = DetailedWindow(
            name=data.get("name", "Neues Fenster"),
            area=data.get("area", 2.0),
            width=data.get("width", 1.2),
            height=data.get("height", 1.5),
            orientation=data.get("orientation", "S"),
            position=position,
            u_value=data.get("u_value", 1.1),
            g_value=data.get("g_value", 0.6),
            glazing_type=data.get("glazing_type", "3-fach"),
            is_openable=data.get("is_openable", True)
        )
        
        return window
    
    def _create_door_from_data(self, data: Dict[str, Any]) -> DetailedDoor:
        """Erstellt Tür aus Daten"""
        position = Position3D(
            x=data.get("position", {}).get("x", 0),
            y=data.get("position", {}).get("y", 0),
            z=data.get("position", {}).get("z", 0)
        )
        
        door = DetailedDoor(
            name=data.get("name", "Neue Tür"),
            area=data.get("area", 2.1),
            width=data.get("width", 1.0),
            height=data.get("height", 2.1),
            orientation=data.get("orientation", "S"),
            position=position,
            u_value=data.get("u_value", 1.8),
            door_type=data.get("door_type", "external"),
            material=data.get("material", "wood"),
            is_main_entrance=data.get("is_main_entrance", False)
        )
        
        return door
    
    def _create_radiator_from_data(self, data: Dict[str, Any]) -> HeatingElement:
        """Erstellt Heizkörper aus Daten"""
        position = Position3D(
            x=data.get("position", {}).get("x", 0),
            y=data.get("position", {}).get("y", 0.1),
            z=data.get("position", {}).get("z", 0)
        )
        
        radiator = HeatingElement(
            name=data.get("name", "Neuer Heizkörper"),
            position=position,
            radiator_type=data.get("radiator_type", "panel"),
            heating_power=data.get("heating_power", 1000.0),
            width=data.get("width", 0.6),
            height=data.get("height", 0.6),
            depth=data.get("depth", 0.1),
            supply_temp=data.get("supply_temp", 55.0),
            return_temp=data.get("return_temp", 45.0),
            has_thermostatic_valve=data.get("has_thermostatic_valve", True)
        )
        
        return radiator
    
    def update_component(self, component_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Aktualisiert Komponente"""
        try:
            component = self.building_manager.get_component(component_id)
            if not component:
                return {"success": False, "error": "Komponente nicht gefunden"}
            
            # Position aktualisieren
            if 'position' in updates:
                pos_data = updates['position']
                component.position.x = pos_data.get('x', component.position.x)
                component.position.y = pos_data.get('y', component.position.y)
                component.position.z = pos_data.get('z', component.position.z)
                component.position.rotation_x = pos_data.get('rotation_x', component.position.rotation_x)
                component.position.rotation_y = pos_data.get('rotation_y', component.position.rotation_y)
                component.position.rotation_z = pos_data.get('rotation_z', component.position.rotation_z)
            
            # Andere Eigenschaften aktualisieren
            for key, value in updates.items():
                if key != 'position' and hasattr(component, key):
                    setattr(component, key, value)
            
            return {"success": True, "component_id": component_id}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def delete_component(self, component_id: str) -> bool:
        """Löscht Komponente"""
        try:
            return self.building_manager.remove_component(component_id)
        except Exception as e:
            return False
    
    def get_standard_materials(self) -> Dict[str, Any]:
        """Gibt Standard-Materialien zurück"""
        try:
            materials = {}
            for key, material in self.building_manager.standard_materials.items():
                materials[key] = {
                    "name": material.name,
                    "lambda_value": material.lambda_value,
                    "density": material.density,
                    "specific_heat": material.specific_heat,
                    "category": getattr(material, 'category', 'other')
                }
            return materials
        except Exception as e:
            return {}
    
    def get_standard_constructions(self) -> Dict[str, Any]:
        """Gibt Standard-Konstruktionen zurück"""
        try:
            constructions = {}
            for key, layers in self.building_manager.standard_constructions.items():
                constructions[key] = {
                    "name": key.replace('_', ' ').title(),
                    "layers": [
                        {
                            "material": layer.material.name,
                            "thickness": layer.thickness,
                            "lambda": layer.material.lambda_value
                        } for layer in layers
                    ]
                }
            return constructions
        except Exception as e:
            return {}

    def add_component_interactive(self, component_type: str, position: Dict[str, float], 
                                properties: Dict[str, Any]) -> Dict[str, Any]:
        """Fügt Komponente interaktiv im 3D-Editor hinzu"""
        try:
            pos = Position3D(
                position.get('x', 0),
                position.get('y', 0), 
                position.get('z', 0),
                position.get('rotation_x', 0),
                position.get('rotation_y', 0),
                position.get('rotation_z', 0)
            )
            
            if component_type == 'wall':
                return self._create_interactive_wall(pos, properties)
            elif component_type == 'window':
                return self._create_interactive_window(pos, properties)
            elif component_type == 'door':
                return self._create_interactive_door(pos, properties)
            elif component_type == 'radiator':
                return self._create_interactive_radiator(pos, properties)
            else:
                return {"success": False, "error": "Unbekannter Komponententyp"}
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _create_interactive_wall(self, position: Position3D, properties: Dict[str, Any]) -> Dict[str, Any]:
        """Erstellt interaktive Wand"""
        # Standard-Materialschichten für verschiedene Standards
        layer_templates = {
            'geg_standard': [
                Layer(self.building_manager.standard_materials["plaster_internal"], 0.015),
                Layer(self.building_manager.standard_materials["brick"], 0.175), 
                Layer(self.building_manager.standard_materials["insulation_eps"], 0.14),
                Layer(self.building_manager.standard_materials["plaster_external"], 0.02)
            ],
            'passivhaus': [
                Layer(self.building_manager.standard_materials["plaster_internal"], 0.015),
                Layer(self.building_manager.standard_materials["concrete"], 0.20),
                Layer(self.building_manager.standard_materials["insulation_mineral"], 0.30),
                Layer(self.building_manager.standard_materials["plaster_external"], 0.02)
            ],
            'kfw_40': [
                Layer(self.building_manager.standard_materials["plaster_internal"], 0.015),
                Layer(self.building_manager.standard_materials["brick"], 0.175),
                Layer(self.building_manager.standard_materials["insulation_eps"], 0.20),
                Layer(self.building_manager.standard_materials["plaster_external"], 0.02)
            ]
        }
        
        standard = properties.get('standard', 'geg_standard')
        layers = layer_templates.get(standard, layer_templates['geg_standard'])
        
        wall = DetailedWall(
            name=properties.get('name', 'Neue Wand'),
            area=properties.get('area', 20.0),
            height=properties.get('height', 2.5),
            orientation=properties.get('orientation', 'S'),
            layers=layers,
            position=position,
            is_external=properties.get('is_external', True)
        )
        
        wall_id = self.building_manager.add_component(wall)
        return {
            "success": True, 
            "component_id": wall_id,
            "u_value": wall.calculate_u_value(),
            "layers": len(layers)
        }
    
    def _create_interactive_window(self, position: Position3D, properties: Dict[str, Any]) -> Dict[str, Any]:
        """Erstellt interaktives Fenster"""
        # U-Werte nach Verglasungstyp
        u_values = {
            '2-fach': 1.3,
            '3-fach': 0.8, 
            '3-fach_passiv': 0.6
        }
        
        glazing_type = properties.get('glazing_type', '3-fach')
        
        window = DetailedWindow(
            name=properties.get('name', 'Neues Fenster'),
            area=properties.get('area', 2.0),
            width=properties.get('width', 1.2),
            height=properties.get('height', 1.5),
            orientation=properties.get('orientation', 'S'),
            position=position,
            u_value=u_values.get(glazing_type, 1.1),
            g_value=properties.get('g_value', 0.6),
            glazing_type=glazing_type
        )
        
        window_id = self.building_manager.add_component(window)
        return {
            "success": True,
            "component_id": window_id, 
            "u_value": window.u_value,
            "g_value": window.g_value
        }
    
    def _create_interactive_door(self, position: Position3D, properties: Dict[str, Any]) -> Dict[str, Any]:
        """Erstellt interaktive Tür"""
        # U-Werte nach Türtyp
        u_values = {
            'wood': 1.8,
            'steel': 2.0,
            'aluminum': 2.5,
            'pvc': 1.5
        }
        
        material = properties.get('material', 'wood')
        
        door = DetailedDoor(
            name=properties.get('name', 'Neue Tür'),
            area=properties.get('area', 2.1),
            width=properties.get('width', 1.0),
            height=properties.get('height', 2.1),
            orientation=properties.get('orientation', 'S'),
            position=position,
            u_value=u_values.get(material, 1.8),
            door_type=properties.get('door_type', 'external'),
            material=material
        )
        
        door_id = self.building_manager.add_component(door)
        return {
            "success": True,
            "component_id": door_id,
            "u_value": door.u_value,
            "material": material
        }
    
    def _create_interactive_radiator(self, position: Position3D, properties: Dict[str, Any]) -> Dict[str, Any]:
        """Erstellt interaktiven Heizkörper"""
        radiator = HeatingElement(
            name=properties.get('name', 'Neuer Heizkörper'),
            position=position,
            radiator_type=properties.get('radiator_type', 'panel'),
            heating_power=properties.get('heating_power', 1500.0),
            width=properties.get('width', 1.0),
            height=properties.get('height', 0.6),
            supply_temp=properties.get('supply_temp', 55.0),
            return_temp=properties.get('return_temp', 45.0),
            has_thermostatic_valve=properties.get('has_thermostatic_valve', True)
        )
        
        radiator_id = self.building_manager.add_component(radiator)
        return {
            "success": True,
            "component_id": radiator_id,
            "heating_power": radiator.heating_power,
            "radiator_type": radiator.radiator_type
        }

    def update_component_u_value(self, component_id: str, layers_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Aktualisiert U-Wert einer Komponente basierend auf Schichtdaten"""
        try:
            component = self.building_manager.get_component(component_id)
            if not component:
                return {"success": False, "error": "Komponente nicht gefunden"}
            
            if hasattr(component, 'layers'):
                # Neue Schichten erstellen
                new_layers = []
                for layer_data in layers_data:
                    material_name = layer_data['material']
                    thickness = float(layer_data['thickness'])
                    
                    if material_name in self.building_manager.standard_materials:
                        material = self.building_manager.standard_materials[material_name]
                        new_layers.append(Layer(material, thickness))
                
                # Schichten aktualisieren
                component.layers = new_layers
                
                # U-Wert neu berechnen
                if hasattr(component, 'calculate_u_value'):
                    u_value = component.calculate_u_value()
                    return {
                        "success": True,
                        "u_value": u_value,
                        "layers_count": len(new_layers)
                    }
            
            return {"success": False, "error": "Komponente unterstützt keine Schichten"}
            
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_component_details(self, component_id: str) -> Dict[str, Any]:
        """Gibt detaillierte Informationen einer Komponente zurück"""
        try:
            component = self.building_manager.get_component(component_id)
            if not component:
                return {"success": False, "error": "Komponente nicht gefunden"}
            
            details = {
                "success": True,
                "type": type(component).__name__.lower().replace('detailed', ''),
                "id": component.id,
                "name": component.name,
                "position": {
                    "x": component.position.x,
                    "y": component.position.y,
                    "z": component.position.z,
                    "rotation_x": component.position.rotation_x,
                    "rotation_y": component.position.rotation_y,  
                    "rotation_z": component.position.rotation_z
                }
            }
            
            # Spezifische Eigenschaften je nach Typ
            if isinstance(component, DetailedWall):
                details.update({
                    "area": component.area,
                    "height": component.height,
                    "width": component.width,
                    "orientation": component.orientation,
                    "u_value": component.u_value or component.calculate_u_value(),
                    "is_external": component.is_external,
                    "layers": [
                        {
                            "material": layer.material.name,
                            "thickness": layer.thickness,
                            "lambda": layer.material.lambda_value
                        } for layer in component.layers
                    ]
                })
            elif isinstance(component, DetailedWindow):
                details.update({
                    "area": component.area,
                    "width": component.width,
                    "height": component.height,
                    "orientation": component.orientation,
                    "u_value": component.u_value,
                    "g_value": component.g_value,
                    "glazing_type": component.glazing_type,
                    "is_openable": component.is_openable
                })
            elif isinstance(component, DetailedDoor):
                details.update({
                    "area": component.area,
                    "width": component.width,
                    "height": component.height,
                    "orientation": component.orientation,
                    "u_value": component.u_value,
                    "door_type": component.door_type,
                    "material": component.material,
                    "is_main_entrance": component.is_main_entrance
                })
            elif isinstance(component, HeatingElement):
                details.update({
                    "heating_power": component.heating_power,
                    "width": component.width,
                    "height": component.height,
                    "radiator_type": component.radiator_type,
                    "supply_temp": component.supply_temp,
                    "return_temp": component.return_temp,
                    "has_thermostatic_valve": component.has_thermostatic_valve
                })
            
            return details
            
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _get_efficiency_recommendations(self, efficiency_class: str, specific_heat_demand: float) -> List[str]:
        """Gibt Effizienzempfehlungen basierend auf Energieanalyse zurück"""
        recommendations = []
        
        if efficiency_class in ["D", "E"]:
            recommendations.extend([
                "Dämmung der Außenwände verstärken (U-Wert < 0.24 W/(m²·K))",
                "Fenstererneuerung mit 3-fach Verglasung (U-Wert < 1.1 W/(m²·K))",
                "Dachdämmung verbessern (U-Wert < 0.20 W/(m²·K))",
                "Wärmebrücken minimieren"
            ])
        elif efficiency_class == "C":
            recommendations.extend([
                "Fenstererneuerung mit 3-fach Verglasung prüfen",
                "Dachdämmung optimieren",
                "Wärmepumpe für Heizung und Warmwasser"
            ])
        elif efficiency_class == "B":
            recommendations.extend([
                "Wärmepumpe installieren",
                "Lüftungsanlage mit Wärmerückgewinnung",
                "Photovoltaikanlage prüfen"
            ])
        else:  # A, A+
            recommendations.extend([
                "Photovoltaikanlage installieren",
                "Smart Home System für optimale Regelung",
                "Batteriespeicher für Eigenverbrauch"
            ])
        
        return recommendations

# Global manager instance will be created on demand

# Flask Routes
@app.route('/api/building/data', methods=['GET'])
def get_building_data():
    """Gibt Gebäudedaten für 3D-Darstellung zurück"""
    try:
        manager = create_building_manager()
        building_data = manager.get_building_3d_data()
        return jsonify({"success": True, "building": building_data})
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/')
def index():
    """Hauptseite der erweiterten 3D-Anwendung"""
    return render_template('index.html')

@app.route('/advanced')
def advanced():
    """Erweiterte Anwendung (Original)"""
    return render_template('index.html')



@app.route('/api/building/load')
def load_building():
    """Lädt vollständige Gebäudedaten"""
    try:
        building_data = building_manager.get_building_3d_data()
        return jsonify(building_data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/simulation/heat-pump-sizing', methods=['POST'])
def calculate_heat_pump_sizing():
    """Berechnet Wärmepumpenauslegung"""
    try:
        data = request.get_json()
        outdoor_temp = data.get('outdoor_temp', -12.0)
        indoor_temp = data.get('indoor_temp', 20.0)
        
        # Heizlast berechnen
        heat_losses = building_manager.building_manager.calculate_total_heat_loss(
            indoor_temp, outdoor_temp
        )
        
        # Zusätzliche Lüftungsverluste schätzen
        building_data = building_manager.get_building_3d_data()
        volume = building_data["dimensions"]["volume"]
        ventilation_rate = 0.5  # 1/h
        ventilation_loss = volume * ventilation_rate * 0.34 * (indoor_temp - outdoor_temp)
        
        total_heat_demand = heat_losses["total_transmission"] + ventilation_loss
        
        # Wärmepumpe dimensionieren (mit Sicherheitsfaktor)
        safety_factor = 1.2
        required_power = total_heat_demand * safety_factor
        
        # COP schätzen
        temp_lift = indoor_temp - outdoor_temp
        estimated_cop = max(2.0, 6.0 - (temp_lift * 0.05))
        
        result = {
            "heat_demand": {
                "transmission_losses": heat_losses["total_transmission"],
                "ventilation_losses": ventilation_loss,
                "total_demand": total_heat_demand
            },
            "heat_pump_sizing": {
                "required_power": required_power,
                "recommended_power": round(required_power / 1000) * 1000,  # Auf kW runden
                "estimated_cop": round(estimated_cop, 2),
                "annual_energy_consumption": round(required_power * 2000 / estimated_cop / 1000),  # kWh/a
                "safety_factor": safety_factor
            },
            "operating_conditions": {
                "outdoor_temp": outdoor_temp,
                "indoor_temp": indoor_temp,
                "supply_temp": 55.0,
                "return_temp": 45.0
            }
        }
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/simulation/run', methods=['POST'])
def run_building_simulation():
    """Führt Gebäudesimulation aus"""
    try:
        data = request.get_json()
        
        # Vereinfachte Simulation - später Integration mit bestehendem System
        building_data = building_manager.get_building_3d_data()
        
        # Simulationsergebnisse mock
        results = {
            "status": "success",
            "simulation_id": "sim_" + str(hash(str(building_data))),
            "results": {
                "heat_demand_annual": 15000,  # kWh/a
                "energy_efficiency_class": "A+",
                "u_value_average": building_data["energy_data"]["u_values_summary"]["walls_avg"],
                "building_volume": building_data["dimensions"]["volume"],
                "heated_area": building_data["energy_data"]["total_heated_area"]
            }
        }
        
        return jsonify(results)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Neue API-Routen für erweiterte 3D-Bearbeitung

@app.route('/api/components/add', methods=['POST'])
def add_component_interactive():
    """Fügt neue Komponente interaktiv hinzu"""
    try:
        data = request.get_json()
        component_type = data.get('type')
        position = data.get('position', {})
        properties = data.get('properties', {})
        
        manager = create_building_manager()
        result = manager.add_component_interactive(component_type, position, properties)
        return jsonify(result)
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/components/<component_id>/details', methods=['GET'])
def get_component_details(component_id):
    """Gibt detaillierte Informationen einer Komponente zurück"""
    try:
        manager = create_building_manager()
        result = manager.get_component_details(component_id)
        return jsonify(result)
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/components/<component_id>/update', methods=['POST'])
def update_component(component_id):
    """Aktualisiert eine Komponente"""
    try:
        data = request.get_json()
        
        manager = create_building_manager()
        
        # Spezielle Behandlung für U-Wert-Updates über Schichtdaten
        if 'layers' in data:
            result = manager.update_component_u_value(component_id, data['layers'])
        else:
            # Normale Komponentenaktualisierung
            result = manager.update_component(component_id, data)
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/components/<component_id>/delete', methods=['DELETE'])
def delete_component(component_id):
    """Löscht eine Komponente"""
    try:
        manager = create_building_manager()
        success = manager.delete_component(component_id)
        return jsonify({"success": success})
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/materials/standards', methods=['GET'])
def get_standard_materials():
    """Gibt Standard-Materialien zurück"""
    try:
        manager = create_building_manager()
        materials = manager.get_standard_materials()
        return jsonify({"success": True, "materials": materials})
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/constructions/standards', methods=['GET'])
def get_standard_constructions():
    """Gibt Standard-Konstruktionen zurück"""
    try:
        manager = create_building_manager()
        constructions = manager.get_standard_constructions()
        return jsonify({"success": True, "constructions": constructions})
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/building/calculate_u_value', methods=['POST'])
def calculate_u_value():
    """Berechnet U-Wert für gegebene Schichtdaten"""
    try:
        manager = create_building_manager()
        data = request.get_json()
        layers_data = data.get('layers', [])
        
        # Temporäre Wand für U-Wert-Berechnung erstellen
        layers = []
        for layer_data in layers_data:
            material_name = layer_data['material']
            thickness = float(layer_data['thickness'])
            
            if material_name in manager.building_manager.standard_materials:
                material = manager.building_manager.standard_materials[material_name]
                layers.append(Layer(material, thickness))
        
        if layers:
            temp_wall = DetailedWall(
                name="Temp",
                area=1.0,
                height=1.0,
                layers=layers,
                position=Position3D(0, 0, 0)
            )
            u_value = temp_wall.calculate_u_value()
            
            return jsonify({
                "success": True,
                "u_value": round(u_value, 3),
                "layers_count": len(layers)
            })
        else:
            return jsonify({"success": False, "error": "Keine gültigen Schichten"})
            
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/building/energy_analysis', methods=['GET'])
def get_energy_analysis():
    """Gibt erweiterte Energieanalyse zurück"""
    try:
        manager = create_building_manager()
        building_data = manager.get_building_3d_data()
        heat_losses = manager.building_manager.calculate_total_heat_loss()
        
        # Energieeffizienzklasse bestimmen
        total_heated_area = building_data["energy_data"]["total_heated_area"]
        specific_heat_demand = heat_losses["total_transmission"] / total_heated_area if total_heated_area > 0 else 0
        
        if specific_heat_demand <= 15:
            efficiency_class = "A+"
        elif specific_heat_demand <= 30:
            efficiency_class = "A"
        elif specific_heat_demand <= 50:
            efficiency_class = "B"
        elif specific_heat_demand <= 75:
            efficiency_class = "C"
        elif specific_heat_demand <= 100:
            efficiency_class = "D"
        else:
            efficiency_class = "E"
        
        analysis = {
            "success": True,
            "building_data": building_data,
            "heat_losses": heat_losses,
            "energy_analysis": {
                "specific_heat_demand": round(specific_heat_demand, 1),
                "efficiency_class": efficiency_class,
                "total_heated_area": total_heated_area,
                "building_volume": building_data["dimensions"]["volume"],
                "envelope_area": building_data["energy_data"]["envelope_area"]
            },
            "recommendations": manager._get_efficiency_recommendations(efficiency_class, specific_heat_demand)
        }
        
        return jsonify(analysis)
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

if __name__ == '__main__':
    # Enhanced Manager wird über create_building_manager() erstellt
    app.run(host='127.0.0.1', port=8080, debug=True)

"""
Detaillierte Gebäudekomponenten für 3D-Editor nach deutschen Normen
=================================================================

Umfassende Gebäudemodellierung mit allen Bauteilen für Wärmepumpenauslegung
nach DIN 4108, DIN EN ISO 13790, GEG und weiteren deutschen Normen.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Union
import uuid
from enum import Enum
import numpy as np

class ComponentType(Enum):
    """Bauteiltypen nach deutscher Bauphysik"""
    WALL = "wall"
    WINDOW = "window"
    DOOR = "door"
    ROOF = "roof"
    FLOOR = "floor"
    CEILING = "ceiling"
    RADIATOR = "radiator"
    THERMAL_BRIDGE = "thermal_bridge"
    SHADING = "shading"

class MaterialType(Enum):
    """Materialtypen mit Standard-λ-Werten"""
    CONCRETE = "concrete"  # λ = 2.1 W/(m·K)
    BRICK = "brick"  # λ = 0.79 W/(m·K)
    INSULATION = "insulation"  # λ = 0.035 W/(m·K)
    WOOD = "wood"  # λ = 0.13 W/(m·K)
    STEEL = "steel"  # λ = 50 W/(m·K)
    GLASS = "glass"  # λ = 1.0 W/(m·K)
    PLASTER = "plaster"  # λ = 0.87 W/(m·K)
    
@dataclass
class Material:
    """Materialspezifikation nach DIN 4108-4"""
    name: str
    lambda_value: float  # Wärmeleitfähigkeit W/(m·K)
    density: float  # kg/m³
    specific_heat: float  # J/(kg·K)
    vapor_diffusion: float  # Wasserdampf-Diffusionswiderstandszahl μ
    fire_class: str = "A1"  # Baustoffklasse nach DIN 4102
    
@dataclass
class Layer:
    """Schichtaufbau nach DIN 4108"""
    material: Material
    thickness: float  # m
    continuous: bool = True  # Unterbrechungsfreie Schicht

@dataclass
class Position3D:
    """3D-Position und Orientierung"""
    x: float
    y: float
    z: float
    rotation_x: float = 0.0
    rotation_y: float = 0.0
    rotation_z: float = 0.0

@dataclass
class DetailedWall:
    """Detaillierte Wandspezifikation nach DIN 4108"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = "Wand"
    area: float = 0.0  # m²
    height: float = 2.5  # m
    width: float = 0.0  # m (wird aus area/height berechnet)
    orientation: str = "S"  # N, NE, E, SE, S, SW, W, NW
    layers: List[Layer] = field(default_factory=list)
    position: Position3D = field(default_factory=lambda: Position3D(0, 0, 0))
    
    # Thermische Eigenschaften
    u_value: Optional[float] = None  # W/(m²·K) - wird berechnet
    thermal_mass: float = 0.0  # Wh/(m²·K)
    
    # Konstruktionsdetails
    is_load_bearing: bool = False
    is_external: bool = True
    adjacent_space: Optional[str] = None
    
    # Wärmebrücken
    thermal_bridges: Dict[str, float] = field(default_factory=dict)
    
    def __post_init__(self):
        if self.width == 0.0 and self.height > 0:
            self.width = self.area / self.height
    
    def calculate_u_value(self) -> float:
        """Berechnet U-Wert nach DIN EN ISO 6946"""
        if not self.layers:
            return 0.0
            
        # Wärmeübergangswiderstände
        r_si = 0.13  # innen, W/(m²·K)
        r_se = 0.04  # außen, W/(m²·K)
        
        r_total = r_si + r_se
        
        # Schichtwiderstände
        for layer in self.layers:
            if layer.thickness > 0 and layer.material.lambda_value > 0:
                r_total += layer.thickness / layer.material.lambda_value
        
        self.u_value = 1.0 / r_total if r_total > 0 else 0.0
        return self.u_value

@dataclass
class DetailedWindow:
    """Detaillierte Fensterspezifikation nach DIN EN 673"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = "Fenster"
    area: float = 0.0  # m²
    width: float = 1.2  # m
    height: float = 1.5  # m
    orientation: str = "S"
    position: Position3D = field(default_factory=lambda: Position3D(0, 1.0, 0))
    
    # Thermische Eigenschaften nach DIN EN 673
    u_value: float = 1.1  # W/(m²·K)
    g_value: float = 0.6  # Gesamtenergiedurchlassgrad
    
    # Rahmeneigenschaften
    frame_u_value: float = 1.3  # W/(m²·K)
    frame_fraction: float = 0.7  # Rahmenanteil
    
    # Verglasung
    glazing_type: str = "3-fach"  # 1-fach, 2-fach, 3-fach
    glass_thickness: List[float] = field(default_factory=lambda: [4, 4, 4])  # mm
    gas_filling: str = "Argon"  # Luft, Argon, Krypton
    
    # Sonnenschutz
    shading_factor: float = 0.8  # Verschattungsfaktor
    has_external_shading: bool = False
    has_internal_shading: bool = True
    
    # Lüftung
    is_openable: bool = True
    opening_type: str = "dreh-kipp"  # dreh-kipp, schiebe, fest
    
    def __post_init__(self):
        if self.area == 0.0:
            self.area = self.width * self.height

@dataclass
class DetailedDoor:
    """Detaillierte Türspezifikation"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = "Tür"
    area: float = 0.0  # m²
    width: float = 0.9  # m
    height: float = 2.1  # m
    orientation: str = "S"
    position: Position3D = field(default_factory=lambda: Position3D(0, 0, 0))
    
    # Thermische Eigenschaften
    u_value: float = 1.8  # W/(m²·K)
    
    # Türeigenschaften
    door_type: str = "external"  # external, internal
    material: str = "wood"  # wood, steel, aluminum, pvc
    insulation_thickness: float = 0.04  # m
    
    # Funktionale Eigenschaften
    is_main_entrance: bool = False
    has_glass_panels: bool = False
    glass_area: float = 0.0  # m²
    
    def __post_init__(self):
        if self.area == 0.0:
            self.area = self.width * self.height

@dataclass
class DetailedRoof:
    """Detaillierte Dachspezifikation nach DIN 4108-2"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = "Dach"
    area: float = 0.0  # m²
    tilt: float = 30.0  # Grad
    orientation: str = "S"  # Hauptorientierung
    layers: List[Layer] = field(default_factory=list)
    position: Position3D = field(default_factory=lambda: Position3D(0, 3.0, 0))
    
    # Dachtyp
    roof_type: str = "geneigt"  # geneigt, flach, walm, satteldach
    construction_type: str = "sparren"  # sparren, pfetten, träger
    
    # Thermische Eigenschaften
    u_value: Optional[float] = None
    thermal_mass: float = 0.0
    
    # Dachaufbau
    has_attic: bool = False
    attic_ventilated: bool = True
    insulation_position: str = "zwischen_sparren"  # zwischen_sparren, auf_sparren, unter_sparren
    
    # PV-Potenzial
    pv_suitable: bool = True
    pv_area_available: float = 0.0  # m²
    shading_objects: List[str] = field(default_factory=list)
    
    def calculate_u_value(self) -> float:
        """Berechnet U-Wert des Daches"""
        if not self.layers:
            return 0.0
            
        r_si = 0.10  # innen (nach oben)
        r_se = 0.04  # außen
        r_total = r_si + r_se
        
        for layer in self.layers:
            if layer.thickness > 0 and layer.material.lambda_value > 0:
                r_total += layer.thickness / layer.material.lambda_value
        
        self.u_value = 1.0 / r_total if r_total > 0 else 0.0
        return self.u_value

@dataclass
class DetailedFloor:
    """Detaillierte Bodenspezifikation nach DIN 4108-2"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = "Boden"
    area: float = 0.0  # m²
    layers: List[Layer] = field(default_factory=list)
    position: Position3D = field(default_factory=lambda: Position3D(0, 0, 0))
    
    # Bodentyp
    floor_type: str = "bodenplatte"  # bodenplatte, keller, obere_geschossdecke
    ground_coupling: bool = True
    basement_type: str = "unbeheizt"  # beheizt, unbeheizt, kein_keller
    
    # Thermische Eigenschaften
    u_value: Optional[float] = None
    thermal_mass: float = 0.0
    
    # Konstruktionsdetails
    has_underfloor_heating: bool = False
    heating_system_position: str = "in_estrich"  # in_estrich, unter_estrich
    
    def calculate_u_value(self) -> float:
        """Berechnet U-Wert des Bodens"""
        if not self.layers:
            return 0.0
            
        r_si = 0.17  # innen (nach unten)
        r_se = 0.04  # außen
        if self.ground_coupling:
            r_se += 0.5  # zusätzlicher Erdreichwiderstand
            
        r_total = r_si + r_se
        
        for layer in self.layers:
            if layer.thickness > 0 and layer.material.lambda_value > 0:
                r_total += layer.thickness / layer.material.lambda_value
        
        self.u_value = 1.0 / r_total if r_total > 0 else 0.0
        return self.u_value

@dataclass
class HeatingElement:
    """Heizkörper und Heizflächen"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = "Heizkörper"
    position: Position3D = field(default_factory=lambda: Position3D(0, 0.1, 0))
    
    # Heizkörpertyp
    radiator_type: str = "panel"  # panel, convector, underfloor, wall_heating
    heating_power: float = 1000.0  # W bei 70/55/20°C
    
    # Dimensionen
    width: float = 0.6  # m
    height: float = 0.6  # m
    depth: float = 0.1  # m
    
    # Betriebsparameter
    supply_temp: float = 55.0  # °C (für Wärmepumpe optimiert)
    return_temp: float = 45.0  # °C
    room_temp: float = 20.0  # °C
    
    # Regelung
    has_thermostatic_valve: bool = True
    control_type: str = "proportional"  # proportional, on_off, smart
    
    def calculate_heating_power(self, supply_temp: float, return_temp: float, room_temp: float) -> float:
        """Berechnet Heizleistung für gegebene Temperaturen"""
        # Vereinfachte Berechnung nach DIN EN 442
        dt_nominal = 50.0  # Normtemperaturdifferenz
        dt_actual = ((supply_temp + return_temp) / 2) - room_temp
        
        if dt_actual <= 0:
            return 0.0
            
        # Leistungsanpassung (n = 1.3 für Heizkörper)
        power_factor = (dt_actual / dt_nominal) ** 1.3
        return self.heating_power * power_factor

@dataclass
class ThermalBridge:
    """Wärmebrücken nach DIN 4108 Beiblatt 2"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = "Wärmebrücke"
    bridge_type: str = "edge"  # edge, corner, penetration, balcony
    position: Position3D = field(default_factory=lambda: Position3D(0, 0, 0))
    
    # Wärmebrückenwert
    psi_value: float = 0.05  # W/(m·K) - linearer Wärmedurchgangskoeffizient
    length: float = 1.0  # m
    
    # Geometrie
    related_components: List[str] = field(default_factory=list)
    
    def calculate_heat_loss(self, delta_t: float) -> float:
        """Berechnet Wärmeverlust durch Wärmebrücke"""
        return self.psi_value * self.length * delta_t

@dataclass
class ShadingElement:
    """Verschattungselemente"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = "Verschattung"
    position: Position3D = field(default_factory=lambda: Position3D(0, 0, 0))
    
    # Verschattungstyp
    shading_type: str = "overhang"  # overhang, side_fin, building, vegetation
    
    # Geometrie
    width: float = 1.0  # m
    height: float = 0.5  # m
    depth: float = 0.3  # m
    
    # Verschattungsfaktor
    shading_factor: float = 0.5  # 0 = keine Verschattung, 1 = vollständig verschattet
    seasonal_variation: bool = True  # Unterschiedliche Verschattung je Jahreszeit

class DetailedBuildingManager:
    """Manager für detaillierte Gebäudekomponenten"""
    
    def __init__(self):
        self.components: Dict[str, Union[DetailedWall, DetailedWindow, DetailedDoor, 
                                      DetailedRoof, DetailedFloor, HeatingElement,
                                      ThermalBridge, ShadingElement]] = {}
        
        # Standard-Materialien nach DIN 4108-4
        self.standard_materials = self._create_standard_materials()
        
        # Standard-Aufbauten
        self.standard_constructions = self._create_standard_constructions()
    
    def _create_standard_materials(self) -> Dict[str, Material]:
        """Erstellt Standard-Materialien nach DIN 4108-4"""
        materials = {}
        
        # Mauerwerk
        materials["brick"] = Material(
            name="Mauerziegel", lambda_value=0.79, density=1800, 
            specific_heat=1000, vapor_diffusion=5.0
        )
        
        materials["concrete"] = Material(
            name="Stahlbeton", lambda_value=2.1, density=2400,
            specific_heat=1000, vapor_diffusion=80.0
        )
        
        # Dämmstoffe
        materials["insulation_eps"] = Material(
            name="EPS-Dämmung", lambda_value=0.035, density=20,
            specific_heat=1500, vapor_diffusion=60.0
        )
        
        materials["insulation_mineral"] = Material(
            name="Mineralwolle", lambda_value=0.035, density=50,
            specific_heat=1000, vapor_diffusion=1.0
        )
        
        materials["insulation_pir"] = Material(
            name="PIR-Dämmung", lambda_value=0.022, density=35,
            specific_heat=1000, vapor_diffusion=100.0
        )
        
        # Putze und Estriche
        materials["plaster_internal"] = Material(
            name="Innenputz", lambda_value=0.87, density=1600,
            specific_heat=1000, vapor_diffusion=8.0
        )
        
        materials["plaster_external"] = Material(
            name="Außenputz", lambda_value=0.87, density=1800,
            specific_heat=1000, vapor_diffusion=15.0
        )
        
        materials["screed"] = Material(
            name="Estrich", lambda_value=1.4, density=2100,
            specific_heat=1000, vapor_diffusion=20.0
        )
        
        # Holz
        materials["wood_construction"] = Material(
            name="Konstruktionsholz", lambda_value=0.13, density=500,
            specific_heat=1600, vapor_diffusion=20.0
        )
        
        return materials
    
    def _create_standard_constructions(self) -> Dict[str, List[Layer]]:
        """Erstellt Standard-Wandaufbauten nach GEG"""
        constructions = {}
        
        # Außenwand - GEG Standard (U ≤ 0.28 W/(m²·K))
        constructions["external_wall_geg"] = [
            Layer(self.standard_materials["plaster_internal"], 0.015),
            Layer(self.standard_materials["brick"], 0.175),
            Layer(self.standard_materials["insulation_eps"], 0.14),
            Layer(self.standard_materials["plaster_external"], 0.02)
        ]
        
        # Außenwand - Passivhaus Standard (U ≤ 0.15 W/(m²·K))
        constructions["external_wall_passive"] = [
            Layer(self.standard_materials["plaster_internal"], 0.015),
            Layer(self.standard_materials["brick"], 0.175),
            Layer(self.standard_materials["insulation_mineral"], 0.24),
            Layer(self.standard_materials["plaster_external"], 0.02)
        ]
        
        # Dach - GEG Standard (U ≤ 0.20 W/(m²·K))
        constructions["roof_geg"] = [
            Layer(self.standard_materials["plaster_internal"], 0.015),
            Layer(self.standard_materials["wood_construction"], 0.04),
            Layer(self.standard_materials["insulation_mineral"], 0.20),
            Layer(self.standard_materials["wood_construction"], 0.025)
        ]
        
        # Bodenplatte - GEG Standard (U ≤ 0.30 W/(m²·K))
        constructions["floor_slab_geg"] = [
            Layer(self.standard_materials["screed"], 0.06),
            Layer(self.standard_materials["insulation_eps"], 0.14),
            Layer(self.standard_materials["concrete"], 0.20)
        ]
        
        return constructions
    
    def add_component(self, component: Union[DetailedWall, DetailedWindow, DetailedDoor,
                                          DetailedRoof, DetailedFloor, HeatingElement,
                                          ThermalBridge, ShadingElement]) -> str:
        """Fügt Komponente hinzu und gibt ID zurück"""
        self.components[component.id] = component
        return component.id
    
    def get_component(self, component_id: str) -> Optional[Union[DetailedWall, DetailedWindow, DetailedDoor,
                                                                DetailedRoof, DetailedFloor, HeatingElement,
                                                                ThermalBridge, ShadingElement]]:
        """Gibt Komponente nach ID zurück"""
        return self.components.get(component_id)
    
    def remove_component(self, component_id: str) -> bool:
        """Entfernt Komponente"""
        if component_id in self.components:
            del self.components[component_id]
            return True
        return False
    
    def get_components_by_type(self, component_type: ComponentType) -> List[Union[DetailedWall, DetailedWindow, DetailedDoor,
                                                                                DetailedRoof, DetailedFloor, HeatingElement,
                                                                                ThermalBridge, ShadingElement]]:
        """Gibt alle Komponenten eines bestimmten Typs zurück"""
        result = []
        for component in self.components.values():
            if isinstance(component, DetailedWall) and component_type == ComponentType.WALL:
                result.append(component)
            elif isinstance(component, DetailedWindow) and component_type == ComponentType.WINDOW:
                result.append(component)
            elif isinstance(component, DetailedDoor) and component_type == ComponentType.DOOR:
                result.append(component)
            elif isinstance(component, DetailedRoof) and component_type == ComponentType.ROOF:
                result.append(component)
            elif isinstance(component, DetailedFloor) and component_type == ComponentType.FLOOR:
                result.append(component)
            elif isinstance(component, HeatingElement) and component_type == ComponentType.RADIATOR:
                result.append(component)
            elif isinstance(component, ThermalBridge) and component_type == ComponentType.THERMAL_BRIDGE:
                result.append(component)
            elif isinstance(component, ShadingElement) and component_type == ComponentType.SHADING:
                result.append(component)
        
        return result
    
    def calculate_total_heat_loss(self, indoor_temp: float = 20.0, outdoor_temp: float = -12.0) -> Dict[str, float]:
        """Berechnet Gesamtwärmeverluste nach DIN EN 12831"""
        delta_t = indoor_temp - outdoor_temp
        losses = {
            "transmission_walls": 0.0,
            "transmission_windows": 0.0,
            "transmission_doors": 0.0,
            "transmission_roof": 0.0,
            "transmission_floor": 0.0,
            "thermal_bridges": 0.0,
            "total_transmission": 0.0
        }
        
        # Transmissionsverluste Wände
        for wall in self.get_components_by_type(ComponentType.WALL):
            if wall.u_value is None:
                wall.calculate_u_value()
            losses["transmission_walls"] += wall.area * wall.u_value * delta_t
        
        # Transmissionsverluste Fenster
        for window in self.get_components_by_type(ComponentType.WINDOW):
            losses["transmission_windows"] += window.area * window.u_value * delta_t
        
        # Transmissionsverluste Türen
        for door in self.get_components_by_type(ComponentType.DOOR):
            losses["transmission_doors"] += door.area * door.u_value * delta_t
        
        # Transmissionsverluste Dach
        for roof in self.get_components_by_type(ComponentType.ROOF):
            if roof.u_value is None:
                roof.calculate_u_value()
            losses["transmission_roof"] += roof.area * roof.u_value * delta_t
        
        # Transmissionsverluste Boden
        for floor in self.get_components_by_type(ComponentType.FLOOR):
            if floor.u_value is None:
                floor.calculate_u_value()
            losses["transmission_floor"] += floor.area * floor.u_value * delta_t
        
        # Wärmebrücken
        for bridge in self.get_components_by_type(ComponentType.THERMAL_BRIDGE):
            losses["thermal_bridges"] += bridge.calculate_heat_loss(delta_t)
        
        # Gesamttransmissionsverluste
        losses["total_transmission"] = sum([
            losses["transmission_walls"],
            losses["transmission_windows"],
            losses["transmission_doors"],
            losses["transmission_roof"],
            losses["transmission_floor"],
            losses["thermal_bridges"]
        ])
        
        return losses
    
    def get_building_3d_data(self) -> Dict:
        """Konvertiert Gebäudekomponenten zu 3D-Darstellungsdaten"""
        data = {
            "walls": [],
            "windows": [],
            "doors": [],
            "roof": None,
            "floor": None,
            "radiators": [],
            "thermal_bridges": [],
            "shading": []
        }
        
        # Wände
        for wall in self.get_components_by_type(ComponentType.WALL):
            if wall.u_value is None:
                wall.calculate_u_value()
                
            data["walls"].append({
                "id": wall.id,
                "name": wall.name,
                "area": wall.area,
                "width": wall.width,
                "height": wall.height,
                "orientation": wall.orientation,
                "u_value": wall.u_value,
                "position": {
                    "x": wall.position.x,
                    "y": wall.position.y,
                    "z": wall.position.z,
                    "rotation": wall.position.rotation_z
                },
                "is_external": wall.is_external,
                "is_load_bearing": wall.is_load_bearing,
                "layers": [
                    {
                        "material": layer.material.name,
                        "thickness": layer.thickness,
                        "lambda": layer.material.lambda_value
                    } for layer in wall.layers
                ]
            })
        
        # Fenster
        for window in self.get_components_by_type(ComponentType.WINDOW):
            data["windows"].append({
                "id": window.id,
                "name": window.name,
                "area": window.area,
                "width": window.width,
                "height": window.height,
                "orientation": window.orientation,
                "u_value": window.u_value,
                "g_value": window.g_value,
                "position": {
                    "x": window.position.x,
                    "y": window.position.y,
                    "z": window.position.z
                },
                "glazing_type": window.glazing_type,
                "frame_u_value": window.frame_u_value,
                "is_openable": window.is_openable
            })
        
        # Türen
        for door in self.get_components_by_type(ComponentType.DOOR):
            data["doors"].append({
                "id": door.id,
                "name": door.name,
                "area": door.area,
                "width": door.width,
                "height": door.height,
                "orientation": door.orientation,
                "u_value": door.u_value,
                "position": {
                    "x": door.position.x,
                    "y": door.position.y,
                    "z": door.position.z
                },
                "door_type": door.door_type,
                "material": door.material,
                "is_main_entrance": door.is_main_entrance
            })
        
        # Dach
        roofs = self.get_components_by_type(ComponentType.ROOF)
        if roofs:
            roof = roofs[0]  # Erstes Dach nehmen
            if roof.u_value is None:
                roof.calculate_u_value()
                
            data["roof"] = {
                "id": roof.id,
                "name": roof.name,
                "area": roof.area,
                "tilt": roof.tilt,
                "orientation": roof.orientation,
                "u_value": roof.u_value,
                "position": {
                    "x": roof.position.x,
                    "y": roof.position.y,
                    "z": roof.position.z
                },
                "roof_type": roof.roof_type,
                "has_attic": roof.has_attic,
                "pv_suitable": roof.pv_suitable,
                "pv_area_available": roof.pv_area_available
            }
        
        # Boden
        floors = self.get_components_by_type(ComponentType.FLOOR)
        if floors:
            floor = floors[0]  # Ersten Boden nehmen
            if floor.u_value is None:
                floor.calculate_u_value()
                
            data["floor"] = {
                "id": floor.id,
                "name": floor.name,
                "area": floor.area,
                "u_value": floor.u_value,
                "position": {
                    "x": floor.position.x,
                    "y": floor.position.y,
                    "z": floor.position.z
                },
                "floor_type": floor.floor_type,
                "ground_coupling": floor.ground_coupling,
                "has_underfloor_heating": floor.has_underfloor_heating
            }
        
        # Heizkörper
        for radiator in self.get_components_by_type(ComponentType.RADIATOR):
            data["radiators"].append({
                "id": radiator.id,
                "name": radiator.name,
                "heating_power": radiator.heating_power,
                "position": {
                    "x": radiator.position.x,
                    "y": radiator.position.y,
                    "z": radiator.position.z
                },
                "dimensions": {
                    "width": radiator.width,
                    "height": radiator.height,
                    "depth": radiator.depth
                },
                "radiator_type": radiator.radiator_type,
                "supply_temp": radiator.supply_temp,
                "return_temp": radiator.return_temp,
                "has_thermostatic_valve": radiator.has_thermostatic_valve
            })
        
        return data

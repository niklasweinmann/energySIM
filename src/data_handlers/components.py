"""
Komponenten-Daten-Handler für energyOS.
Lädt und verwaltet Daten von PV-Modulen, Wechselrichtern und Wärmepumpen.
"""

import json
import os
from dataclasses import dataclass
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)

@dataclass
class PVModule:
    manufacturer: str
    model: str
    peak_power: float
    efficiency: float
    area: float
    temp_coefficient: float
    noct: float
    warranty_years: int
    datasheet_url: str

@dataclass
class Inverter:
    manufacturer: str
    model: str
    nominal_ac_power: float
    max_dc_power: float
    euro_efficiency: float
    max_efficiency: float
    mppt_channels: int
    voltage_range: tuple[float, float]
    warranty_years: int
    datasheet_url: str

@dataclass
class HeatPump:
    manufacturer: str
    model: str
    nominal_heating_power: float
    cop_data: Dict[str, float]
    min_outdoor_temp: float
    max_flow_temp: float
    refrigerant: str
    sound_power: float
    warranty_years: int
    datasheet_url: str

class ComponentsDatabase:
    """Verwaltet die Komponenten-Datenbank für energyOS."""
    
    def __init__(self, components_dir: Optional[str] = None):
        if components_dir is None:
            # Projektverzeichnis ermitteln
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            components_dir = os.path.join(project_root, "data", "components")
            
        self.components_dir = components_dir
        self.pv_modules: Dict[str, PVModule] = {}
        self.inverters: Dict[str, Inverter] = {}
        self.heat_pumps: Dict[str, HeatPump] = {}
        
        self._load_components()
    
    def _load_components(self):
        """Lädt alle Komponenten aus den JSON-Dateien."""
        # PV-Module laden
        pv_modules_path = os.path.join(self.components_dir, "pv_modules.json")
        if os.path.exists(pv_modules_path):
            with open(pv_modules_path, 'r') as f:
                data = json.load(f)
                for key, module_data in data['modules'].items():
                    self.pv_modules[key] = PVModule(**module_data)
        
        # Wechselrichter laden
        inverters_path = os.path.join(self.components_dir, "inverters.json")
        if os.path.exists(inverters_path):
            with open(inverters_path, 'r') as f:
                data = json.load(f)
                for key, inverter_data in data['inverters'].items():
                    self.inverters[key] = Inverter(**inverter_data)
        
        # Wärmepumpen laden
        heat_pumps_path = os.path.join(self.components_dir, "heat_pumps.json")
        if os.path.exists(heat_pumps_path):
            with open(heat_pumps_path, 'r') as f:
                data = json.load(f)
                for key, hp_data in data['heat_pumps'].items():
                    self.heat_pumps[key] = HeatPump(**hp_data)
    
    def get_pv_module(self, key: str) -> Optional[PVModule]:
        """Gibt ein PV-Modul anhand seines Schlüssels zurück."""
        return self.pv_modules.get(key)
    
    def get_inverter(self, key: str) -> Optional[Inverter]:
        """Gibt einen Wechselrichter anhand seines Schlüssels zurück."""
        return self.inverters.get(key)
    
    def get_heat_pump(self, key: str) -> Optional[HeatPump]:
        """Gibt eine Wärmepumpe anhand ihres Schlüssels zurück."""
        return self.heat_pumps.get(key)
    
    def list_pv_modules(self) -> list[str]:
        """Listet alle verfügbaren PV-Module auf."""
        return list(self.pv_modules.keys())
    
    def list_inverters(self) -> list[str]:
        """Listet alle verfügbaren Wechselrichter auf."""
        return list(self.inverters.keys())
    
    def list_heat_pumps(self) -> list[str]:
        """Listet alle verfügbaren Wärmepumpen auf."""
        return list(self.heat_pumps.keys())

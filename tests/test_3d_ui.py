#!/usr/bin/env python3
"""
Teste die 3D-Benutzeroberfläche
"""

import sys
import os
from pathlib import Path

# Projektpfad hinzufügen
project_root = Path(__file__).parent
sys.path.append(str(project_root))

def test_3d_ui():
    """Teste die 3D-UI Komponenten"""
    
    print("🧪 Teste 3D-Benutzeroberfläche...")
    
    try:
        # Teste Web-App Import
        from src.ui.web_app import app, building_manager
        print("✓ Web-App erfolgreich importiert")
        
        # Teste Building Manager
        test_building = building_manager.create_default_building()
        print(f"✓ Test-Gebäude erstellt: {test_building.properties.volume}m³")
        
        # Teste 3D-Datenkonvertierung
        building_3d_data = building_manager.building_to_3d_data(test_building)
        print(f"✓ 3D-Daten generiert: {len(building_3d_data['geometry']['walls'])} Wände")
        
        # Teste API-Endpunkte
        with app.test_client() as client:
            # Teste /api/building/load
            response = client.get('/api/building/load')
            print(f"✓ /api/building/load: {response.status_code}")
            
            # Teste Hauptseite
            response = client.get('/')
            print(f"✓ Hauptseite: {response.status_code}")
        
        print("🎉 Alle Tests erfolgreich!")
        return True
        
    except Exception as e:
        print(f"❌ Test fehlgeschlagen: {e}")
        return False

def test_integration():
    """Teste Integration mit energyOS Core"""
    
    print("\n🔗 Teste Integration mit energyOS Core...")
    
    try:
        # Teste Simulation
        from src.main import run_simulation
        
        results = run_simulation(
            latitude=52.52,
            longitude=13.41,
            building_type="single_family",
            heated_area=150,
            start_date="2025-01-01",
            end_date="2025-01-02",
            save_output=False,
            create_plot=False
        )
        
        print(f"✓ Simulation erfolgreich: {results.get('heat_demand_kWh', 0):.1f} kWh Wärmebedarf")
        print(f"  Verfügbare Schlüssel: {list(results.keys())}")
        
        # Teste Gebäudemodell
        from src.core.building import Building, BuildingProperties, Wall, Window, Roof, Floor
        
        # Erstelle Testgebäude
        walls = [Wall(area=30.0, orientation='S', layers=[(0.2, 0.035)])]
        windows = [Window(area=8.0, u_value=1.1, g_value=0.6, orientation='S', 
                         shading_factor=0.7, frame_factor=0.7)]
        roof = Roof(area=100.0, tilt=30.0, layers=[(0.3, 0.035)])
        floor = Floor(area=100.0, layers=[(0.2, 0.035)], ground_coupling=True)
        
        properties = BuildingProperties(
            walls=walls, windows=windows, roof=roof, floor=floor,
            volume=300.0, infiltration_rate=0.5, thermal_mass=165.0
        )
        
        building = Building(properties)
        print(f"✓ Gebäudemodell erstellt: U-Wert Wand = {building.u_values['wall_0']:.3f} W/(m²K)")
        
        print("🎉 Integration erfolgreich!")
        return True
        
    except Exception as e:
        print(f"❌ Integration fehlgeschlagen: {e}")
        return False

def main():
    """Hauptfunktion für Tests"""
    
    print("🏠 energyOS 3D-UI Tests")
    print("=" * 40)
    
    success = True
    
    # Teste 3D-UI
    if not test_3d_ui():
        success = False
    
    # Teste Integration
    if not test_integration():
        success = False
    
    print("\n" + "=" * 40)
    if success:
        print("🎉 Alle Tests erfolgreich!")
        print("💡 Starten Sie die 3D-UI mit: python run_3d_editor.py")
    else:
        print("❌ Einige Tests sind fehlgeschlagen")
        print("💡 Prüfen Sie die Fehlerausgaben oben")

if __name__ == '__main__':
    main()

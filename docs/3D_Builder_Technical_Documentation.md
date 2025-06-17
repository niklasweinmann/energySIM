# 3D-Gebäudemodellierung - Technische Dokumentation

## Architektur-Überblick

Das 3D-Gebäudemodellierungssystem besteht aus mehreren integrierten Komponenten:

```
┌─ Frontend (Browser) ─────────────────────────────────┐
│  ┌─ building_editor.html ─────┐  ┌─ CSS Styles ─────┐ │
│  │  • UI Layout              │  │  • Toolbar Design │ │
│  │  • Event Handling         │  │  • Responsive UI  │ │
│  │  • Performance Display    │  │  • Animations    │ │
│  └───────────────────────────┘  └──────────────────┘ │
│  ┌─ building_editor.js ──────────────────────────┐ │
│  │  • Three.js Integration   • Smart Snapping       │ │
│  │  • Drag & Drop System     • Component Management │ │
│  │  • Ghost Objects          • Real-time Validation │ │
│  │  • Snap Detection         • Physics Calculations │ │
│  └────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
                               │
                               ▼ HTTP/API
┌─ Backend (Python/Flask) ────────────────────────────────┐
│  ┌─ web_app.py ─────────────────────────────────────────┐ │
│  │  • API Endpoints          • Building3DManager      │ │
│  │  • Data Validation        • Component Conversion   │ │
│  │  • Performance Calc       • Norm Validation        │ │
│  └────────────────────────────────────────────────────┘ │
│  ┌─ Core Integration ─────────────────────────────────┐ │
│  │  • DetailedBuildingManager • Thermal Calculations │ │
│  │  • Component Classes       • Export Functions     │ │
│  └────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

## Neue Dateien und Funktionen

### Frontend-Komponenten

#### `building_editor.js`
**Hauptklasse**: `Advanced3DBuilder`

**Kernfunktionen**:
- **Drag & Drop System**: Intuitive Bauteil-Platzierung
- **Smart Snapping**: Automatische Verbindung von Bauteilen
- **Ghost Objects**: Vorschau beim Platzieren
- **Real-time Physics**: Live-Berechnung der thermischen Performance

**Wichtige Methoden**:
```javascript
// Initialisierung
constructor(containerId)
init()

// Bauteil-Management  
startGhostMode(toolType)
placeTool()
createBuildingComponent(toolType, position)

// Snapping-System
applySnapping(position, toolType)
findNearestWall(position)
updateSnapTargets()

// Performance
calculateThermalPerformance()
updateBuildingPhysics()
```

#### `building_editor.css`
**Features**:
- Responsive Toolbar-Design
- Drag & Drop Visual Feedback
- Performance-Indikator-Styling
- Accessibility-optimiert

### Backend-Erweiterungen

#### `web_app.py` - Neue API-Endpunkte

```python
# Neue Routen
@app.route('/advanced-3d-builder')                    # UI-Route
@app.route('/api/3d-builder/components')              # Verfügbare Komponenten
@app.route('/api/3d-builder/save-building')           # Gebäude speichern
@app.route('/api/3d-builder/load-building/<id>')      # Gebäude laden
@app.route('/api/3d-builder/calculate-performance')   # Performance berechnen
@app.route('/api/3d-builder/validate-building')       # Normvalidierung
```

#### `Building3DManager` - Erweiterte Klasse

**Neue Methoden**:
```python
def save_building_from_3d(building_data)     # 3D → Building-Objekte
def load_building_for_3d(building_id)        # Building → 3D-Format
def calculate_thermal_performance(data)      # Thermische Berechnung
def validate_building(data)                  # Normvalidierung

# Komponenten-Konverter
def _create_wall_from_3d(component, props, pos)
def _create_window_from_3d(component, props, pos)
def _create_door_from_3d(component, props, pos)
```

## Technische Innovationen

### 1. **Intelligentes Snapping-System**

```javascript
// Automatische Erkennung von Verbindungspunkten
updateSnapTargets() {
    this.snapTargets = [];
    
    // Wand-Verbindungspunkte
    this.buildingData.walls.forEach(wall => {
        const corners = this.getWallCorners(wall);
        corners.forEach(corner => {
            this.snapTargets.push({
                type: 'wall-corner',
                position: corner,
                wall: wall
            });
        });
    });
}

// Snap-Anwendung nach Bauteil-Typ
applySnapping(position, toolType) {
    switch (toolType) {
        case 'window':
        case 'door':
            return this.snapToWallSurface(position);
        case 'roof':
            return this.snapToWallTop(position);
        default:
            return this.snapToGrid(position);
    }
}
```

### 2. **Anti-Wärmebrücken-System**

```javascript
// Automatische Verbindungsvalidierung
validateConnection(componentA, componentB) {
    const connection = this.analyzeConnection(componentA, componentB);
    
    if (connection.hasThermalBridge) {
        this.showThermalBridgeWarning(connection);
        return false;
    }
    
    return true;
}

// Optimierte Verbindungsvorschläge
suggestOptimalConnection(component, targetSurface) {
    const suggestions = [];
    
    // Berechne optimale Position ohne Wärmebrücke
    const optimalPos = this.calculateThermalOptimalPosition(
        component, targetSurface
    );
    
    suggestions.push({
        position: optimalPos,
        reason: 'Minimiert Wärmebrücken',
        thermalBenefit: 0.15 // W/m²K Verbesserung
    });
    
    return suggestions;
}
```

### 3. **Echtzeit-Performance-Berechnung**

```javascript
// Live-Berechnung bei jeder Änderung
updateBuildingPhysics() {
    const performance = this.calculateThermalPerformance();
    this.updateThermalVisualization();
    this.checkThermalBridges();
    this.updateUI(performance);
}

// Detaillierte thermische Analyse
calculateThermalPerformance() {
    let totalHeatLoss = 0;
    let totalArea = 0;
    
    // Analysiere jede Komponente
    this.buildingData.components.forEach(component => {
        const analysis = this.analyzeComponent(component);
        totalHeatLoss += analysis.heatLoss;
        totalArea += analysis.area;
    });
    
    return {
        averageUValue: totalHeatLoss / totalArea,
        energyClass: this.calculateEnergyClass(totalHeatLoss / totalArea),
        heatingDemand: this.estimateHeatingDemand(totalHeatLoss),
        co2Emissions: this.calculateCO2Emissions(totalHeatLoss)
    };
}
```

### 4. **Normgerechte Validierung**

```python
def validate_building(self, building_data):
    """Umfassende Validierung nach deutschen Normen"""
    
    validation = {
        'enev_compliance': self.check_enev_compliance(building_data),
        'din_4108_compliance': self.check_din_4108(building_data),
        'thermal_bridges': self.analyze_thermal_bridges(building_data),
        'air_tightness': self.estimate_air_tightness(building_data),
        'recommendations': self.generate_recommendations(building_data)
    }
    
    return validation

def check_enev_compliance(self, building_data):
    """Prüfung gegen EnEV-Anforderungen"""
    requirements = {
        'wall_max_u': 0.28,      # W/m²K
        'window_max_u': 1.3,     # W/m²K  
        'roof_max_u': 0.20,      # W/m²K
        'floor_max_u': 0.35      # W/m²K
    }
    
    violations = []
    
    for component in building_data['components']:
        u_value = component['properties'].get('uValue', 0)
        comp_type = component['type']
        
        if comp_type in requirements:
            max_u = requirements[f'{comp_type}_max_u']
            if u_value > max_u:
                violations.append({
                    'component': component['id'],
                    'type': comp_type,
                    'actual_u': u_value,
                    'required_u': max_u,
                    'severity': 'error' if u_value > max_u * 1.2 else 'warning'
                })
    
    return {
        'compliant': len(violations) == 0,
        'violations': violations
    }
```

## Integration in energyOS

### 1. **Datenfluss**

```
3D-Editor → API → Building3DManager → DetailedBuildingManager → Simulation
    ↑                                                                ↓
    └─────────────── Feedback & Optimization ←──────────────────────┘
```

### 2. **Komponenten-Mapping**

```python
# 3D-Komponente → energyOS Building-Objekt
component_mapping = {
    'wall': DetailedWall,
    'window': DetailedWindow, 
    'door': DetailedDoor,
    'roof': DetailedRoof,
    'floor': DetailedFloor
}
```

### 3. **Export-Integration**

```javascript
// Export für weitere Verarbeitung
exportBuildingData() {
    return {
        // Für energyOS-Simulationen
        components: this.convertToEnergyOSFormat(),
        
        // Für externe Tools (IFC, gbXML)
        geometry: this.extractGeometry(),
        
        // Für Berechnungen
        thermal_properties: this.getThermalProperties(),
        
        // Metadaten
        metadata: {
            created: new Date().toISOString(),
            tool: 'Advanced3DBuilder',
            version: '1.0',
            standards: ['EnEV', 'DIN4108', 'DIN18599']
        }
    };
}
```

## Performance-Optimierungen

### 1. **3D-Rendering**
- **Level-of-Detail**: Automatische Vereinfachung bei Entfernung
- **Frustum Culling**: Nur sichtbare Objekte rendern
- **Instanced Rendering**: Wiederverwendung gleicher Geometrien

### 2. **Berechnungs-Optimierung**
- **Lazy Loading**: Berechnungen nur bei Änderungen  
- **Caching**: Zwischenspeicherung von Ergebnissen
- **Web Workers**: Schwere Berechnungen im Hintergrund

### 3. **Speicher-Management**
- **Object Pooling**: Wiederverwendung von 3D-Objekten
- **Garbage Collection**: Explizite Freigabe ungenutzter Objekte
- **Texture Sharing**: Gemeinsame Nutzung von Materialien

## Erweiterungsmöglichkeiten

### 1. **Zusätzliche Bauteile**
- Treppen und Aufzüge
- Balkone und Terrassen
- Wintergärten
- Garagen und Nebengebäude

### 2. **Erweiterte Physik**
- Statische Berechnungen
- Windlast-Simulation
- Erdbebensicherheit
- Brandschutz-Validierung

### 3. **BIM-Integration**
- IFC-Import/Export
- gbXML-Unterstützung
- Revit-Plugin
- AutoCAD-Schnittstelle

### 4. **KI-Unterstützung**
- Automatische Gebäude-Generierung
- Optimierungsvorschläge
- Erkennung von Konstruktionsfehlern
- Kostenschätzung

## Deployment

### Entwicklungsumgebung
```bash
# Frontend
cd src/ui/static
# Keine zusätzlichen Dependencies - Pure JavaScript + Three.js CDN

# Backend  
cd src/ui
pip install flask flask-cors numpy
python web_app.py
```

### Produktionsumgebung
```bash
# Static Files optimieren
# CSS/JS minifizieren
# Three.js lokal hosten für bessere Performance
# Gzip-Kompression aktivieren
```

## Testing

### Unit Tests
```javascript
// JavaScript Tests (Jest)
describe('Advanced3DBuilder', () => {
    test('should create ghost object correctly', () => {
        const builder = new Advanced3DBuilder('test-div');
        const ghost = builder.createGhostObject('wall');
        expect(ghost.userData.toolType).toBe('wall');
    });
});
```

### Integration Tests  
```python
# Python Tests (pytest)
def test_save_building_from_3d():
    manager = Building3DManager()
    building_data = create_test_building()
    building_id = manager.save_building_from_3d(building_data)
    assert building_id is not None
```

### End-to-End Tests
```javascript
// Playwright/Selenium Tests
test('complete building workflow', async () => {
    await page.goto('/advanced-3d-builder');
    
    // Drag wall from toolbar
    await page.dragAndDrop('.tool-item[data-tool="wall"]', '#building-3d');
    
    // Verify wall is placed
    const components = await page.evaluate(() => window.advanced3DBuilder.buildingData.components.size);
    expect(components).toBe(1);
});
```

---

*Diese Dokumentation wird kontinuierlich aktualisiert. Für Implementierungsdetails siehe Quellcode-Kommentare.*

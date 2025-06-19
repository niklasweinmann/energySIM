/**
 * Schlanker 3D Builder für energyOS
 * Optimiert für minimale CPU-Last
 */

// Debug-Logging
function debugLog(message, type = 'info') {
    const timestamp = new Date().toLocaleTimeString();
    const typeLabel = {
        'info': '[INFO]',
        'warn': '[WARN]',
        'error': '[ERROR]',
        'success': '[SUCCESS]'
    }[type] || '[LOG]';
    
    console.log(`${timestamp} ${typeLabel} ${message}`);
    
    // Debug-Panel-Output wenn vorhanden
    const debugContent = document.getElementById('debug-content');
    if (debugContent) {
        const entry = document.createElement('div');
        entry.className = `debug-log-entry ${type}`;
        entry.textContent = `${timestamp} ${typeLabel} ${message}`;
        debugContent.appendChild(entry);
        debugContent.scrollTop = debugContent.scrollHeight;
        
        // Limitiere Einträge auf 50
        const entries = debugContent.querySelectorAll('.debug-log-entry');
        if (entries.length > 50) {
            for (let i = 0; i < entries.length - 50; i++) {
                entries[i].remove();
            }
        }
    }
}

// Einfacher 3D Builder
class Simple3DBuilder {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        this.scene = null;
        this.camera = null;
        this.renderer = null;
        this.controls = null;
        this.currentTool = 'select';
        this.needsRender = false;
        this.isAnimating = false;
        
        // Bearbeitungsmodus
        this.editMode = false;
        this.selectedObject = null;
        this.ghostObject = null;
        this.isDragging = false;
        this.moveMode = false;
        this.snapMode = true; // Standardmäßig aktiviert
        this.snapDistance = 50; // Snap-Distanz in cm (erhöht für bessere Erkennbarkeit)
        this.mouse = new THREE.Vector2();
        this.raycaster = new THREE.Raycaster();
        this.dragStart = new THREE.Vector2();
        this.justDragged = false;
        
        // Ghost-Fenster System für Live-Vorschau
        this.ghostWindow = null;
        this.ghostDoor = null;
        this.currentGhost = null;
        this.targetWall = null;
        this.originalWallGeometry = null;
        this.isGhostDragging = false;
        this.wallHoles = new Map(); // Speichert Löcher pro Wand
        this.dragPlane = new THREE.Plane(); // Ebene für Drag-Bewegung
        
        // Standardwerte für Komponenten
        this.componentDefaults = {
            wall: { width: 300, height: 250, depth: 20, uValue: 0.18 },
            door: { width: 90, height: 200, depth: 5, uValue: 1.2 },
            window: { width: 120, height: 120, depth: 5, uValue: 0.9 },
            roof: { width: 400, height: 20, depth: 400, uValue: 0.14 },
            floor: { width: 400, height: 20, depth: 400, uValue: 0.25 }
        };
        
        this.firstPlacementDone = false;

        this.init();
    }
    
    init() {
        debugLog('Initialisiere 3D-Builder...', 'info');
        
        try {
            this.setupScene();
            this.setupCamera();
            this.setupRenderer();
            this.setupControls();
            this.setupGrid();
            this.setupLighting();
            this.setupEventListeners();
            this.startRenderLoop();
            
            // UI-Elemente initial konfigurieren
            setTimeout(() => {
                this.updateInitialUI();
            }, 100);
            
            debugLog('3D-Builder erfolgreich initialisiert', 'success');
        } catch (error) {
            debugLog(`Fehler bei Initialisierung: ${error.message}`, 'error');
            throw error;
        }
    }
    
    setupScene() {
        this.scene = new THREE.Scene();
        this.scene.background = new THREE.Color(0xf0f0f0);
        this.scene.fog = new THREE.Fog(0xf0f0f0, 500, 10000);
    }
    
    setupCamera() {
        const width = this.container.clientWidth;
        const height = this.container.clientHeight;
        
        this.camera = new THREE.PerspectiveCamera(50, width / height, 1, 10000);
        this.camera.position.set(500, 800, 1300);
        this.camera.lookAt(0, 0, 0);
    }
    
    setupRenderer() {
        this.renderer = new THREE.WebGLRenderer({ 
            antialias: false, // Deaktiviert für Performance
            alpha: false,
            powerPreference: "high-performance"
        });
        
        // Performance-Optimierungen
        this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
        this.renderer.setSize(this.container.clientWidth, this.container.clientHeight);
        this.renderer.shadowMap.enabled = false; // Schatten deaktiviert für Performance
        this.renderer.outputEncoding = THREE.sRGBEncoding;
        
        this.container.appendChild(this.renderer.domElement);
    }
    
    setupControls() {
        this.controls = new THREE.OrbitControls(this.camera, this.renderer.domElement);
        this.controls.enableDamping = true;
        this.controls.dampingFactor = 0.1;
        this.controls.screenSpacePanning = false;
        this.controls.minDistance = 100;
        this.controls.maxDistance = 5000;
        this.controls.maxPolarAngle = Math.PI / 2;
        
        // Nur rendern wenn sich etwas ändert
        this.controls.addEventListener('change', () => {
            this.needsRender = true;
        });
    }
    
    setupGrid() {
        const gridHelper = new THREE.GridHelper(2000, 100, 0x888888, 0xcccccc);
        gridHelper.position.y = 0;
        this.scene.add(gridHelper);
    }
    
    setupLighting() {
        // Einfache Beleuchtung für Performance
        const ambientLight = new THREE.AmbientLight(0x404040, 0.6);
        this.scene.add(ambientLight);
        
        const directionalLight = new THREE.DirectionalLight(0xffffff, 0.8);
        directionalLight.position.set(100, 100, 50);
        this.scene.add(directionalLight);
    }
    
    setupEventListeners() {
        window.addEventListener('resize', () => this.onWindowResize(), false);
        
        // Mouse events für Bearbeitungsmodus
        this.container.addEventListener('mousedown', (event) => this.onMouseDown(event), false);
        this.container.addEventListener('mousemove', (event) => this.onMouseMove(event), false);
        this.container.addEventListener('mouseup', (event) => this.onMouseUp(event), false);
        this.container.addEventListener('click', (event) => this.onClick(event), false);
    }
    
    startRenderLoop() {
        const animate = () => {
            if (!this.isAnimating) return;
            
            requestAnimationFrame(animate);
            
            if (this.controls) {
                this.controls.update();
            }
            
            // Nur rendern wenn nötig
            if (this.needsRender) {
                this.renderer.render(this.scene, this.camera);
                this.needsRender = false;
            }
        };
        
        this.isAnimating = true;
        this.needsRender = true;
        animate();
    }
    
    onWindowResize() {
        const width = this.container.clientWidth;
        const height = this.container.clientHeight;
        
        this.camera.aspect = width / height;
        this.camera.updateProjectionMatrix();
        
        this.renderer.setSize(width, height);
        this.needsRender = true;
        
        debugLog(`Fenstergröße geändert: ${width}x${height}`, 'info');
    }
    
    // Bearbeitungsmodus Funktionen
    toggleEditMode() {
        this.editMode = !this.editMode;
        debugLog(`Bearbeitungsmodus: ${this.editMode ? 'AN' : 'AUS'}`, 'info');
        
        // UI aktualisieren
        const btn = document.getElementById('edit-mode-btn');
        
        if (this.editMode) {
            btn.classList.add('active');
        } else {
            btn.classList.remove('active');
            // Bereinige Live-Wand-Vorschau beim Beenden des Edit-Modus
            this.cleanupLiveWallPreview();
            this.clearSelection();
            this.clearGhost();
        }
        
        // Text bleibt konstant
        btn.textContent = '✏️ Bearbeiten';
        
        // Tool-Buttons aktivieren/deaktivieren
        this.updateToolButtons();
        
        this.needsRender = true;
    }
    
    setTool(toolType) {
        // Bereinige vorherige Live-Loch-Vorschau
        if (this.currentTool === 'window' || this.currentTool === 'door') {
            this.cleanupLiveWallPreview();
        }
        this.currentTool = toolType;
        this.clearGhost();
        if (this.editMode && toolType !== 'select') {
            this.createGhost(toolType);
            this.showPropertiesPanel(); // Panel für Ghost sofort anzeigen
        } else if (toolType === 'select' && this.selectedObject) {
            this.showPropertiesPanel();
        } else {
            this.hidePropertiesPanel();
        }
        this.updateToolButtons();
        debugLog(`Tool gewechselt zu: ${toolType}`, 'info');
    }
    
    updateToolButtons() {
        const toolButtons = document.querySelectorAll('.tool-btn');
        toolButtons.forEach(btn => {
            btn.classList.remove('active', 'selected');
            
            // Aktiviere/Deaktiviere Buttons basierend auf Edit-Modus
            if (this.editMode) {
                btn.classList.remove('disabled');
                btn.disabled = false;
            } else {
                // Alle Buttons außer "select" deaktivieren
                if (btn.dataset.tool !== 'select') {
                    btn.classList.add('disabled');
                    btn.disabled = true;
                } else {
                    btn.classList.remove('disabled');
                    btn.disabled = false;
                }
            }
            
            if (btn.dataset.tool === this.currentTool) {
                btn.classList.add('active');
            }
            
            // Markiere Button als "selected" wenn entsprechendes Objekt ausgewählt ist
            if (this.selectedObject && btn.dataset.tool === this.selectedObject.userData.type) {
                btn.classList.add('selected');
            }
        });
    }
    
    createGhost(toolType) {
        this.clearGhost();
        const defaults = this.componentDefaults[toolType];
        const geometry = new THREE.BoxGeometry(defaults.width, defaults.height, defaults.depth);
        geometry.translate(defaults.width / 2, defaults.height / 2, defaults.depth / 2);
        const material = new THREE.MeshLambertMaterial({ 
            color: 0x4CAF50, 
            transparent: true, 
            opacity: 0.3 
        });
        this.ghostObject = new THREE.Mesh(geometry, material);
        this.ghostObject.visible = false;
        this.scene.add(this.ghostObject);
        debugLog(`Ghost-Objekt für ${toolType} erstellt`, 'info');
    }
    
    clearGhost() {
        if (this.ghostObject) {
            this.scene.remove(this.ghostObject);
            if (this.ghostObject.geometry) this.ghostObject.geometry.dispose();
            if (this.ghostObject.material) this.ghostObject.material.dispose();
            this.ghostObject = null;
        }
    }
    
    updateMousePosition(event) {
        const rect = this.container.getBoundingClientRect();
        this.mouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
        this.mouse.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;
    }
    
    onMouseDown(event) {
        if (!this.editMode) return;
        this.updateMousePosition(event);
        this.dragStart.copy(this.mouse);
        // Nur im Move-Modus: Drag starten
        if (this.selectedObject && this.moveMode && event.button === 0) {
            this.isDragging = true;
            this.controls.enabled = false;
        }
    }
    
    onMouseMove(event) {
        this.updateMousePosition(event);
        // Ghost-Vorschau für neue Bauteile (nicht select, nicht moveMode)
        if (this.editMode && this.ghostObject && this.currentTool !== 'select' && !this.moveMode) {
            this.raycaster.setFromCamera(this.mouse, this.camera);
            const plane = new THREE.Plane(new THREE.Vector3(0, 1, 0), 0);
            const intersection = new THREE.Vector3();
            if (this.raycaster.ray.intersectPlane(plane, intersection)) {
                let finalPosition = intersection;
                if (this.currentTool === 'window' || this.currentTool === 'door') {
                    const wallProjection = this.projectToNearestWallSurface(intersection);
                    if (wallProjection) {
                        finalPosition = wallProjection.position;
                        this.updateLiveWallHole(wallProjection.wall, finalPosition);
                    }
                } else if (this.currentTool === 'roof') {
                    finalPosition = this.snapAndGlideToWallTops(intersection, this.getAllComponents(), 100, 150) || intersection;
                } else if (this.currentTool === 'floor') {
                    finalPosition = this.snapAndGlideToWallBottoms(intersection, this.getAllComponents(), 100, 150) || intersection;
                } else if (this.currentTool === 'wall' && this.snapMode) {
                    finalPosition = this.snapToNearestWall(intersection, this.currentTool);
                } else if (this.currentTool === 'wall') {
                    finalPosition = intersection;
                }
                this.ghostObject.position.copy(finalPosition);
                this.ghostObject.visible = true;
                this.needsRender = true;
            } else {
                this.ghostObject.visible = false;
            }
        }
        // Nur im Move-Modus: Objekt live bewegen
        if (this.isDragging && this.selectedObject) {
            this.raycaster.setFromCamera(this.mouse, this.camera);
            const plane = new THREE.Plane(new THREE.Vector3(0, 1, 0), this.selectedObject.position.y);
            const intersection = new THREE.Vector3();
            if (this.raycaster.ray.intersectPlane(plane, intersection)) {
                let finalPosition = intersection;
                const componentType = this.selectedObject.userData.type;
                if (componentType === 'window' || componentType === 'door') {
                    if (this.selectedObject.userData.parentWall) {
                        const result = this.constrainToParentWall(intersection, this.selectedObject);
                        if (result) finalPosition = result;
                    }
                } else if (componentType === 'roof') {
                    finalPosition = this.snapAndGlideToWallTops(intersection, this.getAllComponents(), 100, 150) || intersection;
                } else if (componentType === 'floor') {
                    finalPosition = this.snapAndGlideToWallBottoms(intersection, this.getAllComponents(), 100, 150) || intersection;
                } else if (componentType === 'wall' && this.snapMode) {
                    finalPosition = this.snapToNearestWall(intersection, componentType);
                } else if (componentType === 'wall') {
                    finalPosition = intersection;
                }
                this.selectedObject.position.x = finalPosition.x;
                this.selectedObject.position.z = finalPosition.z;
                this.updatePropertiesPanel();
                this.needsRender = true;
            }
        }
    }
    
    onMouseUp(event) {
        if (this.isDragging) {
            this.isDragging = false;
            this.controls.enabled = true;
            this.justDragged = true;
            // Nach Platzierung: Move-Modus aus, Snap bleibt an
            this.moveMode = false;
            if (this.selectedObject && this.selectedObject.material) {
                this.selectedObject.material.transparent = false;
                this.selectedObject.material.opacity = 1.0;
            }
            const btn = document.getElementById('move-btn');
            if (btn) btn.classList.remove('active');
            this.showPropertiesPanel();
            debugLog('Objekt verschoben und Move-Modus beendet', 'info');
            setTimeout(() => { this.justDragged = false; }, 100);
        }
    }
    
    onClick(event) {
        // Vermeide Klick nach Drag
        if (this.justDragged) {
            return;
        }
        this.updateMousePosition(event);
        this.raycaster.setFromCamera(this.mouse, this.camera);
        if (this.currentTool === 'select') {
            // Objekt auswählen (funktioniert immer)
            const intersects = this.raycaster.intersectObjects(this.scene.children, false);
            const clickedObject = intersects.find(i => i.object.userData.isComponent);
            
            if (clickedObject) {
                this.selectObject(clickedObject.object);
            } else {
                this.clearSelection();
            }
        } else if (this.editMode && this.ghostObject && !this.moveMode) {
            // Neues Objekt platzieren an aktueller Ghost-Position
            this.placeComponent(this.currentTool, this.ghostObject.position.clone());
        }
    }
    
    placeComponent(type, position) {
        const defaults = this.componentDefaults[type];
        // Geometrie so verschieben, dass Ursprung in der unteren linken Ecke liegt
        const geometry = new THREE.BoxGeometry(defaults.width, defaults.height, defaults.depth);
        geometry.translate(defaults.width / 2, defaults.height / 2, defaults.depth / 2);
        let color = 0x8BC34A; // Standard grün
        if (type === 'door') color = 0x795548;
        else if (type === 'window') color = 0x2196F3;
        else if (type === 'roof') color = 0x9E9E9E;
        else if (type === 'floor') color = 0x607D8B;
        const material = new THREE.MeshLambertMaterial({ color });
        const component = new THREE.Mesh(geometry, material);
        component.position.copy(position); // Position ist jetzt wirklich die aktuelle Ghost-Position
        // Generiere einen Standard-Namen basierend auf Typ und Anzahl
        const existingComponents = this.getAllComponents().filter(c => c.userData.type === type);
        const defaultName = this.getComponentTypeName(type) + ' ' + (existingComponents.length + 1);
        component.userData = {
            isComponent: true,
            type: type,
            name: defaultName,
            originalColor: color,
            properties: {
                width: defaults.width,
                height: defaults.height,
                depth: defaults.depth,
                uValue: defaults.uValue,
                position: { x: position.x, y: position.y, z: position.z },
                rotation: { x: 0, y: 0, z: 0 }
            }
        };
        this.scene.add(component);
        // Nach Platzierung: Ghost entfernen und auf Auswahl-Tool zurückschalten
        this.clearGhost();
        this.setTool('select'); // Tool nach Platzierung immer auf select
        this.selectObject(component); // Panel für neues Objekt anzeigen
        this.moveMode = false;
        setTimeout(() => {
            const moveBtn = document.getElementById('move-btn');
            if (moveBtn) moveBtn.classList.remove('active');
        }, 0);
        this.updateComponentOverview();
        this.needsRender = true;
        debugLog(`${type} bei (${Math.round(position.x)}, ${Math.round(position.y)}, ${Math.round(position.z)}) platziert`, 'success');
    }
    
    selectObject(object) {
        this.clearSelection();
        
        this.selectedObject = object;
        
        // Highlight-Effekt
        if (object.material.emissive) {
            object.material.emissive.setHex(0x444444);
        }
        
        this.updateToolButtons();
        this.showPropertiesPanel();
        this.needsRender = true;
        
        debugLog(`${object.userData.type} ausgewählt - Properties-Panel sollte angezeigt werden`, 'info');
    }
    
    clearSelection() {
        if (this.selectedObject) {
            // Highlight entfernen
            if (this.selectedObject.material.emissive) {
                this.selectedObject.material.emissive.setHex(0x000000);
            }
            this.selectedObject = null;
            this.hidePropertiesPanel();
            this.needsRender = true;
        }
    }
    
    toggleMoveMode() {
        if (!this.selectedObject) return;
        this.moveMode = !this.moveMode;
        debugLog(`Verschieben-Modus: ${this.moveMode ? 'AN' : 'AUS'}`, 'info');
        this.showPropertiesPanel();
        if (this.selectedObject.material) {
            this.selectedObject.material.transparent = this.moveMode;
            this.selectedObject.material.opacity = this.moveMode ? 0.3 : 1.0;
        }
        // Snap-Button NICHT mehr automatisch aktivieren!
        // (snapMode bleibt wie er ist)
    }
    
    toggleSnapMode() {
        this.snapMode = !this.snapMode;
        debugLog(`Einrasten-Modus: ${this.snapMode ? 'AN' : 'AUS'}`, 'info');
        
        const btn = document.getElementById('snap-btn');
        if (btn) {
            if (this.snapMode) {
                btn.classList.remove('inactive');
            } else {
                btn.classList.add('inactive');
            }
            // Text bleibt konstant
            btn.innerHTML = '🧲 Einrasten';
        }
    }
    
    clearScene() {
        const objectsToRemove = [];
        this.scene.traverse((child) => {
            if (child.isMesh && child.geometry.type === 'BoxGeometry') {
                objectsToRemove.push(child);
            }
        });
        
        objectsToRemove.forEach(obj => {
            this.scene.remove(obj);
            if (obj.geometry) obj.geometry.dispose();
            if (obj.material) obj.material.dispose();
        });
        
        // Bauteilübersicht aktualisieren
        this.updateComponentOverview();
        
        this.needsRender = true;
        debugLog('Szene geleert', 'info');
    }
    
    // Intelligentes Constraint-basiertes Snap-System
    snapToNearestWall(position, componentType) {
        if (!this.snapMode) {
            return position;
        }
        
        const snappedPosition = position.clone();
        const snapDistance = 100;
        const allComponents = this.getAllComponents();
        
        // FENSTER & TÜREN: Nur innerhalb ihrer Mutterwand bewegen
        if (componentType === 'window' || componentType === 'door') {
            if (this.selectedObject && this.selectedObject.userData.constraints) {
                const result = this.constrainToParentWall(position, this.selectedObject);
                if (result) {
                    snappedPosition.set(result.x, result.y, result.z);
                }
            }
        }
        
        // WÄNDE: Entlang anderen Wänden bewegen
        else if (componentType === 'wall') {
            const result = this.snapAndGlideToWallEdge(position, allComponents, snapDistance, 150);
            if (result) {
                snappedPosition.set(result.x, result.y, result.z);
            }
        }
        
        // DÄCHER: Über Wänden bewegen
        else if (componentType === 'roof') {
            const result = this.snapAndGlideToWallTops(position, allComponents, snapDistance, 150);
            if (result) {
                snappedPosition.set(result.x, result.y, result.z);
            }
        }
        
        // BÖDEN: Unter Wänden bewegen
        else if (componentType === 'floor') {
            const result = this.snapAndGlideToWallBottoms(position, allComponents, snapDistance, 150);
            if (result) {
                snappedPosition.set(result.x, result.y, result.z);
            }
        }
        
        return snappedPosition;
    }
    
    dispose() {
        this.isAnimating = false;
        
        if (this.controls) {
            this.controls.dispose();
        }
        
        if (this.renderer) {
            this.renderer.dispose();
        }
        
        debugLog('3D-Builder entsorgt', 'info');
    }
    
    showPropertiesPanel() {
        // Zeige Eigenschaften für Ghost-Objekt, falls vorhanden und kein moveMode
        let obj = this.selectedObject;
        if (this.ghostObject && this.currentTool !== 'select' && !this.moveMode) {
            obj = this.ghostObject;
            obj.userData = obj.userData || { isGhost: true, type: this.currentTool, properties: { ...this.componentDefaults[this.currentTool] } };
        }
        if (!obj) return;
        const panel = document.getElementById('properties-panel');
        const content = document.getElementById('properties-content');
        if (!panel || !content) return;
        const props = obj.userData.properties;
        const type = obj.userData.type;
        const defaults = this.componentDefaults[type];
        const componentName = obj.userData.name || '';
        content.innerHTML = `
            <div class="property-group">
                <div class="property-label">Name</div>
                <input type="text" class="property-input" id="prop-name" value="${componentName}" placeholder="Bauteil-Name eingeben">
            </div>
            <div class="property-group">
                <div class="property-label">Typ</div>
                <div style="font-weight: 500; color: #333;">${type ? type.toUpperCase() : ''}</div>
            </div>
            <div class="property-group">
                <div class="property-label">Abmessungen (cm)</div>
                <div class="property-row">
                    <input type="number" class="property-input" id="prop-width" value="${props.width}" placeholder="Breite">
                    <input type="number" class="property-input" id="prop-height" value="${props.height}" placeholder="Höhe">
                    <input type="number" class="property-input" id="prop-depth" value="${props.depth}" placeholder="Tiefe">
                </div>
            </div>
            <div class="property-group">
                <div class="property-label">U-Wert (W/m²K)</div>
                <input type="number" class="property-input" id="prop-uvalue" value="${props.uValue}" step="0.01" placeholder="U-Wert">
            </div>
            <div class="property-group">
                <div class="property-label">Position (cm)</div>
                <div class="property-row">
                    <input type="number" class="property-input" id="prop-pos-x" value="${Math.round(props.position?.x || 0)}" placeholder="X">
                    <input type="number" class="property-input" id="prop-pos-y" value="${Math.round(props.position?.y || 0)}" placeholder="Y">
                    <input type="number" class="property-input" id="prop-pos-z" value="${Math.round(props.position?.z || 0)}" placeholder="Z">
                </div>
                <div class="position-controls">
                    <button class="move-btn${this.moveMode ? ' active' : ''}" id="move-btn" onclick="toggleMoveMode()">
                        📍 Verschieben
                    </button>
                    <button class="snap-btn${this.snapMode ? '' : ' inactive'}" id="snap-btn" onclick="toggleSnapMode()">
                        🧲 Einrasten
                    </button>
                </div>
            </div>
            <div class="property-group">
                <div class="property-label">Rotation (Grad)</div>
                <div class="property-row">
                    <input type="number" class="property-input" id="prop-rot-x" value="0" placeholder="X">
                    <input type="number" class="property-input" id="prop-rot-y" value="0" placeholder="Y">
                    <input type="number" class="property-input" id="prop-rot-z" value="0" placeholder="Z">
                </div>
            </div>
            <div class="property-actions">
                <button class="delete-btn" onclick="deleteSelectedComponent()">🗑️ Löschen</button>
            </div>
        `;
        this.setDefaultStyles(defaults);
        this.setupAutoUpdate();
        panel.classList.add('open');
        debugLog('Properties-Panel angezeigt', 'success');
    }
    
    hidePropertiesPanel() {
        const panel = document.getElementById('properties-panel');
        if (panel) {
            panel.classList.remove('open');
        }
    }
    
    setDefaultStyles(defaults) {
        const inputs = ['prop-width', 'prop-height', 'prop-depth', 'prop-uvalue'];
        const defaultValues = [defaults.width, defaults.height, defaults.depth, defaults.uValue];
        
        inputs.forEach((id, index) => {
            const input = document.getElementById(id);
            if (input && parseFloat(input.value) === defaultValues[index]) {
                input.classList.add('default');
            }
        });
    }
    
    setupAutoUpdate() {
        const inputs = ['prop-name', 'prop-width', 'prop-height', 'prop-depth', 'prop-uvalue', 
                       'prop-pos-x', 'prop-pos-y', 'prop-pos-z',
                       'prop-rot-x', 'prop-rot-y', 'prop-rot-z'];
        
        inputs.forEach(id => {
            const input = document.getElementById(id);
            if (input) {
                input.addEventListener('input', () => {
                    input.classList.remove('default');
                    this.applyPropertiesAuto();
                });
            }
        });
    }
    
    applyPropertiesAuto() {
        if (!this.selectedObject) return;
        
        const props = this.selectedObject.userData.properties;
        
        // Name
        const name = document.getElementById('prop-name')?.value || '';
        this.selectedObject.userData.name = name;
        
        // Abmessungen
        const width = parseFloat(document.getElementById('prop-width')?.value) || props.width;
        const height = parseFloat(document.getElementById('prop-height')?.value) || props.height;
        const depth = parseFloat(document.getElementById('prop-depth')?.value) || props.depth;
        
        // Position
        const posX = parseFloat(document.getElementById('prop-pos-x')?.value) || props.position.x;
        const posY = parseFloat(document.getElementById('prop-pos-y')?.value) || props.position.y;
        const posZ = parseFloat(document.getElementById('prop-pos-z')?.value) || props.position.z;
        
        // Rotation
        const rotX = (parseFloat(document.getElementById('prop-rot-x')?.value) || 0) * Math.PI / 180;
        const rotY = (parseFloat(document.getElementById('prop-rot-y')?.value) || 0) * Math.PI / 180;
        const rotZ = (parseFloat(document.getElementById('prop-rot-z')?.value) || 0) * Math.PI / 180;
        
        // U-Wert
        const uValue = parseFloat(document.getElementById('prop-uvalue')?.value) || props.uValue;
        
        // Geometrie aktualisieren wenn Abmessungen geändert
        if (width !== props.width || height !== props.height || depth !== props.depth) {
            const newGeometry = new THREE.BoxGeometry(width, height, depth);
            this.selectedObject.geometry.dispose();
            this.selectedObject.geometry = newGeometry;
        }
        
        // Position und Rotation setzen
        this.selectedObject.position.set(posX, posY, posZ);
        this.selectedObject.rotation.set(rotX, rotY, rotZ);
        
        // Properties aktualisieren
        props.width = width;
        props.height = height;
        props.depth = depth;
        props.position = { x: posX, y: posY, z: posZ };
        props.rotation = { x: rotX * 180 / Math.PI, y: rotY * 180 / Math.PI, z: rotZ * 180 / Math.PI };
        props.uValue = uValue;
        
        // Bauteilübersicht aktualisieren (falls Name geändert wurde)
        this.updateComponentOverview();
        
        this.needsRender = true;
    }
    
    updatePropertiesPanel() {
        if (!this.selectedObject) return;
        
        const props = this.selectedObject.userData.properties;
        
        // Position aus 3D-Objekt aktualisieren
        props.position.x = Math.round(this.selectedObject.position.x);
        props.position.y = Math.round(this.selectedObject.position.y);
        props.position.z = Math.round(this.selectedObject.position.z);
        
        // Rotation aus 3D-Objekt aktualisieren
        props.rotation.x = Math.round(this.selectedObject.rotation.x * 180 / Math.PI);
        props.rotation.y = Math.round(this.selectedObject.rotation.y * 180 / Math.PI);
        props.rotation.z = Math.round(this.selectedObject.rotation.z * 180 / Math.PI);
        
        // Input-Felder aktualisieren
        const posX = document.getElementById('prop-pos-x');
        const posY = document.getElementById('prop-pos-y');
        const posZ = document.getElementById('prop-pos-z');
        const rotX = document.getElementById('prop-rot-x');
        const rotY = document.getElementById('prop-rot-y');
        const rotZ = document.getElementById('prop-rot-z');
        
        if (posX) posX.value = props.position.x;
        if (posY) posY.value = props.position.y;
        if (posZ) posZ.value = props.position.z;
        if (rotX) rotX.value = props.rotation.x;
        if (rotY) rotY.value = props.rotation.y;
        if (rotZ) rotZ.value = props.rotation.z;
    }
    
    // Building Management
    getAllComponents() {
        if (!this.scene) return [];
        
        return this.scene.children.filter(child => 
            child.userData && child.userData.isComponent
        );
    }
    
    updateComponentOverview() {
        // Diese Methode wird von der HTML-Seite aufgerufen
        if (typeof updateComponentOverview === 'function') {
            updateComponentOverview();
        }
    }

    deleteSelected() {
        if (this.selectedObject && this.selectedObject.userData.isComponent) {
            const objectToDelete = this.selectedObject;
            
            // Wenn es ein Fenster/Tür ist, setze die Wandfarbe zurück
            if ((objectToDelete.userData.type === 'window' || objectToDelete.userData.type === 'door') 
                && objectToDelete.userData.parentWall) {
                const parentWall = objectToDelete.userData.parentWall;
                parentWall.material.color.setHex(0x8BC34A); // Zurück zu grün
            }
            
            // Das Objekt löschen
            this.scene.remove(objectToDelete);
            if (objectToDelete.geometry) objectToDelete.geometry.dispose();
            if (objectToDelete.material) objectToDelete.material.dispose();
            
            this.clearSelection();
            this.hidePropertiesPanel();
            this.updateComponentOverview();
            this.needsRender = true;
        }
    }

    selectComponentById(componentId) {
        // Suche nach dem Komponenten in der Szene
        const component = this.scene.children.find(child => 
            child.userData && child.userData.isComponent && child.id === componentId
        );
        
        if (component) {
            this.selectObject(component);
        }
    }

    clearAll() {
        // Alle Bauteile löschen
        this.clearScene();
        this.clearSelection();
        this.clearGhost();
        
        // Properties-Panel schließen
        this.hidePropertiesPanel();
        
        // Tool auf "select" zurücksetzen
        this.setTool('select');
        
        debugLog('Gesamtes Gebäude gelöscht', 'info');
    }

    updateInitialUI() {
        // UI-Elemente entsprechend dem initialen editMode aktualisieren
        const btn = document.getElementById('edit-mode-btn');
        
        if (btn) {
            if (this.editMode) {
                btn.classList.add('active');
            } else {
                btn.classList.remove('active');
            }
            // Text bleibt konstant
            btn.textContent = '✏️ Bearbeiten';
        }
        
        // Tool-Buttons initial aktualisieren
        this.updateToolButtons();
        
        // Snap-Button initial konfigurieren (standardmäßig AN)
        const snapBtn = document.getElementById('snap-btn');
        if (snapBtn) {
            if (this.snapMode) {
                snapBtn.classList.remove('inactive');
            } else {
                snapBtn.classList.add('inactive');
            }
            // Text bleibt konstant
            snapBtn.innerHTML = '🧲 Einrasten';
        }
        
        // Move-Button initial konfigurieren
        const moveBtn = document.getElementById('move-btn');
        if (moveBtn) {
            if (this.moveMode) {
                moveBtn.classList.add('active');
            } else {
                moveBtn.classList.remove('active');
            }
            // Text bleibt konstant
            moveBtn.innerHTML = '📍 Verschieben';
        }
    }
    
    getComponentTypeName(type) {
        const names = {
            wall: 'Wand',
            door: 'Tür',
            window: 'Fenster',
            roof: 'Dach',
            floor: 'Boden'
        };
        return names[type] || type;
    }
    
    // Platziere Fenster/Tür mit Live-Loch-Vorschau
    placeOpeningWithLivePreview(type, position, defaults) {
        // Finde die nächste Wand
        const walls = this.getAllComponents().filter(obj => obj.userData.type === 'wall');
        let targetWall = null;
        let minDistance = Infinity;
        
        walls.forEach(wall => {
            const wallPos = wall.position;
            const distance = Math.sqrt(
                Math.pow(position.x - wallPos.x, 2) + 
                Math.pow(position.z - wallPos.z, 2)
            );
            
            if (distance < 200 && distance < minDistance) {
                minDistance = distance;
                targetWall = wall;
            }
        });
        
        if (!targetWall) {
            debugLog(`Keine Wand für ${type} gefunden`, 'warning');
            return null;
        }
        
        // Erstelle Wand mit Live-Loch (ExtrudeGeometry + Shape-Holes)
        return this.createWandWithLiveLoch(targetWall, type, position, defaults);
    }
    
    // Erstelle Wand mit Live-Loch-System
    createWandWithLiveLoch(wall, type, position, defaults) {
        const wallProps = wall.userData;
        const wallPos = wall.position;
        
        // Berechne lokale Koordinaten für das Loch
        const localX = position.x - wallPos.x;
        const localY = position.y - wallPos.y;
        
        // Erstelle Wand-Shape
        const wallShape = new THREE.Shape()
            .moveTo(-wallProps.width / 2, -wallProps.height / 2)
            .lineTo(wallProps.width / 2, -wallProps.height / 2)
            .lineTo(wallProps.width / 2, wallProps.height / 2)
            .lineTo(-wallProps.width / 2, wallProps.height / 2)
            .lineTo(-wallProps.width / 2, -wallProps.height / 2);
        
        // Erstelle Loch-Shape (in lokalen Koordinaten)
        const holeShape = new THREE.Path()
            .moveTo(localX - defaults.width / 2, localY - defaults.height / 2)
            .lineTo(localX + defaults.width / 2, localY - defaults.height / 2)
            .lineTo(localX + defaults.width / 2, localY + defaults.height / 2)
            .lineTo(localX - defaults.width / 2, localY + defaults.height / 2)
            .lineTo(localX - defaults.width / 2, localY - defaults.height / 2);
        
        // Füge Loch zur Wand hinzu
        wallShape.holes = [holeShape];
        
        // Erstelle neue Geometrie mit echtem Loch
        const newGeometry = new THREE.ExtrudeGeometry(wallShape, {
            depth: wallProps.depth,
            bevelEnabled: false
        });
        
        // Ersetze Wand-Geometrie
        const oldGeometry = wall.geometry;
        wall.geometry = newGeometry;
        oldGeometry.dispose();
        
        // Position für das Fenster/die Tür - genau in der Wandmitte
        const finalPosition = new THREE.Vector3(wallPos.x, wallPos.y, wallPos.z);
        
        // Erstelle das Fenster/die Tür
        const openingGeometry = new THREE.BoxGeometry(defaults.width, defaults.height, defaults.depth);
        let color = (type === 'window') ? 0x2196F3 : 0x795548;
        const openingMaterial = new THREE.MeshLambertMaterial({ 
            color, 
            transparent: true, 
            opacity: 0.8 
        });
        const opening = new THREE.Mesh(openingGeometry, openingMaterial);
        
        opening.position.copy(finalPosition);
        
        const existingComponents = this.getAllComponents().filter(c => c.userData.type === type);
        const defaultName = this.getComponentTypeName(type) + ' ' + (existingComponents.length + 1);
        
        opening.userData = {
            isComponent: true,
            type: type,
            name: defaultName,
            originalColor: color,
            parentWall: wall,
            properties: {
                width: defaults.width,
                height: defaults.height,
                depth: defaults.depth,
                uValue: defaults.uValue,
                position: { x: finalPosition.x, y: finalPosition.y, z: finalPosition.z },
                rotation: { x: 0, y: 0, z: 0 }
            }
        };
        
        this.scene.add(opening);
        
        debugLog(`${type} mit echtem Loch in Wand erstellt`, 'success');
        
        return opening;
    }
    
    // Einfache Constraint-Funktion für Fenster/Türen
    constrainToParentWall(position, opening) {
        if (!opening.userData.parentWall) return null;
        
        const wall = opening.userData.parentWall;
        const wallPos = wall.position;
        
        // Halte das Fenster/die Tür nahe der Wand
        return {
            x: wallPos.x,
            y: wallPos.y,
            z: wallPos.z
        };
    }
    
    // Einfache Snap-Funktionen (ohne Gleiten für Performance)
    snapAndGlideToWallEdge(position, allComponents, snapDistance, glideThreshold) {
        const otherWalls = allComponents.filter(obj => obj.userData.type === 'wall' && obj !== this.selectedObject);
        let bestConstraint = null;
        let minDistance = Infinity;
        
        otherWalls.forEach(wall => {
            const wallPos = wall.position;
            const wallWidth = wall.userData.width || this.componentDefaults.wall.width;
            const wallDepth = wall.userData.depth || this.componentDefaults.wall.depth;
            
            // Pivot ist die vordere linke Ecke, daher müssen die Snap-Kanten auf die Außenkanten der Wand bezogen werden
            const pivotOffsetX = (this.selectedObject ? this.selectedObject.userData.width : this.componentDefaults.wall.width) / 2;
            const pivotOffsetZ = (this.selectedObject ? this.selectedObject.userData.depth : this.componentDefaults.wall.depth) / 2;
            const edges = [
                { point: { x: wallPos.x + wallWidth/2, z: wallPos.z }, fixedX: wallPos.x + wallWidth }, // rechte Außenkante
                { point: { x: wallPos.x - wallWidth/2, z: wallPos.z }, fixedX: wallPos.x - wallWidth }, // linke Außenkante
                { point: { x: wallPos.x, z: wallPos.z + wallDepth/2 }, fixedZ: wallPos.z + wallDepth }, // vordere Außenkante
                { point: { x: wallPos.x, z: wallPos.z - wallDepth/2 }, fixedZ: wallPos.z - wallDepth }  // hintere Außenkante
            ];
            
            edges.forEach(edge => {
                const distance = Math.sqrt(
                    Math.pow(position.x - edge.point.x, 2) + 
                    Math.pow(position.z - edge.point.z, 2)
                );
                
                if (distance < snapDistance && distance < minDistance) {
                    minDistance = distance;
                    let constrainedPos = { x: position.x, z: position.z };
                    
                    if (edge.fixedX !== undefined) {
                        constrainedPos.x = edge.fixedX;
                    } else {
                        constrainedPos.z = edge.fixedZ;
                    }
                    
                    bestConstraint = {
                        x: constrainedPos.x,
                        y: wallPos.y,
                        z: constrainedPos.z
                    };
                }
            });
        });
        
        return bestConstraint;
    }
    
    snapAndGlideToWallTops(position, allComponents, snapDistance, glideThreshold) {
        const walls = allComponents.filter(obj => obj.userData.type === 'wall');
        if (walls.length === 0) return null;
        
        let minX = Infinity, maxX = -Infinity, minZ = Infinity, maxZ = -Infinity, maxY = -Infinity;
        
        walls.forEach(wall => {
            const wallPos = wall.position;
            const wallWidth = wall.userData.width || this.componentDefaults.wall.width;
            const wallDepth = wall.userData.depth || this.componentDefaults.wall.depth;
            const wallHeight = wall.userData.height || this.componentDefaults.wall.height;
            
            minX = Math.min(minX, wallPos.x - wallWidth/2);
            maxX = Math.max(maxX, wallPos.x + wallWidth/2);
            minZ = Math.min(minZ, wallPos.z - wallDepth/2);
            maxZ = Math.max(maxZ, wallPos.z + wallDepth/2);
            maxY = Math.max(maxY, wallPos.y + wallHeight/2);
        });
        
        const constrainedX = Math.max(minX, Math.min(maxX, position.x));
        const constrainedZ = Math.max(minZ, Math.min(maxZ, position.z));
        
        return {
            x: constrainedX,
            y: maxY + (this.componentDefaults.roof.height || 20) / 2,
            z: constrainedZ
        };
    }
    
    snapAndGlideToWallBottoms(position, allComponents, snapDistance, glideThreshold) {
        const walls = allComponents.filter(obj => obj.userData.type === 'wall');
        if (walls.length === 0) return null;
        
        let minX = Infinity, maxX = -Infinity, minZ = Infinity, maxZ = -Infinity, minY = Infinity;
        
        walls.forEach(wall => {
            const wallPos = wall.position;
            const wallWidth = wall.userData.width || this.componentDefaults.wall.width;
            const wallDepth = wall.userData.depth || this.componentDefaults.wall.depth;
            const wallHeight = wall.userData.height || this.componentDefaults.wall.height;
            
            minX = Math.min(minX, wallPos.x - wallWidth/2);
            maxX = Math.max(maxX, wallPos.x + wallWidth/2);
            minZ = Math.min(minZ, wallPos.z - wallDepth/2);
            maxZ = Math.max(maxZ, wallPos.z + wallDepth/2);
            minY = Math.min(minY, wallPos.y - wallHeight/2);
        });
        
        const constrainedX = Math.max(minX, Math.min(maxX, position.x));
        const constrainedZ = Math.max(minZ, Math.min(maxZ, position.z));
        
        return {
            x: constrainedX,
            y: minY - (this.componentDefaults.floor.height || 20) / 2,
            z: constrainedZ
        };
    }
    
    // Finde die nächste Wand für Ghost-Object mit freier Bewegung
    findNearestWallPosition(position) {
        const walls = this.getAllComponents().filter(obj => obj.userData.type === 'wall');
        let nearestWall = null;
        let minDistance = Infinity;
        let bestPosition = null;
        
        walls.forEach(wall => {
            const wallPos = wall.position;
            const wallWidth = wall.userData.properties.width;
            const wallHeight = wall.userData.properties.height;
            const wallDepth = wall.userData.properties.depth;
            
            // Berechne Distanz zur Wand
            const distance = Math.sqrt(
                Math.pow(position.x - wallPos.x, 2) + 
                Math.pow(position.z - wallPos.z, 2)
            );
            
            if (distance < 300 && distance < minDistance) { // 300cm Reichweite
                minDistance = distance;
                nearestWall = wall;
                
                // Bestimme die nächste Wandfläche
                const surfaces = [
                    { x: wallPos.x, z: wallPos.z + wallDepth/2, normal: 'north' }, // Vorne
                    { x: wallPos.x, z: wallPos.z - wallDepth/2, normal: 'south' }, // Hinten
                    { x: wallPos.x + wallWidth/2, z: wallPos.z, normal: 'east' },  // Rechts
                    { x: wallPos.x - wallWidth/2, z: wallPos.z, normal: 'west' }   // Links
                ];
                
                let closestSurface = surfaces[0];
                let minSurfaceDistance = Infinity;
                
                surfaces.forEach(surface => {
                    const surfaceDistance = Math.sqrt(
                        Math.pow(position.x - surface.x, 2) + 
                        Math.pow(position.z - surface.z, 2)
                    );
                    if (surfaceDistance < minSurfaceDistance) {
                        minSurfaceDistance = surfaceDistance;
                        closestSurface = surface;
                    }
                });
                
                // Freie Bewegung über die Wandfläche mit Begrenzung
                const openingWidth = this.componentDefaults[this.currentTool].width;
                const openingHeight = this.componentDefaults[this.currentTool].height;
                
                let constrainedX = position.x;
                let constrainedZ = position.z;
                let constrainedY = position.y;
                
                if (closestSurface.normal === 'north' || closestSurface.normal === 'south') {
                    // Nord/Süd-Wand - X kann frei bewegt werden, Z ist fixiert
                    constrainedZ = closestSurface.z;
                    constrainedX = Math.max(wallPos.x - wallWidth/2 + openingWidth/2,
                                          Math.min(wallPos.x + wallWidth/2 - openingWidth/2, position.x));
                } else {
                    // Ost/West-Wand - Z kann frei bewegt werden, X ist fixiert
                    constrainedX = closestSurface.x;
                    constrainedZ = Math.max(wallPos.z - wallDepth/2 + openingWidth/2,
                                          Math.min(wallPos.z + wallDepth/2 - openingWidth/2, position.z));
                }
                
                // Y-Position für Türen vs Fenster
                if (this.currentTool === 'door') {
                    // Tür geht bis zum Boden
                    constrainedY = wallPos.y - wallHeight/2 + openingHeight/2;
                } else {
                    // Fenster kann in der Höhe frei bewegt werden
                    constrainedY = Math.max(wallPos.y - wallHeight/2 + openingHeight/2,
                                          Math.min(wallPos.y + wallHeight/2 - openingHeight/2, position.y));
                }
                
                bestPosition = new THREE.Vector3(constrainedX, constrainedY, constrainedZ);
            }
        });
        
        return bestPosition;
    }
    
    // Projiziere Position auf nächste Wandfläche (für Ghost-Vorschau)
    projectToNearestWallSurface(position) {
        const walls = this.getAllComponents().filter(obj => obj.userData.type === 'wall');
        if (walls.length === 0) return null;
        
        // Verwende Raycasting um nächste Wand zu finden
        const directions = [
            new THREE.Vector3(0, 0, 1),   // Vorne
            new THREE.Vector3(0, 0, -1),  // Hinten
            new THREE.Vector3(1, 0, 0),   // Rechts
            new THREE.Vector3(-1, 0, 0)   // Links
        ];
        
        let closestWall = null;
        let minDistance = Infinity;
        let bestPosition = null;
        
        directions.forEach(direction => {
            const raycaster = new THREE.Raycaster(position, direction);
            const intersects = raycaster.intersectObjects(walls);
            
            if (intersects.length > 0) {
                const hit = intersects[0];
                if (hit.distance < minDistance) {
                    minDistance = hit.distance;
                    closestWall = hit.object;
                    // Positioniere leicht vor der Wandoberfläche
                    bestPosition = hit.point.clone().add(hit.face.normal.multiplyScalar(2));
                }
            }
        });
        
        if (closestWall && bestPosition) {
            return {
                wall: closestWall,
                position: bestPosition
            };
        }
        
        return null;
    }
    
    // Aktualisiere Live-Loch-Vorschau in Wand
    updateLiveWallHole(wall, ghostPosition) {
        if (!wall || !this.ghostObject) return;
        
        const wallProps = wall.userData.properties;
        const wallPos = wall.position;
        const ghostData = this.componentDefaults[this.currentTool];
        
        // Speichere ursprüngliche Geometrie beim ersten Mal
        if (!wall.userData.originalGeometry) {
            wall.userData.originalGeometry = wall.geometry.clone();
        }
        
        // Berechne lokale Koordinaten für das Loch
        const localX = ghostPosition.x - wallPos.x;
        const localY = ghostPosition.y - wallPos.y;
        
        // Erstelle Wand-Shape
        const wallShape = new THREE.Shape()
            .moveTo(-wallProps.width / 2, -wallProps.height / 2)
            .lineTo(wallProps.width / 2, -wallProps.height / 2)
            .lineTo(wallProps.width / 2, wallProps.height / 2)
            .lineTo(-wallProps.width / 2, wallProps.height / 2)
            .lineTo(-wallProps.width / 2, -wallProps.height / 2);
        
        // Erstelle Loch-Shape
        const holeShape = new THREE.Path()
            .moveTo(localX - ghostData.width / 2, localY - ghostData.height / 2)
            .lineTo(localX + ghostData.width / 2, localY - ghostData.height / 2)
            .lineTo(localX + ghostData.width / 2, localY + ghostData.height / 2)
            .lineTo(localX - ghostData.width / 2, localY + ghostData.height / 2)
            .lineTo(localX - ghostData.width / 2, localY - ghostData.height / 2);
        
        // Füge Loch zur Wand hinzu
        wallShape.holes = [holeShape];
        
        // Erstelle neue Geometrie mit Live-Loch
        const newGeometry = new THREE.ExtrudeGeometry(wallShape, {
            depth: wallProps.depth,
            bevelEnabled: false
        });
        
        // Ersetze Wand-Geometrie temporär
        const oldGeometry = wall.geometry;
        wall.geometry = newGeometry;
        oldGeometry.dispose();
        
        debugLog('Live-Loch-Vorschau aktualisiert', 'info');
    }
    
    // Stelle ursprüngliche Wand-Geometrie wieder her
    restoreLiveWallGeometry(wall) {
        if (wall && wall.userData.originalGeometry) {
            const oldGeometry = wall.geometry;
            wall.geometry = wall.userData.originalGeometry.clone();
            oldGeometry.dispose();
            debugLog('Wand-Geometrie wiederhergestellt', 'info');
        }
    }
    
    // Bereinige Live-Wand-Vorschau
    cleanupLiveWallPreview() {
        const walls = this.getAllComponents().filter(obj => obj.userData.type === 'wall');
        walls.forEach(wall => {
            if (wall.userData.originalGeometry) {
                this.restoreLiveWallGeometry(wall);
                delete wall.userData.originalGeometry;
            }
        });
        debugLog('Live-Wand-Vorschau bereinigt', 'info');
    }
}

// Globale Variablen
let builder3d = null;

// Initialisierung
document.addEventListener('DOMContentLoaded', () => {
    debugLog('DOM geladen, starte 3D-Builder...', 'info');
    
    try {
        if (typeof THREE === 'undefined') {
            throw new Error('Three.js nicht geladen');
        }
        
        if (typeof THREE.OrbitControls === 'undefined') {
            throw new Error('OrbitControls nicht geladen');
        }
        
        builder3d = new Simple3DBuilder('building-3d');
        
        // Tool-Buttons setup
        setupToolButtons();
        
        debugLog('3D-Builder bereit', 'success');
        
    } catch (error) {
        debugLog(`Fehler beim Laden: ${error.message}`, 'error');
        
        const container = document.getElementById('building-3d');
        if (container) {
            container.innerHTML = `
                <div style="padding: 40px; text-align: center; color: #666;">
                    <h3>⚠️ 3D-Builder konnte nicht geladen werden</h3>
                    <p>Fehler: ${error.message}</p>
                    <button onclick="location.reload()" style="margin-top: 20px; padding: 10px 20px; background: #4CAF50; color: white; border: none; border-radius: 5px; cursor: pointer;">
                        🔄 Seite neu laden
                    </button>
                </div>
            `;
        }
    }
});

// Tool-Button Setup
function setupToolButtons() {
    const toolButtons = document.querySelectorAll('.tool-btn');
    toolButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            const tool = btn.dataset.tool;
            if (tool && builder3d) {
                toolButtons.forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                builder3d.setTool(tool);
                // Kein Ghost-Panel mehr, nur Eigenschaften-Panel für Auswahl
                if (tool === 'select' && builder3d.selectedObject) {
                    builder3d.showPropertiesPanel();
                } else if (tool !== 'select') {
                    builder3d.hidePropertiesPanel();
                }
                if (tool === 'wall') {
                    builder3d.addCube(0, 0, 0);
                } else if (tool === 'clear') {
                    builder3d.clearScene();
                }
            }
        });
    });
}

// Debug-Panel Funktionen
function toggleDebugPanel() {
    const panel = document.getElementById('debug-panel');
    const toggle = document.getElementById('debug-toggle');
    
    if (panel && toggle) {
        const isOpen = panel.classList.contains('open');
        
        if (isOpen) {
            panel.classList.remove('open');
            toggle.textContent = 'Debug-Log';
        } else {
            panel.classList.add('open');
            toggle.textContent = 'Debug schließen';
        }
        
        debugLog(`Debug-Panel ${isOpen ? 'geschlossen' : 'geöffnet'}`, 'info');
    }
}

function clearDebugLog() {
    const debugContent = document.getElementById('debug-content');
    if (debugContent) {
        debugContent.innerHTML = '';
        debugLog('Debug-Log geleert', 'info');
    }
}

// Hamburger-Menü und Tab-Funktionen
function toggleHamburgerMenu() {
    const menuContent = document.getElementById('hamburger-menu-content');
    if (menuContent) {
        const isOpen = menuContent.style.display === 'block';
        
        menuContent.style.display = isOpen ? 'none' : 'block';
        debugLog(`Hamburger-Menü ${isOpen ? 'geschlossen' : 'geöffnet'}`, 'info');
    }
}

function switchTab(tabName) {
    const tabs = document.querySelectorAll('.tab-content');
    tabs.forEach(tab => {
        tab.style.display = tab.dataset.tab === tabName ? 'block' : 'none';
    });
    
    const tabButtons = document.querySelectorAll('.tab-button');
    tabButtons.forEach(btn => {
        btn.classList.remove('active');
        if (btn.dataset.tab === tabName) {
            btn.classList.add('active');
        }
    });
    
    debugLog(`Wechsel zu Tab: ${tabName}`, 'info');
}

// Globale Funktionen für HTML-Buttons
function toggleMoveMode() {
    if (builder3d) {
        builder3d.toggleMoveMode();
    }
}

function toggleSnapMode() {
    if (builder3d) {
        builder3d.toggleSnapMode();
    }
}

function clearScene() {
    if (builder3d) {
        builder3d.clearScene();
    }
}

function deleteSelectedComponent() {
    if (builder3d) {
        builder3d.deleteSelected();
    }
}

// Initialisierung
defineGlobalFunctions();

function defineGlobalFunctions() {
    window.toggleEditMode = function() {
        if (builder3d) builder3d.toggleEditMode();
    };
    window.toggleMoveMode = toggleMoveMode;
    window.toggleSnapMode = toggleSnapMode;
    window.clearScene = clearScene;
    window.deleteSelectedComponent = deleteSelectedComponent;
}
//# sourceMappingURL=builder3d.js.map

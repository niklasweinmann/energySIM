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
            entries[0].remove();
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
        
        // Standardwerte für Komponenten
        this.componentDefaults = {
            wall: { width: 300, height: 250, depth: 20, uValue: 0.18 },
            door: { width: 90, height: 200, depth: 5, uValue: 1.2 },
            window: { width: 120, height: 120, depth: 5, uValue: 0.9 },
            roof: { width: 400, height: 20, depth: 400, uValue: 0.14 },
            floor: { width: 400, height: 20, depth: 400, uValue: 0.25 }
        };
        
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
        this.currentTool = toolType;
        this.clearGhost();
        
        if (this.editMode && toolType !== 'select') {
            this.createGhost(toolType);
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
        
        if (this.selectedObject && this.moveMode && event.button === 0) {
            this.isDragging = true;
            this.controls.enabled = false;
        }
    }
    
    onMouseMove(event) {
        this.updateMousePosition(event);
        
        if (this.editMode && this.ghostObject && this.currentTool !== 'select') {
            // Ghost-Objekt an Mausposition bewegen
            this.raycaster.setFromCamera(this.mouse, this.camera);
            
            // Schnitt mit Grundebene (y=0)
            const plane = new THREE.Plane(new THREE.Vector3(0, 1, 0), 0);
            const intersection = new THREE.Vector3();
            
            if (this.raycaster.ray.intersectPlane(plane, intersection)) {
                let finalPosition = intersection;
                
                // Nur bei aktiviertem Snap-Modus anwenden
                if (this.snapMode) {
                    finalPosition = this.snapToNearestWall(intersection, this.currentTool);
                }
                
                this.ghostObject.position.copy(finalPosition);
                this.ghostObject.position.y += this.componentDefaults[this.currentTool].height / 2;
                this.ghostObject.visible = true;
                this.needsRender = true;
            }
        }
        
        if (this.isDragging && this.selectedObject) {
            // Ausgewähltes Objekt bewegen
            this.raycaster.setFromCamera(this.mouse, this.camera);
            const plane = new THREE.Plane(new THREE.Vector3(0, 1, 0), this.selectedObject.position.y);
            const intersection = new THREE.Vector3();
            
            if (this.raycaster.ray.intersectPlane(plane, intersection)) {
                let finalPosition = intersection;
                
                // Nur bei aktiviertem Snap-Modus anwenden
                if (this.snapMode) {
                    const componentType = this.selectedObject.userData.type;
                    finalPosition = this.snapToNearestWall(intersection, componentType);
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
            debugLog('Objekt verschoben', 'info');
            
            // Reset nach kurzer Zeit
            setTimeout(() => {
                this.justDragged = false;
            }, 100);
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
        } else if (this.editMode && this.ghostObject && this.ghostObject.visible) {
            // Neues Objekt platzieren (nur im EditMode)
            this.placeComponent(this.currentTool, this.ghostObject.position.clone());
        }
    }
    
    placeComponent(type, position) {
        const defaults = this.componentDefaults[type];
        const geometry = new THREE.BoxGeometry(defaults.width, defaults.height, defaults.depth);
        
        let color = 0x8BC34A; // Standard grün
        if (type === 'door') color = 0x795548;
        else if (type === 'window') color = 0x2196F3;
        else if (type === 'roof') color = 0x9E9E9E;
        else if (type === 'floor') color = 0x607D8B;
        
        const material = new THREE.MeshLambertMaterial({ color });
        const component = new THREE.Mesh(geometry, material);
        
        component.position.copy(position);
        
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
        this.selectObject(component);
        
        // Tool auf "select" zurücksetzen nach Platzierung
        this.setTool('select');
        
        // Bauteilübersicht aktualisieren
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
        this.moveMode = !this.moveMode;
        debugLog(`Verschieben-Modus: ${this.moveMode ? 'AN' : 'AUS'}`, 'info');
        
        const btn = document.getElementById('move-btn');
        if (btn) {
            if (this.moveMode) {
                btn.classList.add('active');
            } else {
                btn.classList.remove('active');
            }
            // Text bleibt konstant
            btn.innerHTML = '📍 Verschieben';
        }
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
            // Kein Snap-Modus - verstecke Feedback
            this.showSnapFeedback(false, false, null);
            return position;
        }
        
        const snappedPosition = position.clone();
        const snapDistance = 100; // 100cm Snap-Reichweite
        const glideThreshold = 150; // 150cm Gleiten-Reichweite (größer als Snap)
        const allComponents = this.getAllComponents();
        
        let snapResult = null;
        let snapType = '';
        
        // FENSTER & TÜREN: Entlang Wandflächen bewegen und gleiten
        if (componentType === 'window' || componentType === 'door') {
            snapResult = this.snapAndGlideToWallSurface(position, allComponents, snapDistance, glideThreshold);
            snapType = 'wall-surface';
            if (snapResult) {
                snappedPosition.set(
                    snapResult.x, 
                    snapResult.y + (componentType === 'window' ? snapResult.wallHeight * 0.2 : -snapResult.wallHeight * 0.4), 
                    snapResult.z
                );
                debugLog(`${componentType} entlang Wand bewegt`, 'success');
            }
        }
        
        // WÄNDE: Entlang anderen Wänden bewegen und gleiten (Kante-an-Kante)
        else if (componentType === 'wall') {
            snapResult = this.snapAndGlideToWallEdge(position, allComponents, snapDistance, glideThreshold);
            snapType = 'wall-edge';
            if (snapResult) {
                snappedPosition.set(snapResult.x, snapResult.y, snapResult.z);
                debugLog('Wand entlang Kante bewegt', 'success');
            }
        }
        
        // DÄCHER: Entlang Wand-Oberkanten bewegen und gleiten
        else if (componentType === 'roof') {
            snapResult = this.snapAndGlideToWallTops(position, allComponents, snapDistance, glideThreshold);
            snapType = 'wall-tops';
            if (snapResult) {
                snappedPosition.set(snapResult.x, snapResult.y, snapResult.z);
                debugLog('Dach entlang Wänden bewegt', 'success');
            }
        }
        
        // BÖDEN: Entlang Wand-Unterkanten bewegen und gleiten
        else if (componentType === 'floor') {
            snapResult = this.snapAndGlideToWallBottoms(position, allComponents, snapDistance, glideThreshold);
            snapType = 'wall-bottoms';
            if (snapResult) {
                snappedPosition.set(snapResult.x, snapResult.y, snapResult.z);
                debugLog('Boden entlang Wänden bewegt', 'success');
            }
        }
        
        // Zeige visuelles Feedback
        if (snapResult) {
            this.showSnapFeedback(snapResult.isGliding === false, snapResult.isGliding === true, snapType);
        } else {
            this.showSnapFeedback(false, false, null);
        }
        
        return snappedPosition;
    }
    
    // Magnetisches Gleiten: Entlang Wandfläche bewegen
    snapAndGlideToWallSurface(position, allComponents, snapDistance, glideThreshold) {
        const walls = allComponents.filter(obj => obj.userData.type === 'wall');
        let bestConstraint = null;
        let minDistance = Infinity;
        let isGliding = false;
        
        walls.forEach(wall => {
            const wallPos = wall.position;
            const wallWidth = wall.userData.width || this.componentDefaults.wall.width;
            const wallDepth = wall.userData.depth || this.componentDefaults.wall.depth;
            const wallHeight = wall.userData.height || this.componentDefaults.wall.height;
            
            // Prüfe alle 4 Wandflächen
            const surfaces = [
                { // Nord (Vorne)
                    normal: { x: 0, z: 1 },
                    surfacePos: { x: wallPos.x, z: wallPos.z + wallDepth/2 },
                    constraint: { // Bewegung entlang X-Achse
                        axis: 'x',
                        fixedZ: wallPos.z + wallDepth/2,
                        minX: wallPos.x - wallWidth/2,
                        maxX: wallPos.x + wallWidth/2
                    }
                },
                { // Süd (Hinten)
                    normal: { x: 0, z: -1 },
                    surfacePos: { x: wallPos.x, z: wallPos.z - wallDepth/2 },
                    constraint: {
                        axis: 'x',
                        fixedZ: wallPos.z - wallDepth/2,
                        minX: wallPos.x - wallWidth/2,
                        maxX: wallPos.x + wallWidth/2
                    }
                },
                { // Ost (Rechts)
                    normal: { x: 1, z: 0 },
                    surfacePos: { x: wallPos.x + wallWidth/2, z: wallPos.z },
                    constraint: { // Bewegung entlang Z-Achse
                        axis: 'z',
                        fixedX: wallPos.x + wallWidth/2,
                        minZ: wallPos.z - wallDepth/2,
                        maxZ: wallPos.z + wallDepth/2
                    }
                },
                { // West (Links)
                    normal: { x: -1, z: 0 },
                    surfacePos: { x: wallPos.x - wallWidth/2, z: wallPos.z },
                    constraint: {
                        axis: 'z',
                        fixedX: wallPos.x - wallWidth/2,
                        minZ: wallPos.z - wallDepth/2,
                        maxZ: wallPos.z + wallDepth/2
                    }
                }
            ];
            
            surfaces.forEach(surface => {
                const distanceToSurface = Math.abs(
                    (position.x - surface.surfacePos.x) * surface.normal.x +
                    (position.z - surface.surfacePos.z) * surface.normal.z
                );
                
                // Erweiterte Reichweite für Gleiten
                const effectiveThreshold = isGliding ? glideThreshold : snapDistance;
                
                if (distanceToSurface < effectiveThreshold && distanceToSurface < minDistance) {
                    minDistance = distanceToSurface;
                    
                    // Berechne Position mit Gleiten-Constraint
                    let constrainedPos = { x: position.x, z: position.z };
                    
                    if (surface.constraint.axis === 'x') {
                        // Gleiten entlang X-Achse, Z fixiert
                        constrainedPos.z = surface.constraint.fixedZ;
                        constrainedPos.x = Math.max(surface.constraint.minX, 
                                                  Math.min(surface.constraint.maxX, position.x));
                        
                        // Prüfe ob wir am Ende der Wand angelangt sind
                        if (position.x < surface.constraint.minX - 50 || position.x > surface.constraint.maxX + 50) {
                            isGliding = false; // Loslassen der Wand
                            return null;
                        }
                    } else {
                        // Gleiten entlang Z-Achse, X fixiert
                        constrainedPos.x = surface.constraint.fixedX;
                        constrainedPos.z = Math.max(surface.constraint.minZ, 
                                                  Math.min(surface.constraint.maxZ, position.z));
                        
                        // Prüfe ob wir am Ende der Wand angelangt sind
                        if (position.z < surface.constraint.minZ - 50 || position.z > surface.constraint.maxZ + 50) {
                            isGliding = false; // Loslassen der Wand
                            return null;
                        }
                    }
                    
                    bestConstraint = {
                        x: constrainedPos.x,
                        y: wallPos.y,
                        z: constrainedPos.z,
                        wallHeight: wallHeight,
                        isGliding: distanceToSurface < snapDistance
                    };
                }
            });
        });
        
        return bestConstraint;
    }
    
    // Magnetisches Gleiten: Entlang Wandkante bewegen
    snapAndGlideToWallEdge(position, allComponents, snapDistance, glideThreshold) {
        const otherWalls = allComponents.filter(obj => obj.userData.type === 'wall' && obj !== this.selectedObject);
        let bestConstraint = null;
        let minDistance = Infinity;
        let isGliding = false;
        
        otherWalls.forEach(wall => {
            const wallPos = wall.position;
            const wallWidth = wall.userData.width || this.componentDefaults.wall.width;
            const wallDepth = wall.userData.depth || this.componentDefaults.wall.depth;
            
            // Kanten der existierenden Wand
            const edges = [
                { // Rechte Kante - Gleiten nach vorne/hinten
                    name: 'right',
                    point: { x: wallPos.x + wallWidth/2, z: wallPos.z },
                    constraint: {
                        fixedX: wallPos.x + wallWidth/2,
                        minZ: wallPos.z - wallDepth/2,
                        maxZ: wallPos.z + wallDepth/2,
                        axis: 'z'
                    }
                },
                { // Linke Kante
                    name: 'left',
                    point: { x: wallPos.x - wallWidth/2, z: wallPos.z },
                    constraint: {
                        fixedX: wallPos.x - wallWidth/2,
                        minZ: wallPos.z - wallDepth/2,
                        maxZ: wallPos.z + wallDepth/2,
                        axis: 'z'
                    }
                },
                { // Vordere Kante - Gleiten nach links/rechts
                    name: 'front',
                    point: { x: wallPos.x, z: wallPos.z + wallDepth/2 },
                    constraint: {
                        fixedZ: wallPos.z + wallDepth/2,
                        minX: wallPos.x - wallWidth/2,
                        maxX: wallPos.x + wallWidth/2,
                        axis: 'x'
                    }
                },
                { // Hintere Kante
                    name: 'back',
                    point: { x: wallPos.x, z: wallPos.z - wallDepth/2 },
                    constraint: {
                        fixedZ: wallPos.z - wallDepth/2,
                        minX: wallPos.x - wallWidth/2,
                        maxX: wallPos.x + wallWidth/2,
                        axis: 'x'
                    }
                }
            ];
            
            edges.forEach(edge => {
                const distance = Math.sqrt(
                    Math.pow(position.x - edge.point.x, 2) + 
                    Math.pow(position.z - edge.point.z, 2)
                );
                
                // Erweiterte Reichweite für Gleiten
                const effectiveThreshold = isGliding ? glideThreshold : snapDistance;
                
                if (distance < effectiveThreshold && distance < minDistance) {
                    minDistance = distance;
                    
                    // Berechne Constraint-Position mit Gleiten
                    let constrainedPos = { x: position.x, z: position.z };
                    
                    if (edge.constraint.axis === 'z') {
                        // Gleiten entlang Z-Achse (bei rechten/linken Kanten)
                        constrainedPos.x = edge.constraint.fixedX;
                        constrainedPos.z = Math.max(edge.constraint.minZ, 
                                                  Math.min(edge.constraint.maxZ, position.z));
                        
                        // Prüfe ob wir am Ende der Kante angelangt sind
                        if (position.z < edge.constraint.minZ - 50 || position.z > edge.constraint.maxZ + 50) {
                            isGliding = false; // Loslassen der Kante
                            return null;
                        }
                    } else {
                        // Gleiten entlang X-Achse (bei vorderen/hinteren Kanten)
                        constrainedPos.z = edge.constraint.fixedZ;
                        constrainedPos.x = Math.max(edge.constraint.minX, 
                                                  Math.min(edge.constraint.maxX, position.x));
                        
                        // Prüfe ob wir am Ende der Kante angelangt sind
                        if (position.x < edge.constraint.minX - 50 || position.x > edge.constraint.maxX + 50) {
                            isGliding = false; // Loslassen der Kante
                            return null;
                        }
                    }
                    
                    bestConstraint = {
                        x: constrainedPos.x,
                        y: wallPos.y,
                        z: constrainedPos.z,
                        isGliding: distance < snapDistance,
                        edgeName: edge.name
                    };
                }
            });
        });
        
        return bestConstraint;
    }
    
    // Magnetisches Gleiten: Entlang Wand-Oberkanten bewegen (für Dächer)
    snapAndGlideToWallTops(position, allComponents, snapDistance, glideThreshold) {
        const walls = allComponents.filter(obj => obj.userData.type === 'wall');
        if (walls.length === 0) return null;
        
        // Berechne erweiterte Bounding Box aller Wände für Gleiten
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
        
        // Prüfe ob Position innerhalb oder nahe der Wand-Bounding-Box ist
        const marginX = 100; // 100cm Spielraum zum Gleiten
        const marginZ = 100;
        
        const extMinX = minX - marginX;
        const extMaxX = maxX + marginX;
        const extMinZ = minZ - marginZ;
        const extMaxZ = maxZ + marginZ;
        
        // Gleiten: Wenn außerhalb der Grundfläche, aber innerhalb der erweiterten Zone
        let constrainedX = position.x;
        let constrainedZ = position.z;
        let isGliding = false;
        
        if (position.x >= extMinX && position.x <= extMaxX && position.z >= extMinZ && position.z <= extMaxZ) {
            // Innerhalb der Gleit-Zone - begrenzen auf Wand-Bounding-Box
            if (position.x < minX) {
                constrainedX = minX;
                isGliding = true;
            } else if (position.x > maxX) {
                constrainedX = maxX;
                isGliding = true;
            }
            
            if (position.z < minZ) {
                constrainedZ = minZ;
                isGliding = true;
            } else if (position.z > maxZ) {
                constrainedZ = maxZ;
                isGliding = true;
            }
            
            return {
                x: constrainedX,
                y: maxY + (this.componentDefaults.roof.height || 20) / 2,
                z: constrainedZ,
                isGliding: isGliding
            };
        }
        
        return null;
    }
    
    // Magnetisches Gleiten: Entlang Wand-Unterkanten bewegen (für Böden)
    snapAndGlideToWallBottoms(position, allComponents, snapDistance, glideThreshold) {
        const walls = allComponents.filter(obj => obj.userData.type === 'wall');
        if (walls.length === 0) return null;
        
        // Berechne erweiterte Bounding Box aller Wände für Gleiten
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
        
        // Prüfe ob Position innerhalb oder nahe der Wand-Bounding-Box ist
        const marginX = 100; // 100cm Spielraum zum Gleiten
        const marginZ = 100;
        
        const extMinX = minX - marginX;
        const extMaxX = maxX + marginX;
        const extMinZ = minZ - marginZ;
        const extMaxZ = maxZ + marginZ;
        
        // Gleiten: Wenn außerhalb der Grundfläche, aber innerhalb der erweiterten Zone
        let constrainedX = position.x;
        let constrainedZ = position.z;
        let isGliding = false;
        
        if (position.x >= extMinX && position.x <= extMaxX && position.z >= extMinZ && position.z <= extMaxZ) {
            // Innerhalb der Gleit-Zone - begrenzen auf Wand-Bounding-Box
            if (position.x < minX) {
                constrainedX = minX;
                isGliding = true;
            } else if (position.x > maxX) {
                constrainedX = maxX;
                isGliding = true;
            }
            
            if (position.z < minZ) {
                constrainedZ = minZ;
                isGliding = true;
            } else if (position.z > maxZ) {
                constrainedZ = maxZ;
                isGliding = true;
            }
            
            return {
                x: constrainedX,
                y: minY - (this.componentDefaults.floor.height || 20) / 2,
                z: constrainedZ,
                isGliding: isGliding
            };
        }
        
        return null;
    }
    
    // Visuelles Feedback für das Kleben/Gleiten
    showSnapFeedback(isSnapped, isGliding, snapType) {
        const feedbackDiv = document.getElementById('snap-feedback') || this.createSnapFeedback();
        
        if (isSnapped || isGliding) {
            let message = '';
            let color = '';
            
            if (isSnapped) {
                message = '🧲 Magnetisch angeklebt';
                color = '#ff6b35'; // Orange für angeklebt
            } else if (isGliding) {
                message = '⟷ Gleitet entlang der Kante';
                color = '#ffa500'; // Hellorange für gleiten
            }
            
            feedbackDiv.textContent = message;
            feedbackDiv.style.backgroundColor = color;
            feedbackDiv.style.opacity = '1';
            feedbackDiv.style.transform = 'translateY(0)';
        } else {
            feedbackDiv.style.opacity = '0';
            feedbackDiv.style.transform = 'translateY(-10px)';
        }
    }
    
    // Erstelle Feedback-Element
    createSnapFeedback() {
        const feedbackDiv = document.createElement('div');
        feedbackDiv.id = 'snap-feedback';
        feedbackDiv.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 10px 20px;
            border-radius: 25px;
            color: white;
            font-weight: bold;
            font-size: 14px;
            z-index: 1000;
            opacity: 0;
            transform: translateY(-10px);
            transition: all 0.3s ease;
            pointer-events: none;
            box-shadow: 0 4px 12px rgba(0,0,0,0.2);
        `;
        document.body.appendChild(feedbackDiv);
        return feedbackDiv;
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
        if (!this.selectedObject) return;
        
        const panel = document.getElementById('properties-panel');
        const content = document.getElementById('properties-content');
        
        if (!panel || !content) return;
        
        const props = this.selectedObject.userData.properties;
        const type = this.selectedObject.userData.type;
        const defaults = this.componentDefaults[type];
        const componentName = this.selectedObject.userData.name || '';
        
        content.innerHTML = `
            <div class="property-group">
                <div class="property-label">Name</div>
                <input type="text" class="property-input" id="prop-name" value="${componentName}" placeholder="Bauteil-Name eingeben">
            </div>
            
            <div class="property-group">
                <div class="property-label">Typ</div>
                <div style="font-weight: 500; color: #333;">${type.toUpperCase()}</div>
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
                    <input type="number" class="property-input" id="prop-pos-x" value="${Math.round(props.position.x)}" placeholder="X">
                    <input type="number" class="property-input" id="prop-pos-y" value="${Math.round(props.position.y)}" placeholder="Y">
                    <input type="number" class="property-input" id="prop-pos-z" value="${Math.round(props.position.z)}" placeholder="Z">
                </div>
                <div class="position-controls">
                    <button class="move-btn" id="move-btn" onclick="toggleMoveMode()">
                        📍 Verschieben
                    </button>
                    <button class="snap-btn" id="snap-btn" onclick="toggleSnapMode()">
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
        
        // Standardwerte-Styling setzen
        this.setDefaultStyles(defaults);
        
        // Auto-Update Events hinzufügen
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
        this.selectedObject.position.set(posX, posY + height/2, posZ);
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
        props.position.y = Math.round(this.selectedObject.position.y - props.height/2);
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
    
    showGhostPropertiesPanel(toolType) {
        const panel = document.getElementById('properties-panel');
        const content = document.getElementById('properties-content');
        
        if (!panel || !content) return;
        
        const defaults = this.componentDefaults[toolType];
        
        content.innerHTML = `
            <div class="property-group">
                <div class="property-label">Neues ${toolType.toUpperCase()}</div>
                <div style="font-size: 11px; color: #666; margin-bottom: 12px;">
                    Eigenschaften für neues Bauteil
                </div>
            </div>
            
            <div class="property-group">
                <div class="property-label">Abmessungen (cm)</div>
                <div class="property-row">
                    <input type="number" class="property-input default" id="ghost-width" value="${defaults.width}" placeholder="Breite">
                    <input type="number" class="property-input default" id="ghost-height" value="${defaults.height}" placeholder="Höhe">
                    <input type="number" class="property-input default" id="ghost-depth" value="${defaults.depth}" placeholder="Tiefe">
                </div>
            </div>
            
            <div class="property-group">
                <div class="property-label">U-Wert (W/m²K)</div>
                <input type="number" class="property-input default" id="ghost-uvalue" value="${defaults.uValue}" step="0.01" placeholder="U-Wert">
            </div>
            
            <div style="margin-top: 16px; padding-top: 12px; border-top: 1px solid #eee; font-size: 11px; color: #666;">
                💡 Klicken Sie in die 3D-Ansicht um das Bauteil zu platzieren
            </div>
        `;
        
        panel.classList.add('open');
        
        // Auto-Update für Ghost-Properties
        this.setupGhostAutoUpdate(toolType);
        
        debugLog(`Eigenschaften-Panel für ${toolType} angezeigt`, 'info');
    }
    
    setupGhostAutoUpdate(toolType) {
        const inputs = ['ghost-width', 'ghost-height', 'ghost-depth', 'ghost-uvalue'];
        
        inputs.forEach(inputId => {
            const input = document.getElementById(inputId);
            if (input) {
                // Entferne default-Klasse bei Eingabe
                input.addEventListener('input', () => {
                    input.classList.remove('default');
                    this.updateGhostFromInputs(toolType);
                });
                
                // Focus/Blur Events für bessere UX
                input.addEventListener('focus', () => {
                    input.classList.remove('default');
                });
            }
        });
    }
    
    updateGhostFromInputs(toolType) {
        if (!this.ghostObject) return;
        
        const width = parseFloat(document.getElementById('ghost-width').value) || this.componentDefaults[toolType].width;
        const height = parseFloat(document.getElementById('ghost-height').value) || this.componentDefaults[toolType].height;
        const depth = parseFloat(document.getElementById('ghost-depth').value) || this.componentDefaults[toolType].depth;
        
        // Ghost-Geometrie aktualisieren
        const newGeometry = new THREE.BoxGeometry(width, height, depth);
        this.ghostObject.geometry.dispose();
        this.ghostObject.geometry = newGeometry;
        
        // Defaults für spätere Platzierung aktualisieren
        this.componentDefaults[toolType].width = width;
        this.componentDefaults[toolType].height = height;
        this.componentDefaults[toolType].depth = depth;
        
        const uValue = parseFloat(document.getElementById('ghost-uvalue').value);
        if (uValue) {
            this.componentDefaults[toolType].uValue = uValue;
        }
        
        this.needsRender = true;
        debugLog(`Ghost ${toolType} Eigenschaften aktualisiert`, 'info');
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
            this.scene.remove(this.selectedObject);
            
            // Ressourcen freigeben
            if (this.selectedObject.geometry) this.selectedObject.geometry.dispose();
            if (this.selectedObject.material) this.selectedObject.material.dispose();
            
            debugLog(`${this.selectedObject.userData.type} gelöscht`, 'info');
            
            this.clearSelection();
            this.hidePropertiesPanel();
            
            // Bauteilübersicht aktualisieren
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
            moveBtn.innerHTML = '� Verschieben';
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
                // Alle Buttons deaktivieren
                toolButtons.forEach(b => b.classList.remove('active'));
                
                // Aktuellen Button aktivieren
                btn.classList.add('active');
                
                // Tool setzen
                builder3d.setTool(tool);
                
                // Eigenschaften-Panel für Ghost-Objekt anzeigen wenn Bauteil-Tool gewählt
                if (tool !== 'select') {
                    builder3d.showGhostPropertiesPanel(tool);
                } else {
                    // Bei "select" Tool Properties Panel nur anzeigen wenn Objekt ausgewählt
                    if (!builder3d.selectedObject) {
                        builder3d.hidePropertiesPanel();
                    }
                }
                
                // Spezielle Aktionen
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

// Globale Funktionen
window.debugLog = debugLog;
window.toggleDebugPanel = toggleDebugPanel;
window.clearDebugLog = clearDebugLog;

// Edit Mode Toggle
function toggleEditMode() {
    if (builder3d) {
        builder3d.toggleEditMode();
        
        const btn = document.getElementById('edit-mode-btn');
        
        if (builder3d.editMode) {
            btn.classList.add('active');
            btn.textContent = '✏️ Bearbeiten deaktivieren';
        } else {
            btn.classList.remove('active');
            btn.textContent = '✏️ Bearbeiten aktivieren';
        }
    }
}

window.toggleEditMode = toggleEditMode;

// Globale Funktionen für Properties-Panel
// Globale Funktionen
function toggleEditMode() {
    if (builder3d) {
        builder3d.toggleEditMode();
    }
}

function toggleMoveMode() {
    if (builder3d && builder3d.selectedObject) {
        builder3d.toggleMoveMode();
    }
}

function deleteSelectedComponent() {
    if (builder3d) {
        builder3d.deleteSelected();
    }
}

function toggleSnapMode() {
    if (builder3d) {
        builder3d.toggleSnapMode();
    }
}

// Close Properties Panel
function closePropertiesPanel() {
    if (builder3d) {
        builder3d.hidePropertiesPanel();
        builder3d.clearSelection();
    }
}

// Globale Funktionen verfügbar machen
window.toggleEditMode = toggleEditMode;
window.toggleMoveMode = toggleMoveMode;
window.toggleSnapMode = toggleSnapMode;
window.deleteSelectedComponent = deleteSelectedComponent;
window.closePropertiesPanel = closePropertiesPanel;

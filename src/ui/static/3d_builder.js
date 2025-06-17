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
        this.editMode = true; // Standardmäßig aktiviert für bessere UX
        this.selectedObject = null;
        this.ghostObject = null;
        this.isDragging = false;
        this.moveMode = false;
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
            this.updateInitialUI();
            
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
    
    updateInitialUI() {
        // UI-Elemente entsprechend dem initialen editMode aktualisieren
        const btn = document.getElementById('edit-mode-btn');
        
        if (this.editMode) {
            if (btn) {
                btn.classList.add('active');
                btn.textContent = '✏️ Bearbeiten deaktivieren';
            }
        } else {
            if (btn) {
                btn.classList.remove('active');
                btn.textContent = '✏️ Bearbeiten aktivieren';
            }
        }
        
        // Tool-Buttons initial aktualisieren
        this.updateToolButtons();
    }

    // Bearbeitungsmodus Funktionen
    toggleEditMode() {
        this.editMode = !this.editMode;
        debugLog(`Bearbeitungsmodus: ${this.editMode ? 'AN' : 'AUS'}`, 'info');
        
        // UI aktualisieren
        const btn = document.getElementById('edit-mode-btn');
        
        if (this.editMode) {
            btn.classList.add('active');
            btn.textContent = '✏️ Bearbeiten deaktivieren';
        } else {
            btn.classList.remove('active');
            btn.textContent = '✏️ Bearbeiten aktivieren';
            this.clearSelection();
            this.clearGhost();
        }
        
        // Tool-Buttons aktivieren/deaktivieren
        this.updateToolButtons();
        
        this.needsRender = true;
    }
    
    updateToolButtons() {
        const toolButtons = document.querySelectorAll('.tool-btn');
        toolButtons.forEach(btn => {
            if (this.editMode) {
                btn.classList.remove('disabled');
                btn.disabled = false;
            } else {
                btn.classList.add('disabled');
                btn.disabled = true;
                // Nur Auswählen-Button bleibt aktiv
                if (btn.dataset.tool !== 'select') {
                    btn.classList.remove('active');
                }
            }
        });
    }
    
    setTool(toolType) {
        this.currentTool = toolType;
        this.clearGhost();
        
        if (this.editMode && toolType !== 'select') {
            this.createGhost(toolType);
            // Zeige Properties-Panel für Ghost-Objekt
            this.showPropertiesPanel('ghost', toolType);
        } else if (toolType === 'select') {
            // Bei "select" Tool Properties Panel nur anzeigen wenn Objekt ausgewählt
            if (!this.selectedObject) {
                this.hidePropertiesPanel();
            }
        }
        
        this.updateToolButtons();
        
        debugLog(`Tool gewechselt zu: ${toolType}`, 'info');
    }
    
    updateToolButtons() {
        const toolButtons = document.querySelectorAll('.tool-btn');
        toolButtons.forEach(btn => {
            btn.classList.remove('active', 'selected');
            
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
                this.ghostObject.position.copy(intersection);
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
                this.selectedObject.position.x = intersection.x;
                this.selectedObject.position.z = intersection.z;
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
        
        // Name aus Properties-Panel übernehmen, falls vorhanden
        const nameInput = document.getElementById('prop-name');
        const componentName = nameInput ? nameInput.value : '';
        
        component.position.copy(position);
        component.userData = {
            isComponent: true,
            type: type,
            originalColor: color,
            properties: {
                name: componentName,
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
        this.showPropertiesPanel('placed');
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
                btn.innerHTML = '🔒 Stopp';
            } else {
                btn.classList.remove('active');
                btn.innerHTML = '📍 Verschieben';
            }
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
        
        this.needsRender = true;
        debugLog('Szene geleert', 'info');
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
    
    showPropertiesPanel(mode = 'placed', toolType = null) {
        const panel = document.getElementById('properties-panel');
        const content = document.getElementById('properties-content');
        
        if (!panel || !content) return;
        
        let props, type, defaults, isGhost = false;
        
        if (mode === 'ghost' && toolType) {
            // Ghost-Modus
            isGhost = true;
            type = toolType;
            defaults = this.componentDefaults[toolType];
            props = {
                name: '',
                width: defaults.width,
                height: defaults.height,
                depth: defaults.depth,
                uValue: defaults.uValue,
                position: { x: 0, y: 0, z: 0 },
                rotation: { x: 0, y: 0, z: 0 }
            };
        } else if (this.selectedObject) {
            // Platziertes Objekt
            props = this.selectedObject.userData.properties;
            type = this.selectedObject.userData.type;
            defaults = this.componentDefaults[type];
        } else {
            return;
        }
        
        // Deutsche Typnamen
        const typeNames = {
            wall: 'Wand',
            door: 'Tür', 
            window: 'Fenster',
            roof: 'Dach',
            floor: 'Boden'
        };
        
        const displayType = typeNames[type] || type.toUpperCase();
        const nameValue = props.name || '';
        
        content.innerHTML = `
            <div class="property-group">
                <div class="property-label">Name</div>
                <input type="text" class="property-input" id="prop-name" value="${nameValue}" placeholder="Bauteil-Name eingeben">
            </div>
            
            <div class="property-group">
                <div class="property-label">Typ</div>
                <div style="font-weight: 500; color: #333; padding: 6px 8px; background: #f9f9f9; border-radius: 3px;">${displayType}</div>
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
            
            ${!isGhost ? `
            <div class="property-group">
                <div class="property-label">Position (cm)</div>
                <div class="property-row">
                    <input type="number" class="property-input" id="prop-pos-x" value="${Math.round(props.position.x)}" placeholder="X">
                    <input type="number" class="property-input" id="prop-pos-y" value="${Math.round(props.position.y)}" placeholder="Y">
                    <input type="number" class="property-input" id="prop-pos-z" value="${Math.round(props.position.z)}" placeholder="Z">
                </div>
                <button class="move-btn" id="move-btn" onclick="toggleMoveMode()">
                    📍 Verschieben
                </button>
            </div>
            
            <div class="property-group">
                <div class="property-label">Rotation (Grad)</div>
                <div class="property-row">
                    <input type="number" class="property-input" id="prop-rot-x" value="${Math.round(props.rotation.x)}" placeholder="X">
                    <input type="number" class="property-input" id="prop-rot-y" value="${Math.round(props.rotation.y)}" placeholder="Y">
                    <input type="number" class="property-input" id="prop-rot-z" value="${Math.round(props.rotation.z)}" placeholder="Z">
                </div>
            </div>
            
            <div class="property-actions">
                <button class="delete-btn" onclick="deleteSelectedComponent()">🗑️ Löschen</button>
            </div>
            ` : `
            <div style="margin-top: 16px; padding-top: 12px; border-top: 1px solid #eee; font-size: 11px; color: #666;">
                💡 Klicken Sie in die 3D-Ansicht um das Bauteil zu platzieren
            </div>
            `}
        `;
        
        // Standardwerte-Styling setzen
        this.setDefaultStyles(defaults);
        
        // Auto-Update Events hinzufügen
        this.setupAutoUpdate(isGhost, toolType);
        
        panel.classList.add('open');
        debugLog(`Properties-Panel angezeigt (${isGhost ? 'Ghost' : 'Platziert'})`, 'success');
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
    
    setupAutoUpdate(isGhost = false, toolType = null) {
        const inputs = ['prop-name', 'prop-width', 'prop-height', 'prop-depth', 'prop-uvalue'];
        
        if (!isGhost) {
            inputs.push('prop-pos-x', 'prop-pos-y', 'prop-pos-z', 'prop-rot-x', 'prop-rot-y', 'prop-rot-z');
        }
        
        inputs.forEach(id => {
            const input = document.getElementById(id);
            if (input) {
                input.addEventListener('input', () => {
                    input.classList.remove('default');
                    if (isGhost && toolType) {
                        this.updateGhostFromInputs(toolType);
                    } else {
                        this.applyPropertiesAuto();
                    }
                });
            }
        });
    }
    
    applyPropertiesAuto() {
        if (!this.selectedObject) return;
        
        const props = this.selectedObject.userData.properties;
        
        // Name
        const name = document.getElementById('prop-name')?.value || '';
        
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
        props.name = name;
        props.width = width;
        props.height = height;
        props.depth = depth;
        props.position = { x: posX, y: posY, z: posZ };
        props.rotation = { x: rotX * 180 / Math.PI, y: rotY * 180 / Math.PI, z: rotZ * 180 / Math.PI };
        props.uValue = uValue;
        
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
    
    setupGhostAutoUpdate(toolType) {
        // Diese Funktion wird nicht mehr benötigt - alles läuft über setupAutoUpdate
        debugLog(`Legacy setupGhostAutoUpdate für ${toolType} übersprungen`, 'info');
    }
    
    updateGhostFromInputs(toolType) {
        if (!this.ghostObject) return;
        
        const width = parseFloat(document.getElementById('prop-width')?.value) || this.componentDefaults[toolType].width;
        const height = parseFloat(document.getElementById('prop-height')?.value) || this.componentDefaults[toolType].height;
        const depth = parseFloat(document.getElementById('prop-depth')?.value) || this.componentDefaults[toolType].depth;
        
        // Ghost-Geometrie aktualisieren
        const newGeometry = new THREE.BoxGeometry(width, height, depth);
        this.ghostObject.geometry.dispose();
        this.ghostObject.geometry = newGeometry;
        
        // Defaults für spätere Platzierung aktualisieren
        this.componentDefaults[toolType].width = width;
        this.componentDefaults[toolType].height = height;
        this.componentDefaults[toolType].depth = depth;
        
        const uValue = parseFloat(document.getElementById('prop-uvalue')?.value);
        if (uValue) {
            this.componentDefaults[toolType].uValue = uValue;
        }
        
        this.needsRender = true;
        debugLog(`Ghost ${toolType} Eigenschaften aktualisiert`, 'info');
    }
    
    // Building Management
    clearAll() {
        this.clearScene();
        this.clearSelection();
        this.clearGhost();
        debugLog('Gesamtes Gebäude gelöscht', 'info');
    }
    
    exportBuilding() {
        const buildingData = {
            version: '1.0',
            timestamp: new Date().toISOString(),
            components: this.scene.children
                .filter(child => child.userData && child.userData.type)
                .map(child => ({
                    type: child.userData.type,
                    position: child.position.toArray(),
                    rotation: child.rotation.toArray(),
                    scale: child.scale.toArray(),
                    properties: child.userData.properties || {}
                }))
        };
        debugLog(`Gebäude exportiert: ${buildingData.components.length} Komponenten`, 'info');
        return buildingData;
    }
    
    importBuilding(buildingData) {
        // Erst alles löschen
        this.clearAll();
        
        if (!buildingData.components) {
            throw new Error('Ungültiges Gebäude-Format');
        }
        
        // Komponenten laden
        buildingData.components.forEach(comp => {
            // Hier würde die Logik zum Erstellen der Komponenten stehen
            // Für jetzt nur ein Platzhalter
            debugLog(`Importiere Komponente: ${comp.type}`, 'info');
        });
        
        debugLog(`Gebäude importiert: ${buildingData.components.length} Komponenten`, 'info');
        this.needsRender = true;
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
                    builder3d.showPropertiesPanel('ghost', tool);
                } else {
                    // Bei "select" Tool Properties Panel nur anzeigen wenn Objekt ausgewählt
                    if (!builder3d.selectedObject) {
                        builder3d.hidePropertiesPanel();
                    } else {
                        builder3d.showPropertiesPanel('placed');
                    }
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

// Close Properties Panel
function closePropertiesPanel() {
    if (builder3d) {
        builder3d.hidePropertiesPanel();
        builder3d.clearSelection();
    }
}

// Globale Funktionen verfügbar machen
window.toggleMoveMode = toggleMoveMode;
window.deleteSelectedComponent = deleteSelectedComponent;
window.closePropertiesPanel = closePropertiesPanel;

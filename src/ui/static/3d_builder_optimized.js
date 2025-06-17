/**
 * Schlanker 3D Builder für energyOS - Optimiert
 */

// Debug-Logging
function debugLog(message, type = 'info') {
    const timestamp = new Date().toLocaleTimeString();
    const typeLabel = { 'info': '[INFO]', 'warn': '[WARN]', 'error': '[ERROR]', 'success': '[SUCCESS]' }[type] || '[LOG]';
    console.log(`${timestamp} ${typeLabel} ${message}`);
    
    const debugContent = document.getElementById('debug-content');
    if (debugContent) {
        const entry = document.createElement('div');
        entry.className = `debug-log-entry ${type}`;
        entry.textContent = `${timestamp} ${typeLabel} ${message}`;
        debugContent.appendChild(entry);
        debugContent.scrollTop = debugContent.scrollHeight;
        
        const entries = debugContent.querySelectorAll('.debug-log-entry');
        if (entries.length > 50) entries[0].remove();
    }
}

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
        this.moveMode = false;
        this.isDragging = false;
        this.justDragged = false;
        this.mouse = new THREE.Vector2();
        this.raycaster = new THREE.Raycaster();
        this.dragStart = new THREE.Vector2();
        
        // Default-Werte für Komponenten
        this.componentDefaults = {
            wall: { width: 200, height: 250, depth: 20, uValue: 0.24, color: 0x8BC34A },
            door: { width: 80, height: 200, depth: 5, uValue: 1.8, color: 0x795548 },
            window: { width: 120, height: 100, depth: 5, uValue: 1.3, color: 0x2196F3 },
            roof: { width: 300, height: 20, depth: 300, uValue: 0.18, color: 0x9E9E9E },
            floor: { width: 300, height: 20, depth: 300, uValue: 0.35, color: 0x607D8B }
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
        this.renderer = new THREE.WebGLRenderer({ antialias: false, alpha: false, powerPreference: "high-performance" });
        this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
        this.renderer.setSize(this.container.clientWidth, this.container.clientHeight);
        this.renderer.shadowMap.enabled = false;
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
        this.controls.addEventListener('change', () => { this.needsRender = true; });
    }
    
    setupGrid() {
        const gridHelper = new THREE.GridHelper(2000, 100, 0x888888, 0xcccccc);
        gridHelper.position.y = 0;
        this.scene.add(gridHelper);
    }
    
    setupLighting() {
        const ambientLight = new THREE.AmbientLight(0x404040, 0.6);
        this.scene.add(ambientLight);
        const directionalLight = new THREE.DirectionalLight(0xffffff, 0.8);
        directionalLight.position.set(100, 100, 50);
        this.scene.add(directionalLight);
    }
    
    setupEventListeners() {
        window.addEventListener('resize', () => this.onWindowResize(), false);
        this.container.addEventListener('mousedown', (e) => this.onMouseDown(e), false);
        this.container.addEventListener('mousemove', (e) => this.onMouseMove(e), false);
        this.container.addEventListener('mouseup', (e) => this.onMouseUp(e), false);
        this.container.addEventListener('click', (e) => this.onClick(e), false);
    }
    
    startRenderLoop() {
        const animate = () => {
            if (!this.isAnimating) return;
            requestAnimationFrame(animate);
            if (this.controls) this.controls.update();
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
            this.raycaster.setFromCamera(this.mouse, this.camera);
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
            setTimeout(() => { this.justDragged = false; }, 100);
            debugLog('Objekt verschoben', 'info');
        }
    }
    
    onClick(event) {
        if (!this.editMode || this.justDragged) return;
        this.updateMousePosition(event);
        this.raycaster.setFromCamera(this.mouse, this.camera);
        
        if (this.currentTool === 'select') {
            const intersects = this.raycaster.intersectObjects(this.scene.children, false);
            const clickedObject = intersects.find(i => i.object.userData.isComponent);
            if (clickedObject) {
                this.selectObject(clickedObject.object);
            } else {
                this.clearSelection();
            }
        } else if (this.ghostObject && this.ghostObject.visible) {
            this.placeComponent(this.currentTool, this.ghostObject.position.clone());
        }
    }
    
    toggleEditMode() {
        this.editMode = !this.editMode;
        const btn = document.getElementById('edit-mode-btn');
        const info = document.getElementById('edit-mode-info');
        
        if (this.editMode) {
            btn.classList.add('active');
            btn.textContent = '✏️ Bearbeitung AUS';
            info.style.display = 'block';
        } else {
            btn.classList.remove('active');
            btn.textContent = '✏️ Bearbeitung AN';
            info.style.display = 'none';
            this.clearSelection();
            this.clearGhost();
        }
        
        this.needsRender = true;
        debugLog(`Bearbeitungsmodus: ${this.editMode ? 'AN' : 'AUS'}`, 'info');
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
    
    createGhost(toolType) {
        const defaults = this.componentDefaults[toolType];
        const geometry = new THREE.BoxGeometry(defaults.width, defaults.height, defaults.depth);
        const material = new THREE.MeshLambertMaterial({ color: 0x4CAF50, transparent: true, opacity: 0.3 });
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
    
    placeComponent(type, position) {
        const defaults = this.componentDefaults[type];
        const geometry = new THREE.BoxGeometry(defaults.width, defaults.height, defaults.depth);
        const material = new THREE.MeshLambertMaterial({ color: defaults.color });
        const component = new THREE.Mesh(geometry, material);
        
        component.position.copy(position);
        component.userData = {
            isComponent: true,
            type: type,
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
        this.setTool('select');
        this.needsRender = true;
        debugLog(`${type} bei (${Math.round(position.x)}, ${Math.round(position.y)}, ${Math.round(position.z)}) platziert`, 'success');
    }
    
    selectObject(object) {
        this.clearSelection();
        this.selectedObject = object;
        if (object.material.emissive) {
            object.material.emissive.setHex(0x444444);
        }
        this.showPropertiesPanel();
        this.needsRender = true;
        debugLog(`${object.userData.type} ausgewählt`, 'info');
    }
    
    clearSelection() {
        if (this.selectedObject) {
            if (this.selectedObject.material.emissive) {
                this.selectedObject.material.emissive.setHex(0x000000);
            }
            this.selectedObject = null;
            this.hidePropertiesPanel();
            this.needsRender = true;
        }
    }
    
    showPropertiesPanel() {
        if (!this.selectedObject) return;
        const panel = document.getElementById('properties-panel');
        const content = document.getElementById('properties-content');
        const props = this.selectedObject.userData.properties;
        const type = this.selectedObject.userData.type;
        const defaults = this.componentDefaults[type];
        
        content.innerHTML = `
            <div class="property-group">
                <div class="property-label">Typ</div>
                <div style="font-weight: 500; color: #333;">${type.toUpperCase()}</div>
            </div>
            
            <div class="property-group">
                <div class="property-label">Abmessungen (cm)</div>
                <div class="property-row">
                    <input type="number" class="property-input ${props.width === defaults.width ? 'default' : ''}" id="prop-width" value="${props.width}" placeholder="Breite">
                    <input type="number" class="property-input ${props.height === defaults.height ? 'default' : ''}" id="prop-height" value="${props.height}" placeholder="Höhe">
                    <input type="number" class="property-input ${props.depth === defaults.depth ? 'default' : ''}" id="prop-depth" value="${props.depth}" placeholder="Tiefe">
                </div>
            </div>
            
            <div class="property-group">
                <div class="property-label">U-Wert (W/m²K)</div>
                <input type="number" class="property-input ${props.uValue === defaults.uValue ? 'default' : ''}" id="prop-uvalue" value="${props.uValue}" step="0.01" placeholder="U-Wert">
            </div>
            
            <div class="property-group">
                <div class="property-label">Position (cm)</div>
                <div class="property-row two-col">
                    <input type="number" class="property-input" id="prop-pos-x" value="${Math.round(props.position.x)}" placeholder="X">
                    <input type="number" class="property-input" id="prop-pos-y" value="${Math.round(props.position.y)}" placeholder="Y">
                    <input type="number" class="property-input" id="prop-pos-z" value="${Math.round(props.position.z)}" placeholder="Z">
                    <button class="move-btn ${this.moveMode ? 'active' : ''}" id="move-btn" onclick="toggleMoveMode()">↔️</button>
                </div>
            </div>
            
            <div class="property-group">
                <div class="property-label">Rotation (°)</div>
                <div class="property-row">
                    <input type="number" class="property-input" id="prop-rot-x" value="${Math.round(props.rotation.x * 180 / Math.PI)}" placeholder="X">
                    <input type="number" class="property-input" id="prop-rot-y" value="${Math.round(props.rotation.y * 180 / Math.PI)}" placeholder="Y">
                    <input type="number" class="property-input" id="prop-rot-z" value="${Math.round(props.rotation.z * 180 / Math.PI)}" placeholder="Z">
                </div>
            </div>
            
            <div class="property-actions">
                <button class="delete-btn" onclick="deleteSelected()">🗑️ Löschen</button>
            </div>
        `;
        
        panel.style.display = 'block';
        this.setupAutoUpdate();
    }
    
    hidePropertiesPanel() {
        const panel = document.getElementById('properties-panel');
        panel.style.display = 'none';
    }
    
    setupAutoUpdate() {
        const inputs = ['prop-width', 'prop-height', 'prop-depth', 'prop-uvalue', 'prop-pos-x', 'prop-pos-y', 'prop-pos-z', 'prop-rot-x', 'prop-rot-y', 'prop-rot-z'];
        inputs.forEach(id => {
            const input = document.getElementById(id);
            if (input) {
                input.addEventListener('input', () => {
                    input.classList.remove('default');
                    this.applyProperties();
                });
            }
        });
    }
    
    updatePropertiesPanel() {
        if (!this.selectedObject) return;
        const props = this.selectedObject.userData.properties;
        const posX = document.getElementById('prop-pos-x');
        const posY = document.getElementById('prop-pos-y');
        const posZ = document.getElementById('prop-pos-z');
        if (posX) posX.value = Math.round(props.position.x);
        if (posY) posY.value = Math.round(props.position.y);
        if (posZ) posZ.value = Math.round(props.position.z);
    }
    
    applyProperties() {
        if (!this.selectedObject) return;
        const props = this.selectedObject.userData.properties;
        
        const width = parseFloat(document.getElementById('prop-width').value) || props.width;
        const height = parseFloat(document.getElementById('prop-height').value) || props.height;
        const depth = parseFloat(document.getElementById('prop-depth').value) || props.depth;
        const posX = parseFloat(document.getElementById('prop-pos-x').value) || props.position.x;
        const posY = parseFloat(document.getElementById('prop-pos-y').value) || props.position.y;
        const posZ = parseFloat(document.getElementById('prop-pos-z').value) || props.position.z;
        const rotX = (parseFloat(document.getElementById('prop-rot-x').value) || 0) * Math.PI / 180;
        const rotY = (parseFloat(document.getElementById('prop-rot-y').value) || 0) * Math.PI / 180;
        const rotZ = (parseFloat(document.getElementById('prop-rot-z').value) || 0) * Math.PI / 180;
        const uValue = parseFloat(document.getElementById('prop-uvalue').value) || props.uValue;
        
        if (width !== props.width || height !== props.height || depth !== props.depth) {
            const newGeometry = new THREE.BoxGeometry(width, height, depth);
            this.selectedObject.geometry.dispose();
            this.selectedObject.geometry = newGeometry;
        }
        
        this.selectedObject.position.set(posX, posY, posZ);
        this.selectedObject.rotation.set(rotX, rotY, rotZ);
        
        props.width = width;
        props.height = height;
        props.depth = depth;
        props.position = { x: posX, y: posY, z: posZ };
        props.rotation = { x: rotX, y: rotY, z: rotZ };
        props.uValue = uValue;
        
        this.needsRender = true;
    }
    
    updateToolButtons() {
        const toolButtons = document.querySelectorAll('.tool-btn');
        toolButtons.forEach(btn => {
            btn.classList.remove('active');
            if (btn.dataset.tool === this.currentTool) {
                btn.classList.add('active');
            }
        });
    }
    
    clearScene() {
        const objectsToRemove = [];
        this.scene.traverse((child) => {
            if (child.userData && child.userData.isComponent) {
                objectsToRemove.push(child);
            }
        });
        objectsToRemove.forEach(obj => {
            this.scene.remove(obj);
            if (obj.geometry) obj.geometry.dispose();
            if (obj.material) obj.material.dispose();
        });
        this.clearSelection();
        this.needsRender = true;
        debugLog('Szene geleert', 'info');
    }
    
    dispose() {
        this.isAnimating = false;
        if (this.controls) this.controls.dispose();
        if (this.renderer) this.renderer.dispose();
        debugLog('3D-Builder entsorgt', 'info');
    }
}

// Globale Variablen
let builder3d = null;

// Initialisierung
document.addEventListener('DOMContentLoaded', () => {
    debugLog('DOM geladen, starte 3D-Builder...', 'info');
    try {
        if (typeof THREE === 'undefined') throw new Error('Three.js nicht geladen');
        if (typeof THREE.OrbitControls === 'undefined') throw new Error('OrbitControls nicht geladen');
        
        builder3d = new Simple3DBuilder('building-3d');
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
            }
        });
    });
}

// Globale Funktionen
function toggleEditMode() {
    if (builder3d) builder3d.toggleEditMode();
}

function toggleMoveMode() {
    if (builder3d) {
        builder3d.moveMode = !builder3d.moveMode;
        const btn = document.getElementById('move-btn');
        if (btn) {
            btn.classList.toggle('active', builder3d.moveMode);
        }
        debugLog(`Verschieben-Modus: ${builder3d.moveMode ? 'AN' : 'AUS'}`, 'info');
    }
}

function deleteSelected() {
    if (builder3d && builder3d.selectedObject) {
        const type = builder3d.selectedObject.userData.type;
        builder3d.scene.remove(builder3d.selectedObject);
        if (builder3d.selectedObject.geometry) builder3d.selectedObject.geometry.dispose();
        if (builder3d.selectedObject.material) builder3d.selectedObject.material.dispose();
        builder3d.selectedObject = null;
        builder3d.hidePropertiesPanel();
        builder3d.needsRender = true;
        debugLog(`${type} gelöscht`, 'info');
    }
}

function clearScene() {
    if (builder3d) builder3d.clearScene();
}

function saveBuilding() {
    if (!builder3d) return;
    const components = [];
    builder3d.scene.traverse((child) => {
        if (child.userData && child.userData.isComponent) {
            components.push({
                type: child.userData.type,
                properties: child.userData.properties,
                position: { x: child.position.x, y: child.position.y, z: child.position.z },
                rotation: { x: child.rotation.x, y: child.rotation.y, z: child.rotation.z }
            });
        }
    });
    localStorage.setItem('energyOS_building', JSON.stringify(components));
    debugLog('Gebäude gespeichert', 'success');
}

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

// Globale Funktionen verfügbar machen
window.debugLog = debugLog;
window.toggleEditMode = toggleEditMode;
window.toggleMoveMode = toggleMoveMode;
window.deleteSelected = deleteSelected;
window.clearScene = clearScene;
window.saveBuilding = saveBuilding;
window.toggleDebugPanel = toggleDebugPanel;
window.clearDebugLog = clearDebugLog;

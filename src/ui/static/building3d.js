/**
 * Building3D - 3D-Gebäudevisualisierung und -editor
 * Basiert auf Three.js für die 3D-Darstellung
 */

class Building3D {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        this.buildingData = null;
        this.selectedObject = null;
        this.wireframeMode = false;
        
        // Three.js Komponenten
        this.scene = null;
        this.camera = null;
        this.renderer = null;
        this.controls = null;
        
        // Gebäude-Objekte
        this.buildingGroup = null;
        this.walls = [];
        this.windows = [];
        this.roof = null;
        this.floor = null;
        
        // Materialien
        this.materials = {};
        
        this.init();
    }
    
    init() {
        this.setupScene();
        this.setupCamera();
        this.setupRenderer();
        this.setupControls();
        this.setupLights();
        this.setupMaterials();
        this.setupEventListeners();
        this.animate();
    }
    
    setupScene() {
        this.scene = new THREE.Scene();
        this.scene.background = new THREE.Color(0x87CEEB); // Himmelblau
        
        // Fog für Tiefenwahrnehmung
        this.scene.fog = new THREE.Fog(0x87CEEB, 10, 1000);
        
        // Hauptgruppe für das Gebäude
        this.buildingGroup = new THREE.Group();
        this.scene.add(this.buildingGroup);
        
        // Boden/Grundstück
        this.createGround();
    }
    
    setupCamera() {
        this.camera = new THREE.PerspectiveCamera(
            75, 
            this.container.clientWidth / this.container.clientHeight, 
            0.1, 
            1000
        );
        this.camera.position.set(15, 10, 15);
        this.camera.lookAt(0, 0, 0);
    }
    
    setupRenderer() {
        this.renderer = new THREE.WebGLRenderer({ antialias: true });
        this.renderer.setSize(this.container.clientWidth, this.container.clientHeight);
        this.renderer.setPixelRatio(window.devicePixelRatio);
        this.renderer.shadowMap.enabled = true;
        this.renderer.shadowMap.type = THREE.PCFSoftShadowMap;
        this.container.appendChild(this.renderer.domElement);
    }
    
    setupControls() {
        // OrbitControls richtig initialisieren - verschiedene Import-Wege unterstützen
        let OrbitControlsClass = THREE.OrbitControls || window.OrbitControls;
        
        if (!OrbitControlsClass) {
            console.error('OrbitControls nicht verfügbar');
            return;
        }
        
        this.controls = new OrbitControlsClass(this.camera, this.renderer.domElement);
        this.controls.enableDamping = true;
        this.controls.dampingFactor = 0.05;
        this.controls.enableZoom = true;
        this.controls.enablePan = true;
        this.controls.maxPolarAngle = Math.PI / 2; // Verhindert Kamera unter dem Boden
        this.controls.minDistance = 2;
        this.controls.maxDistance = 100;
    }
    
    setupLights() {
        // Hauptlicht (Sonne)
        const directionalLight = new THREE.DirectionalLight(0xffffff, 1);
        directionalLight.position.set(50, 50, 50);
        directionalLight.castShadow = true;
        directionalLight.shadow.mapSize.width = 2048;
        directionalLight.shadow.mapSize.height = 2048;
        directionalLight.shadow.camera.near = 0.5;
        directionalLight.shadow.camera.far = 500;
        directionalLight.shadow.camera.left = -50;
        directionalLight.shadow.camera.right = 50;
        directionalLight.shadow.camera.top = 50;
        directionalLight.shadow.camera.bottom = -50;
        this.scene.add(directionalLight);
        
        // Umgebungslicht
        const ambientLight = new THREE.AmbientLight(0x404040, 0.3);
        this.scene.add(ambientLight);
        
        // Hemisphärisches Licht für natürlichere Beleuchtung
        const hemiLight = new THREE.HemisphereLight(0xffffbb, 0x080820, 0.3);
        this.scene.add(hemiLight);
    }
    
    setupMaterials() {
        // Wandmaterial
        this.materials.wall = new THREE.MeshLambertMaterial({
            color: 0xffffff,
            transparent: true,
            opacity: 0.9
        });
        
        this.materials.wallWireframe = new THREE.MeshBasicMaterial({
            color: 0x000000,
            wireframe: true
        });
        
        // Fenstermaterial
        this.materials.window = new THREE.MeshPhysicalMaterial({
            color: 0x87CEEB,
            transparent: true,
            opacity: 0.3,
            transmission: 0.9,
            ior: 1.5
        });
        
        // Dachmaterial
        this.materials.roof = new THREE.MeshLambertMaterial({
            color: 0x8B4513
        });
        
        // Bodenmaterial
        this.materials.floor = new THREE.MeshLambertMaterial({
            color: 0xD2B48C
        });
        
        // Grundstücksmaterial
        this.materials.ground = new THREE.MeshLambertMaterial({
            color: 0x228B22
        });
        
        // Auswahlmaterial
        this.materials.selected = new THREE.MeshBasicMaterial({
            color: 0xff0000,
            transparent: true,
            opacity: 0.5
        });
    }
    
    createGround() {
        const groundGeometry = new THREE.PlaneGeometry(50, 50);
        const ground = new THREE.Mesh(groundGeometry, this.materials.ground);
        ground.rotation.x = -Math.PI / 2;
        ground.position.y = -0.1;
        ground.receiveShadow = true;
        this.scene.add(ground);
    }
    
    setupEventListeners() {
        // Fenstergröße ändern
        window.addEventListener('resize', () => this.onWindowResize());
        
        // Mausklicks für Objektauswahl
        this.renderer.domElement.addEventListener('click', (event) => this.onMouseClick(event));
        
        // Tastatureingaben
        window.addEventListener('keydown', (event) => this.onKeyDown(event));
    }
    
    loadBuilding(buildingData) {
        this.buildingData = buildingData;
        this.clearBuilding();
        this.createBuilding();
    }
    
    clearBuilding() {
        // Alle Gebäude-Objekte entfernen
        while (this.buildingGroup.children.length > 0) {
            this.buildingGroup.remove(this.buildingGroup.children[0]);
        }
        
        this.walls = [];
        this.windows = [];
        this.roof = null;
        this.floor = null;
    }
    
    createBuilding() {
        if (!this.buildingData) return;
        
        const geometry = this.buildingData.geometry;
        
        // Wände erstellen
        this.createWalls(geometry.walls);
        
        // Fenster erstellen
        this.createWindows(geometry.windows);
        
        // Dach erstellen
        this.createRoof(geometry.roof);
        
        // Boden erstellen
        this.createFloor(geometry.floor);
        
        // Schatten aktivieren
        this.buildingGroup.traverse((child) => {
            if (child.isMesh) {
                child.castShadow = true;
                child.receiveShadow = true;
            }
        });
    }
    
    createWalls(wallsData) {
        wallsData.forEach((wallData, index) => {
            const geometry = new THREE.BoxGeometry(
                wallData.width, 
                wallData.height, 
                0.3
            );
            
            const wall = new THREE.Mesh(geometry, this.materials.wall);
            
            // Position setzen
            wall.position.set(
                wallData.position.x,
                wallData.height / 2,
                wallData.position.z
            );
            
            // Rotation setzen
            wall.rotation.y = THREE.MathUtils.degToRad(wallData.position.rotation);
            
            // Metadaten speichern
            wall.userData = {
                type: 'wall',
                id: wallData.id,
                orientation: wallData.orientation,
                uValue: wallData.u_value
            };
            
            this.walls.push(wall);
            this.buildingGroup.add(wall);
        });
    }
    
    createWindows(windowsData) {
        windowsData.forEach((windowData, index) => {
            const geometry = new THREE.BoxGeometry(
                windowData.width,
                windowData.height,
                0.1
            );
            
            const window = new THREE.Mesh(geometry, this.materials.window);
            
            // Position leicht vor der Wand
            window.position.set(
                windowData.position.x,
                windowData.position.y,
                windowData.position.z
            );
            
            // Rotation entsprechend der Wand
            window.rotation.y = THREE.MathUtils.degToRad(windowData.position.rotation);
            
            // Fenster leicht vor die Wand setzen
            const offset = 0.2;
            switch(windowData.orientation) {
                case 'S':
                    window.position.z -= offset;
                    break;
                case 'N':
                    window.position.z += offset;
                    break;
                case 'E':
                    window.position.x -= offset;
                    break;
                case 'W':
                    window.position.x += offset;
                    break;
            }
            
            // Metadaten speichern
            window.userData = {
                type: 'window',
                id: windowData.id,
                orientation: windowData.orientation,
                uValue: windowData.u_value,
                gValue: windowData.g_value
            };
            
            this.windows.push(window);
            this.buildingGroup.add(window);
        });
    }
    
    createRoof(roofData) {
        const geometry = new THREE.BoxGeometry(
            roofData.width + 1,  // Dachüberstand
            0.3,
            roofData.depth + 1
        );
        
        this.roof = new THREE.Mesh(geometry, this.materials.roof);
        
        // Position und Neigung
        this.roof.position.set(
            roofData.width / 2,
            this.buildingData.geometry.dimensions.height + 0.5,
            roofData.depth / 2
        );
        
        // Dachneigung
        this.roof.rotation.z = THREE.MathUtils.degToRad(roofData.tilt);
        
        // Metadaten
        this.roof.userData = {
            type: 'roof',
            tilt: roofData.tilt,
            area: roofData.area
        };
        
        this.buildingGroup.add(this.roof);
    }
    
    createFloor(floorData) {
        const geometry = new THREE.BoxGeometry(
            floorData.width,
            0.2,
            floorData.depth
        );
        
        this.floor = new THREE.Mesh(geometry, this.materials.floor);
        
        this.floor.position.set(
            floorData.width / 2,
            0,
            floorData.depth / 2
        );
        
        // Metadaten
        this.floor.userData = {
            type: 'floor',
            area: floorData.area
        };
        
        this.buildingGroup.add(this.floor);
    }
    
    updateDimensions(width, depth, height) {
        if (!this.buildingData) return;
        
        // Gebäudedaten aktualisieren
        this.buildingData.geometry.dimensions = { width, depth, height };
        
        // Gebäude neu erstellen
        this.createBuilding();
    }
    
    updateWalls(wallType, selectedWall) {
        const uValues = {
            'standard': 0.24,
            'insulated': 0.15,
            'passive': 0.10
        };
        
        const colors = {
            'standard': 0xffffff,
            'insulated': 0xf0f8ff,
            'passive': 0xe6ffe6
        };
        
        const uValue = uValues[wallType] || 0.24;
        const color = colors[wallType] || 0xffffff;
        
        this.walls.forEach(wall => {
            if (selectedWall === 'all' || wall.userData.orientation === selectedWall.toUpperCase()) {
                wall.material.color.setHex(color);
                wall.userData.uValue = uValue;
            }
        });
    }
    
    addWindow(windowConfig) {
        // Implementierung für das Hinzufügen neuer Fenster
        console.log('Füge Fenster hinzu:', windowConfig);
        
        // TODO: Fenster zur entsprechenden Wand hinzufügen
        // Gebäude neu erstellen mit aktualisierten Daten
        this.createBuilding();
    }
    
    removeSelectedWindow() {
        if (this.selectedObject && this.selectedObject.userData.type === 'window') {
            this.buildingGroup.remove(this.selectedObject);
            this.windows = this.windows.filter(w => w !== this.selectedObject);
            this.selectedObject = null;
        }
    }
    
    updateRoof(tilt, type) {
        if (!this.roof) return;
        
        // Dachneigung aktualisieren
        this.roof.rotation.z = THREE.MathUtils.degToRad(tilt);
        this.roof.userData.tilt = tilt;
        
        // Dachmaterial je nach Typ
        const colors = {
            'standard': 0x8B4513,
            'insulated': 0x696969,
            'passive': 0x2F4F4F
        };
        
        this.roof.material.color.setHex(colors[type] || 0x8B4513);
    }
    
    toggleWireframe() {
        this.wireframeMode = !this.wireframeMode;
        
        this.buildingGroup.traverse((child) => {
            if (child.isMesh) {
                child.material.wireframe = this.wireframeMode;
            }
        });
    }
    
    resetCamera() {
        this.camera.position.set(15, 10, 15);
        this.camera.lookAt(0, 0, 0);
        this.controls.reset();
    }
    
    onWindowResize() {
        this.camera.aspect = this.container.clientWidth / this.container.clientHeight;
        this.camera.updateProjectionMatrix();
        this.renderer.setSize(this.container.clientWidth, this.container.clientHeight);
    }
    
    onMouseClick(event) {
        // Raycasting für Objektauswahl
        const mouse = new THREE.Vector2();
        const rect = this.renderer.domElement.getBoundingClientRect();
        
        mouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
        mouse.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;
        
        const raycaster = new THREE.Raycaster();
        raycaster.setFromCamera(mouse, this.camera);
        
        const intersects = raycaster.intersectObjects(this.buildingGroup.children);
        
        if (intersects.length > 0) {
            this.selectObject(intersects[0].object);
        } else {
            this.deselectObject();
        }
    }
    
    selectObject(object) {
        // Vorherige Auswahl zurücksetzen
        this.deselectObject();
        
        this.selectedObject = object;
        
        // Auswahlhighlight
        object.originalMaterial = object.material;
        object.material = this.materials.selected;
        
        // Objektinformationen anzeigen
        this.displayObjectInfo(object);
    }
    
    deselectObject() {
        if (this.selectedObject) {
            // Material zurücksetzen
            this.selectedObject.material = this.selectedObject.originalMaterial;
            this.selectedObject = null;
        }
    }
    
    displayObjectInfo(object) {
        const info = object.userData;
        console.log('Ausgewähltes Objekt:', info);
        
        // TODO: Objektinformationen in der UI anzeigen
    }
    
    onKeyDown(event) {
        switch(event.code) {
            case 'Delete':
                if (this.selectedObject && this.selectedObject.userData.type === 'window') {
                    this.removeSelectedWindow();
                }
                break;
            case 'Escape':
                this.deselectObject();
                break;
        }
    }
    
    animate() {
        requestAnimationFrame(() => this.animate());
        
        // Steuerung aktualisieren
        this.controls.update();
        
        // Statistiken aktualisieren
        this.updateStats();
        
        // Szene rendern
        this.renderer.render(this.scene, this.camera);
    }
    
    updateStats() {
        // FPS-Zähler (vereinfacht)
        if (!this.lastTime) this.lastTime = performance.now();
        const now = performance.now();
        const fps = Math.round(1000 / (now - this.lastTime));
        this.lastTime = now;
        
        // Stats anzeigen
        document.getElementById('fps').textContent = fps;
        document.getElementById('polygons').textContent = this.renderer.info.render.triangles;
        document.getElementById('objects').textContent = this.scene.children.length;
    }
}

// Utility-Funktionen
function getUValueColor(uValue) {
    // Farbkodierung basierend auf U-Wert
    if (uValue <= 0.15) return 0x00ff00; // Grün - sehr gut
    if (uValue <= 0.24) return 0xffff00; // Gelb - gut
    if (uValue <= 0.40) return 0xff8000; // Orange - mäßig
    return 0xff0000; // Rot - schlecht
}

function formatEnergyValue(value, unit) {
    return `${value.toFixed(2)} ${unit}`;
}

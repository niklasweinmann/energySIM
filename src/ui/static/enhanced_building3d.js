/**
 * Erweiterte 3D-Gebäudedarstellung für energyOS
 * ============================================
 * 
 * Detaillierte 3D-Visualisierung mit allen Bauteilen:
 * - Wände mit U-Werten und Materialien
 * - Fenster und Türen mit thermischen Eigenschaften
 * - Dachflächen mit PV-Potenzial
 * - Heizkörper und Heizflächen
 * - Wärmebrücken und Verschattungselemente
 * - Interaktive Bearbeitung mit Drag & Drop
 * - Erweiterte Bauteilbearbeitung
 */

class EnhancedBuilding3D {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        this.buildingData = null;
        this.selectedObject = null;
        this.wireframeMode = false;
        this.editMode = false;
        this.isPlacing = false;
        this.placingType = null;
        
        // Three.js Komponenten
        this.scene = null;
        this.camera = null;
        this.renderer = null;
        this.controls = null;
        this.raycaster = new THREE.Raycaster();
        this.mouse = new THREE.Vector2();
        
        // Gebäude-Objekte
        this.buildingGroup = null;
        this.walls = [];
        this.windows = [];
        this.doors = [];
        this.roof = null;
        this.floor = null;
        this.radiators = [];
        this.thermalBridges = [];
        this.shadingElements = [];
        
        // Materialien
        this.materials = {};
        
        // UI-Elemente
        this.infoPanel = null;
        this.editPanel = null;
        
        // Bearbeitungshelfer
        this.dragControls = null;
        this.ghostObject = null;
        
        this.init();
    }
    
    init() {
        try {
            console.log('🏗️ Starting EnhancedBuilding3D initialization...');
            
            this.setupScene();
            console.log('✅ Scene setup complete');
            
            this.setupCamera();
            console.log('✅ Camera setup complete');
            
            this.setupRenderer();
            console.log('✅ Renderer setup complete');
            
            this.setupControls();
            console.log('✅ Controls setup complete');
            
            this.setupLights();
            console.log('✅ Lights setup complete');
            
            this.setupMaterials();
            console.log('✅ Materials setup complete');
            
            // Erstelle ein einfaches Test-Gebäude als Fallback
            this.createDefaultBuilding();
            console.log('✅ Default building created');
            
            this.setupInfoPanel();
            console.log('✅ Info panel setup complete');
            
            this.setupEventListeners();
            console.log('✅ Event listeners setup complete');
            
            this.animate();
            console.log('✅ Animation started');
            
            console.log('🎉 EnhancedBuilding3D initialization complete!');
            
        } catch (error) {
            console.error('❌ Error during EnhancedBuilding3D initialization:', error);
            // Fallback: Erstelle minimale 3D-Szene
            this.createMinimalScene();
        }
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
        this.camera.position.set(20, 15, 20);
        this.camera.lookAt(0, 0, 0);
    }
    
    setupRenderer() {
        this.renderer = new THREE.WebGLRenderer({ 
            antialias: true,
            alpha: true
        });
        this.renderer.setSize(this.container.clientWidth, this.container.clientHeight);
        this.renderer.setPixelRatio(window.devicePixelRatio);
        this.renderer.shadowMap.enabled = true;
        this.renderer.shadowMap.type = THREE.PCFSoftShadowMap;
        this.renderer.outputEncoding = THREE.sRGBEncoding;
        this.renderer.toneMapping = THREE.ACESFilmicToneMapping;
        this.renderer.toneMappingExposure = 1.2;
        this.container.appendChild(this.renderer.domElement);
    }
    
    setupControls() {
        // OrbitControls richtig initialisieren
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
        this.controls.maxPolarAngle = Math.PI / 2;
        this.controls.minDistance = 5;
        this.controls.maxDistance = 200;
        
        // Smooth zoom
        this.controls.enableZoom = true;
        this.controls.zoomSpeed = 0.8;
        
        // Auto-rotate für Präsentation
        this.controls.autoRotate = false;
        this.controls.autoRotateSpeed = 0.2;
    }
    
    setupLights() {
        // Umgebungslicht
        const ambientLight = new THREE.AmbientLight(0x404040, 0.6);
        this.scene.add(ambientLight);
        
        // Direktionales Licht (Sonne)
        const directionalLight = new THREE.DirectionalLight(0xffffff, 1.0);
        directionalLight.position.set(50, 100, 50);
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
        
        // Punktlicht für bessere Ausleuchtung
        const pointLight = new THREE.PointLight(0xffffff, 0.5, 100);
        pointLight.position.set(-20, 20, 20);
        this.scene.add(pointLight);
        
        // Hemisphere Light für natürliche Beleuchtung
        const hemisphereLight = new THREE.HemisphereLight(0x87CEEB, 0x8B4513, 0.4);
        this.scene.add(hemisphereLight);
    }
    
    setupMaterials() {
        // Wandmaterialien mit verschiedenen U-Werten
        this.materials.wall_good = new THREE.MeshLambertMaterial({
            color: 0xf0f0f0,
            transparent: true,
            opacity: 0.9
        });
        
        this.materials.wall_medium = new THREE.MeshLambertMaterial({
            color: 0xffcc99,
            transparent: true,
            opacity: 0.9
        });
        
        this.materials.wall_poor = new THREE.MeshLambertMaterial({
            color: 0xff9999,
            transparent: true,
            opacity: 0.9
        });
        
        // Fenstermaterialien
        this.materials.window_2pane = new THREE.MeshPhysicalMaterial({
            color: 0x87CEEB,
            transparent: true,
            opacity: 0.3,
            transmission: 0.9,
            ior: 1.5,
            roughness: 0.1,
            metalness: 0.0
        });
        
        this.materials.window_3pane = new THREE.MeshPhysicalMaterial({
            color: 0x6BB6FF,
            transparent: true,
            opacity: 0.25,
            transmission: 0.95,
            ior: 1.5,
            roughness: 0.05,
            metalness: 0.0
        });
        
        // Türmaterialien
        this.materials.door_wood = new THREE.MeshLambertMaterial({
            color: 0x8B4513
        });
        
        this.materials.door_steel = new THREE.MeshLambertMaterial({
            color: 0x708090
        });
        
        // Dachmaterialien
        this.materials.roof_standard = new THREE.MeshLambertMaterial({
            color: 0x8B4513
        });
        
        this.materials.roof_pv = new THREE.MeshLambertMaterial({
            color: 0x1a1a2e
        });
        
        // Bodenmaterial
        this.materials.floor = new THREE.MeshLambertMaterial({
            color: 0xD2B48C
        });
        
        // Heizkörpermaterial
        this.materials.radiator = new THREE.MeshLambertMaterial({
            color: 0xffffff
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
        
        // Wärmebrückenmaterial
        this.materials.thermal_bridge = new THREE.MeshBasicMaterial({
            color: 0xff4444,
            transparent: true,
            opacity: 0.7
        });
        
        // Verschattungsmaterial
        this.materials.shading = new THREE.MeshLambertMaterial({
            color: 0x654321,
            transparent: true,
            opacity: 0.6
        });
    }
    
    setupInfoPanel() {
        // Info-Panel für Objektinformationen
        this.infoPanel = document.createElement('div');
        this.infoPanel.style.cssText = `
            position: absolute;
            top: 10px;
            left: 10px;
            background: rgba(0,0,0,0.8);
            color: white;
            padding: 10px;
            border-radius: 5px;
            font-family: monospace;
            font-size: 12px;
            display: none;
            max-width: 300px;
            z-index: 1000;
        `;
        this.container.appendChild(this.infoPanel);
    }
    
    createGround() {
        const groundGeometry = new THREE.PlaneGeometry(100, 100);
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
        this.renderer.domElement.addEventListener('mousemove', (event) => this.onMouseMove(event));
        
        // Tastatureingaben
        window.addEventListener('keydown', (event) => this.onKeyDown(event));
    }
    
    loadBuilding(buildingData) {
        this.buildingData = buildingData;
        this.clearBuilding();
        this.createBuilding();
    }
    
    clearBuilding() {
        // Entferne alle Gebäude-Objekte
        while (this.buildingGroup.children.length > 0) {
            this.buildingGroup.remove(this.buildingGroup.children[0]);
        }
        
        // Reset Arrays
        this.walls = [];
        this.windows = [];
        this.doors = [];
        this.radiators = [];
        this.thermalBridges = [];
        this.shadingElements = [];
        this.roof = null;
        this.floor = null;
    }
    
    createBuilding() {
        if (!this.buildingData) return;
        
        // Erstelle Bauteile in korrekter Reihenfolge
        this.createFloor();
        this.createWalls();
        this.createWindows();
        this.createDoors();
        this.createRoof();
        this.createRadiators();
        this.createThermalBridges();
        this.createShadingElements();
        
        // Zentriere Kamera auf Gebäude
        this.centerCameraOnBuilding();
    }
    
    createWalls() {
        if (!this.buildingData.walls) return;
        
        this.buildingData.walls.forEach(wallData => {
            // Wähle Material basierend auf U-Wert
            let material;
            if (wallData.u_value <= 0.15) {
                material = this.materials.wall_good;
            } else if (wallData.u_value <= 0.28) {
                material = this.materials.wall_medium;
            } else {
                material = this.materials.wall_poor;
            }
            
            // Erstelle Wandgeometrie
            const geometry = new THREE.BoxGeometry(
                wallData.width,
                wallData.height,
                0.3
            );
            
            const wall = new THREE.Mesh(geometry, material);
            
            // Positionierung
            wall.position.set(
                wallData.position.x,
                wallData.position.y + wallData.height / 2,
                wallData.position.z
            );
            
            // Rotation
            wall.rotation.y = THREE.MathUtils.degToRad(wallData.position.rotation);
            
            // Schatten
            wall.castShadow = true;
            wall.receiveShadow = true;
            
            // Metadaten
            wall.userData = {
                type: 'wall',
                id: wallData.id,
                name: wallData.name,
                area: wallData.area,
                u_value: wallData.u_value,
                orientation: wallData.orientation,
                is_external: wallData.is_external,
                layers: wallData.layers
            };
            
            this.walls.push(wall);
            this.buildingGroup.add(wall);
        });
    }
    
    createWindows() {
        if (!this.buildingData.windows) return;
        
        this.buildingData.windows.forEach(windowData => {
            // Wähle Material basierend auf Verglasungstyp
            const material = windowData.glazing_type === '3-fach' ? 
                this.materials.window_3pane : this.materials.window_2pane;
            
            // Erstelle Fenstergeometrie
            const geometry = new THREE.BoxGeometry(
                windowData.width,
                windowData.height,
                0.1
            );
            
            const window = new THREE.Mesh(geometry, material);
            
            // Positionierung
            window.position.set(
                windowData.position.x,
                windowData.position.y + windowData.height / 2,
                windowData.position.z
            );
            
            // Metadaten
            window.userData = {
                type: 'window',
                id: windowData.id,
                name: windowData.name,
                area: windowData.area,
                u_value: windowData.u_value,
                g_value: windowData.g_value,
                orientation: windowData.orientation,
                glazing_type: windowData.glazing_type,
                is_openable: windowData.is_openable
            };
            
            this.windows.push(window);
            this.buildingGroup.add(window);
        });
    }
    
    createDoors() {
        if (!this.buildingData.doors) return;
        
        this.buildingData.doors.forEach(doorData => {
            // Wähle Material basierend auf Türmaterial
            const material = doorData.material === 'steel' ? 
                this.materials.door_steel : this.materials.door_wood;
            
            // Erstelle Türgeometrie
            const geometry = new THREE.BoxGeometry(
                doorData.width,
                doorData.height,
                0.1
            );
            
            const door = new THREE.Mesh(geometry, material);
            
            // Positionierung
            door.position.set(
                doorData.position.x,
                doorData.position.y + doorData.height / 2,
                doorData.position.z
            );
            
            // Schatten
            door.castShadow = true;
            door.receiveShadow = true;
            
            // Metadaten
            door.userData = {
                type: 'door',
                id: doorData.id,
                name: doorData.name,
                area: doorData.area,
                u_value: doorData.u_value,
                orientation: doorData.orientation,
                door_type: doorData.door_type,
                material: doorData.material,
                is_main_entrance: doorData.is_main_entrance
            };
            
            this.doors.push(door);
            this.buildingGroup.add(door);
        });
    }
    
    createRoof() {
        if (!this.buildingData.roof) return;
        
        const roofData = this.buildingData.roof;
        
        // Wähle Material basierend auf PV-Eignung
        const material = roofData.pv_suitable ? 
            this.materials.roof_pv : this.materials.roof_standard;
        
        // Berechne Dachmaße basierend auf Gebäudedimensionen
        const dimensions = this.buildingData.dimensions;
        const roofWidth = dimensions.width + 1; // Dachüberstand
        const roofDepth = dimensions.depth + 1;
        
        // Erstelle Dachgeometrie
        const geometry = new THREE.BoxGeometry(
            roofWidth,
            0.3,
            roofDepth
        );
        
        this.roof = new THREE.Mesh(geometry, material);
        
        // Position und Neigung
        this.roof.position.set(
            dimensions.width / 2,
            dimensions.height + 0.5,
            dimensions.depth / 2
        );
        
        // Dachneigung
        this.roof.rotation.z = THREE.MathUtils.degToRad(roofData.tilt);
        
        // Schatten
        this.roof.castShadow = true;
        this.roof.receiveShadow = true;
        
        // Metadaten
        this.roof.userData = {
            type: 'roof',
            id: roofData.id,
            name: roofData.name,
            area: roofData.area,
            u_value: roofData.u_value,
            tilt: roofData.tilt,
            orientation: roofData.orientation,
            roof_type: roofData.roof_type,
            pv_suitable: roofData.pv_suitable,
            pv_area_available: roofData.pv_area_available
        };
        
        this.buildingGroup.add(this.roof);
    }
    
    createFloor() {
        if (!this.buildingData.floor) return;
        
        const floorData = this.buildingData.floor;
        const dimensions = this.buildingData.dimensions;
        
        // Erstelle Bodengeometrie
        const geometry = new THREE.BoxGeometry(
            dimensions.width,
            0.2,
            dimensions.depth
        );
        
        this.floor = new THREE.Mesh(geometry, this.materials.floor);
        
        this.floor.position.set(
            dimensions.width / 2,
            0,
            dimensions.depth / 2
        );
        
        // Schatten
        this.floor.receiveShadow = true;
        
        // Metadaten
        this.floor.userData = {
            type: 'floor',
            id: floorData.id,
            name: floorData.name,
            area: floorData.area,
            u_value: floorData.u_value,
            floor_type: floorData.floor_type,
            ground_coupling: floorData.ground_coupling,
            has_underfloor_heating: floorData.has_underfloor_heating
        };
        
        this.buildingGroup.add(this.floor);
    }
    
    createRadiators() {
        if (!this.buildingData.radiators) return;
        
        this.buildingData.radiators.forEach(radiatorData => {
            // Erstelle Heizkörpergeometrie
            const geometry = new THREE.BoxGeometry(
                radiatorData.dimensions.width,
                radiatorData.dimensions.height,
                radiatorData.dimensions.depth
            );
            
            const radiator = new THREE.Mesh(geometry, this.materials.radiator);
            
            // Positionierung
            radiator.position.set(
                radiatorData.position.x,
                radiatorData.position.y + radiatorData.dimensions.height / 2,
                radiatorData.position.z
            );
            
            // Schatten
            radiator.castShadow = true;
            radiator.receiveShadow = true;
            
            // Metadaten
            radiator.userData = {
                type: 'radiator',
                id: radiatorData.id,
                name: radiatorData.name,
                heating_power: radiatorData.heating_power,
                radiator_type: radiatorData.radiator_type,
                supply_temp: radiatorData.supply_temp,
                return_temp: radiatorData.return_temp,
                has_thermostatic_valve: radiatorData.has_thermostatic_valve
            };
            
            this.radiators.push(radiator);
            this.buildingGroup.add(radiator);
        });
    }
    
    createThermalBridges() {
        // Visualisierung von Wärmebrücken als kleine rote Linien/Punkte
        // TODO: Implementierung basierend auf Wärmebrückendaten
    }
    
    createShadingElements() {
        // Visualisierung von Verschattungselementen
        // TODO: Implementierung basierend auf Verschattungsdaten
    }
    
    centerCameraOnBuilding() {
        if (!this.buildingData || !this.buildingData.dimensions) return;
        
        const dimensions = this.buildingData.dimensions;
        const distance = Math.max(dimensions.width, dimensions.depth, dimensions.height) * 2;
        
        this.camera.position.set(
            dimensions.width / 2 + distance * 0.7,
            dimensions.height + distance * 0.5,
            dimensions.depth / 2 + distance * 0.7
        );
        
        this.camera.lookAt(
            dimensions.width / 2,
            dimensions.height / 2,
            dimensions.depth / 2
        );
        
        if (this.controls) {
            this.controls.target.set(
                dimensions.width / 2,
                dimensions.height / 2,
                dimensions.depth / 2
            );
            this.controls.update();
        }
    }
    
    updateDimensions(width, depth, height) {
        if (!this.buildingData) return;
        
        // Aktualisiere Gebäudedaten
        this.buildingData.dimensions = { width, depth, height };
        
        // Gebäude neu erstellen
        this.createBuilding();
    }
    
    updateRoof(tilt) {
        if (!this.roof || !this.buildingData.roof) return;
        
        // Dachneigung aktualisieren
        this.roof.rotation.z = THREE.MathUtils.degToRad(tilt);
        this.roof.userData.tilt = tilt;
        this.buildingData.roof.tilt = tilt;
    }
    
    toggleWireframe() {
        this.wireframeMode = !this.wireframeMode;
        
        this.buildingGroup.traverse((child) => {
            if (child.isMesh && child.material) {
                child.material.wireframe = this.wireframeMode;
            }
        });
    }
    
    resetCamera() {
        this.centerCameraOnBuilding();
    }
    
    onWindowResize() {
        this.camera.aspect = this.container.clientWidth / this.container.clientHeight;
        this.camera.updateProjectionMatrix();
        this.renderer.setSize(this.container.clientWidth, this.container.clientHeight);
    }
    
    enableEditMode() {
        // Aktiviert den Bearbeitungsmodus
        this.editMode = true;
        this.container.style.cursor = 'crosshair';
        
        // Drag Controls für Objekte aktivieren
        this.setupDragControls();
        
        // Edit Panel anzeigen
        this.showEditPanel();
    }
    
    disableEditMode() {
        // Deaktiviert den Bearbeitungsmodus
        this.editMode = false;
        this.isPlacing = false;
        this.placingType = null;
        this.container.style.cursor = 'default';
        
        // Drag Controls deaktivieren
        if (this.dragControls) {
            this.dragControls.dispose();
            this.dragControls = null;
        }
        
        // Ghost Object entfernen
        if (this.ghostObject) {
            this.scene.remove(this.ghostObject);
            this.ghostObject = null;
        }
        
        // Edit Panel verstecken
        this.hideEditPanel();
    }
    
    setupDragControls() {
        // Setzt Drag Controls für bewegbare Objekte auf
        // Nur Heizkörper und andere bewegbare Objekte
        const movableObjects = [...this.radiators];
        
        if (movableObjects.length > 0) {
            this.dragControls = new THREE.DragControls(movableObjects, this.camera, this.renderer.domElement);
            
            this.dragControls.addEventListener('dragstart', (event) => {
                this.controls.enabled = false;
                event.object.material.opacity = 0.5;
            });
            
            this.dragControls.addEventListener('dragend', (event) => {
                this.controls.enabled = true;
                event.object.material.opacity = 1.0;
                
                // Position aktualisieren
                this.updateComponentPosition(event.object);
            });
        }
    }
    
    startPlacing(componentType) {
        // Startet Platzierungsmodus für neue Komponente
        this.isPlacing = true;
        this.placingType = componentType;
        this.container.style.cursor = 'crosshair';
        
        // Ghost Object erstellen
        this.createGhostObject(componentType);
    }
    
    createGhostObject(componentType) {
        // Erstellt Ghost Object für Platzierungsvorschau
        let geometry, material;
        
        switch (componentType) {
            case 'wall':
                geometry = new THREE.BoxGeometry(0.2, 2.5, 4);
                material = new THREE.MeshBasicMaterial({
                    color: 0xffffff,
                    transparent: true,
                    opacity: 0.5,
                    wireframe: true
                });
                break;
                
            case 'window':
                geometry = new THREE.BoxGeometry(0.1, 1.5, 1.2);
                material = new THREE.MeshBasicMaterial({
                    color: 0x87CEEB,
                    transparent: true,
                    opacity: 0.3
                });
                break;
                
            case 'door':
                geometry = new THREE.BoxGeometry(0.1, 2.1, 1.0);
                material = new THREE.MeshBasicMaterial({
                    color: 0x8B4513,
                    transparent: true,
                    opacity: 0.5
                });
                break;
                
            case 'radiator':
                geometry = new THREE.BoxGeometry(1.0, 0.6, 0.15);
                material = new THREE.MeshBasicMaterial({
                    color: 0xffffff,
                    transparent: true,
                    opacity: 0.5
                });
                break;
        }
        
        this.ghostObject = new THREE.Mesh(geometry, material);
        this.scene.add(this.ghostObject);
    }
    
    updateGhostPosition(event) {
        // Aktualisiert Ghost Object Position basierend auf Mausposition
        if (!this.ghostObject) return;
        
        // Mouse Position normalisieren
        const rect = this.renderer.domElement.getBoundingClientRect();
        this.mouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
        this.mouse.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;
        
        // Raycasting für Bodenposition
        this.raycaster.setFromCamera(this.mouse, this.camera);
        
        // Intersect mit Boden oder Wänden
        const intersects = this.raycaster.intersectObjects([this.floor, ...this.walls]);
        
        if (intersects.length > 0) {
            const intersection = intersects[0];
            this.ghostObject.position.copy(intersection.point);
            
            // Höhe je nach Objekttyp anpassen
            if (this.placingType === 'radiator') {
                this.ghostObject.position.y = 0.3; // Heizkörper auf Boden
            } else if (this.placingType === 'window') {
                this.ghostObject.position.y = 1.5; // Fenster in Wandmitte
            } else if (this.placingType === 'door') {
                this.ghostObject.position.y = 1.05; // Tür vom Boden
            }
        }
    }
    
    placeComponent(event) {
        // Platziert neue Komponente an Ghost Object Position
        if (!this.ghostObject || !this.isPlacing) return;
        
        const position = {
            x: this.ghostObject.position.x,
            y: this.ghostObject.position.y,
            z: this.ghostObject.position.z,
            rotation_x: 0,
            rotation_y: 0,
            rotation_z: 0
        };
        
        // Standardeigenschaften je nach Typ
        const properties = this.getDefaultProperties(this.placingType);
        
        // API-Aufruf für Komponentenerstellung
        this.addComponentToBuilding(this.placingType, position, properties);
        
        // Platzierungsmodus beenden
        this.isPlacing = false;
        this.placingType = null;
        this.scene.remove(this.ghostObject);
        this.ghostObject = null;
        this.container.style.cursor = 'default';
    }
    
    getDefaultProperties(componentType) {
        // Gibt Standardeigenschaften für Komponententyp zurück
        switch (componentType) {
            case 'wall':
                return {
                    name: 'Neue Wand',
                    area: 20.0,
                    height: 2.5,
                    orientation: 'S',
                    standard: 'geg_standard',
                    is_external: true
                };
                
            case 'window':
                return {
                    name: 'Neues Fenster',
                    area: 2.0,
                    width: 1.2,
                    height: 1.5,
                    orientation: 'S',
                    glazing_type: '3-fach',
                    g_value: 0.6
                };
                
            case 'door':
                return {
                    name: 'Neue Tür',
                    area: 2.1,
                    width: 1.0,
                    height: 2.1,
                    orientation: 'S',
                    door_type: 'external',
                    material: 'wood'
                };
                
            case 'radiator':
                return {
                    name: 'Neuer Heizkörper',
                    heating_power: 1500.0,
                    width: 1.0,
                    height: 0.6,
                    radiator_type: 'panel',
                    supply_temp: 55.0,
                    return_temp: 45.0,
                    has_thermostatic_valve: true
                };
        }
        return {};
    }
    
    async addComponentToBuilding(componentType, position, properties) {
        // Fügt Komponente zum Gebäude hinzu
        try {
            const response = await fetch('/api/components/add', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    type: componentType,
                    position: position,
                    properties: properties
                })
            });
            
            const result = await response.json();
            
            if (result.success) {
                // Gebäude neu laden
                this.loadBuildingData();
                
                // Erfolgs-Feedback
                this.showNotification(`${componentType} erfolgreich hinzugefügt`, 'success');
            } else {
                this.showNotification(`Fehler beim Hinzufügen: ${result.error}`, 'error');
            }
        } catch (error) {
            console.error('Fehler beim Hinzufügen der Komponente:', error);
            this.showNotification('Netzwerkfehler beim Hinzufügen', 'error');
        }
    }
    
    async updateComponentPosition(object) {
        // Aktualisiert Position einer Komponente
        if (!object.userData || !object.userData.id) return;
        
        const position = {
            x: object.position.x,
            y: object.position.y,
            z: object.position.z
        };
        
        try {
            const response = await fetch(`/api/components/${object.userData.id}/update`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ position: position })
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.showNotification('Position aktualisiert', 'success');
            } else {
                this.showNotification(`Fehler: ${result.error}`, 'error');
            }
        } catch (error) {
            console.error('Fehler beim Aktualisieren der Position:', error);
        }
    }
    
    async deleteSelectedComponent() {
        // Löscht ausgewählte Komponente
        if (!this.selectedObject || !this.selectedObject.userData.id) return;
        
        const componentId = this.selectedObject.userData.id;
        const componentName = this.selectedObject.userData.name;
        
        if (confirm(`Möchten Sie "${componentName}" wirklich löschen?`)) {
            try {
                const response = await fetch(`/api/components/${componentId}/delete`, {
                    method: 'DELETE'
                });
                
                const result = await response.json();
                
                if (result.success) {
                    // Objekt aus Szene entfernen
                    this.scene.remove(this.selectedObject);
                    
                    // Aus Arrays entfernen
                    this.removeFromArrays(this.selectedObject);
                    
                    // Auswahl aufheben
                    this.deselectObject();
                    
                    // Gebäude neu laden
                    this.loadBuildingData();
                    
                    this.showNotification(`${componentName} gelöscht`, 'success');
                } else {
                    this.showNotification(`Fehler beim Löschen: ${result.error}`, 'error');
                }
            } catch (error) {
                console.error('Fehler beim Löschen:', error);
                this.showNotification('Netzwerkfehler beim Löschen', 'error');
            }
        }
    }
    
    removeFromArrays(object) {
        // Entfernt Objekt aus den entsprechenden Arrays
        const type = object.userData.type;
        
        switch (type) {
            case 'wall':
                this.walls = this.walls.filter(wall => wall !== object);
                break;
            case 'window':
                this.windows = this.windows.filter(window => window !== object);
                break;
            case 'door':
                this.doors = this.doors.filter(door => door !== object);
                break;
            case 'radiator':
                this.radiators = this.radiators.filter(radiator => radiator !== object);
                break;
        }
    }
    
    showEditPanel() {
        // Zeigt das Bearbeitungspanel an
        if (!this.editPanel) {
            this.createEditPanel();
        }
        this.editPanel.style.display = 'block';
    }
    
    hideEditPanel() {
        // Versteckt das Bearbeitungspanel
        if (this.editPanel) {
            this.editPanel.style.display = 'none';
        }
    }
    
    createEditPanel() {
        // Erstellt das Bearbeitungspanel
        this.editPanel = document.createElement('div');
        this.editPanel.style.cssText = `
            position: absolute;
            top: 10px;
            left: 10px;
            background: rgba(0,0,0,0.8);
            color: white;
            padding: 15px;
            border-radius: 8px;
            z-index: 1000;
            min-width: 200px;
        `;
        
        this.editPanel.innerHTML = `
            <h4>Bearbeitungsmodus</h4>
            <div style="margin-top: 10px;">
                <button onclick="building3D.startPlacing('wall')" class="edit-btn">+ Wand</button>
                <button onclick="building3D.startPlacing('window')" class="edit-btn">+ Fenster</button>
                <button onclick="building3D.startPlacing('door')" class="edit-btn">+ Tür</button>
                <button onclick="building3D.startPlacing('radiator')" class="edit-btn">+ Heizkörper</button>
            </div>
            <div style="margin-top: 10px;">
                <button onclick="building3D.deleteSelectedComponent()" class="edit-btn danger">Löschen</button>
                <button onclick="building3D.disableEditMode()" class="edit-btn">Beenden</button>
            </div>
        `;
        
        // CSS für Buttons hinzufügen
        const style = document.createElement('style');
        style.textContent = `
            .edit-btn {
                background: #4CAF50;
                color: white;
                border: none;
                padding: 5px 10px;
                margin: 2px;
                border-radius: 4px;
                cursor: pointer;
                font-size: 12px;
            }
            .edit-btn:hover {
                background: #45a049;
            }
            .edit-btn.danger {
                background: #f44336;
            }
            .edit-btn.danger:hover {
                background: #da190b;
            }
        `;
        document.head.appendChild(style);
        
        this.container.appendChild(this.editPanel);
    }
    
    showNotification(message, type = 'info') {
        // Zeigt Benachrichtigung an
        const notification = document.createElement('div');
        notification.style.cssText = `
            position: absolute;
            top: 50px;
            right: 10px;
            background: ${type === 'error' ? '#f44336' : type === 'success' ? '#4CAF50' : '#2196F3'};
            color: white;
            padding: 10px 15px;
            border-radius: 4px;
            z-index: 10000;
            font-size: 14px;
        `;
        notification.textContent = message;
        
        this.container.appendChild(notification);
        
        // Nach 3 Sekunden entfernen
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 3000);
    }
    
    async loadBuildingData() {
        // Lädt Gebäudedaten neu
        try {
            const response = await fetch('/api/building/data');
            const data = await response.json();
            
            if (data.success) {
                this.loadBuilding(data.building);
            }
        } catch (error) {
            console.error('Fehler beim Laden der Gebäudedaten:', error);
        }
    }

    // Erweiterte Mausbehandlung für Bearbeitungsmodus
    onMouseMove(event) {
        if (this.isPlacing) {
            this.updateGhostPosition(event);
            return;
        }
        
        // Ursprüngliche Mausbehandlung
        const rect = this.renderer.domElement.getBoundingClientRect();
        this.mouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
        this.mouse.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;
        
        // Hover-Effekt für Objekte
        if (!this.editMode) {
            this.raycaster.setFromCamera(this.mouse, this.camera);
            const intersects = this.raycaster.intersectObjects(this.buildingGroup.children);
            
            if (intersects.length > 0) {
                this.container.style.cursor = 'pointer';
            } else {
                this.container.style.cursor = 'default';
            }
        }
    }
    
    onMouseClick(event) {
        if (this.isPlacing) {
            this.placeComponent(event);
            return;
        }
        
        // Ursprüngliche Klick-Behandlung
        const rect = this.renderer.domElement.getBoundingClientRect();
        this.mouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
        this.mouse.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;
        
        this.raycaster.setFromCamera(this.mouse, this.camera);
        const intersects = this.raycaster.intersectObjects(this.buildingGroup.children);
        
        if (intersects.length > 0) {
            this.selectObject(intersects[0].object);
        } else {
            this.deselectObject();
        }
    }
    
    // Erweiterte Tastaturbehandlung
    onKeyDown(event) {
        switch (event.key) {
            case 'Escape':
                if (this.isPlacing) {
                    // Platzierungsmodus abbrechen
                    this.isPlacing = false;
                    this.placingType = null;
                    if (this.ghostObject) {
                        this.scene.remove(this.ghostObject);
                        this.ghostObject = null;
                    }
                    this.container.style.cursor = 'default';
                } else if (this.editMode) {
                    this.disableEditMode();
                } else {
                    this.deselectObject();
                }
                break;
                
            case 'Delete':
            case 'Backspace':
                if (this.selectedObject && this.editMode) {
                    this.deleteSelectedComponent();
                }
                break;
                
            case 'e':
            case 'E':
                if (event.ctrlKey) {
                    event.preventDefault();
                    if (this.editMode) {
                        this.disableEditMode();
                    } else {
                        this.enableEditMode();
                    }
                }
                break;
        }
    }

    animate() {
        requestAnimationFrame(() => this.animate());
        
        // Steuerung aktualisieren
        if (this.controls) {
            this.controls.update();
        }
        
        // Szene rendern
        this.renderer.render(this.scene, this.camera);
    }
    
    // Hilfsmethoden für UI-Integration
    getSelectedObjectInfo() {
        return this.selectedObject ? this.selectedObject.userData : null;
    }
    
    highlightComponentsByType(type) {
        this.buildingGroup.traverse((child) => {
            if (child.userData && child.userData.type === type) {
                // Temporäres Highlighting
                if (child.material && !child.userData.originalMaterial) {
                    child.userData.originalMaterial = child.material;
                    child.material = this.materials.selected;
                    
                    // Highlight nach 2 Sekunden entfernen
                    setTimeout(() => {
                        if (child.userData.originalMaterial) {
                            child.material = child.userData.originalMaterial;
                            delete child.userData.originalMaterial;
                        }
                    }, 2000);
                }
            }
        });
    }
    
    exportToJSON() {
        return JSON.stringify(this.buildingData, null, 2);
    }
    
    // Debugging und Entwicklung
    logBuildingStats() {
        console.log('Gebäudestatistiken:');
        console.log('- Wände:', this.walls.length);
        console.log('- Fenster:', this.windows.length);
        console.log('- Türen:', this.doors.length);
        console.log('- Heizkörper:', this.radiators.length);
        console.log('- Objekte gesamt:', this.buildingGroup.children.length);
    }
    
    createDefaultBuilding() {
        // Einfaches Standard-Gebäude als Fallback
        try {
            // Boden
            const floorGeometry = new THREE.PlaneGeometry(10, 10);
            const floorMaterial = new THREE.MeshLambertMaterial({ color: 0x8B4513 });
            const floor = new THREE.Mesh(floorGeometry, floorMaterial);
            floor.rotation.x = -Math.PI / 2;
            this.buildingGroup.add(floor);
            
            // Wände
            const wallMaterial = new THREE.MeshLambertMaterial({ color: 0xDDDDDD });
            
            // Südwand
            const southWallGeometry = new THREE.BoxGeometry(10, 3, 0.2);
            const southWall = new THREE.Mesh(southWallGeometry, wallMaterial);
            southWall.position.set(0, 1.5, -5);
            this.buildingGroup.add(southWall);
            
            // Nordwand
            const northWall = new THREE.Mesh(southWallGeometry, wallMaterial);
            northWall.position.set(0, 1.5, 5);
            this.buildingGroup.add(northWall);
            
            // Ost-/Westwände
            const sideWallGeometry = new THREE.BoxGeometry(0.2, 3, 10);
            const eastWall = new THREE.Mesh(sideWallGeometry, wallMaterial);
            eastWall.position.set(5, 1.5, 0);
            this.buildingGroup.add(eastWall);
            
            const westWall = new THREE.Mesh(sideWallGeometry, wallMaterial);
            westWall.position.set(-5, 1.5, 0);
            this.buildingGroup.add(westWall);
            
            // Dach
            const roofGeometry = new THREE.PlaneGeometry(12, 12);
            const roofMaterial = new THREE.MeshLambertMaterial({ color: 0x8B0000 });
            const roof = new THREE.Mesh(roofGeometry, roofMaterial);
            roof.rotation.x = -Math.PI / 2;
            roof.position.y = 3;
            this.buildingGroup.add(roof);
            
            console.log('✅ Default building created successfully');
        } catch (error) {
            console.error('❌ Error creating default building:', error);
        }
    }
    
    createMinimalScene() {
        // Allerletzter Fallback - minimale Szene
        try {
            console.log('🆘 Creating minimal fallback scene...');
            
            this.scene = new THREE.Scene();
            this.scene.background = new THREE.Color(0x87CEEB);
            
            this.camera = new THREE.PerspectiveCamera(75, this.container.clientWidth / this.container.clientHeight, 0.1, 1000);
            this.camera.position.set(10, 10, 10);
            
            this.renderer = new THREE.WebGLRenderer({ antialias: true });
            this.renderer.setSize(this.container.clientWidth, this.container.clientHeight);
            this.container.appendChild(this.renderer.domElement);
            
            this.controls = new THREE.OrbitControls(this.camera, this.renderer.domElement);
            
            // Einfacher Würfel als Test
            const geometry = new THREE.BoxGeometry(2, 2, 2);
            const material = new THREE.MeshBasicMaterial({ color: 0x00ff00 });
            const cube = new THREE.Mesh(geometry, material);
            this.scene.add(cube);
            
            // Licht
            const light = new THREE.DirectionalLight(0xffffff, 1);
            light.position.set(10, 10, 5);
            this.scene.add(light);
            
            // Animation
            const animate = () => {
                requestAnimationFrame(animate);
                this.controls.update();
                this.renderer.render(this.scene, this.camera);
            };
            animate();
            
            console.log('✅ Minimal scene created');
        } catch (error) {
            console.error('❌ Even minimal scene failed:', error);
        }
    }
}

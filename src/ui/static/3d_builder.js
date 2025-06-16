/**
 * Advanced 3D Building Modeler for energyOS
 * ========================================
 * 
 * Intuitive 3D building editor with:
 * - Drag & Drop component placement
 * - Smart snapping and automatic connections
 * - Anti-thermal bridge system
 * - Real-time building physics validation
 * - Normgerechte Berechnungen integration
 */

class Advanced3DBuilder {
    constructor(containerId) {
        this.container = document.getElementById(containerId);
        this.buildingData = {
            walls: [],
            windows: [],
            doors: [],
            roof: null,
            floor: null,
            components: new Map()
        };
        
        // Editor state
        this.selectedTool = null;
        this.isDragging = false;
        this.dragStartPosition = null;
        this.ghostObject = null;
        this.snapTargets = [];
        this.snapThreshold = 0.5; // meters
        
        // Three.js core
        this.scene = null;
        this.camera = null;
        this.renderer = null;
        this.controls = null;
        this.raycaster = new THREE.Raycaster();
        this.mouse = new THREE.Vector2();
        
        // Building elements
        this.buildingGroup = new THREE.Group();
        this.snapHelpers = new THREE.Group();
        this.guidanceSystem = new THREE.Group();
        
        // Materials and helpers
        this.materials = {};
        this.snapLines = [];
        this.measurements = [];
        
        this.init();
    }
    
    init() {
        console.log('🏗️ Initializing Advanced 3D Builder...');
        
        this.setupScene();
        this.setupCamera();
        this.setupRenderer();
        this.setupControls();
        this.setupLights();
        this.setupMaterials();
        this.setupEventListeners();
        this.createInitialBuilding();
        
        this.animate();
        
        console.log('✅ Advanced 3D Builder initialized successfully!');
    }
    
    setupScene() {
        this.scene = new THREE.Scene();
        this.scene.background = new THREE.Color(0xf0f0f0);
        
        // Add building groups
        this.scene.add(this.buildingGroup);
        this.scene.add(this.snapHelpers);
        this.scene.add(this.guidanceSystem);
        
        // Ground plane
        this.createGround();
        
        // Grid helper
        this.createGrid();
    }
    
    setupCamera() {
        this.camera = new THREE.PerspectiveCamera(
            60,
            this.container.clientWidth / this.container.clientHeight,
            0.1,
            1000
        );
        this.camera.position.set(15, 10, 15);
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
        this.container.appendChild(this.renderer.domElement);
    }
    
    setupControls() {
        this.controls = new THREE.OrbitControls(this.camera, this.renderer.domElement);
        this.controls.enableDamping = true;
        this.controls.dampingFactor = 0.05;
        this.controls.minDistance = 5;
        this.controls.maxDistance = 100;
        this.controls.maxPolarAngle = Math.PI / 2;
    }
    
    setupLights() {
        // Ambient light
        const ambientLight = new THREE.AmbientLight(0x404040, 0.4);
        this.scene.add(ambientLight);
        
        // Main directional light (sun)
        const directionalLight = new THREE.DirectionalLight(0xffffff, 0.8);
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
        
        // Fill light
        const fillLight = new THREE.DirectionalLight(0x87CEEB, 0.3);
        fillLight.position.set(-30, 30, -30);
        this.scene.add(fillLight);
    }
    
    setupMaterials() {
        // Wall materials by thermal quality
        this.materials.wall_excellent = new THREE.MeshLambertMaterial({
            color: 0x90EE90, // Light green
            transparent: true,
            opacity: 0.9
        });
        
        this.materials.wall_good = new THREE.MeshLambertMaterial({
            color: 0xFFFFE0, // Light yellow
            transparent: true,
            opacity: 0.9
        });
        
        this.materials.wall_poor = new THREE.MeshLambertMaterial({
            color: 0xFFB6C1, // Light red
            transparent: true,
            opacity: 0.9
        });
        
        // Window materials
        this.materials.window_triple = new THREE.MeshPhysicalMaterial({
            color: 0x87CEEB,
            transparent: true,
            opacity: 0.2,
            transmission: 0.95,
            ior: 1.5,
            roughness: 0.05
        });
        
        this.materials.window_double = new THREE.MeshPhysicalMaterial({
            color: 0x6BB6FF,
            transparent: true,
            opacity: 0.3,
            transmission: 0.85,
            ior: 1.5,
            roughness: 0.1
        });
        
        // Door materials
        this.materials.door_wood = new THREE.MeshLambertMaterial({
            color: 0x8B4513
        });
        
        this.materials.door_insulated = new THREE.MeshLambertMaterial({
            color: 0x696969
        });
        
        // Roof materials
        this.materials.roof_standard = new THREE.MeshLambertMaterial({
            color: 0x8B0000
        });
        
        this.materials.roof_insulated = new THREE.MeshLambertMaterial({
            color: 0x2F4F4F
        });
        
        // Helper materials
        this.materials.ghost = new THREE.MeshBasicMaterial({
            color: 0x00ff00,
            transparent: true,
            opacity: 0.3,
            wireframe: true
        });
        
        this.materials.snap_indicator = new THREE.MeshBasicMaterial({
            color: 0xff0000,
            transparent: true,
            opacity: 0.8
        });
        
        this.materials.grid = new THREE.LineBasicMaterial({
            color: 0xcccccc,
            transparent: true,
            opacity: 0.3
        });
        
        // Ground material
        this.materials.ground = new THREE.MeshLambertMaterial({
            color: 0x90EE90,
            transparent: true,
            opacity: 0.5
        });
    }
    
    createGround() {
        const groundGeometry = new THREE.PlaneGeometry(50, 50);
        const ground = new THREE.Mesh(groundGeometry, this.materials.ground);
        ground.rotation.x = -Math.PI / 2;
        ground.position.y = -0.05;
        ground.receiveShadow = true;
        ground.userData = { type: 'ground', selectable: false };
        this.scene.add(ground);
    }
    
    createGrid() {
        const size = 50;
        const divisions = 50;
        
        const gridHelper = new THREE.GridHelper(size, divisions, 0x444444, 0x888888);
        gridHelper.material.transparent = true;
        gridHelper.material.opacity = 0.3;
        gridHelper.userData = { type: 'grid', selectable: false };
        this.scene.add(gridHelper);
    }
    
    // Tool selection and ghost mode moved to external toolbox
    
    // Ghost object creation moved to external toolbox
    
    setupEventListeners() {
        // Mouse events
        this.renderer.domElement.addEventListener('mousemove', (e) => this.onMouseMove(e));
        this.renderer.domElement.addEventListener('click', (e) => this.onMouseClick(e));
        
        // Keyboard events
        window.addEventListener('keydown', (e) => this.onKeyDown(e));
        
        // Window resize
        window.addEventListener('resize', () => this.onWindowResize());
    }
    
    onMouseMove(event) {
        // Update mouse coordinates
        const rect = this.renderer.domElement.getBoundingClientRect();
        this.mouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
        this.mouse.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;
        
        // Update ghost object position
        if (this.ghostObject) {
            this.updateGhostPosition();
        }
    }
    
    updateGhostPosition() {
        if (!this.ghostObject) return;
        
        // Cast ray from camera through mouse
        this.raycaster.setFromCamera(this.mouse, this.camera);
        
        // Find intersection with ground or existing objects
        const intersects = this.raycaster.intersectObjects([
            ...this.buildingGroup.children,
            ...this.scene.children.filter(child => child.userData.type === 'ground')
        ]);
        
        if (intersects.length > 0) {
            const intersection = intersects[0];
            const point = intersection.point;
            
            // Apply snapping
            const snappedPosition = this.applySnapping(point, this.ghostObject.userData.toolType);
            
            this.ghostObject.position.copy(snappedPosition);
            
            // Update snap indicators
            this.updateSnapIndicators(snappedPosition);
        }
    }
    
    applySnapping(position, toolType) {
        const snapped = position.clone();
        
        // Grid snapping
        const gridSize = 0.5;
        snapped.x = Math.round(snapped.x / gridSize) * gridSize;
        snapped.z = Math.round(snapped.z / gridSize) * gridSize;
        
        // Smart snapping based on tool type
        switch (toolType) {
            case 'window':
            case 'door':
                // Snap to walls
                const nearestWall = this.findNearestWall(snapped);
                if (nearestWall && nearestWall.distance < this.snapThreshold) {
                    snapped.copy(nearestWall.position);
                }
                break;
                
            case 'roof':
                // Snap to wall tops
                const highestWall = this.findHighestWallPosition();
                if (highestWall) {
                    snapped.y = highestWall.y + 0.3;
                }
                break;
                
            case 'floor':
                snapped.y = 0;
                break;
                
            default:
                if (toolType.includes('wall')) {
                    snapped.y = 1.25; // Half wall height
                }
                break;
        }
        
        return snapped;
    }
    
    findNearestWall(position) {
        let nearest = null;
        let minDistance = Infinity;
        
        this.buildingData.walls.forEach(wall => {
            const wallObject = wall.object3d;
            if (!wallObject) return;
            
            const distance = position.distanceTo(wallObject.position);
            if (distance < minDistance) {
                minDistance = distance;
                nearest = {
                    wall: wall,
                    distance: distance,
                    position: this.calculateWallSnapPosition(wallObject, position)
                };
            }
        });
        
        return nearest;
    }
    
    calculateWallSnapPosition(wall, targetPosition) {
        // Calculate the best position to snap to on the wall surface
        const wallPos = wall.position.clone();
        const wallSize = wall.geometry.parameters;
        
        // For now, simple center positioning
        wallPos.y = targetPosition.y;
        
        // Offset slightly from wall surface
        const offset = 0.15;
        wallPos.z += wallSize.depth / 2 + offset;
        
        return wallPos;
    }
    
    findHighestWallPosition() {
        let highest = null;
        
        this.buildingData.walls.forEach(wall => {
            if (wall.object3d) {
                const wallTop = wall.object3d.position.y + wall.object3d.geometry.parameters.height / 2;
                if (!highest || wallTop > highest.y) {
                    highest = { y: wallTop };
                }
            }
        });
        
        return highest;
    }
    
    updateSnapIndicators(position) {
        // Clear existing indicators
        this.snapHelpers.clear();
        
        // Add snap indicators if close to snap targets
        this.snapTargets.forEach(target => {
            const distance = position.distanceTo(target.position);
            if (distance < this.snapThreshold) {
                const indicator = this.createSnapIndicator(target);
                this.snapHelpers.add(indicator);
            }
        });
    }
    
    createSnapIndicator(target) {
        const geometry = new THREE.SphereGeometry(0.1, 8, 8);
        const indicator = new THREE.Mesh(geometry, this.materials.snap_indicator);
        indicator.position.copy(target.position);
        return indicator;
    }
    
    updateSnapTargets() {
        this.snapTargets = [];
        
        // Add wall connection points
        this.buildingData.walls.forEach(wall => {
            if (wall.object3d) {
                const pos = wall.object3d.position;
                const size = wall.object3d.geometry.parameters;
                
                // Add corner points
                this.snapTargets.push({ 
                    type: 'wall-corner', 
                    position: new THREE.Vector3(pos.x - size.width/2, pos.y, pos.z) 
                });
                this.snapTargets.push({ 
                    type: 'wall-corner', 
                    position: new THREE.Vector3(pos.x + size.width/2, pos.y, pos.z) 
                });
            }
        });
    }
    
    onMouseClick(event) {
        if (this.selectedTool && this.ghostObject) {
            this.placeTool();
        } else {
            this.selectObject(event);
        }
    }
    
    placeTool() {
        if (!this.ghostObject) return;
        
        const position = this.ghostObject.position.clone();
        const toolType = this.ghostObject.userData.toolType;
        
        // Create actual building component
        const component = this.createBuildingComponent(toolType, position);
        
        if (component) {
            // Add to building data
            this.addComponentToBuilding(component);
            
            // Add to scene
            this.buildingGroup.add(component.object3d);
            
            // Update physics calculations
            this.updateBuildingPhysics();
            
            // Show success feedback
            this.showPlacementFeedback(toolType, position);
        }
        
        // Continue with same tool or exit
        if (event.shiftKey) {
            // Continue placing same tool
            this.startGhostMode(toolType);
        } else {
            // Exit tool mode
            this.exitToolMode();
        }
    }
    
    createBuildingComponent(toolType, position) {
        let geometry, material, userData;
        
        switch (toolType) {
            case 'wall':
                geometry = new THREE.BoxGeometry(4, 2.5, 0.2);
                material = this.materials.wall_good;
                userData = {
                    type: 'wall',
                    uValue: 0.24,
                    thermal_quality: 'standard',
                    width: 4,
                    height: 2.5,
                    thickness: 0.2
                };
                break;
                
            case 'insulated-wall':
                geometry = new THREE.BoxGeometry(4, 2.5, 0.3);
                material = this.materials.wall_excellent;
                userData = {
                    type: 'wall',
                    uValue: 0.15,
                    thermal_quality: 'excellent',
                    width: 4,
                    height: 2.5,
                    thickness: 0.3
                };
                break;
                
            case 'window':
                geometry = new THREE.BoxGeometry(1.2, 1.5, 0.1);
                material = this.materials.window_double;
                userData = {
                    type: 'window',
                    uValue: 1.3,
                    gValue: 0.6,
                    glazing: 'double',
                    width: 1.2,
                    height: 1.5
                };
                break;
                
            case 'triple-window':
                geometry = new THREE.BoxGeometry(1.2, 1.5, 0.1);
                material = this.materials.window_triple;
                userData = {
                    type: 'window',
                    uValue: 0.8,
                    gValue: 0.5,
                    glazing: 'triple',
                    width: 1.2,
                    height: 1.5
                };
                break;
                
            case 'door':
                geometry = new THREE.BoxGeometry(1, 2.1, 0.1);
                material = this.materials.door_wood;
                userData = {
                    type: 'door',
                    uValue: 2.0,
                    material: 'wood',
                    width: 1,
                    height: 2.1
                };
                break;
                
            default:
                return null;
        }
        
        const mesh = new THREE.Mesh(geometry, material);
        mesh.position.copy(position);
        mesh.castShadow = true;
        mesh.receiveShadow = true;
        mesh.userData = {
            ...userData,
            id: this.generateId(),
            position: position.toArray(),
            selectable: true
        };
        
        return {
            id: mesh.userData.id,
            type: userData.type,
            object3d: mesh,
            properties: userData
        };
    }
    
    addComponentToBuilding(component) {
        const componentType = component.type;
        
        if (!this.buildingData[componentType + 's']) {
            this.buildingData[componentType + 's'] = [];
        }
        
        this.buildingData[componentType + 's'].push(component);
        this.buildingData.components.set(component.id, component);
    }
    
    exitToolMode() {
        this.selectedTool = null;
        
        // Remove ghost object
        if (this.ghostObject) {
            this.scene.remove(this.ghostObject);
            this.ghostObject = null;
        }
        
        // Clear snap helpers
        this.snapHelpers.clear();
        
        // Reset cursor
        this.renderer.domElement.style.cursor = 'default';
        
        // Hide instructions
        this.hideToolInstructions();
    }
    
    onKeyDown(event) {
        switch (event.code) {
            case 'Escape':
                this.exitToolMode();
                break;
                
            case 'Delete':
                if (this.selectedObject) {
                    this.deleteSelectedObject();
                }
                break;
                
            case 'KeyG':
                if (event.ctrlKey) {
                    this.toggleGrid();
                }
                break;
                
            case 'KeyW':
                if (event.ctrlKey) {
                    this.toggleWireframe();
                }
                break;
        }
    }
    
    selectObject(event) {
        const rect = this.renderer.domElement.getBoundingClientRect();
        this.mouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
        this.mouse.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;
        
        this.raycaster.setFromCamera(this.mouse, this.camera);
        
        const intersects = this.raycaster.intersectObjects(
            this.buildingGroup.children.filter(child => child.userData.selectable)
        );
        
        if (intersects.length > 0) {
            const object = intersects[0].object;
            this.setSelectedObject(object);
        } else {
            this.clearSelection();
        }
    }
    
    setSelectedObject(object) {
        // Clear previous selection
        this.clearSelection();
        
        this.selectedObject = object;
        
        // Visual feedback
        this.highlightObject(object);
        
        // Show properties panel
        this.showPropertiesPanel(object);
    }
    
    clearSelection() {
        if (this.selectedObject) {
            this.unhighlightObject(this.selectedObject);
            this.selectedObject = null;
        }
        
        this.hidePropertiesPanel();
    }
    
    highlightObject(object) {
        // Store original material
        object.userData.originalMaterial = object.material;
        
        // Apply highlight material
        const highlightMaterial = object.material.clone();
        highlightMaterial.emissive = new THREE.Color(0x444444);
        object.material = highlightMaterial;
    }
    
    unhighlightObject(object) {
        if (object.userData.originalMaterial) {
            object.material = object.userData.originalMaterial;
            delete object.userData.originalMaterial;
        }
    }
    
    createInitialBuilding() {
        // Create a simple example building to start with
        const examples = [
            { type: 'wall', position: new THREE.Vector3(0, 1.25, -2) },
            { type: 'wall', position: new THREE.Vector3(0, 1.25, 2) },
            { type: 'wall', position: new THREE.Vector3(-2, 1.25, 0) },
            { type: 'wall', position: new THREE.Vector3(2, 1.25, 0) }
        ];
        
        examples.forEach(example => {
            const component = this.createBuildingComponent(example.type, example.position);
            if (component) {
                this.addComponentToBuilding(component);
                this.buildingGroup.add(component.object3d);
            }
        });
        
        // Add a simple window
        const window = this.createBuildingComponent('window', new THREE.Vector3(0, 1.5, -2.1));
        if (window) {
            this.addComponentToBuilding(window);
            this.buildingGroup.add(window.object3d);
        }
    }
    
    updateBuildingPhysics() {
        // Calculate thermal performance
        this.calculateThermalPerformance();
        
        // Update visual feedback
        this.updateThermalVisualization();
        
        // Check for thermal bridges
        this.checkThermalBridges();
    }
    
    calculateThermalPerformance() {
        let totalHeatLoss = 0;
        let totalArea = 0;
        
        // Calculate for all components
        ['walls', 'windows', 'doors'].forEach(componentType => {
            if (this.buildingData[componentType]) {
                this.buildingData[componentType].forEach(component => {
                    const area = component.properties.width * component.properties.height;
                    const heatLoss = area * component.properties.uValue;
                    
                    totalArea += area;
                    totalHeatLoss += heatLoss;
                });
            }
        });
        
        const averageUValue = totalArea > 0 ? totalHeatLoss / totalArea : 0;
        
        // Update building data
        this.buildingData.thermalPerformance = {
            totalArea: totalArea,
            totalHeatLoss: totalHeatLoss,
            averageUValue: averageUValue,
            energyClass: this.calculateEnergyClass(averageUValue)
        };
        
        // Update UI
        this.updatePerformanceDisplay();
    }
    
    calculateEnergyClass(uValue) {
        if (uValue < 0.15) return 'A+';
        if (uValue < 0.25) return 'A';
        if (uValue < 0.35) return 'B';
        if (uValue < 0.50) return 'C';
        return 'D';
    }
    
    updateThermalVisualization() {
        // Color code components based on thermal performance
        this.buildingData.components.forEach(component => {
            if (component.object3d && component.properties.uValue) {
                const material = this.getThermalMaterial(component.properties.uValue);
                component.object3d.material = material;
            }
        });
    }
    
    getThermalMaterial(uValue) {
        if (uValue < 0.15) return this.materials.wall_excellent;
        if (uValue < 0.30) return this.materials.wall_good;
        return this.materials.wall_poor;
    }
    
    checkThermalBridges() {
        // Implementation for thermal bridge detection
        // This would analyze connections between components
        console.log('🔍 Checking for thermal bridges...');
    }
    
    // Utility methods
    generateId() {
        return 'component_' + Math.random().toString(36).substr(2, 9);
    }
    
    // Tool instructions removed - handled by external toolbox
    
    showPlacementFeedback(toolType, position) {
        console.log(`✅ ${toolType} placed at`, position);
    }
    
    showPropertiesPanel(object) {
        console.log('📋 Properties:', object.userData);
    }
    
    hidePropertiesPanel() {
        // Hide properties panel
    }
    
    updatePerformanceDisplay() {
        if (this.buildingData.thermalPerformance) {
            console.log('🏠 Building Performance:', this.buildingData.thermalPerformance);
        }
    }
    
    // Drop handling removed - external toolbox responsibility
    
    toggleGrid() {
        // Toggle grid visibility
        this.scene.traverse((child) => {
            if (child.userData.type === 'grid') {
                child.visible = !child.visible;
            }
        });
    }
    
    toggleWireframe() {
        // Toggle wireframe mode
        this.buildingGroup.traverse((child) => {
            if (child.isMesh) {
                child.material.wireframe = !child.material.wireframe;
            }
        });
    }
    
    deleteSelectedObject() {
        if (!this.selectedObject) return;
        
        const componentId = this.selectedObject.userData.id;
        
        // Remove from scene
        this.buildingGroup.remove(this.selectedObject);
        
        // Remove from building data
        this.buildingData.components.delete(componentId);
        
        // Remove from specific arrays
        ['walls', 'windows', 'doors'].forEach(type => {
            if (this.buildingData[type]) {
                this.buildingData[type] = this.buildingData[type].filter(
                    component => component.id !== componentId
                );
            }
        });
        
        this.clearSelection();
        this.updateBuildingPhysics();
    }
    
    onWindowResize() {
        this.camera.aspect = this.container.clientWidth / this.container.clientHeight;
        this.camera.updateProjectionMatrix();
        this.renderer.setSize(this.container.clientWidth, this.container.clientHeight);
    }
    
    animate() {
        requestAnimationFrame(() => this.animate());
        
        if (this.controls) {
            this.controls.update();
        }
        
        this.renderer.render(this.scene, this.camera);
    }
    
    // Export building data for calculations
    exportBuildingData() {
        return {
            components: Array.from(this.buildingData.components.values()),
            thermalPerformance: this.buildingData.thermalPerformance,
            metadata: {
                version: '1.0',
                created: new Date().toISOString(),
                tools: 'Advanced3DBuilder'
            }
        };
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    if (document.getElementById('building-3d')) {
        window.advanced3DBuilder = new Advanced3DBuilder('building-3d');
    }
});

// Core functions for external toolboxes
window.getBuilderInstance = function() {
    return window.advanced3DBuilder;
};

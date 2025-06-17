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
    
    setTool(toolType) {
        this.currentTool = toolType;
        debugLog(`Tool gewechselt zu: ${toolType}`, 'info');
    }
    
    addCube(x = 0, y = 0, z = 0) {
        const geometry = new THREE.BoxGeometry(100, 100, 100);
        const material = new THREE.MeshLambertMaterial({ color: 0x4CAF50 });
        const cube = new THREE.Mesh(geometry, material);
        
        cube.position.set(x, y + 50, z);
        this.scene.add(cube);
        this.needsRender = true;
        
        debugLog(`Würfel hinzugefügt bei (${x}, ${y}, ${z})`, 'info');
        return cube;
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

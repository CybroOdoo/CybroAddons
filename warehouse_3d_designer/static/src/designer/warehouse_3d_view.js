/** @odoo-module **/

/**
 * Warehouse 3D View — WebGL renderer using Three.js
 *
 * Realistic 3D warehouse with distinct shapes, orbit/pan/zoom controls,
 * walls, labels, and product search highlighting.
 *
 * Controls:
 *   Right-click + drag  → Orbit (rotate)
 *   Middle-click + drag → Pan (also Shift+left-drag)
 *   Scroll wheel        → Zoom
 *   Left-click           → Select location
 */

import { Component, onMounted, onWillUnmount, onWillUpdateProps, useRef } from "@odoo/owl";

export class Warehouse3DView extends Component {
    static template = "warehouse_3d_designer.Warehouse3DView";
    static props = {
        locations: { type: Array },
        layoutData: { type: Object },
        mapObjects: { type: Array },
        gridEnabled: { type: Boolean },
        heatmapEnabled: { type: Boolean },
        heatmapData: { type: Object },
        zoomLevel: { type: Number },
        selectedLocationId: { type: [Number, { value: null }], optional: true },
        highlightedLocationId: { type: [Number, { value: null }], optional: true },
        productSearchResults: { type: Array },
        onLocationSelected: { type: Function },
        siblingFloors: { type: Array, optional: true },
        allFloorData: { type: [Array, { value: null }], optional: true },
        showAllFloors: { type: Boolean, optional: true },
        selectedLayoutId: { type: [Number, { value: null }], optional: true },
        onToggleAllFloors: { type: Function, optional: true },
    };

    setup() {
        this.containerRef = useRef("container3d");
        this.scene = null;
        this.camera = null;
        this.renderer = null;
        this.animationId = null;
        this.locationMeshes = new Map();
        this.mapObjectMeshes = [];
        this.detailMeshes = [];
        this.labelSprites = [];
        this.raycaster = null;
        this.mouse = null;
        this._highlightTime = 0;

        // Hover tooltip state
        this._3dTooltipEl = null;
        this._3dTooltipLocId = null;
        this._3dTooltipHideTimer = null;
        this._3dTooltipStyle = null;

        // Multi-floor meshes (for stacked view)
        this.otherFloorMeshes = [];

        onMounted(() => {
            this._initScene();
            this._buildWarehouse();
            this._animate();
        });

        onWillUpdateProps((nextProps) => {
            this._pendingRebuild = true;
            this._nextProps = nextProps;
        });

        onWillUnmount(() => {
            this._hide3DProductTooltip();
            this._cleanup();
        });
    }

    // ========================================================================
    // Scene Initialization
    // ========================================================================

    _initScene() {
        const container = this.containerRef.el;
        if (!container || typeof THREE === "undefined") {
            return;
        }

        const width = container.clientWidth;
        const height = container.clientHeight;

        // Scene
        this.scene = new THREE.Scene();
        this.scene.background = new THREE.Color(0xe8edf2);
        this.scene.fog = new THREE.FogExp2(0xe8edf2, 0.005);

        // Camera
        this.camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 800);
        const layout = this.props.layoutData;
        const centerX = (layout?.canvas_width || 40) / 2;
        const centerZ = (layout?.canvas_height || 30) / 2;
        this.camera.position.set(centerX + 25, 35, centerZ + 35);
        this.camera.lookAt(centerX, 0, centerZ);

        // Renderer — high quality
        this.renderer = new THREE.WebGLRenderer({
            antialias: true,
            alpha: false,
            powerPreference: 'high-performance',
        });
        this.renderer.setSize(width, height);
        this.renderer.setPixelRatio(window.devicePixelRatio);
        this.renderer.shadowMap.enabled = true;
        this.renderer.shadowMap.type = THREE.PCFSoftShadowMap;
        this.renderer.toneMapping = THREE.ACESFilmicToneMapping;
        this.renderer.toneMappingExposure = 1.2;
        if (this.renderer.outputColorSpace !== undefined) {
            this.renderer.outputColorSpace = THREE.SRGBColorSpace;
        }
        container.appendChild(this.renderer.domElement);

        // Controls
        this._setupControls(container);

        // Raycaster
        this.raycaster = new THREE.Raycaster();
        this.mouse = new THREE.Vector2();

        // Lighting
        this._setupLighting();

        // Floor & Walls
        this._createEnvironment();

        // Events — track drag to prevent click on orbit
        this._hasDragged = false;
        this.renderer.domElement.addEventListener("click", (e) => {
            if (!this._hasDragged) this._onClick(e);
        });
        this.renderer.domElement.addEventListener("mousemove", this._onHover.bind(this));
        this._boundResize = this._onResize.bind(this);
        window.addEventListener("resize", this._boundResize);
    }

    _setupLighting() {
        // Soft ambient for base illumination
        this.scene.add(new THREE.AmbientLight(0xffffff, 0.65));

        // Key light — main directional with high-res shadows
        const key = new THREE.DirectionalLight(0xfff5e6, 0.9);
        key.position.set(40, 60, 30);
        key.castShadow = true;
        key.shadow.mapSize.set(4096, 4096);
        key.shadow.camera.near = 0.5;
        key.shadow.camera.far = 300;
        key.shadow.camera.left = -80;
        key.shadow.camera.right = 80;
        key.shadow.camera.top = 80;
        key.shadow.camera.bottom = -80;
        key.shadow.bias = -0.0005;
        key.shadow.normalBias = 0.02;
        key.shadow.radius = 2;
        this.scene.add(key);

        // Hemisphere — sky blue / warm ground bounce
        this.scene.add(new THREE.HemisphereLight(0x8EC8F0, 0xB09060, 0.4));

        // Fill light from back-left
        const fill = new THREE.DirectionalLight(0xe8f0ff, 0.3);
        fill.position.set(-25, 25, -20);
        this.scene.add(fill);

        // Rim light from back-right for depth
        const rim = new THREE.DirectionalLight(0xffeedd, 0.15);
        rim.position.set(30, 15, -25);
        this.scene.add(rim);
    }

    _createEnvironment() {
        const layout = this.props.layoutData;
        const w = layout?.canvas_width || 40;
        const h = layout?.canvas_height || 30;

        // Polished concrete floor — matches canvas boundaries exactly
        const floorGeo = new THREE.PlaneGeometry(w, h, 1, 1);
        const floorMat = new THREE.MeshStandardMaterial({
            color: 0xc8c8c8,
            roughness: 0.85,
            metalness: 0.05,
        });
        const floor = new THREE.Mesh(floorGeo, floorMat);
        floor.rotation.x = -Math.PI / 2;
        floor.position.set(w / 2, -0.01, h / 2);
        floor.receiveShadow = true;
        this.scene.add(floor);

        // Subtle grid lines — matches canvas size
        const gridSize = Math.max(w, h);
        this._gridMesh = new THREE.GridHelper(gridSize, gridSize, 0xaaaaaa, 0xd5d5d5);
        this._gridMesh.position.set(w / 2, 0.01, h / 2);
        this._gridMesh.material.opacity = 0.4;
        this._gridMesh.material.transparent = true;
        this._gridMesh.visible = this.props.gridEnabled;
        this.scene.add(this._gridMesh);

        // Decorative walls — back and left, flush with canvas boundary
        const wallH = 8;
        const wallMat = new THREE.MeshStandardMaterial({
            color: 0xeaedf0,
            roughness: 0.75,
            metalness: 0.0,
            side: THREE.DoubleSide,
        });

        // Back wall — at z=0 (back edge of canvas)
        const backGeo = new THREE.PlaneGeometry(w, wallH);
        const backWall = new THREE.Mesh(backGeo, wallMat);
        backWall.position.set(w / 2, wallH / 2, 0);
        backWall.receiveShadow = true;
        this.scene.add(backWall);

        // Left wall — at x=0 (left edge of canvas)
        const leftGeo = new THREE.PlaneGeometry(h, wallH);
        const leftWall = new THREE.Mesh(leftGeo, wallMat);
        leftWall.rotation.y = Math.PI / 2;
        leftWall.position.set(0, wallH / 2, h / 2);
        leftWall.receiveShadow = true;
        this.scene.add(leftWall);

        // Floor edge marking (yellow safety line) — at canvas boundary
        const lineGeo = new THREE.BoxGeometry(w, 0.02, 0.15);
        const lineMat = new THREE.MeshStandardMaterial({ color: 0xf0c040, roughness: 0.6 });
        const line1 = new THREE.Mesh(lineGeo, lineMat);
        line1.position.set(w / 2, 0.02, 0);
        this.scene.add(line1);
        const line2Geo = new THREE.BoxGeometry(0.15, 0.02, h);
        const line2 = new THREE.Mesh(line2Geo, lineMat);
        line2.position.set(0, 0.02, h / 2);
        this.scene.add(line2);
    }

    // ========================================================================
    // Camera Controls — Right-click orbit, middle/shift pan, scroll zoom
    // ========================================================================

    _setupControls(container) {
        const layout = this.props.layoutData;
        this._ctrl = {
            isOrbiting: false,
            isPanning: false,
            lastX: 0,
            lastY: 0,
            dragDist: 0,
            spherical: { radius: 45, theta: Math.PI / 4, phi: Math.PI / 3.2 },
            target: new THREE.Vector3(
                (layout?.canvas_width || 40) / 2,
                0,
                (layout?.canvas_height || 30) / 2
            ),
        };
        this._updateCameraFromSpherical();

        const el = this.renderer.domElement;

        el.addEventListener("mousedown", (e) => {
            this._ctrl.lastX = e.clientX;
            this._ctrl.lastY = e.clientY;
            this._ctrl.dragDist = 0;
            this._hasDragged = false;

            // Left-click (no shift) → orbit
            if (e.button === 0 && !e.shiftKey) {
                this._ctrl.isOrbiting = true;
                e.preventDefault();
            }
            // Middle-click or Shift+left or Right-click → pan
            if (e.button === 1 || (e.button === 0 && e.shiftKey) || e.button === 2) {
                this._ctrl.isPanning = true;
                e.preventDefault();
            }
        });

        el.addEventListener("mousemove", (e) => {
            const dx = e.clientX - this._ctrl.lastX;
            const dy = e.clientY - this._ctrl.lastY;
            this._ctrl.lastX = e.clientX;
            this._ctrl.lastY = e.clientY;
            this._ctrl.dragDist += Math.abs(dx) + Math.abs(dy);

            if (this._ctrl.dragDist > 4) {
                this._hasDragged = true;
            }

            if (this._ctrl.isOrbiting) {
                this._ctrl.spherical.theta -= dx * 0.006;
                this._ctrl.spherical.phi = Math.max(0.05, Math.min(Math.PI / 2 - 0.02,
                    this._ctrl.spherical.phi - dy * 0.006));
                this._updateCameraFromSpherical();
            }
            if (this._ctrl.isPanning) {
                const panSpeed = this._ctrl.spherical.radius * 0.0025;
                const forward = new THREE.Vector3().subVectors(
                    this.camera.position, this._ctrl.target
                ).normalize();
                const right = new THREE.Vector3().crossVectors(
                    new THREE.Vector3(0, 1, 0), forward
                ).normalize();
                const up = new THREE.Vector3(0, 1, 0);

                this._ctrl.target.addScaledVector(right, -dx * panSpeed);
                this._ctrl.target.addScaledVector(up, dy * panSpeed);
                this._updateCameraFromSpherical();
            }
        });

        el.addEventListener("mouseup", () => {
            this._ctrl.isOrbiting = false;
            this._ctrl.isPanning = false;
        });
        el.addEventListener("mouseleave", () => {
            this._ctrl.isOrbiting = false;
            this._ctrl.isPanning = false;
        });

        el.addEventListener("wheel", (e) => {
            e.preventDefault();
            const factor = 1.1;
            if (e.deltaY > 0) {
                this._ctrl.spherical.radius = Math.min(200, this._ctrl.spherical.radius * factor);
            } else {
                this._ctrl.spherical.radius = Math.max(3, this._ctrl.spherical.radius / factor);
            }
            this._updateCameraFromSpherical();
        }, { passive: false });

        el.addEventListener("contextmenu", (e) => e.preventDefault());
    }

    _updateCameraFromSpherical() {
        const { radius, theta, phi } = this._ctrl.spherical;
        const t = this._ctrl.target;
        this.camera.position.set(
            t.x + radius * Math.sin(phi) * Math.cos(theta),
            t.y + radius * Math.cos(phi),
            t.z + radius * Math.sin(phi) * Math.sin(theta)
        );
        this.camera.lookAt(t);
    }

    // ========================================================================
    // UI On-Screen Controls
    // ========================================================================

    startAction(action) {
        if (this._uiActionInterval) return;
        this._currentAction = action;
        this._executeAction();
        // Use a ~60fps interval for continuous movement.
        this._uiActionInterval = setInterval(() => this._executeAction(), 16);
    }

    stopAction() {
        if (this._uiActionInterval) {
            clearInterval(this._uiActionInterval);
            this._uiActionInterval = null;
        }
        this._currentAction = null;
    }

    _executeAction() {
        if (!this._currentAction) return;

        const panSpeed = this._ctrl.spherical.radius * 0.015;
        const orbitSpeed = 0.03;
        const zoomFactor = 1.025;

        const forward = new THREE.Vector3().subVectors(this.camera.position, this._ctrl.target).normalize();
        const right = new THREE.Vector3().crossVectors(new THREE.Vector3(0, 1, 0), forward).normalize();
        const floorForward = new THREE.Vector3(forward.x, 0, forward.z).normalize();

        switch (this._currentAction) {
            case 'panUp':
                this._ctrl.target.addScaledVector(floorForward, -panSpeed);
                break;
            case 'panDown':
                this._ctrl.target.addScaledVector(floorForward, panSpeed);
                break;
            case 'panLeft':
                this._ctrl.target.addScaledVector(right, -panSpeed);
                break;
            case 'panRight':
                this._ctrl.target.addScaledVector(right, panSpeed);
                break;
            case 'orbitLeft':
                this._ctrl.spherical.theta -= orbitSpeed;
                break;
            case 'orbitRight':
                this._ctrl.spherical.theta += orbitSpeed;
                break;
            case 'orbitUp':
                this._ctrl.spherical.phi = Math.max(0.05, this._ctrl.spherical.phi - orbitSpeed);
                break;
            case 'orbitDown':
                this._ctrl.spherical.phi = Math.min(Math.PI / 2 - 0.02, this._ctrl.spherical.phi + orbitSpeed);
                break;
            case 'zoomIn':
                this._ctrl.spherical.radius = Math.max(3, this._ctrl.spherical.radius / zoomFactor);
                break;
            case 'zoomOut':
                this._ctrl.spherical.radius = Math.min(200, this._ctrl.spherical.radius * zoomFactor);
                break;
        }
        this._updateCameraFromSpherical();
    }

    uiResetCamera() {
        const layout = this.props.layoutData;
        this._ctrl.spherical = { radius: 45, theta: Math.PI / 4, phi: Math.PI / 3.2 };
        this._ctrl.target = new THREE.Vector3(
            (layout?.canvas_width || 40) / 2,
            0,
            (layout?.canvas_height || 30) / 2
        );
        this._updateCameraFromSpherical();
    }

    // ========================================================================
    // Build 3D Warehouse
    // ========================================================================

    _buildWarehouse() {
        // Sync grid visibility with current prop
        if (this._gridMesh) {
            this._gridMesh.visible = this.props.gridEnabled;
        }

        // Clear location meshes
        for (const [, mesh] of this.locationMeshes) {
            this.scene.remove(mesh);
            mesh.geometry?.dispose();
            if (Array.isArray(mesh.material)) mesh.material.forEach(m => m.dispose());
            else mesh.material?.dispose();
        }
        this.locationMeshes.clear();

        // Clear details
        for (const m of this.detailMeshes) {
            this.scene.remove(m);
            m.geometry?.dispose();
            m.material?.dispose();
        }
        this.detailMeshes = [];

        // Clear labels
        for (const s of this.labelSprites) {
            this.scene.remove(s);
            s.material?.map?.dispose();
            s.material?.dispose();
        }
        this.labelSprites = [];

        // Clear map objects
        for (const m of this.mapObjectMeshes) {
            this.scene.remove(m);
            m.geometry?.dispose();
            m.material?.dispose();
        }
        this.mapObjectMeshes = [];

        // Clear other-floor meshes (multi-floor stacked view)
        for (const m of this.otherFloorMeshes) {
            this.scene.remove(m);
            m.traverse?.((child) => {
                if (child.isMesh) {
                    child.geometry?.dispose();
                    if (Array.isArray(child.material)) child.material.forEach(mt => mt.dispose());
                    else child.material?.dispose();
                }
            });
        }
        this.otherFloorMeshes = [];

        // Build search hit set
        const searchLocIds = new Set();
        for (const r of this.props.productSearchResults) {
            searchLocIds.add(r.location_id);
        }

        // Build locations for current/active floor
        for (const loc of this.props.locations) {
            this._createLocationMesh(loc, searchLocIds);
        }

        // Build map objects for current floor
        for (const obj of this.props.mapObjects) {
            this._createMapObjectMesh(obj);
        }

        // ── Multi-floor stacked rendering ──
        if (this.props.showAllFloors && this.props.allFloorData && this.props.allFloorData.length > 1) {
            const FLOOR_HEIGHT = 12;
            const activeFloorLevel = this.props.layoutData.floor_level || 0;

            for (const floor of this.props.allFloorData) {
                if (floor.layout_id === this.props.selectedLayoutId) {
                    continue; // Already rendered as the active floor
                }

                const yOffset = (floor.floor_level - activeFloorLevel) * FLOOR_HEIGHT;
                this._buildOtherFloor(floor, yOffset);

                // Add transparent floor plate separator
                this._buildFloorPlate(
                    floor.canvas_width || this.props.layoutData.canvas_width || 40,
                    floor.canvas_height || this.props.layoutData.canvas_height || 30,
                    yOffset,
                    floor.name,
                    floor.floor_level
                );
            }
        }

        // ── Heatmap legend overlay ──
        this._updateHeatmapLegend();
    }

    /**
     * Render a transparent floor plate at a given Y offset (for stacked multi-floor).
     */
    _buildFloorPlate(w, h, yOffset, floorName, floorLevel) {
        // Translucent floor plane
        const geo = new THREE.PlaneGeometry(w + 4, h + 4);
        const mat = new THREE.MeshStandardMaterial({
            color: 0xc8c8c8,
            transparent: true,
            opacity: 0.25,
            roughness: 0.9,
            side: THREE.DoubleSide,
        });
        const plane = new THREE.Mesh(geo, mat);
        plane.rotation.x = -Math.PI / 2;
        plane.position.set(w / 2, yOffset - 0.01, h / 2);
        plane.receiveShadow = true;
        this.scene.add(plane);
        this.otherFloorMeshes.push(plane);

        // Floor label text
        let label = floorName || '';
        if (floorLevel === 0) label += ' (GF)';
        else if (floorLevel < 0) label += ` (B${Math.abs(floorLevel)})`;
        else label += ` (F${floorLevel})`;

        const canvas = document.createElement('canvas');
        canvas.width = 512;
        canvas.height = 64;
        const ctx = canvas.getContext('2d');
        ctx.fillStyle = 'rgba(0,0,0,0)';
        ctx.fillRect(0, 0, 512, 64);
        ctx.font = 'bold 32px Inter, Arial, sans-serif';
        ctx.fillStyle = '#475569';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText(label, 256, 32);

        const tex = new THREE.CanvasTexture(canvas);
        const spriteMat = new THREE.SpriteMaterial({ map: tex, transparent: true, opacity: 0.7 });
        const sprite = new THREE.Sprite(spriteMat);
        sprite.scale.set(8, 1, 1);
        sprite.position.set(w / 2, yOffset + 0.5, -2);
        this.scene.add(sprite);
        this.otherFloorMeshes.push(sprite);
    }

    /**
     * Render an entire floor's locations and map objects at a Y offset,
     * using the same full-detail shape builders as the active floor.
     */
    _buildOtherFloor(floorData, yOffset) {
        const floorW = floorData.canvas_width || this.props.layoutData?.canvas_width || 40;
        const floorH = floorData.canvas_height || this.props.layoutData?.canvas_height || 30;
        // ── Full-detail locations ──
        for (const loc of (floorData.locations || [])) {
            const shape = loc.location_shape || "rack";
            const sx = loc.size_x || 2;
            const sz = loc.size_y || 1;
            const color = loc.location_color || "#4A90D9";

            const meshGroup = new THREE.Group();
            meshGroup.userData.locationId = loc.id;
            meshGroup.userData.locationName = loc.name;

            switch (shape) {
                case 'rack': this._buildRack(meshGroup, sx, sz, color, loc); break;
                case 'shelf': this._buildShelf(meshGroup, sx, sz, color, loc); break;
                case 'bin': this._buildBin(meshGroup, sx, sz, color); break;
                case 'zone': this._buildZone(meshGroup, sx, sz, color); break;
                case 'dock': this._buildDock(meshGroup, sx, sz, color, loc); break;
                case 'wall': this._buildWall(meshGroup, sx, sz, color, loc, floorW, floorH); break;
                case 'floor': this._buildFloor(meshGroup, sx, sz, color); break;
                case 'packing': this._buildPacking(meshGroup, sx, sz, color); break;
                case 'refrigerator': this._buildRefrigerator(meshGroup, sx, sz, color); break;
                case 'qc_area': this._buildQCArea(meshGroup, sx, sz, color); break;
                default: this._buildRack(meshGroup, sx, sz, color, loc);
            }

            meshGroup.position.set(loc.pos_x + sx / 2, yOffset, loc.pos_y + sz / 2);
            this.scene.add(meshGroup);
            this.otherFloorMeshes.push(meshGroup);
        }

        // ── Full-detail map objects ──
        for (const obj of (floorData.mapObjects || [])) {
            const sx = obj.size_x || 1;
            const sz = obj.size_y || 1;
            const c = new THREE.Color(obj.color || "#95A5A6");
            let mesh;

            switch (obj.object_type) {
                case 'fire_extinguisher': {
                    const geo = new THREE.CylinderGeometry(0.15, 0.15, 1.0, 12);
                    const mat = new THREE.MeshStandardMaterial({ color: 0xCC0000, roughness: 0.3, metalness: 0.6 });
                    mesh = new THREE.Mesh(geo, mat);
                    mesh.position.set(obj.pos_x + 0.5, yOffset + 0.5, obj.pos_y + 0.5);
                    mesh.castShadow = true;
                    break;
                }
                case 'water_point': {
                    const geo = new THREE.CylinderGeometry(0.2, 0.2, 0.8, 12);
                    const mat = new THREE.MeshStandardMaterial({ color: 0x2196F3, roughness: 0.4, metalness: 0.3 });
                    mesh = new THREE.Mesh(geo, mat);
                    mesh.position.set(obj.pos_x + 0.5, yOffset + 0.4, obj.pos_y + 0.5);
                    mesh.castShadow = true;
                    break;
                }
                case 'pillar': {
                    const geo = new THREE.CylinderGeometry(0.3, 0.3, 5, 16);
                    const mat = new THREE.MeshStandardMaterial({ color: 0x888888, roughness: 0.8 });
                    mesh = new THREE.Mesh(geo, mat);
                    mesh.position.set(obj.pos_x + 0.5, yOffset + 2.5, obj.pos_y + 0.5);
                    mesh.castShadow = true;
                    break;
                }
                case 'door': {
                    const geo = new THREE.BoxGeometry(sx * 0.9, 3.0, 0.15);
                    const mat = new THREE.MeshStandardMaterial({ color: 0x8B4513, roughness: 0.7 });
                    mesh = new THREE.Mesh(geo, mat);
                    mesh.position.set(obj.pos_x + sx / 2, yOffset + 1.5, obj.pos_y + sz / 2);
                    mesh.castShadow = true;
                    break;
                }
                case 'conveyor': {
                    const geo = new THREE.BoxGeometry(sx * 0.9, 0.8, sz * 0.7);
                    const mat = new THREE.MeshStandardMaterial({ color: 0x777777, metalness: 0.5, roughness: 0.4 });
                    mesh = new THREE.Mesh(geo, mat);
                    mesh.position.set(obj.pos_x + sx / 2, yOffset + 0.4, obj.pos_y + sz / 2);
                    mesh.castShadow = true;
                    break;
                }
                case 'wall': {
                    mesh = new THREE.Group();
                    this._buildWall(mesh, sx, sz, obj.color || "#555555", obj, floorW, floorH);
                    mesh.position.set(obj.pos_x + sx / 2, yOffset, obj.pos_y + sz / 2);
                    break;
                }
                case 'room': {
                    mesh = new THREE.Group();
                    this._buildRoom(mesh, sx, sz, obj.color || "#7F8C8D", obj);
                    mesh.position.set(obj.pos_x + sx / 2, yOffset, obj.pos_y + sz / 2);
                    break;
                }
                default: {
                    const geo = new THREE.BoxGeometry(sx * 0.8, 0.5, sz * 0.8);
                    const mat = new THREE.MeshStandardMaterial({ color: c, roughness: 0.7 });
                    mesh = new THREE.Mesh(geo, mat);
                    mesh.position.set(obj.pos_x + sx / 2, yOffset + 0.25, obj.pos_y + sz / 2);
                    break;
                }
            }

            if (mesh) {
                this.scene.add(mesh);
                this.otherFloorMeshes.push(mesh);
            }
        }
    }

    _createLocationMesh(loc, searchLocIds) {
        const shape = loc.location_shape || "rack";
        const sx = loc.size_x || 2;
        const sz = loc.size_y || 1;
        const isHighlighted = loc.id === this.props.highlightedLocationId || searchLocIds.has(loc.id);

        let color = loc.location_color || "#4A90D9";
        if (this.props.heatmapEnabled) {
            const hd = this.props.heatmapData[loc.id];
            if (hd) color = this._getHeatmapHex(hd.fill_pct);
        }

        const meshGroup = new THREE.Group();
        meshGroup.userData.locationId = loc.id;
        meshGroup.userData.locationName = loc.name;

        switch (shape) {
            case 'rack':
                this._buildRack(meshGroup, sx, sz, color, loc);
                break;
            case 'shelf':
                this._buildShelf(meshGroup, sx, sz, color, loc);
                break;
            case 'bin':
                this._buildBin(meshGroup, sx, sz, color);
                break;
            case 'zone':
                this._buildZone(meshGroup, sx, sz, color);
                break;
            case 'dock':
                this._buildDock(meshGroup, sx, sz, color, loc);
                break;
            case 'wall': {
                const _cw = this.props.layoutData?.canvas_width || 40;
                const _ch = this.props.layoutData?.canvas_height || 30;
                this._buildWall(meshGroup, sx, sz, color, loc, _cw, _ch);
            }
                break;
            case 'floor':
                this._buildFloor(meshGroup, sx, sz, color);
                break;
            case 'packing':
                this._buildPacking(meshGroup, sx, sz, color);
                break;
            case 'refrigerator':
                this._buildRefrigerator(meshGroup, sx, sz, color);
                break;
            case 'qc_area':
                this._buildQCArea(meshGroup, sx, sz, color);
                break;
            default:
                this._buildRack(meshGroup, sx, sz, color, loc);
        }

        meshGroup.position.set(loc.pos_x + sx / 2, 0, loc.pos_y + sz / 2);
        this.scene.add(meshGroup);
        this.locationMeshes.set(loc.id, meshGroup);

        // Label (Draw for all shapes to display product summaries)
        const maxH = this._getShapeHeight(shape);
        this._addLabel(loc, meshGroup.position, maxH, isHighlighted);

        // Highlight glow
        if (isHighlighted) {
            this._addHighlightRing(meshGroup.position, sx, sz);
        }
    }

    _getShapeHeight(shape) {
        const map = {
            rack: 4, shelf: 2.5, bin: 1.5, zone: 0.15, dock: 4.0, floor: 0.1,
            packing: 1.2, refrigerator: 3.5, qc_area: 0.2, wall: 4.0
        };
        return map[shape] || 2;
    }

    // ---- Shape Builders ----

    _buildRack(group, sx, sz, color, loc) {
        const children = loc.children || [];
        const childCount = children.length;
        const c = new THREE.Color(color);

        // Height scales with number of child layers
        const layerH = 0.9;
        const baseThick = 0.12;
        const h = childCount > 0
            ? Math.min(baseThick + childCount * layerH + 0.15, 6)
            : 0.8; // bare rack — low flat surface

        const panelThick = 0.05;
        const darkColor = c.clone().multiplyScalar(0.6);
        const metalMat = new THREE.MeshStandardMaterial({
            color: 0x777777, metalness: 0.7, roughness: 0.35,
        });

        // ── Flat base platform ──
        const baseGeo = new THREE.BoxGeometry(sx * 0.94, baseThick, sz * 0.94);
        const baseMat = new THREE.MeshStandardMaterial({
            color: c, roughness: 0.55, metalness: 0.15,
        });
        const base = new THREE.Mesh(baseGeo, baseMat);
        base.position.y = baseThick / 2;
        base.castShadow = true;
        base.receiveShadow = true;
        group.add(base);
        this.detailMeshes.push(base);

        // ── Side panels (left & right walls) ──
        const sideMat = new THREE.MeshStandardMaterial({
            color: darkColor, roughness: 0.5, metalness: 0.2,
        });
        const sideGeo = new THREE.BoxGeometry(panelThick, h, sz * 0.92);
        for (const xSide of [-sx * 0.47, sx * 0.47]) {
            const panel = new THREE.Mesh(sideGeo, sideMat);
            panel.position.set(xSide, h / 2, 0);
            panel.castShadow = true;
            panel.receiveShadow = true;
            group.add(panel);
            this.detailMeshes.push(panel);
        }

        // ── Back panel ──
        const backGeo = new THREE.BoxGeometry(sx * 0.94, h, panelThick);
        const backMat = new THREE.MeshStandardMaterial({
            color: darkColor.clone().multiplyScalar(0.9), roughness: 0.6, metalness: 0.1,
        });
        const back = new THREE.Mesh(backGeo, backMat);
        back.position.set(0, h / 2, -sz * 0.46);
        back.castShadow = true;
        back.receiveShadow = true;
        group.add(back);
        this.detailMeshes.push(back);

        // ── Front lip (thin bar at front for item retention) ──
        const lipGeo = new THREE.BoxGeometry(sx * 0.94, 0.06, panelThick);
        const lip = new THREE.Mesh(lipGeo, metalMat);
        lip.position.set(0, baseThick + 0.03, sz * 0.46);
        group.add(lip);
        this.detailMeshes.push(lip);

        if (childCount === 0) {
            return;
        }

        // ── Dynamic shelf layers — one flat board per child ──
        for (let i = 0; i < childCount; i++) {
            const child = children[i];
            const layerY = baseThick + i * layerH;

            // Per-child heatmap color or shaded parent color
            const layerColor = this._getChildLayerColor(child, c, i, childCount);

            // Shelf board inside rack body
            const boardGeo = new THREE.BoxGeometry(sx * 0.88, 0.06, sz * 0.88);
            const boardMat = new THREE.MeshStandardMaterial({
                color: layerColor,
                roughness: 0.5,
                metalness: 0.12,
            });
            const board = new THREE.Mesh(boardGeo, boardMat);
            board.position.set(0, layerY, 0);
            board.castShadow = true;
            board.receiveShadow = true;
            group.add(board);
            this.detailMeshes.push(board);

            // Thin metal divider rails on each side
            const railGeo = new THREE.BoxGeometry(panelThick * 0.6, 0.03, sz * 0.86);
            for (const xr of [-sx * 0.44, sx * 0.44]) {
                const rail = new THREE.Mesh(railGeo, metalMat);
                rail.position.set(xr, layerY + 0.04, 0);
                group.add(rail);
                this.detailMeshes.push(rail);
            }

            // Child name label on the layer face
            // if (child.name) {
            //     this._addLayerLabel(group, child.name, sx, sz, layerY + 0.08);
            // }
        }

        // ── Top cap ──
        const topY = baseThick + childCount * layerH;
        const topGeo = new THREE.BoxGeometry(sx * 0.94, 0.05, sz * 0.94);
        const topMat = new THREE.MeshStandardMaterial({
            color: c.clone().multiplyScalar(0.85),
            roughness: 0.5,
            metalness: 0.15,
        });
        const topCap = new THREE.Mesh(topGeo, topMat);
        topCap.position.y = topY;
        topCap.castShadow = true;
        group.add(topCap);
        this.detailMeshes.push(topCap);
    }

    _buildShelf(group, sx, sz, color, loc) {
        const children = loc.children || [];
        const c = new THREE.Color(color);

        // If no children, but user specified rows, we draw empty layers.
        // If children exceed shelf_rows, we draw enough for children.
        const extraLayers = Math.max((loc.shelf_rows || 1) - 1, children.length);
        const childCount = children.length; // for color calc

        // Heights: base rack always present + extraLayers above it
        const layerH = 0.8;
        const baseH = 0.15;  // ground clearance
        const totalLayers = 1 + extraLayers;
        const h = Math.min(baseH + totalLayers * layerH + 0.3, 6);

        // 4 vertical legs (metal posts)
        const legGeo = new THREE.BoxGeometry(0.08, h, 0.08);
        const legMat = new THREE.MeshStandardMaterial({
            color: 0x555555,
            metalness: 0.8,
            roughness: 0.3,
        });
        const legPositions = [
            [-sx * 0.44, h / 2, -sz * 0.44],
            [sx * 0.44, h / 2, -sz * 0.44],
            [-sx * 0.44, h / 2, sz * 0.44],
            [sx * 0.44, h / 2, sz * 0.44],
        ];
        for (const p of legPositions) {
            const leg = new THREE.Mesh(legGeo, legMat);
            leg.position.set(...p);
            leg.castShadow = true;
            group.add(leg);
            this.detailMeshes.push(leg);
        }

        const railMat = new THREE.MeshStandardMaterial({ color: 0x666666, metalness: 0.7, roughness: 0.3 });

        // ── Default base rack (always present) ──
        const baseY = baseH;
        const baseBoardGeo = new THREE.BoxGeometry(sx * 0.86, 0.05, sz * 0.86);
        const baseBoardMat = new THREE.MeshStandardMaterial({
            color: c.clone().multiplyScalar(0.55),
            roughness: 0.45,
            metalness: 0.15,
        });
        const baseBoard = new THREE.Mesh(baseBoardGeo, baseBoardMat);
        baseBoard.position.y = baseY;
        baseBoard.castShadow = true;
        baseBoard.receiveShadow = true;
        group.add(baseBoard);
        this.detailMeshes.push(baseBoard);

        // Base rack side rails
        const baseRailGeo = new THREE.BoxGeometry(0.03, 0.03, sz * 0.86);
        for (const side of [-sx * 0.44, sx * 0.44]) {
            const rail = new THREE.Mesh(baseRailGeo, railMat);
            rail.position.set(side, baseY + 0.04, 0);
            group.add(rail);
            this.detailMeshes.push(rail);
        }
        // Base rack back cross bar
        const baseCrossGeo = new THREE.BoxGeometry(sx * 0.86, 0.03, 0.03);
        const baseCross = new THREE.Mesh(baseCrossGeo, railMat);
        baseCross.position.set(0, baseY + 0.04, -sz * 0.44);
        group.add(baseCross);
        this.detailMeshes.push(baseCross);

        // Label for the shelf itself on the base rack
        // this._addLayerLabel(group, loc.name || "Shelf", sx, sz, baseY + 0.08);

        // ── Stack child rack layers above the base ──
        for (let i = 0; i < extraLayers; i++) {
            const child = children[i];
            const layerY = baseH + (i + 1) * layerH;  // +1 to stack above base

            // Per-child heatmap color or shaded parent color
            const layerColor = child ? this._getChildLayerColor(child, c, i, childCount) : c.clone().multiplyScalar(0.7 - (i % 2) * 0.05);

            // Rack layer board
            const boardGeo = new THREE.BoxGeometry(sx * 0.86, 0.05, sz * 0.86);
            const boardMat = new THREE.MeshStandardMaterial({
                color: layerColor,
                roughness: 0.5,
                metalness: 0.1,
            });
            const board = new THREE.Mesh(boardGeo, boardMat);
            board.position.y = layerY;
            board.castShadow = true;
            board.receiveShadow = true;
            group.add(board);
            this.detailMeshes.push(board);

            // Side rails
            const railGeo = new THREE.BoxGeometry(0.03, 0.03, sz * 0.86);
            for (const side of [-sx * 0.44, sx * 0.44]) {
                const rail = new THREE.Mesh(railGeo, railMat);
                rail.position.set(side, layerY + 0.04, 0);
                group.add(rail);
                this.detailMeshes.push(rail);
            }

            // Cross bar at the back
            const crossGeo = new THREE.BoxGeometry(sx * 0.86, 0.03, 0.03);
            const cross = new THREE.Mesh(crossGeo, railMat);
            cross.position.set(0, layerY + 0.04, -sz * 0.44);
            group.add(cross);
            this.detailMeshes.push(cross);

            // Child name label
            // if (child && child.name) {
            //     this._addLayerLabel(group, child.name, sx, sz, layerY + 0.08);
            // }
        }

        // Top cap
        const topY = baseH + totalLayers * layerH;
        const topGeo = new THREE.BoxGeometry(sx * 0.86, 0.04, sz * 0.86);
        const topMat = new THREE.MeshStandardMaterial({
            color: c.clone().multiplyScalar(0.9),
            roughness: 0.5,
            metalness: 0.1,
        });
        const topCap = new THREE.Mesh(topGeo, topMat);
        topCap.position.y = topY;
        topCap.castShadow = true;
        group.add(topCap);
        this.detailMeshes.push(topCap);
    }

    _buildBin(group, sx, sz, color) {
        const h = 1.5;
        const c = new THREE.Color(color);

        // Open-top box
        const wallThick = 0.06;
        const outerGeo = new THREE.BoxGeometry(sx * 0.9, h, sz * 0.9);
        const outerMat = new THREE.MeshStandardMaterial({ color: c, roughness: 0.7, metalness: 0.05 });
        const outer = new THREE.Mesh(outerGeo, outerMat);
        outer.position.y = h / 2;
        outer.castShadow = true;
        group.add(outer);
        this.detailMeshes.push(outer);

        // Inner cavity (darker)
        const innerGeo = new THREE.BoxGeometry(sx * 0.9 - wallThick * 2, h * 0.3, sz * 0.9 - wallThick * 2);
        const innerMat = new THREE.MeshStandardMaterial({ color: c.clone().multiplyScalar(0.5) });
        const inner = new THREE.Mesh(innerGeo, innerMat);
        inner.position.y = h - h * 0.15;
        group.add(inner);
        this.detailMeshes.push(inner);
    }

    _buildZone(group, sx, sz, color) {
        // Darker gray override for zone center
        const c = new THREE.Color(0x555555);
        const geo = new THREE.PlaneGeometry(sx * 0.98, sz * 0.98);
        const mat = new THREE.MeshStandardMaterial({
            color: c,
            transparent: true,
            opacity: 0.5,
            roughness: 1.0,
            side: THREE.DoubleSide,
        });
        const plane = new THREE.Mesh(geo, mat);
        plane.rotation.x = -Math.PI / 2;
        plane.position.y = 0.05;
        plane.receiveShadow = true;
        group.add(plane);
        this.detailMeshes.push(plane);

        // Striped tape boundaries
        const borderThick = 0.15;

        // Helper to create a striped repeating canvas texture 
        const createStripeMaterial = (repX, repY) => {
            const canvas = document.createElement('canvas');
            canvas.width = 64;
            canvas.height = 64;
            const ctx = canvas.getContext('2d');
            ctx.fillStyle = '#FFDD00';
            ctx.fillRect(0, 0, 64, 64);
            ctx.fillStyle = '#111111';
            ctx.beginPath();
            for (let i = -64; i < 128; i += 64) {
                ctx.moveTo(i, 0);
                ctx.lineTo(i + 64, 64);
                ctx.lineTo(i + 64 + 40, 64);
                ctx.lineTo(i + 40, 0);
            }
            ctx.fill();
            const tex = new THREE.CanvasTexture(canvas);
            tex.wrapS = THREE.RepeatWrapping;
            tex.wrapT = THREE.RepeatWrapping;
            tex.repeat.set(repX, repY);
            return new THREE.MeshStandardMaterial({ map: tex, roughness: 0.8, side: THREE.DoubleSide });
        };

        // Left and Right borders
        const zGeo = new THREE.PlaneGeometry(borderThick, sz * 0.98 - borderThick * 2);
        const zMat = createStripeMaterial(borderThick * 4, sz * 4);
        for (const bx of [-sx / 2 + borderThick / 2 + 0.01, sx / 2 - borderThick / 2 - 0.01]) {
            const zBorder = new THREE.Mesh(zGeo, zMat);
            zBorder.rotation.x = -Math.PI / 2;
            zBorder.position.set(bx, 0.06, 0); // slightly above the zone plane
            zBorder.receiveShadow = true;
            group.add(zBorder);
            this.detailMeshes.push(zBorder);
        }

        // Top and Bottom borders
        const xGeo = new THREE.PlaneGeometry(sx * 0.98, borderThick);
        const xMat = createStripeMaterial(sx * 4, borderThick * 4);
        for (const bz of [-sz / 2 + borderThick / 2 + 0.01, sz / 2 - borderThick / 2 - 0.01]) {
            const xBorder = new THREE.Mesh(xGeo, xMat);
            xBorder.rotation.x = -Math.PI / 2;
            xBorder.position.set(0, 0.06, bz);
            xBorder.receiveShadow = true;
            group.add(xBorder);
            this.detailMeshes.push(xBorder);
        }
    }

    _buildDock(group, sx, sz, color, loc) {
        const c = new THREE.Color(color);
        const shutterH = 4.0;

        const dockGroup = new THREE.Group();
        group.add(dockGroup);

        const rot = loc.location_rotation || 0;
        const rad = rot * (Math.PI / 180);
        dockGroup.rotation.y = -rad; // Three.js uses counter-clockwise for positive Y rotation, we want standard compass direction

        let bSx = sx;
        let bSz = sz;

        // Door frame
        const frameThick = 0.2;
        const frameMat = new THREE.MeshStandardMaterial({ color: 0x555555, roughness: 0.6, metalness: 0.3 });

        // Left frame
        const leftGeo = new THREE.BoxGeometry(frameThick, shutterH, frameThick);
        const leftFrame = new THREE.Mesh(leftGeo, frameMat);
        leftFrame.position.set(-bSx * 0.45, shutterH / 2, -bSz * 0.4);
        leftFrame.castShadow = true;
        dockGroup.add(leftFrame);
        this.detailMeshes.push(leftFrame);

        // Right frame
        const rightGeo = new THREE.BoxGeometry(frameThick, shutterH, frameThick);
        const rightFrame = new THREE.Mesh(rightGeo, frameMat);
        rightFrame.position.set(bSx * 0.45, shutterH / 2, -bSz * 0.4);
        rightFrame.castShadow = true;
        dockGroup.add(rightFrame);
        this.detailMeshes.push(rightFrame);

        // Top frame / Roller housing
        const topGeo = new THREE.BoxGeometry(bSx * 0.9 + frameThick * 2, frameThick * 2, frameThick * 2);
        const topFrame = new THREE.Mesh(topGeo, frameMat);
        topFrame.position.set(0, shutterH, -bSz * 0.4);
        topFrame.castShadow = true;
        dockGroup.add(topFrame);
        this.detailMeshes.push(topFrame);

        // The shutter door itself (corrugated metal look)
        const doorW = bSx * 0.9; // fit inside frames
        const doorGeo = new THREE.BoxGeometry(doorW, shutterH * 0.95, 0.05);
        const doorMat = new THREE.MeshStandardMaterial({
            color: c,
            roughness: 0.4,
            metalness: 0.5
        });
        const door = new THREE.Mesh(doorGeo, doorMat);
        door.position.set(0, shutterH * 0.95 / 2, -bSz * 0.4);
        door.castShadow = true;
        dockGroup.add(door);
        this.detailMeshes.push(door);

        // Horizontal lines to simulate slats
        const slatMat = new THREE.MeshStandardMaterial({ color: 0x333333 });
        const numSlats = 15;
        const slatGeo = new THREE.BoxGeometry(doorW, 0.02, 0.07);
        for (let i = 1; i < numSlats; i++) {
            const h = (shutterH * 0.95 / numSlats) * i;
            const slat = new THREE.Mesh(slatGeo, slatMat);
            slat.position.set(0, h, -bSz * 0.4);
            dockGroup.add(slat);
            this.detailMeshes.push(slat);
        }

        // Yellow floor marker indicating dock area
        const markerGeo = new THREE.PlaneGeometry(bSx * 0.9, bSz * 0.8);
        const markerMat = new THREE.MeshStandardMaterial({ color: 0xFFCC00, transparent: true, opacity: 0.3, side: THREE.DoubleSide });
        const marker = new THREE.Mesh(markerGeo, markerMat);
        marker.rotation.x = -Math.PI / 2;
        marker.position.y = 0.02;
        marker.position.z = bSz * 0.05;
        marker.receiveShadow = true;
        dockGroup.add(marker);
        this.detailMeshes.push(marker);

        // Side safety bollards
        const bollardGeo = new THREE.CylinderGeometry(0.08, 0.08, 0.8, 16);
        const bollardMat = new THREE.MeshStandardMaterial({ color: 0xFFDD00, roughness: 0.4 });
        for (const bx of [-bSx * 0.4, bSx * 0.4]) {
            const bollard = new THREE.Mesh(bollardGeo, bollardMat);
            bollard.position.set(bx, 0.4, bSz * 0.3);
            bollard.castShadow = true;
            dockGroup.add(bollard);
            this.detailMeshes.push(bollard);

            // Black stripe on bollard
            const stripeGeo = new THREE.CylinderGeometry(0.082, 0.082, 0.15, 16);
            const stripeMat = new THREE.MeshStandardMaterial({ color: 0x111111 });
            const stripe = new THREE.Mesh(stripeGeo, stripeMat);
            stripe.position.set(bx, 0.6, bSz * 0.3);
            dockGroup.add(stripe);
            this.detailMeshes.push(stripe);
        }
    }

    _buildFloor(group, sx, sz, color) {
        const c = new THREE.Color(color);
        const geo = new THREE.PlaneGeometry(sx * 0.98, sz * 0.98);
        const mat = new THREE.MeshStandardMaterial({
            color: c,
            transparent: true,
            opacity: 0.25,
            roughness: 1.0,
            side: THREE.DoubleSide,
        });
        const plane = new THREE.Mesh(geo, mat);
        plane.rotation.x = -Math.PI / 2;
        plane.position.y = 0.03;
        plane.receiveShadow = true;
        group.add(plane);
        this.detailMeshes.push(plane);
    }

    _buildWall(group, sx, sz, color, loc, canvasW, canvasH) {
        const c = new THREE.Color(color);
        const wallGroup = new THREE.Group();
        group.add(wallGroup);

        const rot = loc.location_rotation || 0;
        const rad = rot * (Math.PI / 180);
        wallGroup.rotation.y = -rad;

        // Base height for walls
        const h = 4.0;

        // Make the wall thinner. The smaller dimension becomes the thickness.
        let wX = sx;
        let wZ = sz;
        const thickness = 0.15;

        let offsetX = 0;
        let offsetZ = 0;
        const flipped = !!loc.is_flipped;

        // The wall's absolute world-space origin (center of its cell area)
        const posX = loc.pos_x || 0;
        const posY = loc.pos_y || 0;
        // Canvas bounds (default to large values if not provided)
        const cW = canvasW || 9999;
        const cH = canvasH || 9999;

        if (sx <= sz) {
            // Vertical wall — thin in X, long in Z
            wX = thickness;

            // Auto-snap thin dimension to canvas edge for boundary walls,
            // so walls at the map edge are always flush with the boundary.
            const atLeftEdge = posX <= 0;
            const atRightEdge = (posX + sx) >= cW;
            if (atRightEdge && !atLeftEdge) {
                // Snap wall's right face to the right canvas boundary
                offsetX = (sx / 2) - (thickness / 2);
            } else if (atLeftEdge && !atRightEdge) {
                // Snap wall's left face to the left canvas boundary
                offsetX = -(sx / 2) + (thickness / 2);
            } else {
                // Interior wall (or spanning full width): use is_flipped flag
                offsetX = flipped
                    ? (sx / 2) - (thickness / 2)
                    : -(sx / 2) + (thickness / 2);
            }

            // Clamp wZ (the long axis) so the wall doesn't extend past canvas bounds.
            const centerZ = posY + sz / 2;
            const minZ = centerZ - wZ / 2;
            const maxZ = centerZ + wZ / 2;
            const clampedMin = Math.max(0, minZ);
            const clampedMax = Math.min(cH, maxZ);
            if (clampedMax > clampedMin) {
                const newLen = clampedMax - clampedMin;
                const newCenter = (clampedMin + clampedMax) / 2;
                wZ = newLen;
                offsetZ = newCenter - centerZ;
            }
        } else {
            // Horizontal wall — thin in Z, long in X
            wZ = thickness;

            // Auto-snap thin dimension to canvas edge for boundary walls.
            const atTopEdge = posY <= 0;
            const atBottomEdge = (posY + sz) >= cH;
            if (atBottomEdge && !atTopEdge) {
                // Snap wall's bottom face to the bottom canvas boundary
                offsetZ = (sz / 2) - (thickness / 2);
            } else if (atTopEdge && !atBottomEdge) {
                // Snap wall's top face to the top canvas boundary
                offsetZ = -(sz / 2) + (thickness / 2);
            } else {
                // Interior wall: use is_flipped flag
                offsetZ = flipped
                    ? (sz / 2) - (thickness / 2)
                    : -(sz / 2) + (thickness / 2);
            }

            // Clamp wX (the long axis) so the wall doesn't extend past canvas bounds.
            const centerX = posX + sx / 2;
            const minX = centerX - wX / 2;
            const maxX = centerX + wX / 2;
            const clampedMin = Math.max(0, minX);
            const clampedMax = Math.min(cW, maxX);
            if (clampedMax > clampedMin) {
                const newLen = clampedMax - clampedMin;
                const newCenter = (clampedMin + clampedMax) / 2;
                wX = newLen;
                offsetX = newCenter - centerX;
            }
        }

        // Wall
        const wallGeo = new THREE.BoxGeometry(wX, h, wZ);
        const wallMat = new THREE.MeshStandardMaterial({
            color: c,
            roughness: 0.85,  // Matte finish
            metalness: 0.05,
        });
        const wall = new THREE.Mesh(wallGeo, wallMat);
        wall.position.set(offsetX, h / 2, offsetZ);
        wall.castShadow = true;
        wall.receiveShadow = true;
        wallGroup.add(wall);
        this.detailMeshes.push(wall);

        // Darker Baseboard (to add simple realism)
        const baseH = 0.2;
        const baseboardOffset = 0.05;
        const baseGeo = new THREE.BoxGeometry(wX + (sx <= sz ? baseboardOffset : 0), baseH, wZ + (sx > sz ? baseboardOffset : 0));
        const baseMat = new THREE.MeshStandardMaterial({
            color: c.clone().multiplyScalar(0.5),
            roughness: 0.9
        });
        const baseboard = new THREE.Mesh(baseGeo, baseMat);
        baseboard.position.set(offsetX, baseH / 2, offsetZ);
        wallGroup.add(baseboard);
        this.detailMeshes.push(baseboard);

        // Top cap
        const capGeo = new THREE.BoxGeometry(wX + (sx <= sz ? baseboardOffset : 0), 0.05, wZ + (sx > sz ? baseboardOffset : 0));
        const capMat = new THREE.MeshStandardMaterial({
            color: c.clone().multiplyScalar(0.7),
            roughness: 0.8
        });
        const cap = new THREE.Mesh(capGeo, capMat);
        cap.position.set(offsetX, h + 0.025, offsetZ);
        wallGroup.add(cap);
        this.detailMeshes.push(cap);
    }

    _buildRoom(group, sx, sz, color, loc) {
        const c = new THREE.Color(color);
        const roomGroup = new THREE.Group();
        group.add(roomGroup);

        const rot = loc.location_rotation || 0;
        const rad = rot * (Math.PI / 180);
        roomGroup.rotation.y = -rad;

        // Ensure we use the base dimensions before any rotation swaps them,
        // because the UI rotation rotates the entire group, preserving local dimensions.
        const w = sx;
        const d = sz;
        const h = 3.0; // Wall height
        const t = 0.15; // Wall thickness

        // Semi-transparent wall material
        const wallMat = new THREE.MeshStandardMaterial({
            color: c,
            transparent: true,
            opacity: 0.6,
            roughness: 0.7,
            metalness: 0.1,
            side: THREE.DoubleSide
        });

        // Floor inside the room
        const floorGeo = new THREE.PlaneGeometry(w - t * 2, d - t * 2);
        const floorMat = new THREE.MeshStandardMaterial({
            color: c.clone().multiplyScalar(0.7),
            roughness: 0.9
        });
        const floor = new THREE.Mesh(floorGeo, floorMat);
        floor.rotation.x = -Math.PI / 2;
        floor.position.y = 0.05;
        floor.receiveShadow = true;
        roomGroup.add(floor);
        this.detailMeshes.push(floor);

        // Back Wall
        const backGeo = new THREE.BoxGeometry(w, h, t);
        const backWall = new THREE.Mesh(backGeo, wallMat);
        backWall.position.set(0, h / 2, -d / 2 + t / 2);
        backWall.castShadow = true;
        backWall.receiveShadow = true;
        roomGroup.add(backWall);
        this.detailMeshes.push(backWall);

        // Left Wall
        const sideGeo = new THREE.BoxGeometry(t, h, d - t * 2);
        const leftWall = new THREE.Mesh(sideGeo, wallMat);
        leftWall.position.set(-w / 2 + t / 2, h / 2, 0);
        leftWall.castShadow = true;
        leftWall.receiveShadow = true;
        roomGroup.add(leftWall);
        this.detailMeshes.push(leftWall);

        // Right Wall
        const rightWall = new THREE.Mesh(sideGeo, wallMat);
        rightWall.position.set(w / 2 - t / 2, h / 2, 0);
        rightWall.castShadow = true;
        rightWall.receiveShadow = true;
        roomGroup.add(rightWall);
        this.detailMeshes.push(rightWall);

        // Front Wall (with door cutout)
        // We build this with 3 pieces: left side, right side, top header
        const doorW = Math.min(1.2, w * 0.4);
        const doorH = 2.0;
        const sideW = (w - doorW) / 2;

        // Front Left side
        const fLeftGeo = new THREE.BoxGeometry(sideW, h, t);
        const fLeft = new THREE.Mesh(fLeftGeo, wallMat);
        fLeft.position.set(-w / 2 + sideW / 2, h / 2, d / 2 - t / 2);
        fLeft.castShadow = true;
        fLeft.receiveShadow = true;
        roomGroup.add(fLeft);
        this.detailMeshes.push(fLeft);

        // Front Right side
        const fRightGeo = new THREE.BoxGeometry(sideW, h, t);
        const fRight = new THREE.Mesh(fRightGeo, wallMat);
        fRight.position.set(w / 2 - sideW / 2, h / 2, d / 2 - t / 2);
        fRight.castShadow = true;
        fRight.receiveShadow = true;
        roomGroup.add(fRight);
        this.detailMeshes.push(fRight);

        // Front Header (above door)
        const fTopH = h - doorH;
        if (fTopH > 0) {
            const fTopGeo = new THREE.BoxGeometry(doorW, fTopH, t);
            const fTop = new THREE.Mesh(fTopGeo, wallMat);
            fTop.position.set(0, doorH + fTopH / 2, d / 2 - t / 2);
            fTop.castShadow = true;
            fTop.receiveShadow = true;
            roomGroup.add(fTop);
            this.detailMeshes.push(fTop);
        }
    }

    _buildPacking(group, sx, sz, color) {
        const c = new THREE.Color(color);

        // Table
        const tableGeo = new THREE.BoxGeometry(sx * 0.9, 0.08, sz * 0.7);
        const tableMat = new THREE.MeshStandardMaterial({ color: c, roughness: 0.5 });
        const table = new THREE.Mesh(tableGeo, tableMat);
        table.position.set(0, 1.0, 0);
        table.castShadow = true;
        group.add(table);
        this.detailMeshes.push(table);

        // Table legs
        const legGeo = new THREE.BoxGeometry(0.06, 1.0, 0.06);
        const legMat = new THREE.MeshStandardMaterial({ color: 0x555555 });
        const legs = [[-sx * 0.4, 0.5, -sz * 0.3], [sx * 0.4, 0.5, -sz * 0.3],
        [-sx * 0.4, 0.5, sz * 0.3], [sx * 0.4, 0.5, sz * 0.3]];
        for (const p of legs) {
            const leg = new THREE.Mesh(legGeo, legMat);
            leg.position.set(...p);
            group.add(leg);
            this.detailMeshes.push(leg);
        }

        // "Conveyor" rollers on table
        const rollerGeo = new THREE.CylinderGeometry(0.04, 0.04, sz * 0.6, 8);
        const rollerMat = new THREE.MeshStandardMaterial({ color: 0x999999, metalness: 0.6 });
        for (let i = 0; i < 4; i++) {
            const roller = new THREE.Mesh(rollerGeo, rollerMat);
            roller.rotation.x = Math.PI / 2;
            roller.position.set(-sx * 0.3 + i * (sx * 0.2), 1.08, 0);
            group.add(roller);
            this.detailMeshes.push(roller);
        }
    }

    _buildRefrigerator(group, sx, sz, color) {
        const h = 3.5;
        const c = new THREE.Color(color);

        // Main body
        const bodyGeo = new THREE.BoxGeometry(sx * 0.92, h, sz * 0.92);
        const bodyMat = new THREE.MeshStandardMaterial({
            color: c,
            roughness: 0.3,
            metalness: 0.4,
        });
        const body = new THREE.Mesh(bodyGeo, bodyMat);
        body.position.y = h / 2;
        body.castShadow = true;
        body.receiveShadow = true;
        group.add(body);
        this.detailMeshes.push(body);

        // Door line
        const doorGeo = new THREE.BoxGeometry(0.02, h * 0.85, sz * 0.85);
        const doorMat = new THREE.MeshStandardMaterial({ color: c.clone().multiplyScalar(0.8) });
        const door = new THREE.Mesh(doorGeo, doorMat);
        door.position.set(sx * 0.47, h * 0.45, 0);
        group.add(door);
        this.detailMeshes.push(door);

        // Handle
        const handleGeo = new THREE.BoxGeometry(0.04, 0.5, 0.04);
        const handleMat = new THREE.MeshStandardMaterial({ color: 0xCCCCCC, metalness: 0.8 });
        const handle = new THREE.Mesh(handleGeo, handleMat);
        handle.position.set(sx * 0.5, h * 0.55, 0);
        group.add(handle);
        this.detailMeshes.push(handle);

        // Vent lines on top
        const ventMat = new THREE.MeshStandardMaterial({ color: 0x333333 });
        for (let i = 0; i < 3; i++) {
            const ventGeo = new THREE.BoxGeometry(sx * 0.5, 0.02, 0.02);
            const vent = new THREE.Mesh(ventGeo, ventMat);
            vent.position.set(0, h + 0.02, -sz * 0.2 + i * sz * 0.2);
            group.add(vent);
            this.detailMeshes.push(vent);
        }
    }

    _buildQCArea(group, sx, sz, color) {
        const c = new THREE.Color(color);

        // Ground marking
        const groundGeo = new THREE.PlaneGeometry(sx * 0.98, sz * 0.98);
        const groundMat = new THREE.MeshStandardMaterial({
            color: c,
            transparent: true,
            opacity: 0.35,
            side: THREE.DoubleSide,
        });
        const ground = new THREE.Mesh(groundGeo, groundMat);
        ground.rotation.x = -Math.PI / 2;
        ground.position.y = 0.04;
        ground.receiveShadow = true;
        group.add(ground);
        this.detailMeshes.push(ground);

        // Corner posts (like stanchions)
        const stanchGeo = new THREE.CylinderGeometry(0.04, 0.04, 1.2, 8);
        const stanchMat = new THREE.MeshStandardMaterial({ color: c.clone().multiplyScalar(0.7), metalness: 0.5 });
        const corners = [[-sx / 2 + 0.1, 0.6, -sz / 2 + 0.1], [sx / 2 - 0.1, 0.6, -sz / 2 + 0.1],
        [-sx / 2 + 0.1, 0.6, sz / 2 - 0.1], [sx / 2 - 0.1, 0.6, sz / 2 - 0.1]];
        for (const p of corners) {
            const s = new THREE.Mesh(stanchGeo, stanchMat);
            s.position.set(...p);
            s.castShadow = true;
            group.add(s);
            this.detailMeshes.push(s);
        }

        // Rope/chain between posts (top bar only on front)
        const ropeGeo = new THREE.CylinderGeometry(0.02, 0.02, sx - 0.2, 6);
        const ropeMat = new THREE.MeshStandardMaterial({ color: 0xFFCC00 });
        const rope = new THREE.Mesh(ropeGeo, ropeMat);
        rope.rotation.z = Math.PI / 2;
        rope.position.set(0, 1.0, sz / 2 - 0.1);
        group.add(rope);
        this.detailMeshes.push(rope);
    }

    // ---- Map Objects (non-location) ----

    _createMapObjectMesh(obj) {
        const sx = obj.size_x || 1;
        const sz = obj.size_y || 1;
        const c = new THREE.Color(obj.color || "#95A5A6");
        let mesh;

        switch (obj.object_type) {
            case 'fire_extinguisher': {
                const geo = new THREE.CylinderGeometry(0.15, 0.15, 1.0, 12);
                const mat = new THREE.MeshStandardMaterial({ color: 0xCC0000, roughness: 0.3, metalness: 0.6 });
                mesh = new THREE.Mesh(geo, mat);
                mesh.position.set(obj.pos_x + 0.5, 0.5, obj.pos_y + 0.5);
                mesh.castShadow = true;
                break;
            }
            case 'water_point': {
                const geo = new THREE.CylinderGeometry(0.2, 0.2, 0.8, 12);
                const mat = new THREE.MeshStandardMaterial({ color: 0x2196F3, roughness: 0.4, metalness: 0.3 });
                mesh = new THREE.Mesh(geo, mat);
                mesh.position.set(obj.pos_x + 0.5, 0.4, obj.pos_y + 0.5);
                mesh.castShadow = true;
                break;
            }
            case 'pillar': {
                const geo = new THREE.CylinderGeometry(0.3, 0.3, 5, 16);
                const mat = new THREE.MeshStandardMaterial({ color: 0x888888, roughness: 0.8 });
                mesh = new THREE.Mesh(geo, mat);
                mesh.position.set(obj.pos_x + 0.5, 2.5, obj.pos_y + 0.5);
                mesh.castShadow = true;
                break;
            }
            case 'door': {
                const geo = new THREE.BoxGeometry(sx * 0.9, 3.0, 0.15);
                const mat = new THREE.MeshStandardMaterial({ color: 0x8B4513, roughness: 0.7 });
                mesh = new THREE.Mesh(geo, mat);
                mesh.position.set(obj.pos_x + sx / 2, 1.5, obj.pos_y + sz / 2);
                mesh.castShadow = true;
                break;
            }
            case 'conveyor': {
                const geo = new THREE.BoxGeometry(sx * 0.9, 0.8, sz * 0.7);
                const mat = new THREE.MeshStandardMaterial({ color: 0x777777, metalness: 0.5, roughness: 0.4 });
                mesh = new THREE.Mesh(geo, mat);
                mesh.position.set(obj.pos_x + sx / 2, 0.4, obj.pos_y + sz / 2);
                mesh.castShadow = true;
                break;
            }
            case 'wall': {
                mesh = new THREE.Group();
                const _cw = this.props.layoutData?.canvas_width || 40;
                const _ch = this.props.layoutData?.canvas_height || 30;
                this._buildWall(mesh, sx, sz, obj.color || "#555555", obj, _cw, _ch);
                mesh.position.set(obj.pos_x + sx / 2, 0, obj.pos_y + sz / 2);
                break;
            }
            case 'room': {
                mesh = new THREE.Group();
                this._buildRoom(mesh, sx, sz, obj.color || "#7F8C8D", obj);
                mesh.position.set(obj.pos_x + sx / 2, 0, obj.pos_y + sz / 2);
                break;
            }
            default: {
                const geo = new THREE.BoxGeometry(sx * 0.8, 0.5, sz * 0.8);
                const mat = new THREE.MeshStandardMaterial({ color: c, roughness: 0.7 });
                mesh = new THREE.Mesh(geo, mat);
                mesh.position.set(obj.pos_x + sx / 2, 0.25, obj.pos_y + sz / 2);
                break;
            }
        }

        if (mesh) {
            this.scene.add(mesh);
            this.mapObjectMeshes.push(mesh);
        }
    }

    // ---- Helpers ----

    _addLabel(loc, position, height, isHighlighted) {
        const products = loc.product_summary || [];
        const hasProducts = products.length > 0;
        // Cap inline list to 3 products — rest visible via hover tooltip
        const MAX_INLINE = 3;
        const visibleProducts = products.slice(0, MAX_INLINE);
        const extraCount = products.length - MAX_INLINE;

        const canvas = document.createElement("canvas");
        const ctx = canvas.getContext("2d");

        canvas.width = 300;
        let baseHeight = 64;
        let productLineHeight = 28;
        let padBottom = 12;

        const rowCount = visibleProducts.length + (extraCount > 0 ? 1 : 0);
        canvas.height = baseHeight + (hasProducts ? rowCount * productLineHeight + padBottom : 0);

        ctx.fillStyle = isHighlighted ? "rgba(245, 158, 11, 0.9)" : "rgba(15, 23, 42, 0.88)";
        ctx.beginPath();
        ctx.roundRect(0, 0, canvas.width, canvas.height, 10);
        ctx.fill();

        ctx.fillStyle = "#FFFFFF";
        ctx.font = "bold 26px Inter, system-ui, sans-serif";
        ctx.textAlign = "center";

        let locNameY = hasProducts ? 34 : canvas.height / 2;
        ctx.textBaseline = "middle";

        let label = loc.name || "Location";
        if (label.length > 16) label = label.slice(0, 14) + "…";
        ctx.fillText(label, canvas.width / 2, locNameY);

        if (hasProducts) {
            ctx.strokeStyle = "rgba(255, 255, 255, 0.2)";
            ctx.lineWidth = 1.5;
            ctx.beginPath();
            ctx.moveTo(16, 54);
            ctx.lineTo(canvas.width - 16, 54);
            ctx.stroke();

            ctx.font = "16px Inter, sans-serif";
            ctx.textBaseline = "middle";

            let y = 54 + productLineHeight / 2;
            for (let i = 0; i < visibleProducts.length; i++) {
                const prod = visibleProducts[i];
                // zebra stripe
                if (i % 2 === 0) {
                    ctx.fillStyle = "rgba(255,255,255,0.05)";
                    ctx.fillRect(0, y - productLineHeight / 2, canvas.width, productLineHeight);
                }
                let prodName = prod.name || prod.product_name || '';
                if (prodName.length > 18) prodName = prodName.slice(0, 16) + "…";
                ctx.fillStyle = "#cbd5e1";
                ctx.textAlign = "left";
                ctx.fillText(prodName, 16, y);
                ctx.fillStyle = "#a5b4fc";
                ctx.textAlign = "right";
                ctx.fillText(`${prod.qty}${prod.uom ? ' ' + prod.uom : ''}`, canvas.width - 16, y);
                y += productLineHeight;
            }

            if (extraCount > 0) {
                ctx.fillStyle = "rgba(255,255,255,0.4)";
                ctx.font = "italic 14px Inter, sans-serif";
                ctx.textAlign = "center";
                ctx.fillText(`+${extraCount} more — hover to see all`, canvas.width / 2, y);
            }
        } else if (isHighlighted) {
            const result = this.props.productSearchResults.find(r => r.location_id === loc.id);
            if (result) {
                ctx.font = "bold 18px Inter, sans-serif";
                ctx.textAlign = "center";
                ctx.fillText(`${result.qty} ${result.uom || ''}`, canvas.width / 2, 48);
            }
        }

        const texture = new THREE.CanvasTexture(canvas);
        const spriteMat = new THREE.SpriteMaterial({ map: texture, transparent: true });
        const sprite = new THREE.Sprite(spriteMat);

        const spriteW = 2.8;
        const spriteH = spriteW * (canvas.height / canvas.width);
        const yOffset = height + 0.5 + (spriteH / 2);

        sprite.position.set(position.x, yOffset, position.z);
        sprite.scale.set(spriteW, spriteH, 1);
        sprite.userData.isLabel = true;
        this.scene.add(sprite);
        this.labelSprites.push(sprite);
    }

    // ========================================================================
    // 3D Product Hover Tooltip
    // ========================================================================

    _show3DProductTooltip(loc, screenX, screenY) {
        const summary = loc.product_summary || [];
        if (summary.length === 0) return;
        if (this._3dTooltipLocId === loc.id && this._3dTooltipEl) {
            this._reposition3DTooltip(screenX, screenY);
            return;
        }
        this._hide3DProductTooltip();
        this._3dTooltipLocId = loc.id;

        const el = document.createElement('div');
        el.className = 'o_wh3d_product_tooltip';
        el.style.cssText = [
            'position:fixed', 'z-index:9999',
            'background:linear-gradient(135deg,#1e293b,#0f172a)',
            'color:#f1f5f9', 'border-radius:12px',
            'box-shadow:0 8px 32px rgba(0,0,0,0.6)',
            'min-width:220px', 'max-width:320px',
            'font-family:Inter,system-ui,sans-serif', 'font-size:12px',
            'border:1px solid rgba(255,255,255,0.1)', 'overflow:hidden',
            'transition:opacity 0.15s ease', 'opacity:0', 'pointer-events:auto',
        ].join(';');

        const header = document.createElement('div');
        header.style.cssText = 'padding:10px 14px 8px;border-bottom:1px solid rgba(255,255,255,0.1);background:rgba(255,255,255,0.05);';
        header.innerHTML = `<div style="display:flex;align-items:center;gap:6px;">
            <span style="font-size:15px;">📦</span>
            <div>
                <div style="font-weight:700;font-size:12px;color:#f8fafc;">${loc.name || 'Location'}</div>
                <div style="font-size:10px;color:#94a3b8;margin-top:1px;">${summary.length} product${summary.length !== 1 ? 's' : ''} stored</div>
            </div></div>`;
        el.appendChild(header);

        const body = document.createElement('div');
        body.style.cssText = 'max-height:200px;overflow-y:auto;padding:6px 0;scrollbar-width:thin;scrollbar-color:#334155 transparent;';

        const style = document.createElement('style');
        style.textContent = `.o_wh3d_product_tooltip .body-scroll::-webkit-scrollbar{width:4px;}.o_wh3d_product_tooltip .body-scroll::-webkit-scrollbar-thumb{background:#334155;border-radius:2px;}`;
        document.head.appendChild(style);
        this._3dTooltipStyle = style;
        body.classList.add('body-scroll');

        const totalQty = summary.reduce((s, p) => s + (parseFloat(p.qty) || 0), 0);
        summary.forEach((p, idx) => {
            const row = document.createElement('div');
            row.style.cssText = ['display:flex', 'align-items:center',
                'justify-content:space-between', 'padding:5px 14px',
                idx % 2 === 0 ? 'background:rgba(255,255,255,0.03)' : '',
                'gap:8px'].join(';');
            const name = document.createElement('span');
            name.style.cssText = 'flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;color:#cbd5e1;font-size:11px;';
            name.textContent = p.product_name || p.name || 'Unknown';
            name.title = p.product_name || p.name || '';
            const badge = document.createElement('span');
            badge.style.cssText = 'background:rgba(99,102,241,0.3);color:#a5b4fc;border-radius:20px;padding:1px 8px;font-size:10px;font-weight:700;white-space:nowrap;border:1px solid rgba(99,102,241,0.4);';
            badge.textContent = `${p.qty}${p.uom ? ' ' + p.uom : ''}`;
            row.appendChild(name); row.appendChild(badge); body.appendChild(row);
        });
        el.appendChild(body);

        if (summary.length > 1) {
            const footer = document.createElement('div');
            footer.style.cssText = 'padding:6px 14px;border-top:1px solid rgba(255,255,255,0.08);display:flex;justify-content:space-between;align-items:center;';
            footer.innerHTML = `<span style="color:#64748b;font-size:10px;font-style:italic;">Scroll to see all</span><span style="color:#38bdf8;font-size:10px;font-weight:700;">Total: ${totalQty.toFixed(2).replace(/\.?0+$/, '')}</span>`;
            el.appendChild(footer);
        }

        document.body.appendChild(el);
        this._3dTooltipEl = el;
        this._reposition3DTooltip(screenX, screenY);

        el.addEventListener('mouseenter', () => {
            if (this._3dTooltipHideTimer) { clearTimeout(this._3dTooltipHideTimer); this._3dTooltipHideTimer = null; }
        });
        el.addEventListener('mouseleave', () => {
            this._3dTooltipHideTimer = setTimeout(() => this._hide3DProductTooltip(), 150);
        });

        requestAnimationFrame(() => { el.style.opacity = '1'; });
    }

    _reposition3DTooltip(screenX, screenY) {
        if (!this._3dTooltipEl) return;
        const el = this._3dTooltipEl;
        const margin = 14;
        const vw = window.innerWidth, vh = window.innerHeight;
        const elW = el.offsetWidth || 240, elH = el.offsetHeight || 200;
        let left = screenX + margin, top = screenY - elH / 2;
        if (left + elW > vw - 10) left = screenX - elW - margin;
        if (top < 10) top = 10;
        if (top + elH > vh - 10) top = vh - elH - 10;
        el.style.left = `${left}px`;
        el.style.top = `${top}px`;
    }

    _hide3DProductTooltip() {
        if (this._3dTooltipHideTimer) { clearTimeout(this._3dTooltipHideTimer); this._3dTooltipHideTimer = null; }
        if (this._3dTooltipEl) { this._3dTooltipEl.remove(); this._3dTooltipEl = null; }
        if (this._3dTooltipStyle) { this._3dTooltipStyle.remove(); this._3dTooltipStyle = null; }
        this._3dTooltipLocId = null;
    }

    _addHighlightRing(position, sx, sz) {
        const geo = new THREE.RingGeometry(Math.max(sx, sz) * 0.6, Math.max(sx, sz) * 0.7, 32);
        const mat = new THREE.MeshBasicMaterial({
            color: 0xF59E0B,
            transparent: true,
            opacity: 0.6,
            side: THREE.DoubleSide,
        });
        const ring = new THREE.Mesh(geo, mat);
        ring.rotation.x = -Math.PI / 2;
        ring.position.set(position.x, 0.1, position.z);
        this.scene.add(ring);
        this.detailMeshes.push(ring);
    }

    _getHeatmapHex(fillPct) {
        // Smooth HSL interpolation: green (120°) → red (0°)
        const clamped = Math.max(0, Math.min(fillPct, 100));
        const hue = 120 - (clamped / 100) * 120;
        // Convert HSL to hex
        const s = 0.8, l = 0.45;
        const c = (1 - Math.abs(2 * l - 1)) * s;
        const x = c * (1 - Math.abs(((hue / 60) % 2) - 1));
        const m = l - c / 2;
        let r, g, b;
        if (hue < 60) { r = c; g = x; b = 0; }
        else if (hue < 120) { r = x; g = c; b = 0; }
        else { r = 0; g = c; b = x; }
        const toHex = (v) => Math.round((v + m) * 255).toString(16).padStart(2, '0');
        return `#${toHex(r)}${toHex(g)}${toHex(b)}`;
    }

    /**
     * Returns a THREE.Color for a child layer.
     * When heatmap is enabled and data exists for the child, uses the child's
     * own fill percentage color. Otherwise returns a gradient shade of the
     * parent color based on layer index.
     */
    _getChildLayerColor(child, parentColor, layerIndex, totalLayers) {
        if (this.props.heatmapEnabled && child && child.id) {
            const hd = this.props.heatmapData[child.id];
            if (hd) {
                return new THREE.Color(this._getHeatmapHex(hd.fill_pct));
            }
        }
        // Gradient shade: bottom layers darker, top lighter
        const shade = 0.65 + (layerIndex / Math.max(totalLayers, 1)) * 0.3;
        return parentColor.clone().multiplyScalar(shade);
    }

    /**
     * Adds a small text label sprite on a rack/shelf layer surface.
     * Positioned at the front face of the layer board.
     */
    _addLayerLabel(group, text, sx, sz, yPos) {
        let label = text || "";
        if (label.length > 18) label = label.slice(0, 16) + "…";

        // Measure text first to size the canvas to fit
        const tmpCanvas = document.createElement("canvas");
        const tmpCtx = tmpCanvas.getContext("2d");
        tmpCtx.font = "bold 32px Inter, system-ui, sans-serif";
        const textW = tmpCtx.measureText(label).width;

        const pad = 24;
        const canvas = document.createElement("canvas");
        const ctx = canvas.getContext("2d");
        canvas.width = Math.ceil(textW + pad * 2);
        canvas.height = 48;

        ctx.fillStyle = "rgba(0, 0, 0, 0.6)";
        ctx.beginPath();
        ctx.roundRect(2, 2, canvas.width - 4, 44, 6);
        ctx.fill();

        ctx.fillStyle = "#FFFFFF";
        ctx.font = "bold 32px Inter, system-ui, sans-serif";
        ctx.textAlign = "center";
        ctx.textBaseline = "middle";
        ctx.fillText(label, canvas.width / 2, 24);

        const texture = new THREE.CanvasTexture(canvas);
        texture.minFilter = THREE.LinearFilter;
        const spriteMat = new THREE.SpriteMaterial({ map: texture, transparent: true });
        const sprite = new THREE.Sprite(spriteMat);
        sprite.position.set(0, yPos, sz * 0.48);
        // Width from aspect ratio, height fixed at 0.5
        const spriteW = 0.5 * (canvas.width / canvas.height);
        sprite.scale.set(spriteW, 0.5, 1);
        group.add(sprite);
        this.labelSprites.push(sprite);
    }

    // ========================================================================
    // Interaction
    // ========================================================================

    _onClick(event) {
        if (this._ctrl.isOrbiting || this._ctrl.isPanning) return;

        const rect = this.renderer.domElement.getBoundingClientRect();
        this.mouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
        this.mouse.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;

        this.raycaster.setFromCamera(this.mouse, this.camera);

        // Collect all child meshes from location groups
        const allMeshes = [];
        for (const [, group] of this.locationMeshes) {
            group.traverse((child) => {
                if (child.isMesh) allMeshes.push(child);
            });
        }

        const intersects = this.raycaster.intersectObjects(allMeshes);
        if (intersects.length > 0) {
            // Walk up to find the group with locationId
            let obj = intersects[0].object;
            while (obj && !obj.userData.locationId) obj = obj.parent;
            if (obj?.userData.locationId) {
                this.props.onLocationSelected(obj.userData.locationId);
                this._highlightSelected(obj.userData.locationId);
                return;
            }
        }
        this.props.onLocationSelected(null);
        this._clearHighlight();
    }

    _onHover(event) {
        if (this._ctrl.isOrbiting || this._ctrl.isPanning) return;

        const rect = this.renderer.domElement.getBoundingClientRect();
        this.mouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
        this.mouse.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;

        this.raycaster.setFromCamera(this.mouse, this.camera);
        const allMeshes = [];
        for (const [, group] of this.locationMeshes) {
            group.traverse((child) => { if (child.isMesh) allMeshes.push(child); });
        }
        const intersects = this.raycaster.intersectObjects(allMeshes);
        this.renderer.domElement.style.cursor = intersects.length > 0 ? "pointer" : "default";

        if (intersects.length > 0) {
            let obj = intersects[0].object;
            while (obj && !obj.userData.locationId) obj = obj.parent;
            if (obj?.userData.locationId) {
                const locId = obj.userData.locationId;
                if (this._3dTooltipLocId !== locId) {
                    if (this._3dTooltipHideTimer) clearTimeout(this._3dTooltipHideTimer);
                    const loc = this.props.locations.find(l => l.id === locId);
                    if (loc && (loc.product_summary || []).length > 0) {
                        this._3dTooltipHideTimer = setTimeout(() => {
                            this._show3DProductTooltip(loc, event.clientX, event.clientY);
                        }, 280);
                    }
                } else {
                    this._reposition3DTooltip(event.clientX, event.clientY);
                }
                return;
            }
        }

        // Mouse not over any location
        if (this._3dTooltipLocId !== null) {
            if (this._3dTooltipHideTimer) clearTimeout(this._3dTooltipHideTimer);
            this._3dTooltipHideTimer = setTimeout(() => this._hide3DProductTooltip(), 150);
        }
    }

    _highlightSelected(locationId) {
        for (const [id, group] of this.locationMeshes) {
            group.traverse((child) => {
                if (child.isMesh && child.material?.emissive) {
                    child.material.emissive.setHex(id === locationId ? 0x3B82F6 : 0x000000);
                    child.material.emissiveIntensity = id === locationId ? 0.35 : 0;
                }
            });
        }
    }

    _clearHighlight() {
        for (const [, group] of this.locationMeshes) {
            group.traverse((child) => {
                if (child.isMesh && child.material?.emissive) {
                    child.material.emissive.setHex(0x000000);
                    child.material.emissiveIntensity = 0;
                }
            });
        }
    }

    // ========================================================================
    // Animation Loop
    // ========================================================================

    _animate() {
        this.animationId = requestAnimationFrame(() => this._animate());

        if (this._pendingRebuild) {
            this._pendingRebuild = false;
            this._buildWarehouse();
        }

        // Pulse highlight rings
        this._highlightTime += 0.03;
        for (const m of this.detailMeshes) {
            if (m.geometry?.type === "RingGeometry" && m.material) {
                m.material.opacity = 0.3 + Math.sin(this._highlightTime * 3) * 0.3;
            }
        }

        if (this.renderer && this.scene && this.camera) {
            this.renderer.render(this.scene, this.camera);
        }
    }

    _onResize() {
        const container = this.containerRef.el;
        if (!container || !this.camera || !this.renderer) return;
        const w = container.clientWidth;
        const h = container.clientHeight;
        this.camera.aspect = w / h;
        this.camera.updateProjectionMatrix();
        this.renderer.setSize(w, h);
    }

    _cleanup() {
        if (this.animationId) cancelAnimationFrame(this.animationId);
        if (this.renderer) {
            this.renderer.dispose();
            this.renderer.domElement.remove();
        }
        for (const [, group] of this.locationMeshes) {
            group.traverse((child) => {
                if (child.isMesh) {
                    child.geometry?.dispose();
                    if (Array.isArray(child.material)) child.material.forEach(m => m.dispose());
                    else child.material?.dispose();
                }
            });
        }
        this.locationMeshes.clear();
        for (const m of this.detailMeshes) {
            m.geometry?.dispose();
            m.material?.dispose();
        }
        for (const s of this.labelSprites) {
            s.material?.map?.dispose();
            s.material?.dispose();
        }
        for (const m of this.mapObjectMeshes) {
            m.geometry?.dispose();
            m.material?.dispose();
        }
        if (this._boundResize) window.removeEventListener("resize", this._boundResize);
        // Cleanup other-floor meshes
        for (const m of this.otherFloorMeshes) {
            m.traverse?.((child) => {
                if (child.isMesh) {
                    child.geometry?.dispose();
                    if (Array.isArray(child.material)) child.material.forEach(mt => mt.dispose());
                    else child.material?.dispose();
                }
            });
        }
        this._removeHeatmapLegend();
    }

    // ========================================================================
    // Heatmap Legend (HTML overlay on 3D view)
    // ========================================================================

    _updateHeatmapLegend() {
        if (this.props.heatmapEnabled) {
            if (!this._heatmapLegendEl) {
                const el = document.createElement('div');
                el.className = 'o_heatmap_legend';
                el.innerHTML = `
                    <div class="o_heatmap_legend_title">Stock Density</div>
                    <div class="o_heatmap_legend_bar"></div>
                    <div class="o_heatmap_legend_labels">
                        <span>0% Empty</span>
                        <span>50%</span>
                        <span>100% Full</span>
                    </div>
                `;
                const container = this.containerRef.el;
                if (container) {
                    container.parentElement.appendChild(el);
                }
                this._heatmapLegendEl = el;
            }
        } else {
            this._removeHeatmapLegend();
        }
    }

    _removeHeatmapLegend() {
        if (this._heatmapLegendEl) {
            this._heatmapLegendEl.remove();
            this._heatmapLegendEl = null;
        }
    }
}

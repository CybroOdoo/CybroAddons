/** @odoo-module **/

import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { onWillStart, onMounted, useState, useRef, Component, onWillUnmount } from "@odoo/owl";
import { loadJS } from "@web/core/assets";
import { rpc } from "@web/core/network/rpc";
import { Dialog } from "@web/core/dialog/dialog";

export class LocationDialog extends Component {
    static template = "stock_3d_view.LocationDialog";
    static components = { Dialog };
    static props = {
        title: String,
        data: Object,
        close: Function,
    };
}
const actionRegistry = registry.category("actions");
class Form3DView extends Component {
    setup() {
        this.actionService = useService("action");
        this.rootRef = useRef("root");
        this.canvasRef = useRef("canvasContainer");
        this.animationFrameId = null;
        this.dialogService = useService("dialog");
        this.companyService = useService("company");
        this.onClickCloseBound = () => {
            this.onDialogClosed();
        };
        this.onPointerMoveBound = this.onPointerMove.bind(this);
        this.state = useState({
            wh_data: "",
            data: "",
            loc_quant: "",
            controls: "",
            renderer: null,
            clock: null,
            scene: null,
            camera: null,
            pointer: new THREE.Vector3(),
            raycaster: new THREE.Raycaster(),
            group: new THREE.Group(),
            selectedObject: null,
            dialogs: null,
            wh_id: "",
            location_id: this.props.action.context.default_location_id || localStorage.getItem("location_id"),
            breadcrumbs: this.env.config.breadcrumbs,
            isDialogOpen: false,
        });
        onWillStart(async () => {
            this.props.title = '3D Form View';
            this.three = await loadJS('https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js');
            this.OrbitControls = await loadJS('https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.min.js');

        });
        onMounted(async () => {
            await this.Open3DView();
        });
        onWillUnmount(() => {
            if (this.state.renderer && this.state.renderer.domElement) {
                this.state.renderer.domElement.removeEventListener('dblclick', this.onPointerMoveBound);
            }
            if (this.animationFrameId) {
                cancelAnimationFrame(this.animationFrameId);
            }
        });
    }
    async Open3DView() {
        if (this.props.action.context.default_location_id != null) {
            localStorage.setItem("location_id", this.props.action.context.default_location_id);
        }
        const container = this.canvasRef.el;
        if (!container) return;
        container.style.backgroundColor = 'white';
        // Add color legend box
        const colorDiv = this.createLegendBox();
        const stockData = await rpc('/3Dstock/data/standalone', {
            company_id: this.companyService.currentCompany.id,
            loc_id: localStorage.getItem("location_id"),
        });
        this.state.data = stockData;
        // Scene Setup
        const scene = new THREE.Scene();
        scene.background = new THREE.Color(0xffffff);
        this.state.scene = scene;
        const clock = new THREE.Clock();
        this.state.clock = clock;
        const rect = container.getBoundingClientRect();
        const camera = new THREE.PerspectiveCamera(60, rect.width / rect.height, 0.5, 6000);
        camera.position.set(0, 200, 300);
        this.state.camera = camera;
        const renderer = new THREE.WebGLRenderer({ antialias: true });
        renderer.setSize(rect.width, rect.height);
        renderer.setPixelRatio(window.devicePixelRatio);
        this.state.renderer = renderer;
        if (container) {
            container.append(renderer.domElement);
            container.append(colorDiv);
        }
        this.state.controls = new THREE.OrbitControls(camera, renderer.domElement);
        renderer.domElement.addEventListener('dblclick', this.onPointerMoveBound);
        const baseGeometry = new THREE.BoxGeometry(800, 0, 800);
        const baseMaterial = new THREE.MeshBasicMaterial({ color: 0xD3D3D3 });
        const baseCube = new THREE.Mesh(baseGeometry, baseMaterial);
        scene.add(baseCube);
        const group = new THREE.Group();
        this.state.group = group;
        for (let [key, value] of Object.entries(stockData)) {
            if ((value[0] > 0) || (value[1] > 0) || (value[2] > 0) || (value[3] > 0) || (value[4] > 0) || (value[5] > 0)) {
                const geometry = new THREE.BoxGeometry(value[3], value[5], value[4]);
                geometry.translate(0, value[5] / 2, 0);
                const edges = new THREE.EdgesGeometry(geometry);
                await rpc('/3Dstock/data/quantity', { 'loc_code': key }).then((quant_data) => {
                    this.state.loc_quant = quant_data;
                });
                let color = 0x8c8c8c;
                let opacity = 0.5;
                if (localStorage.getItem("location_id") == value[6]) {
                    const [qty, capacity] = this.state.loc_quant;
                    if (qty > 0) {
                        if (capacity > 100) {
                            color = 0xcc0000;
                        } else if (capacity > 50) {
                            color = 0xe6b800;
                        } else {
                            color = 0x00802b;
                        }
                    } else {
                        color = (capacity === -1) ? 0x00802b : 0x0066ff;
                    }
                    opacity = 0.8;
                }
                const material = new THREE.MeshBasicMaterial({ color, transparent: true, opacity });
                const mesh = new THREE.Mesh(geometry, material);
                mesh.position.set(value[0], value[1], value[2]);
                const line = new THREE.LineSegments(edges, new THREE.LineBasicMaterial({ color: 0x404040 }));
                line.position.set(value[0], value[1], value[2]);
                const loader = new THREE.FontLoader();
                loader.load('https://threejs.org/examples/fonts/droid/droid_sans_bold.typeface.json', (font) => {
                    const size = Math.min(value[3], value[4]) / 3;
                    const shapes = font.generateShapes(key, size);
                    const textGeo = new THREE.ShapeGeometry(shapes);
                    const textMat = new THREE.MeshBasicMaterial({ color: 0x000000, side: THREE.DoubleSide });
                    const textMesh = new THREE.Mesh(textGeo, textMat);
                    textGeo.translate(0, value[5] / 2, 0);
                    textMesh.position.set(value[0], value[1], value[2]);
                    this.state.scene.add(textMesh);
                });
                mesh.name = key;
                mesh.userData = { color, loc_id: value[6] };
                this.state.scene.add(mesh, line);
                group.add(mesh);
            }
        }
        scene.add(group);
        this.animate();
    }
    async animate() {
        if (!this.canvasRef || !this.canvasRef.el) {
            return;
        }
        try {
            this.animationFrameId = requestAnimationFrame(this.animate.bind(this));
            const delta = this.state.clock.getDelta();
            this.state.renderer.render(this.state.scene, this.state.camera);
            const canvas = this.state.renderer.domElement;
            const colorBox = this.canvasRef.el.querySelector(".rectangle");
            if (canvas && colorBox) {
                colorBox.style.display = "block";
            } else if (colorBox) {
                colorBox.style.display = "none";
            }
        } catch (error) {
            console.error("3D View animation error:", error);
        }
    }
    createLegendBox() {
        const colorDiv = document.createElement("div");
        colorDiv.classList.add("rectangle");
        const colors = [
            ["square1", "Overload"],
            ["square2", "Almost Full"],
            ["square3", "Free Space Available"],
            ["square4blue", "No Product/Load"],
        ];
        for (const [cls, label] of colors) {
            const box = document.createElement("div");
            box.classList.add(cls);
            const text = document.createElement("div");
            text.classList.add(cls.replace("square", "squareText").replace("blue", ""));
            text.innerHTML = label;
            colorDiv.append(box, text);
        }
        return colorDiv;
    }
    async onPointerMove(event) {
        const canvas = this.state.renderer?.domElement;
        if (!canvas || this.state.dialogs || this.state.isDialogOpen) return;
        if (this.state.selectedObject) {
            this.state.selectedObject.material.color.set(this.state.selectedObject.userData.color);
            this.state.selectedObject = null;
        }
        const rect = canvas.getBoundingClientRect();
        this.state.pointer.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
        this.state.pointer.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;
        this.state.raycaster.setFromCamera(this.state.pointer, this.state.camera);
        const intersects = this.state.raycaster.intersectObject(this.state.group, true);
        const selectableIntersects = intersects.filter((intersect) => {
            const params = intersect?.object?.geometry?.parameters;
            return params && Number.isFinite(params.width) && Number.isFinite(params.height) && Number.isFinite(params.depth);
        });
        if (!selectableIntersects.length) return;
        // Pick the smallest box-like object to handle nested locations correctly.
        selectableIntersects.sort((a, b) => {
            const paramsA = a.object.geometry.parameters;
            const paramsB = b.object.geometry.parameters;
            const volA = paramsA.width * paramsA.height * paramsA.depth;
            const volB = paramsB.width * paramsB.height * paramsB.depth;
            return volA - volB;
        });
        const intersect = selectableIntersects[0];
        const res = await rpc('/3Dstock/data/product', { loc_code: intersect.object.name });
        this.state.selectedObject = intersect.object;
        this.state.selectedObject.material.color.set(0x00ffcc);
        this.state.isDialogOpen = true;
        this.state.dialogs = this.dialogService.add(
            LocationDialog,
            {
                title: `Location: ${intersect.object.name}`,
                data: res,
                close: this.onClickCloseBound,
            },
            {
                onClose: this.onClickCloseBound,
            }
        );
    }
    onDialogClosed() {
        this.state.isDialogOpen = false;
        this.state.dialogs = null;
        if (this.state.selectedObject) {
            this.state.selectedObject.material.color.set(this.state.selectedObject.userData.color);
            this.state.selectedObject = null;
        }
    }
    onBreadcrumbClick(ev) {
        ev.preventDefault();
        const jsId = ev.currentTarget.getAttribute("jsId");
        if (jsId) {
            this.actionService.restore(jsId);
        }
    }
}
Form3DView.template = "Location3DFormView";
actionRegistry.add("stock_3d_view.open_form_3d_view", Form3DView);

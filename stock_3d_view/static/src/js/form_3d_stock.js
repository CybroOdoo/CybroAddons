/** @odoo-module **/

import { registry } from "@web/core/registry";
import { Dialog } from "@web/core/dialog/dialog";
const actionRegistry = registry.category("actions");
import { useService } from "@web/core/utils/hooks";
import { Component, onWillStart, onMounted, onWillUnmount, proxy, signal, useProps } from "@odoo/owl";
import { standardActionServiceProps } from "@web/webclient/actions/action_plugin";
import { loadJS } from "@web/core/assets";
import { rpc } from "@web/core/network/rpc";
import { Breadcrumbs } from "@web/search/breadcrumbs/breadcrumbs";

export class StockLocationDialog extends Component {
    static template = "stock_3d_view.StockLocationDialog";
    static components = { Dialog };
    props = useProps({
        title: { type: String, optional: true },
        data: { type: Object, optional: true },
        close: { type: Function, optional: true },
    });
}

class Form3DView extends Component {
    props = useProps(standardActionServiceProps);

    setup() {
        this.dialogService = useService("dialog");
        this.canvasContainer = signal.ref();
        this.contentDiv = signal.ref();

        this.state = proxy({
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
            location_id: this.props.action?.context?.default_location_id || localStorage.getItem("location_id"),
            breadcrumbs: this.env.config?.breadcrumbs || [],
            isDialogOpen: false,
        });

        this._onPointerDblClick = this.onBoxClick.bind(this);
        this._downPos = { x: 0, y: 0 };
        this._onPointerDown = (e) => {
            this._downPos = { x: e.clientX, y: e.clientY };
        };
        this._onPointerUp = (e) => {
            const dist = Math.hypot(e.clientX - this._downPos.x, e.clientY - this._downPos.y);
            if (dist < 6) {
                this.onBoxClick(e);
            }
        };

        onWillUnmount(() => {
            window.removeEventListener('dblclick', this._onPointerDblClick);
            const canvas = this.state.renderer?.domElement;
            if (canvas) {
                canvas.removeEventListener('pointerdown', this._onPointerDown);
                canvas.removeEventListener('pointerup', this._onPointerUp);
            }
        });

        onWillStart(async () => {
            this.three = await loadJS('https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js');
            this.OrbitControls = await loadJS('https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.min.js');
        });

        onMounted(async () => {
            await this.Open3DView();
        });
    }


    async Open3DView() {
         const container = this.contentDiv?.el || document.getElementsByClassName("o_content")[0];
         if (container) {
             container.style.backgroundColor = 'white';
         }

        if (!container) return;
        if (this.props.action?.context?.default_location_id != null) {
            localStorage.setItem("location_id", this.props.action.context.default_location_id);
            localStorage.setItem("company_id", this.props.action.context.company_id);
        }

        // Add color legend box
        const colorDiv = this.createLegendBox();

        const stockData = await rpc('/3Dstock/data/standalone', {
            company_id: localStorage.getItem("company_id"),
            loc_id: localStorage.getItem("location_id"),
        });
        this.state.data = stockData;

        // Scene Setup
        const scene = new THREE.Scene();
        scene.background = new THREE.Color(0xffffff);
        this.state.scene = scene;

        const clock = new THREE.Clock();
        this.state.clock = clock;

        const camera = new THREE.PerspectiveCamera(60, window.innerWidth / window.innerHeight, 0.5, 6000);
        camera.position.set(0, 160, 260);
        this.state.camera = camera;

        const renderer = new THREE.WebGLRenderer({ antialias: true });
        renderer.setSize(window.innerWidth, window.innerHeight);
        renderer.setPixelRatio(window.devicePixelRatio);
        this.state.renderer = renderer;

        if (container){
            container.append(renderer.domElement);
            container.append(colorDiv);
        }

        renderer.domElement.addEventListener('pointerdown', this._onPointerDown);
        renderer.domElement.addEventListener('pointerup', this._onPointerUp);
        window.addEventListener('dblclick', this._onPointerDblClick);

        this.state.controls = new THREE.OrbitControls(camera, renderer.domElement);
        this.state.controls.target.set(0, 35, 0);
        this.state.controls.update();

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

                await rpc('/3Dstock/data/quantity', { 'loc_code': key, 'loc_id': value[6] }).then((quant_data) => {
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
                    const textLen = key.length || 6;
                    const maxTextWidth = value[3] * 0.72;
                    const maxTextHeight = value[5] * 0.40;
                    const size = Math.max(Math.min(maxTextWidth / (textLen * 0.65), maxTextHeight), 1.2);

                    const shapes = font.generateShapes(key, size);
                    const textGeo = new THREE.ShapeGeometry(shapes);
                    textGeo.computeBoundingBox();
                    textGeo.center();

                    const isSelected = localStorage.getItem("location_id") == value[6];
                    const textMat = new THREE.MeshBasicMaterial({
                        color: isSelected ? 0xffffff : 0x222222,
                        side: THREE.DoubleSide
                    });
                    const textMesh = new THREE.Mesh(textGeo, textMat);
                    textMesh.position.set(value[0], value[1] + value[5] / 2, value[2] + value[4] / 2 + 0.2);
                    this.state.scene.add(textMesh);
                });

                mesh.name = key;
                mesh.userData = { color, opacity, loc_id: value[6] };
                this.state.scene.add(mesh, line);
                group.add(mesh);
            }
        }
        scene.add(group);
        this.animate();
    }

    async onBoxClick(event) {
        const canvas = this.state.renderer?.domElement;
        if (!canvas || this.state.dialogs || this.state.isDialogOpen) return;

        if (this.state.selectedObject) {
            this.state.selectedObject.material.color.set(this.state.selectedObject.userData.color);
            if (this.state.selectedObject.userData.opacity !== undefined) {
                this.state.selectedObject.material.opacity = this.state.selectedObject.userData.opacity;
            }
            this.state.selectedObject = null;
        }

        const rect = canvas.getBoundingClientRect();
        this.state.pointer.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
        this.state.pointer.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;
        this.state.raycaster.setFromCamera(this.state.pointer, this.state.camera);

        const intersects = this.state.raycaster.intersectObjects(this.state.group.children, true);
        if (!intersects.length) return;

        const intersect = intersects.find(res => res?.object && res.object.name);
        if (!intersect || !intersect.object?.name) return;

        const res = await rpc('/3Dstock/data/product', {
            loc_code: intersect.object.name,
            loc_id: intersect.object.userData?.loc_id
        });
        this.state.selectedObject = intersect.object;
        this.state.selectedObject.material.color.set(0x00ffcc);
        this.state.selectedObject.material.opacity = 0.95;
        this.state.isDialogOpen = true;

        this.state.dialogs = this.dialogService.add(StockLocationDialog, {
            title: `Location: ${intersect.object.name}`,
            data: res
        }, {
            onClose: () => this.onClickClose()
        });
    }

    onClickClose() {
        if (this.state.selectedObject) {
            this.state.selectedObject.material.color.set(this.state.selectedObject.userData.color);
            if (this.state.selectedObject.userData.opacity !== undefined) {
                this.state.selectedObject.material.opacity = this.state.selectedObject.userData.opacity;
            }
            this.state.selectedObject = null;
        }
        this.state.dialogs = null;
        this.state.isDialogOpen = false;
    }

    async animate() {
        try {
            requestAnimationFrame(this.animate.bind(this));
            if (this.state.controls) {
                this.state.controls.update();
            }
            const delta = this.state.clock.getDelta();
            this.state.renderer.render(this.state.scene, this.state.camera);

            const canvas = this.state.renderer.domElement;
            const canvasEl = this.canvasContainer?.el;
            const colorBox = canvasEl?.querySelector(".rectangle") || document.querySelector(".rectangle");
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
            ["square_blue4", "No Product/Load"],
        ];

        for (const [cls, label] of colors) {
            const box = document.createElement("div");
            box.classList.add(cls);
            const text = document.createElement("div");
            text.classList.add("squareText" + cls.slice(-1));
            text.innerHTML = label;
            colorDiv.append(box, text);
        }

        return colorDiv;
    }

}
Form3DView.template = "Location3DFormView";
Form3DView.components = { Breadcrumbs };
actionRegistry.add("stock_3d_view.open_form_3d_view", Form3DView);


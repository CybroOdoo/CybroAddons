/** @odoo-module **/

import { registry } from "@web/core/registry";
import { Dialog } from "@web/core/dialog/dialog";
const actionRegistry = registry.category("actions");
import { useService } from "@web/core/utils/hooks";
import { Component, onWillStart, onMounted, useState, useRef } from "@odoo/owl";
import { FormController } from "@web/views/form/form_controller";
import { loadJS } from "@web/core/assets";
import { rpc } from "@web/core/network/rpc";
import { Breadcrumbs } from "@web/search/breadcrumbs/breadcrumbs";

class Form3DView extends FormController {
    setup() {
        this.rootRef = useRef("root");
        this.canvasRef = useRef("canvasContainer");

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
    }


    async Open3DView() {
         const container = document.getElementsByClassName("o_content")[0];
         container.style.backgroundColor = 'white';

        if (!container) return;
        if (this.props.action.context.default_location_id != null) {
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
        camera.position.set(0, 200, 300);
        this.state.camera = camera;

        const renderer = new THREE.WebGLRenderer({ antialias: true });
        renderer.setSize(window.innerWidth, window.innerHeight);
        renderer.setPixelRatio(window.devicePixelRatio);
        this.state.renderer = renderer;

        if (container){
            container.append(renderer.domElement);
            container.append(colorDiv);
        }

        this.state.controls = new THREE.OrbitControls(camera, renderer.domElement);

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
        try {
            requestAnimationFrame(this.animate.bind(this));
            const delta = this.state.clock.getDelta();
            this.state.renderer.render(this.state.scene, this.state.camera);

            const canvas = this.state.renderer.domElement;
            const colorBox = this.canvasRef?.el?.querySelector(".rectangle");
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
Form3DView.props = {
    action: { type: Object, optional: true },
    actionId: { type: Number, optional: true },
    "*": true, // Allow any additional props
};
Form3DView.template = "Location3DFormView";
Form3DView.components = {...Form3DView.components,Breadcrumbs}
actionRegistry.add("stock_3d_view.open_form_3d_view", Form3DView);


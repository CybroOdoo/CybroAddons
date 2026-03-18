/** @odoo-module **/

import { registry } from '@web/core/registry';
import { listView } from '@web/views/list/list_view';
import { ListController } from '@web/views/list/list_controller';
import { onMounted, useState, onWillUnmount, useRef, onWillStart, Component } from "@odoo/owl";
import { loadJS } from "@web/core/assets";
import { rpc } from "@web/core/network/rpc";
import { useService } from "@web/core/utils/hooks";
import { renderToFragment } from "@web/core/utils/render";
import { user } from "@web/core/user";
import { Dialog } from "@web/core/dialog/dialog";

export class StockLocationDialog extends Component {
    static template = "stock_3d_view.StockLocationDialog";
    static components = { Dialog };
    static props = {
        title: { type: String, optional: true },
        data: { type: Object, optional: true },
        close: { type: Function, optional: true },
    };
}

class StockListController extends ListController {
    async setup() {
        super.setup();
        this.user = user
        this.company = user.activeCompany
        this.oContentRef = useRef("oContent");
        this.rootRef = useRef("root"); // Add a ref for the root element

        this.state = useState({
            wh_data: [],
            data: {},
            wh_id: null,
            dialogs: null,
            isRendering: false,
            isDialogOpen: false,
            selectedObject: null,
            renderer: null,
            camera: null,
            scene: null,
            group: null,
            controls: null,
            clock: null,
            pointer: new THREE.Vector3(),
            raycaster: new THREE.Raycaster(),
        });

        this.bus = this.env.services.bus_service;
        this.bus.addEventListener('dialog:close', this.onClickClose);

        onWillUnmount(() => {
            this.bus.removeEventListener('dialog:close', this.onClickClose);
            window.removeEventListener('dblclick', this.onPointerMove);
        });

        onMounted(async () => {
            window.addEventListener('dblclick', this.onPointerMove.bind(this));

        });

        onWillStart(async () => {
            this.three = await loadJS('https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js')
            this.OrbitControls = await loadJS('https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.min.js')
        });

    }

    async OnClickList3DvView(ev) {
        ev.preventDefault();
        if (this.state.isRendering) return;
        this.state.isRendering = true;

        const res = await rpc('/3Dstock/warehouse', {
            company_id: this.company.id,
        });

        this.state.wh_data = res;
        this.state.wh_id = res[0][0];

        await this._render3DView();
    }

    async _render3DView() {
        const o_content = this.rootRef.el?.querySelector('.o_content');
        if (!o_content) return;

        document.querySelector('.o_list_renderer')?.style.setProperty('display', 'none');

        const select = document.createElement("div");
        select.classList.add("select", "customselect");
        select.style.position = "relative";
        select.style.backgroundColor = "#fff";

        const selected = document.createElement("div");
        selected.classList.add("selected-display");
        selected.textContent = "Select Warehouse";
        select.appendChild(selected);

        const optionsContainer = document.createElement("div");
        optionsContainer.classList.add("options-container");
        optionsContainer.style.display = "none";
        optionsContainer.style.position = "absolute";
        optionsContainer.style.top = "100%";
        optionsContainer.style.left = "0";
        optionsContainer.style.right = "0";
        optionsContainer.style.zIndex = "999";
        optionsContainer.style.background = "#fff";
        optionsContainer.style.border = "1px solid #ccc";

        for (let i = 0; i < this.state.wh_data.length; i++) {
            const option = document.createElement("div");
            option.classList.add("option");

            const value = this.state.wh_data[i][0];
            const label = this.state.wh_data[i][1];

            option.setAttribute("data-value", value);
            option.textContent = label;

            if (String(this.state.wh_id) === String(value)) {
                option.classList.add("selected");
                selected.textContent = label;
            }

            option.addEventListener("click", async () => {
                // Prevent re-render if same warehouse is selected
                if (this.state.wh_id === value) {
                    optionsContainer.style.display = "none";
                    return;
                }

                this.state.wh_id = value;
                selected.textContent = label;

                // Clear previous selected styling
                optionsContainer.querySelectorAll('.option.selected').forEach(opt => opt.classList.remove('selected'));
                option.classList.add('selected');

                optionsContainer.style.display = "none";

                // Remove existing 3D elements
                const o_content = this.oContentRef.el || this.rootRef.el?.querySelector('.o_content');
                if (o_content) {
                    o_content.querySelectorAll(".custom-3d-element").forEach(el => el.remove());
                }

                this.state.isRendering = false;

                // Re-render view
                await this._render3DView();
            });

            optionsContainer.appendChild(option);
        }

        select.appendChild(optionsContainer);

        selected.addEventListener("click", () => {
            const isVisible = optionsContainer.style.display === "block";
            optionsContainer.style.display = isVisible ? "none" : "block";
        });

        document.body.appendChild(select);

        const closeDiv = document.createElement("div");
        closeDiv.classList.add("button", "closeBtn");
        closeDiv.innerHTML = "&times;";

        const colorDiv = document.createElement("div");
        colorDiv.classList.add("rectangle");

        const colors = [
            { class: 'square1', text: 'Overload' },
            { class: 'square2', text: 'Almost Full' },
            { class: 'square3', text: 'Free Space Available' },
            { class: 'square4', text: 'No Product/Load' }
        ];

        colors.forEach((c) => {
            let color = document.createElement("div");
            color.classList.add(c.class);
            colorDiv.appendChild(color);

            let colorText = document.createElement("div");
            colorText.classList.add(c.class.replace("square", "squareText"));
            colorText.innerHTML = c.text;
            colorDiv.appendChild(colorText);
        });

        const stockData = await rpc('/3Dstock/data', {
            company_id: this.company.id,
            wh_id: this.state.wh_id,
        });

        this.state.data = stockData;

        await this._setupScene();

        this.state.renderer.domElement.classList.add('custom-3d-element');
        select.classList.add('custom-3d-element');
        colorDiv.classList.add('custom-3d-element');
        closeDiv.classList.add('custom-3d-element');

        o_content.append(this.state.renderer.domElement, select, colorDiv, closeDiv);
    }

    async _setupScene() {
        this.state.scene = new THREE.Scene();
        this.state.scene.background = new THREE.Color(0xdfdfdf);
        this.state.clock = new THREE.Clock();

        this.state.camera = new THREE.PerspectiveCamera(60, window.innerWidth / window.innerHeight, 0.5, 6000);
        this.state.camera.position.set(0, 200, 300);

        this.state.renderer = new THREE.WebGLRenderer({ antialias: true });
        this.state.renderer.setSize(window.innerWidth, window.innerHeight);
        this.state.renderer.setPixelRatio(window.devicePixelRatio);

        // Base ground
        const baseCube = new THREE.Mesh(
            new THREE.BoxGeometry(800, 0, 800),
            new THREE.MeshBasicMaterial({ color: 0xffffff })
        );
        this.state.scene.add(baseCube);

        // Group to hold all stock location cubes
        this.state.group = new THREE.Group();

        // Loop through stock data and create blocks
        const dataArray = Object.entries(this.state.data);

        for (const loc of dataArray) {
            const [x, y, z, width, height, depth, loc_code, status] = loc[1];

            const loc_quant = await rpc('/3Dstock/data/quantity', {
                'loc_code': loc[0],
            });

            let color = 0xf2f2f2;  // default light gray
            if (loc_quant[0] > 0) {
                if (loc_quant[1] > 100) color = 0xcc0000;      // overload
                else if (loc_quant[1] > 50) color = 0xe6b800;   // almost full
                else color = 0x00802b;                          // free space
            } else {
                color = loc_quant[1] === -1 ? 0x00802b : 0x8c8c8c; // empty
            }

            // Create main cube
            const cube = new THREE.Mesh(
                new THREE.BoxGeometry(width, height, depth),
                new THREE.MeshPhongMaterial({ color, shininess: 50 })


            );
            cube.position.set(x, y, z);
            cube.name = loc[0];
            cube.userData = { color };
            this.state.group.add(cube);

            // Add cube edges in black
            const edges = new THREE.EdgesGeometry(new THREE.BoxGeometry(width, height, depth));
            const line = new THREE.LineSegments(edges, new THREE.LineBasicMaterial({ color: 0x000000 }));
            line.position.set(x, y, z);
            this.state.group.add(line);

            // Create canvas label texture
            const canvas = document.createElement('canvas');
            canvas.width = 256;
            canvas.height = 128;
            const ctx = canvas.getContext('2d');
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            ctx.fillStyle = "black";
            ctx.font = "bold 24px Arial";
            ctx.textAlign = "center";
            ctx.fillText(loc[0], canvas.width / 2, canvas.height / 2 + 10);

            // Create texture and sprite for label
            const texture = new THREE.CanvasTexture(canvas);
            texture.encoding = THREE.sRGBEncoding;
            texture.needsUpdate = true;

            const spriteMaterial = new THREE.SpriteMaterial({
                map: texture,
                transparent: true,       // allow full transparency
                depthTest: false,        // render above cube faces
            });

            const sprite = new THREE.Sprite(spriteMaterial);

            // Resize and position the label inside the cube
            sprite.scale.set(width * 0.8, height * 0.25, 1);  // adjust as needed
            sprite.position.set(x, y, z);  // center of the cube

            this.state.group.add(sprite);
        }


        this.state.scene.add(this.state.group);

        // Add lighting
        const ambientLight = new THREE.AmbientLight(0xffffff, 0.6);
        const directionalLight = new THREE.DirectionalLight(0xffffff, 0.8);
        directionalLight.position.set(100, 200, 100).normalize();

        this.state.scene.add(ambientLight);
        this.state.scene.add(directionalLight);

        // Controls
        this.state.controls = new THREE.OrbitControls(this.state.camera, this.state.renderer.domElement);

        this.animate();
    }


    async warehouseChange() {
        const select = document.querySelector(".customselect");
        this.state.wh_id = select?.value;
        const o_content = this.oContentRef.el;
        if (!o_content) return;
        o_content.querySelectorAll(".custom-3d-element").forEach(el => el.remove());
        await this._render3DView();
    }

    animate() {
        requestAnimationFrame(() => this.animate());
        this.state.renderer.render(this.state.scene, this.state.camera);

        const delta = this.state.clock.getDelta();
        let canvas = document.getElementsByTagName("canvas")[0];
        let colorBox = document.querySelector(".rectangle");
    }

    async onPointerMove(event) {
        const canvas = this.state.renderer?.domElement;
        if (!canvas || this.state.dialogs || this.state.isDialogOpen) return;

        if (this.state.selectedObject) {
            this.state.selectedObject.material.color.set(this.state.selectedObject.userData.color);
            this.state.selectedObject = null;
        }

        this.state.pointer.x = (event.clientX / window.innerWidth) * 2 - 1;
        this.state.pointer.y = -(event.clientY / window.innerHeight) * 2 + 1;
        this.state.raycaster.setFromCamera(this.state.pointer, this.state.camera);

        const intersects = this.state.raycaster.intersectObject(this.state.group, true);
        if (!intersects.length) return;

        const intersect = intersects.find(res => res?.object);
        console.log(intersect,'intersect.object.name')
//        if (!intersect) return;

        if (!intersect || !intersect.object?.name) return;

        const res = await rpc('/3Dstock/data/product', { loc_code: intersect.object.name });
        this.state.selectedObject = intersect.object;
        this.state.selectedObject.material.color.set(0x00ffcc);
        this.state.isDialogOpen = true;

        this.state.dialogs = this.env.services.dialog.add(StockLocationDialog, {
            title: `Location: ${intersect.object.name}`,
            data: res
        }, {
            onClose: () => this.onClickClose()
        });
    }

    onClickClose() {
        if (this.state.selectedObject) {
            this.state.selectedObject.material.color.set(this.state.selectedObject.userData.color);
            this.state.selectedObject = null;
        }
        this.state.dialogs = null;
        this.state.isDialogOpen = false;
    }
}

registry.category("views").add("3d_button_in_stock", {
    ...listView,
    Controller: StockListController,
    buttonTemplate: "stock_3d_view.ListView.Buttons",
});

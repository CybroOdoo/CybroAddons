/** @odoo-module **/

import { registry } from '@web/core/registry';
import { listView } from '@web/views/list/list_view';
import { ListController } from '@web/views/list/list_controller';
import { onMounted, useState, onWillUnmount, useRef, onWillStart, Component } from "@odoo/owl";
import { loadJS } from "@web/core/assets";
import { rpc } from "@web/core/network/rpc";
import { useService } from "@web/core/utils/hooks";
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
export class List3DView extends Component {
    setup() {
        this.company = useService("company");
        this.actionService = useService("action");
        this.oContentRef = useRef("oContent");
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
            breadcrumbs: this.env.config.breadcrumbs,
        });
        this.animationFrameId = null;
        this.onClickCloseBound = this.onClickClose.bind(this);
        this.onPointerMoveBound = this.onPointerMove.bind(this);
        onMounted(async () => {
            const res = await rpc('/3Dstock/warehouse', {
                company_id: this.company.currentCompany.id,
            });
            this.state.wh_data = res;
            if (res && res.length > 0) {
                this.state.wh_id = res[0][0];
            }
            await this._render3DView();
        });
        onWillUnmount(() => {
            if (this.state.renderer && this.state.renderer.domElement) {
                this.state.renderer.domElement.removeEventListener('dblclick', this.onPointerMoveBound);
            }
            if (this.animationFrameId) {
                cancelAnimationFrame(this.animationFrameId);
            }
            if (this.state.renderer) {
                this.state.renderer.dispose();
            }
        });
        onWillStart(async () => {
            this.props.title = '3D View';
            this.three = await loadJS('https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js')
            this.OrbitControls = await loadJS('https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.min.js')
        });
    }
    async _render3DView() {
        const o_content = this.oContentRef.el;
        if (!o_content) return;
        o_content.querySelectorAll(".custom-3d-element").forEach(el => el.remove());
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
            company_id: this.company.currentCompany.id,
            wh_id: this.state.wh_id,
        });
        this.state.data = stockData;
        await this._setupScene();
        this.state.renderer.domElement.classList.add('custom-3d-element');
        colorDiv.classList.add('custom-3d-element');
        o_content.append(this.state.renderer.domElement, colorDiv);
    }
    async _setupScene() {
        const container = this.oContentRef.el;
        if (!container) return;
        const rect = container.getBoundingClientRect();
        this.state.scene = new THREE.Scene();
        this.state.scene.background = new THREE.Color(0xdfdfdf);
        this.state.clock = new THREE.Clock();
        this.state.camera = new THREE.PerspectiveCamera(60, rect.width / rect.height, 0.5, 6000);
        this.state.camera.position.set(0, 200, 300);
        this.state.renderer = new THREE.WebGLRenderer({ antialias: true });
        this.state.renderer.setSize(rect.width, rect.height);
        this.state.renderer.setPixelRatio(window.devicePixelRatio);
        const baseCube = new THREE.Mesh(
            new THREE.BoxGeometry(800, 0, 800),
            new THREE.MeshBasicMaterial({ color: 0xffffff })
        );
        this.state.scene.add(baseCube);
        this.state.group = new THREE.Group();
        const dataArray = Object.entries(this.state.data);
        for (const loc of dataArray) {
            const [x, y, z, width, height, depth, loc_code, status] = loc[1];
            // Safety check: Skip if there are no dimensions or if Location Code (loc[0]) is empty
            if (!loc[0] || loc[0] === "false" || loc[0] === "undefined") continue;
            if (width === 0 && height === 0 && depth === 0 && x === 0 && y === 0 && z === 0) continue;
            const loc_quant = await rpc('/3Dstock/data/quantity', {
                'loc_code': loc[0],
            });
            let color = 0xf2f2f2;
            if (loc_quant[0] > 0) {
                if (loc_quant[1] > 100) color = 0xcc0000;
                else if (loc_quant[1] > 50) color = 0xe6b800;
                else color =  0x00802b;
            } else {
                color = loc_quant[1] === -1 ? 0x00802b : 0x8c8c8c;
            }
            const cube = new THREE.Mesh(
                new THREE.BoxGeometry(width, height, depth),
                new THREE.MeshPhongMaterial({ 
                    color, 
                    shininess: 50,
                    transparent: true,
                    opacity: 0.6
                })
            );
            cube.position.set(x, y, z);
            cube.name = loc[0];
            cube.userData = { color };
            this.state.group.add(cube);
            const edges = new THREE.EdgesGeometry(new THREE.BoxGeometry(width, height, depth));
            const line = new THREE.LineSegments(edges, new THREE.LineBasicMaterial({ color: 0x000000 }));
            line.position.set(x, y, z);
            this.state.group.add(line);
            const canvas = document.createElement('canvas');
            canvas.width = 256;
            canvas.height = 128;
            const ctx = canvas.getContext('2d');
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            ctx.fillStyle = "black";
            ctx.font = "bold 24px Arial";
            ctx.textAlign = "center";
            ctx.fillText(loc[0], canvas.width / 2, canvas.height / 2 + 10);
            const texture = new THREE.CanvasTexture(canvas);
            texture.encoding = THREE.sRGBEncoding;
            texture.needsUpdate = true;
            const spriteMaterial = new THREE.SpriteMaterial({
                map: texture,
                transparent: true,
                depthTest: false,
            });
            const sprite = new THREE.Sprite(spriteMaterial);
            sprite.scale.set(width * 0.8, height * 0.25, 1);
            sprite.position.set(x, y, z);
            this.state.group.add(sprite);
        }
        this.state.scene.add(this.state.group);
        const ambientLight = new THREE.AmbientLight(0xffffff, 0.6);
        const directionalLight = new THREE.DirectionalLight(0xffffff, 0.8);
        directionalLight.position.set(100, 200, 100).normalize();
        this.state.scene.add(ambientLight);
        this.state.scene.add(directionalLight);
        this.state.controls = new THREE.OrbitControls(this.state.camera, this.state.renderer.domElement);
        this.state.renderer.domElement.addEventListener('dblclick', this.onPointerMoveBound);
        this.animate();
    }
    animate() {
        if (!this.oContentRef || !this.oContentRef.el) {
            return;
        }
        this.animationFrameId = requestAnimationFrame(() => this.animate());
        this.state.renderer.render(this.state.scene, this.state.camera);
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
        this.state.dialogs = this.env.services.dialog.add(
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
    onClickClose() {
        if (this.state.selectedObject) {
            this.state.selectedObject.material.color.set(this.state.selectedObject.userData.color);
            this.state.selectedObject = null;
        }
        this.state.dialogs = null;
        this.state.isDialogOpen = false;
    }
    async onWarehouseChange(ev) {
        this.state.wh_id = parseInt(ev.target.value);
        if (this.state.renderer) {
            this.state.renderer.dispose();
        }
        this.state.isRendering = false;
        await this._render3DView();
    }
    onBreadcrumbClick(ev) {
        ev.preventDefault();
        const jsId = ev.currentTarget.getAttribute("jsId");
        if (jsId) {
            this.actionService.restore(jsId);
        }
    }
}
List3DView.template = "Location3DListView";
actionRegistry.add("stock_3d_view.open_list_3d_view", List3DView);
class StockListController extends ListController {
    setup() {
        super.setup();
    }
    async OnClickList3DvView(ev) {
        ev.preventDefault();
        this.env.services.action.doAction({
            type: 'ir.actions.client',
            tag: 'stock_3d_view.open_list_3d_view',
            target: 'current',
        });
    }
}
registry.category("views").add("3d_button_in_stock", {
    ...listView,
    Controller: StockListController,
    buttonTemplate: "stock_3d_view.ListView.Buttons",
});

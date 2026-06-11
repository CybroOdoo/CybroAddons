/** @odoo-module */
import { ListController } from "@web/views/list/list_controller";
import { registry } from '@web/core/registry';
import { listView } from '@web/views/list/list_view';
import { onMounted, onWillUnmount, useState, onWillStart, useRef } from "@odoo/owl";
import { loadJS } from "@web/core/assets";
import { jsonrpc } from "@web/core/network/rpc_service";
import { useService } from "@web/core/utils/hooks";
import { Dialog } from "@web/core/dialog/dialog";

/**
 * Dialog for displaying location details in list view.
 */
export class PositionDialog extends Dialog {
    static template = "stock_3d_view.PositionDialog";
    setup() {
        super.setup();
        this.pointer = this.props.pointer;
    }
}

/**
 * Custom ListController that integrates 3D warehouse view.
 */
export class StockListController extends ListController {
    /**
     * Component setup: initialization of services, state, and lifecycle hooks.
     */
    setup() {
        super.setup();
        this.company = useService("company");
        this.content3DRef = useRef("content3D");
        this.state = useState({
            wh_data: [],
            data: {},
            loc_quant: null,
            controls: null,
            renderer: null,
            clock: null,
            scene: null,
            camera: null,
            pointer: null,
            raycaster: null,
            group: null,
            mesh: null,
            material: null,
            loc_color: null,
            loc_opacity: 0.5,
            textSize: 0,
            selectedObject: null,
            dialogs: null,
            wh_id: null,
            isRendering: false,
            isDialogOpen: false,
            show3D: false,
        });

        onWillStart(async () => {
            await loadJS('/stock_3d_view/static/src/js/three.js');
            await loadJS('/stock_3d_view/static/src/js/OrbitControls.js');
            this.env.bus.addEventListener('dialog:close', this.onClickClose.bind(this));
        });

        onMounted(() => {
        });

        onWillUnmount(() => {
            this.env.bus.removeEventListener('dialog:close', this.onClickClose);
        });
    }

    /**
     * Open the 3D view from the list view buttons.
     * @param {Event} ev
     */
    async OnClickList3DvView(ev) {
        ev.preventDefault();
        if (this.state.isRendering) return;
        this.state.isRendering = true;
        const res = await jsonrpc('/3Dstock/warehouse', {
            'company_id': this.company.currentCompany.id,
        });
        if (res && res.length > 0) {
            this.state.wh_data = res;
            this.state.wh_id = res[0][0];
            this.state.show3D = true;
            await this._render3DView();
        } else {
            this.state.isRendering = false;
        }
    }

    /**
     * Initialize Three.js scene, camera, and renderer. Fetches data for the selected warehouse.
     */
    async _render3DView() {
        const res = await jsonrpc('/3Dstock/data', {
            'company_id': this.company.currentCompany.id,
            'wh_id': this.state.wh_id,
        });
        this.state.data = res;

        this.state.scene = new THREE.Scene();
        this.state.scene.background = new THREE.Color(0xdfdfdf);
        this.state.clock = new THREE.Clock();
        const width = this.content3DRef.el.clientWidth || window.innerWidth;
        const height = this.content3DRef.el.clientHeight || window.innerHeight;
        this.state.camera = new THREE.PerspectiveCamera(60, width / height, 0.5, 6000);
        this.state.camera.position.set(0, 200, 300);

        this.state.renderer = new THREE.WebGLRenderer({ antialias: true });
        this.state.renderer.setSize(width, height);
        this.state.renderer.setPixelRatio(window.devicePixelRatio);
        
        if (this.content3DRef.el) {
            this.content3DRef.el.appendChild(this.state.renderer.domElement);
        }

        this.state.controls = new THREE.OrbitControls(this.state.camera, this.state.renderer.domElement);
        this.state.scene.add(new THREE.Mesh(
            new THREE.BoxGeometry(800, 0, 800),
            new THREE.MeshBasicMaterial({ color: 0xffffff, transparent: false, opacity: 1, side: THREE.FrontSide })
        ));
        
        this.state.group = new THREE.Group();
        for (let [key, value] of Object.entries(this.state.data)) {
            if ((value[0] > 0) || (value[1] > 0) || (value[2] > 0) || (value[3] > 0) || (value[4] > 0) || (value[5] > 0)) {
                await this._createLocationMesh(key, value);
            }
        }
        this.state.scene.add(this.state.group);
        this.state.raycaster = new THREE.Raycaster();
        this.state.pointer = new THREE.Vector3();
        this.animate();
    }

    /**
     * Internal method to create a single location 3D object for the list view scene.
     * @private
     */
    async _createLocationMesh(key, value) {
        const geometry = new THREE.BoxGeometry(value[3], value[5], value[4]);
        geometry.translate(0, (value[5] / 2), 0);
        const edges = new THREE.EdgesGeometry(geometry);
        const quant_data = await jsonrpc('/3Dstock/data/quantity', { 'loc_code': key });

        let loc_color = 0x8c8c8c;
        let loc_opacity = 0.5;
        if (quant_data[0] > 0) {
            if (quant_data[1] > 100) loc_color = 0xcc0000;
            else if (quant_data[1] > 50) loc_color = 0xe6b800;
            else loc_color = 0x00802b;
            loc_opacity = 0.8;
        } else if (quant_data[1] == -1) {
            loc_color = 0x00802b;
            loc_opacity = 0.8;
        }

        const mesh = new THREE.Mesh(geometry, new THREE.MeshBasicMaterial({ color: loc_color, transparent: true, opacity: loc_opacity }));
        const line = new THREE.LineSegments(edges, new THREE.LineBasicMaterial({ color: 0x404040 }));
        [mesh.position.x, mesh.position.y, mesh.position.z] = [value[0], value[1], value[2]];
        [line.position.x, line.position.y, line.position.z] = [value[0], value[1], value[2]];
        mesh.name = key;
        mesh.userData = { color: loc_color, loc_id: value[6] };
        this.state.group.add(mesh);
        this.state.scene.add(line);
        this._addLocationText(key, value);
    }

    /**
     * Add label text to a location.
     * @private
     */
    _addLocationText(key, value) {
        new THREE.FontLoader().load('https://threejs.org/examples/fonts/droid/droid_sans_bold.typeface.json', (font) => {
            let textSize = Math.abs(value[3] > value[4] ? (value[4] / 2) - (value[4] / 2.9) : (value[3] / 2) - (value[3] / 2.9));
            const textgeom = new THREE.ShapeGeometry(font.generateShapes(key, textSize));
            textgeom.translate(0, ((value[5] / 2) - (textSize / (textSize - 1.5))), 0);
            const text = new THREE.Mesh(textgeom, new THREE.MeshBasicMaterial({ color: 0x000000, side: THREE.DoubleSide }));
            if (value[4] > value[3]) {
                text.rotation.y = Math.PI / 2;
                [text.position.x, text.position.y, text.position.z] = [value[0], value[1], value[2] + (textSize * 2) + ((value[3] / 3.779 / 2) / 2) + (textSize / 2)];
            } else {
                [text.position.x, text.position.y, text.position.z] = [value[0] - (textSize * 2) - ((value[4] / 3.779 / 2) / 2) - (textSize / 2), value[1], value[2]];
            }
            this.state.scene.add(text);
        });
    }

    /**
     * Handle warehouse change from the selector.
     * @param {Event} ev
     */
    async warehouseChange(ev) {
        this.state.wh_id = ev.target.value;
        if (this.state.renderer) {
            this.state.renderer.dispose();
            this.state.renderer = null;
        }
        await this._render3DView();
    }

    /**
     * Close the 3D warehouse view and return to the list.
     */
    onClickClose3D() {
        this.state.show3D = false;
        this.state.isRendering = false;
        if (this.state.renderer) {
            this.state.renderer.dispose();
            this.state.renderer = null;
        }
    }

    /**
     * Rendering loop for the Three.js scene.
     */
    animate() {
        if (!this.state.renderer) return;
        requestAnimationFrame(() => this.animate());
        this.state.renderer.render(this.state.scene, this.state.camera);
    }

    /**
     * Mouse pointer event handler for raycasting.
     * @param {Event} event
     */
    async onPointerMove(event) {
        if (!this.state.show3D || this.state.dialogs || this.state.isDialogOpen) return;
        const rect = this.content3DRef.el.getBoundingClientRect();
        const pointer = new THREE.Vector2(
            ((event.clientX - rect.left) / rect.width) * 2 - 1,
            -((event.clientY - rect.top) / rect.height) * 2 + 1
        );
        this.state.raycaster.setFromCamera(pointer, this.state.camera);
        const intersects = this.state.raycaster.intersectObject(this.state.group, true);
        if (intersects.length > 0) {
            const obj = intersects[0].object;
            if (obj.userData.loc_id) {
                const products = await jsonrpc('/3Dstock/data/product', { 'loc_code': obj.name });
                this.state.selectedObject = obj;
                this.state.selectedObject.material.color.set(0x00ffcc);
                this.state.isDialogOpen = true;
                this.state.dialogs = await this.env.services.dialog.add(PositionDialog, {
                    title: `Location: ${obj.name}`,
                    size: 'small',
                    data: products,
                    pointer: { x: event.clientX, y: 100 },
                    close: this.onClickClose
                });
            }
        }
    }

    /**
     * Close the dialog and reset highlighted object.
     */
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


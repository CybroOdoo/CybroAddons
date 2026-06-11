/** @odoo-module **/
import { registry } from "@web/core/registry";
import { Dialog } from "@web/core/dialog/dialog";
import { useService } from "@web/core/utils/hooks";
import { jsonrpc } from "@web/core/network/rpc_service";
import { loadJS } from "@web/core/assets";
import { Component, onWillStart, onMounted, onWillUnmount, useState, useRef } from "@odoo/owl";

const actionRegistry = registry.category("actions");

/**
 * Dialog for displaying 3D position data in form view.
 */
export class PositionFormDialog extends Dialog {
    static template = "stock_3d_view.PositionDialog";
    setup() {
        super.setup();
        this.pointer = this.props.pointer;
    }
}

/**
 * Controller for the 3D representation of a stock location in form view.
 */
class Form3DView extends Component {
    /**
     * Component setup: initialization of services, state, and lifecycle hooks.
     */
    setup() {
        super.setup();
        this.actionService = useService("action");
        this.contentRef = useRef("contentDiv");
        this.onClickClose = this.onClickClose.bind(this);

        this.state = useState({
            wh_data: "",
            data: "",
            loc_quant: "",
            controls: "",
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
            wh_id: "",
            location_id: this.props.action.context.default_location_id || localStorage.getItem("location_id"),
            breadcrumbs: this.env.config.breadcrumbs,
            isDialogOpen: false,
            showLegend: false,
        });

        onWillStart(async () => {
            await loadJS('/stock_3d_view/static/src/js/three.js');
            await loadJS('/stock_3d_view/static/src/js/OrbitControls.js');
            this.env.bus.addEventListener('dialog:close', this.onClickClose);
        });

        onMounted(() => {
            this.state.showLegend = true;
            this.Open3DView();
        });

        onWillUnmount(() => {
            this.env.bus.removeEventListener('dialog:close', this.onClickClose);
        });
    }

    /**
     * Restore the action for breadcrumb navigations.
     * @param {Event} ev
     */
    async onBreadcrumbClick(ev) {
        const jsId = ev.target.getAttribute('t-att-jsId');
        this.actionService.restore(jsId);
    }

    /**
     * Initialize Three.js scene, camera, and renderer. Fetches initial data.
     */
    async Open3DView() {
        if (this.props.action.context.default_location_id != null) {
            localStorage.setItem("location_id", this.props.action.context.default_location_id);
            localStorage.setItem("company_id", this.props.action.context.company_id);
        }

        const res = await jsonrpc('/3Dstock/data/standalone', {
            'company_id': localStorage.getItem("company_id"),
            'loc_id': localStorage.getItem("location_id"),
        });
        if (res) this.state.data = res;

        this.state.scene = new THREE.Scene();
        this.state.scene.background = new THREE.Color(0xdfdfdf);
        this.state.clock = new THREE.Clock();
        const width = this.contentRef.el.clientWidth || window.innerWidth;
        const height = this.contentRef.el.clientHeight || window.innerHeight;
        this.state.camera = new THREE.PerspectiveCamera(60, width / height, 0.5, 6000);
        this.state.camera.position.set(0, 200, 300);

        this.state.renderer = new THREE.WebGLRenderer({ antialias: true });
        this.state.renderer.setSize(width, height);
        this.state.renderer.setPixelRatio(window.devicePixelRatio);
        
        if (this.contentRef.el) {
            this.contentRef.el.appendChild(this.state.renderer.domElement);
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
     * Internal method to create a single location 3D object.
     * @private
     */
    async _createLocationMesh(key, value) {
        const geometry = new THREE.BoxGeometry(value[3], value[5], value[4]);
        geometry.translate(0, (value[5] / 2), 0);
        const edges = new THREE.EdgesGeometry(geometry);
        const quant_data = await jsonrpc('/3Dstock/data/quantity', { 'loc_code': key });
        
        // Color Determination
        let loc_color = 0x8c8c8c;
        let loc_opacity = 0.5;
        if (localStorage.getItem("location_id") == value[6]) {
            loc_opacity = 0.8;
            if (quant_data[0] > 0) {
                if (quant_data[1] > 100) loc_color = 0xcc0000;
                else if (quant_data[1] > 50) loc_color = 0xe6b800;
                else loc_color = 0x00802b;
            } else {
                loc_color = quant_data[1] == -1 ? 0x00802b : 0x0066ff;
            }
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
     * Add label text to a location in the 3D scene.
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
     * Rendering loop for the Three.js scene.
     */
    animate() {
        if (!this.state.renderer) return;
        requestAnimationFrame(() => this.animate());
        this.state.renderer.render(this.state.scene, this.state.camera);
    }

    /**
     * Mouse pointer event handler for raycasting and dialog opening.
     * @param {Event} event
     */
    async onPointerMoveForm(event) {
        if (this.state.dialogs || this.state.isDialogOpen) return;
        const rect = this.contentRef.el.getBoundingClientRect();
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
                this.state.dialogs = await this.env.services.dialog.add(PositionFormDialog, {
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
     * Close the position dialog and reset highlighted object.
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

Form3DView.template = "Location3DFormView";
actionRegistry.add('stock_3d_view.open_form_3d_view', Form3DView);

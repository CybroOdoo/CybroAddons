/** @odoo-module **/

import { registry } from "@web/core/registry";
import { Component, onMounted, onWillUnmount, useRef } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { SelectCreateDialog } from "@web/views/view_dialogs/select_create_dialog";
import { standardActionServiceProps } from "@web/webclient/actions/action_service";
import { loadBundle } from "@web/core/assets";

export class ExcalidrawClientAction extends Component {
    static template = "odoo_excalidraw.ExcalidrawClientAction";
    static props = {
        ...standardActionServiceProps,
    };

    setup() {
        this.root = useRef("excalidraw-root");
        this.orm = useService("orm");
        this.dialog = useService("dialog");
        this.notification = useService("notification");
        this.reactRoot = null;

        onMounted(async () => {
            // Ensure global libraries are loaded if not already (safeguard)
            // In Odoo, they should be loaded by the asset bundle, but we can verify.

            if (!window.React || !window.ReactDOM) {
                console.error("React or ReactDOM not found");
                return;
            }

            const excalidrawLib = window.ExcalidrawLib || window.Excalidraw;
            if (!excalidrawLib) {
                console.error("Excalidraw library not found");
                return;
            }

            // The UMD likely exports the component as Excalidraw or named export
            const ExcalidrawComponent = excalidrawLib.Excalidraw || excalidrawLib;
            this.exportToBlob = excalidrawLib.exportToBlob;

            const App = React.createElement(ExcalidrawComponent, {
                excalidrawAPI: (api) => this.excalidrawAPI = api,
            });

            this.reactRoot = ReactDOM.createRoot(this.root.el);
            this.reactRoot.render(App);
        });

        onWillUnmount(() => {
            if (this.reactRoot) {
                this.reactRoot.unmount();
            }
        });
    }

    async onAttach() {
        if (!this.excalidrawAPI || !this.exportToBlob) {
            this.notification.add("Canvas not ready", { type: "danger" });
            return;
        }

        this.dialog.add(SelectCreateDialog, {
            title: "Select Manufacturing Order",
            resModel: "mrp.production",
            multiSelect: false,
            noCreate: true,
            onSelected: async (resIds) => {
                if (resIds.length === 0) return;
                const resId = resIds[0];
                await this.saveAttachment(resId);
            },
        });
    }

    async saveAttachment(resId) {
        try {
            const elements = this.excalidrawAPI.getSceneElements();
            const appState = this.excalidrawAPI.getAppState();
            const files = this.excalidrawAPI.getFiles();

            const blob = await this.exportToBlob({
                elements,
                appState,
                files,
                mimeType: "image/png",
            });

            const reader = new FileReader();
            reader.readAsDataURL(blob);
            reader.onloadend = async () => {
                const base64data = reader.result.split(",")[1];
                await this.orm.create("ir.attachment", [{
                    name: `Sketch_${new Date().toISOString()}.png`,
                    res_model: "mrp.production",
                    res_id: resId,
                    datas: base64data,
                    type: "binary",
                    mimetype: "image/png",
                }]);

                this.notification.add("Sketch attached successfully", { type: "success" });
            };
        } catch (e) {
            console.error("Failed to save attachment", e);
            this.notification.add("Failed to attach sketch", { type: "danger" });
        }
    }

    async onDownload() {
        if (!this.excalidrawAPI || !this.exportToBlob) {
            console.error("Excalidraw API not ready");
            return;
        }

        try {
            const elements = this.excalidrawAPI.getSceneElements();
            const appState = this.excalidrawAPI.getAppState();
            const files = this.excalidrawAPI.getFiles();

            // We export as PNG for simplicity as PDF export often requires additional dependencies 
            // (like window.resvg) not guaranteed to be present in the minified bundle.
            const blob = await this.exportToBlob({
                elements,
                appState,
                files,
                mimeType: "image/png",
            });

            const url = window.URL.createObjectURL(blob);
            const a = document.createElement("a");
            a.href = url;
            a.download = "drawing.png";
            a.click();
            window.URL.revokeObjectURL(url);
        } catch (e) {
            console.error("Download failed", e);
        }
    }
}

registry.category("actions").add("odoo_excalidraw.excalidraw_client_action", ExcalidrawClientAction);

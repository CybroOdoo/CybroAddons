/** @odoo-module **/

import { registry } from "@web/core/registry";
import { Component, onMounted, onWillUnmount, useRef } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { standardActionServiceProps } from "@web/webclient/actions/action_service";

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
        this.action = useService("action");
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
        try {
            const elements = this.excalidrawAPI.getSceneElements();
            const appState = this.excalidrawAPI.getAppState();
            const files = this.excalidrawAPI.getFiles();
            if (!elements || elements.length === 0) {
                this.notification.add("Canvas is empty", { type: "warning" });
                return;
            }
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
                this.action.doAction({
                    type: 'ir.actions.act_window',
                    name: 'Attach Sketch to Record',
                    res_model: 'excalidraw.attach.wizard',
                    views: [[false, 'form']],
                    target: 'new',
                    context: {
                        default_sketch_data: base64data,
                    }
                });
            };
        } catch (e) {
            console.error("Failed to prepare attachment", e);
            this.notification.add("Failed to prepare sketch for attachment", { type: "danger" });
        }
    }
    onDownloadPNG() {
        this.onDownloadFormat('image');
    }
    onDownloadPDF() {
        this.onDownloadFormat('pdf');
    }
    onDownloadExcel() {
        this.onDownloadFormat('excel');
    }
    onDownloadWord() {
        this.onDownloadFormat('word');
    }
    async onDownloadFormat(format) {
        if (!this.excalidrawAPI || !this.exportToBlob) {
            this.notification.add("Canvas not ready", { type: "danger" });
            return;
        }
        try {
            const elements = this.excalidrawAPI.getSceneElements();
            const appState = this.excalidrawAPI.getAppState();
            const files = this.excalidrawAPI.getFiles();
            if (!elements || elements.length === 0) {
                this.notification.add("Canvas is empty", { type: "warning" });
                return;
            }
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
                if (format === 'image') {
                    this.downloadFile(base64data, `drawing_${new Date().toISOString().slice(0, 10)}.png`, 'image/png');
                } else {
                    const res = await this.orm.call(
                        "excalidraw.attach.wizard",
                        "convert_sketch_format",
                        [base64data, format]
                    );
                    this.downloadFile(res.data, res.filename, res.mimetype);
                }
            };
        } catch (e) {
            console.error("Download failed", e);
            this.notification.add("Download failed", { type: "danger" });
        }
    }
    downloadFile(base64Data, filename, mimetype) {
        const byteCharacters = atob(base64Data);
        const byteNumbers = new Array(byteCharacters.length);
        for (let i = 0; i < byteCharacters.length; i++) {
            byteNumbers[i] = byteCharacters.charCodeAt(i);
        }
        const byteArray = new Uint8Array(byteNumbers);
        const blob = new Blob([byteArray], { type: mimetype });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = filename;
        a.click();
        window.URL.revokeObjectURL(url);
    }
}
registry.category("actions").add("odoo_excalidraw.excalidraw_client_action", ExcalidrawClientAction);

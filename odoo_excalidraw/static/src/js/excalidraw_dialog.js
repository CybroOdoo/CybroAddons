/** @odoo-module **/

import { Component, onMounted, onWillUnmount, useRef } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { Dialog } from "@web/core/dialog/dialog";

export class ExcalidrawDialog extends Component {
    static template = "odoo_excalidraw.ExcalidrawDialog";
    static components = { Dialog };
    static props = {
        close: { type: Function },
        onSave: { type: Function, optional: true },
    };

    setup() {
        this.root = useRef("excalidraw-root");
        this.notification = useService("notification");
        this.reactRoot = null;
        this.excalidrawAPI = null;

        onMounted(() => {
            if (!window.React || !window.ReactDOM) {
                console.error("React or ReactDOM not found");
                return;
            }

            const excalidrawLib = window.ExcalidrawLib || window.Excalidraw;
            if (!excalidrawLib) {
                console.error("Excalidraw library not found");
                return;
            }

            const ExcalidrawComponent = excalidrawLib.Excalidraw || excalidrawLib;
            this.exportToBlob = excalidrawLib.exportToBlob;

            const App = window.React.createElement(ExcalidrawComponent, {
                excalidrawAPI: (api) => this.excalidrawAPI = api,
            });

            this.reactRoot = window.ReactDOM.createRoot(this.root.el);
            this.reactRoot.render(App);
        });

        onWillUnmount(() => {
            if (this.reactRoot) {
                this.reactRoot.unmount();
            }
        });
    }

    async onSave() {
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

            const base64data = await new Promise((resolve, reject) => {
                const reader = new FileReader();
                reader.onloadend = () => resolve(reader.result);
                reader.onerror = reject;
                reader.readAsDataURL(blob);
            });

            if (this.props.onSave) {
                await this.props.onSave(base64data);
            }
            this.props.close();
        } catch (e) {
            console.error("Failed to export image", e);
            this.notification.add("Failed to save sketch", { type: "danger" });
        }
    }
}

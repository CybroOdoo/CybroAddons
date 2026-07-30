/** @odoo-module **/

/**
 * Odoo 17 compatible ExcalidrawClientAction.
 *
 * KEY DIFFERENCE vs Odoo 18/19:
 *  - Same React version fix as excalidraw_dialog.js:
 *    ReactDOM.render() instead of ReactDOM.createRoot().render()
 *    ReactDOM.unmountComponentAtNode() instead of reactRoot.unmount()
 */

import { registry } from "@web/core/registry";
import { Component, onMounted, onWillUnmount, useRef } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { SelectCreateDialog } from "@web/views/view_dialogs/select_create_dialog";
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
        this.excalidrawAPI = null;
        this._storageListener = null;

        this.LIBRARY_KEY = "odoo_excalidraw_client_library";
        this.PENDING_KEY = "excalidraw_pending_library";

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

            const libraryReturnUrl =
                window.location.origin +
                "/odoo_excalidraw/static/library_redirect.html";

            let initialLibraryItems = [];
            try {
                const stored = localStorage.getItem(this.LIBRARY_KEY);
                if (stored) initialLibraryItems = JSON.parse(stored);
            } catch (_e) { /* ignore */ }

            const App = window.React.createElement(ExcalidrawComponent, {
                excalidrawAPI: (api) => (this.excalidrawAPI = api),
                libraryReturnUrl: libraryReturnUrl,
                initialData: { libraryItems: initialLibraryItems },
                onLibraryChange: (items) => {
                    try {
                        localStorage.setItem(this.LIBRARY_KEY, JSON.stringify(items));
                    } catch (_e) { /* ignore */ }
                },
            });

            // Odoo 17 / React 17: use legacy render API
            window.ReactDOM.render(App, this.root.el);

            this._storageListener = async (e) => {
                if (e.key !== this.PENDING_KEY || !e.newValue) return;
                localStorage.removeItem(this.PENDING_KEY);
                try {
                    const { libraryUrl } = JSON.parse(e.newValue);
                    if (libraryUrl) await this._installLibrary(libraryUrl);
                } catch (_e) { /* ignore */ }
            };
            window.addEventListener("storage", this._storageListener);
        });

        onWillUnmount(() => {
            if (this._storageListener) {
                window.removeEventListener("storage", this._storageListener);
                this._storageListener = null;
            }
            if (this.root.el) {
                window.ReactDOM.unmountComponentAtNode(this.root.el);
            }
        });
    }

    /**
     * Fetch the .excalidrawlib JSON and install it into the running instance.
     */
    async _installLibrary(libraryUrl) {
        if (!this.excalidrawAPI) {
            this.notification.add("Canvas not ready — please try again", { type: "warning" });
            return;
        }
        try {
            const res = await fetch(libraryUrl);
            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            const json = await res.json();
            // Force status "published" so items appear under the
            // "Excalidraw Library" section rather than "Personal Library".
            const items = (json.libraryItems || json.library || []).map((item) => ({
                ...item,
                status: "published",
            }));
            await this.excalidrawAPI.updateLibrary({
                libraryItems: items,
                merge: true,
                openLibraryMenu: true,
            });
            this.notification.add("Library added successfully!", { type: "success" });
        } catch (e) {
            console.error("[Excalidraw] failed to install library", e);
            this.notification.add("Failed to add library — check network connection.", { type: "danger" });
        }
    }

    async onAttach() {
        if (!this.excalidrawAPI || !this.exportToBlob) {
            this.notification.add("Canvas not ready", { type: "danger" });
            return;
        }

        const elements = this.excalidrawAPI.getSceneElements();
        if (!elements || elements.length === 0) {
            this.notification.add("Canvas is empty", { type: "warning" });
            return;
        }

        this.dialog.add(SelectCreateDialog, {
            title: "Select Manufacturing Order",
            resModel: "mrp.production",
            multiSelect: false,
            noCreate: true,
            onSelected: async (resIds) => {
                if (resIds.length === 0) return;
                await this.saveAttachment(resIds[0]);
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

        const elements = this.excalidrawAPI.getSceneElements();
        if (!elements || elements.length === 0) {
            this.notification.add("Canvas is empty", { type: "warning" });
            return;
        }

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

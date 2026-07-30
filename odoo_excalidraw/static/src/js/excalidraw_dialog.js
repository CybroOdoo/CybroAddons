/** @odoo-module **/

/**
 * Odoo 17 compatible Excalidraw Dialog.
 *
 * KEY DIFFERENCE vs Odoo 18/19:
 *  - Odoo 17 bundles React 17, which uses the legacy ReactDOM.render() API.
 *  - Odoo 18/19 bundles React 18, which uses ReactDOM.createRoot().render().
 *
 *  Using createRoot() on React 17 silently fails or throws, which is why
 *  the canvas never appeared in Odoo 17.
 */

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
        this.excalidrawAPI = null;
        this._storageListener = null;

        // localStorage key used by the static relay page
        // (static/library_redirect.html) to hand off the library URL.
        this.LIBRARY_KEY = "odoo_excalidraw_dialog_library";
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

            // ---- libraryReturnUrl ----------------------------------------
            // Point to the static relay page served directly by the web
            // server.  The external library site redirects its popup tab
            // there; that page writes to localStorage and closes itself.
            // We must NOT point to the main Odoo /web URL because Odoo's
            // hash router would intercept the #addLibrary fragment and
            // navigate to the home page.
            const libraryReturnUrl =
                window.location.origin +
                "/odoo_excalidraw/static/library_redirect.html";

            // ---- Restore previously saved library items ------------------
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
                    // Persist every library change so items survive dialog
                    // re-opens and page refreshes.
                    try {
                        localStorage.setItem(this.LIBRARY_KEY, JSON.stringify(items));
                    } catch (_e) { /* ignore */ }
                },
            });

            window.ReactDOM.render(App, this.root.el);

            // ---- storage event listener ----------------------------------
            // When the static relay page (library_redirect.html) runs in the
            // popup tab it writes the library URL to localStorage and then
            // closes itself.  Because the write happens in a DIFFERENT tab,
            // the main Odoo tab receives a 'storage' event instantly — no
            // page reload required.
            this._storageListener = async (e) => {
                if (e.key !== this.PENDING_KEY || !e.newValue) return;
                // Consume immediately so other tabs don't also pick it up.
                localStorage.removeItem(this.PENDING_KEY);
                try {
                    const { libraryUrl } = JSON.parse(e.newValue);
                    if (libraryUrl) await this._installLibrary(libraryUrl);
                } catch (_e) { /* malformed JSON, ignore */ }
            };
            window.addEventListener("storage", this._storageListener);
        });

        onWillUnmount(() => {
            if (this._storageListener) {
                window.removeEventListener("storage", this._storageListener);
                this._storageListener = null;
            }
            if (this.root.el) {
                // React 17 unmount API
                window.ReactDOM.unmountComponentAtNode(this.root.el);
            }
        });
    }

    /**
     * Fetch the .excalidrawlib JSON from libraryUrl and install it into the
     * running Excalidraw instance via excalidrawAPI.updateLibrary.
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

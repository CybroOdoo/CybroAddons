/** @odoo-module **/
import { useApp } from "@odoo/owl";
import { _t } from "@web/core/l10n/translation";
import { rpc } from "@web/core/network/rpc";
import { patch } from "@web/core/utils/patch";
import { EditorClientAction } from "@backend_theme_infinito/js/editor_client_action";
import { AdvancedFeatures } from "./AdvancedFeatures";

patch(EditorClientAction.prototype, {
    setup() {
        super.setup(...arguments);
        // The Plus sidebar is a second root of the same app, so it shares
        // the plugins, the services and the templates of the web client.
        this._plusApp = useApp();
    },

    async _onResetClick() {
        await rpc("/theme_studio_plus/reset_to_default_style");
        return super._onResetClick(...arguments);
    },

    /**
     * Closes the Infinito Plus sidebar. Safe to call more than once.
     */
    _closePlusSidebar() {
        // Stop listening for the Close button event
        if (this._plusCloseHandler) {
            document.removeEventListener("infinito-plus-close", this._plusCloseHandler);
            this._plusCloseHandler = null;
        }
        const mainDiv = document.querySelector(".marg_main");
        if (mainDiv) {
            mainDiv.style.marginLeft = "0";
            mainDiv.style.width = "100%";
        }
        if (this._plusToggler) {
            this._plusToggler.classList.remove("open");
        }
        // _plusSidebar holds the root that renders the Plus sidebar
        const root = this._plusSidebar;
        this._plusSidebar = null;
        if (root) {
            root.destroy();
        }
        document.querySelector(".sidebar_simple_editor")?.remove();
        if (this.state) {
            this.state.sidebarOpen = false;
        }
    },

    async _onThemeStudioToggleSidebar(ev) {
        ev.preventDefault();
        if (this._plusOpening) {
            return;
        }
        if (this._plusSidebar) {
            this._closePlusSidebar();
            return;
        }
        // Read currentTarget before any await
        const toggler = ev.currentTarget;
        this._plusToggler = toggler;
        this._plusOpening = true;
        toggler.classList.add("open");
        let root = null;
        try {
            if (document.getElementById("theme_editor_sidebar_preset")
                && typeof this._closePresetSidebar === "function") {
                this._closePresetSidebar();
            }
            // The Close button in Sidebar.js fires this event
            this._plusCloseHandler = () => this._closePlusSidebar();
            document.addEventListener("infinito-plus-close", this._plusCloseHandler);

            root = this._plusApp.createRoot(AdvancedFeatures);
            this._plusSidebar = root;
            await root.mount(document.body);

            const mainDiv = document.querySelector(".marg_main");
            if (mainDiv) {
                mainDiv.style.marginLeft = "340px";
                mainDiv.style.width = "calc(100% - 340px)";
            }
            if (this.state) {
                this.state.sidebarOpen = true;
            }
        } catch (error) {
            this.env.services.notification.add(
                error?.message || _t("Could not open the Infinito Plus sidebar."),
                { type: "danger" });
            toggler.classList.remove("open");
            this._plusSidebar = null;
            root?.destroy();
            if (this._plusCloseHandler) {
                document.removeEventListener("infinito-plus-close", this._plusCloseHandler);
                this._plusCloseHandler = null;
            }
        } finally {
            this._plusOpening = false;
        }
    },
});
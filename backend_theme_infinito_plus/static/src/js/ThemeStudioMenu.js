/** @odoo-module **/
import { mount } from "@odoo/owl";
import { rpc } from "@web/core/network/rpc";
import { patch } from "@web/core/utils/patch";
import { EditorClientAction } from "@backend_theme_infinito/js/editor_client_action";
import { AdvancedFeatures } from "./AdvancedFeatures";

patch(EditorClientAction.prototype, {
    async _onResetClick() {
        await rpc("/theme_studio_plus/reset_to_default_style");
        return super._onResetClick(...arguments);
    },

    async _onThemeStudioToggleSidebar(ev) {
        ev.currentTarget.classList.toggle("open");
        ev.preventDefault();
        const mainDiv = document.querySelector(".marg_main");
        this.state.sidebarOpen = !this.state.sidebarOpen;
        if (!mainDiv) {
            return;
        }
        if (this.state.sidebarOpen) {
            if (document.getElementById("theme_editor_sidebar_preset")) {
                this._closePresetSidebar();
            }
            if (!this._plusSidebar) {
                this._plusSidebar = await mount(
                    AdvancedFeatures, document.body, { env: this.env });
            }
            mainDiv.style.marginLeft = "340px";
            mainDiv.style.width = "calc(100% - 340px)";
        } else {
            mainDiv.style.marginLeft = "0";
            mainDiv.style.width = "100%";
            if (this._plusSidebar) {
                this._plusSidebar.__owl__.app.destroy();
                this._plusSidebar = null;
            }
            document.querySelector(".sidebar_simple_editor")?.remove();
        }
    },
});
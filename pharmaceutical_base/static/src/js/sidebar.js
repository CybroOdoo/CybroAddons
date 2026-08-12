/** @odoo-module */

import { Component, reactive, useState } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useBus, useService } from "@web/core/utils/hooks";

/**
 * Shared rail state. The navbar patch in search_apps.js drives it (toggle
 * button, app switches) and the rail below reads it, so neither one has to
 * reach into the other's DOM.
 */
export const sidebarState = reactive({
    activeApp: null,
    isHidden: false,
});

/**
 * App rail displayed on the left of every backend screen.
 *
 * It is registered as a main component rather than xpath'd into web.NavBar:
 * Enterprise forks the navbar into its own primary template
 * (web_enterprise.EnterpriseNavBar), and a primary fork only picks up the
 * web.NavBar extensions registered *before* it in the assets bundle. This
 * module loads after web_enterprise, so an extension on web.NavBar was
 * silently dropped as soon as an Enterprise app (Accounting, ...) was
 * installed — taking the rail with it. Rendering the rail on its own keeps
 * it working on both Community and Enterprise.
 */
export class PharmaSidebar extends Component {
    static template = "pharmaceutical_base.Sidebar";
    static props = {};

    setup() {
        this.menuService = useService("menu");
        this.state = useState(sidebarState);
        if (!this.state.activeApp) {
            this.state.activeApp = parseInt(sessionStorage.getItem("activeApp")) || null;
        }

        // Fired by the menu service whenever the current app changes or the
        // menus are reloaded, wherever the switch came from.
        useBus(this.env.bus, "MENUS:APP-CHANGED", () => {
            this.syncActiveApp();
            this.render();
        });
        this.syncActiveApp();
    }

    syncActiveApp() {
        const currentApp = this.menuService.getCurrentApp();
        if (currentApp) {
            this.state.activeApp = currentApp.id;
            this.state.isHidden = false;
            sessionStorage.setItem("activeApp", currentApp.id);
        }
    }

    onAppClick(app) {
        this.state.activeApp = app.id;
        this.state.isHidden = false;
        sessionStorage.setItem("activeApp", app.id);
        this.menuService.selectMenu(app);
    }
}

registry.category("main_components").add("pharmaceutical_base.Sidebar", {
    Component: PharmaSidebar,
});

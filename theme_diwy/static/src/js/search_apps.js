/** @odoo-module */

import { NavBar } from "@web/webclient/navbar/navbar";
import { registry } from "@web/core/registry";
import { computeAppsAndMenuItems } from "@web/webclient/menus/menu_helpers";
import { useBus, useService } from "@web/core/utils/hooks";
import { useRef, onMounted, useState } from "@odoo/owl";
import { patch } from "@web/core/utils/patch";

patch(NavBar.prototype, {
    // To modify the Navbar properties and functions.
    setup() {
        super.setup()
        const isSidebarHidden = sessionStorage.getItem("isSidebarHidden") === "true";
        this.sidebarRef = useRef("sidebar");
        this.menu_sectionsRef = useRef("menu_sections")
        this.busService = useService("bus_service");
        const { apps } = computeAppsAndMenuItems(this.menuService.getMenuAsTree("root"));
        this._apps = apps;
        Object.assign(this.state, {
            activeApp: parseInt(sessionStorage.getItem("activeApp")) || null,
            isSidebarHidden: isSidebarHidden,
        });
        useBus(this.env.bus, "app-selected", (event) => {
            this.onAppClick(event.detail.activeApp);
        });
        onMounted(() => {
            this.applySidebarState();
        });
    },

    applySidebarState() {
        const sidebarElement = this.sidebarRef.el;
        const sectionsElement = this.menu_sectionsRef.el;
        if (sidebarElement) {
            const actionManagerElement = document.querySelector(".o_action_manager");
            if (this.state.isSidebarHidden) {
                sidebarElement.classList.add("o_hidden");
                sectionsElement.classList.add("o_hidden");
                actionManagerElement?.style.setProperty("margin-left", "0", "important");
            } else {
                sidebarElement.classList.remove("o_hidden");
                sectionsElement.classList.remove("o_hidden");
                actionManagerElement?.style.setProperty("margin-left", "98px");
            }
        }
    },

    onAppClick(app) {
        const sidebarElement = this.sidebarRef.el; // Access the DOM element
        const sectionsElement = this.menu_sectionsRef.el;
        sidebarElement?.classList.remove("o_hidden"); // Remove the 'o_hidden' class to show the sidebar
        sectionsElement?.classList.remove("o_hidden"); // Remove the 'o_hidden' class to show the sidebar
        const actionManagerElement = document.querySelector(".o_action_manager");
        actionManagerElement?.style.setProperty("margin-left", "98px");
        this.state.isSidebarHidden = false;
        sessionStorage.setItem("isSidebarHidden", "false");
        this.state.activeApp = app.id;
        sessionStorage.setItem("activeApp", this.state.activeApp);
        this.onNavBarDropdownItemSelection(app);
    },

    async _onClickMenusPanel() {
        const sidebarElement = this.sidebarRef.el; // Access the DOM element
        const sectionsElement = this.menu_sectionsRef.el;
        sidebarElement?.classList.add("o_hidden"); // Add the 'o_hidden' class to hide the sidebar
        sectionsElement?.classList.add("o_hidden"); // Add the 'o_hidden' class to hide the sidebar
        const actionManagerElement = document.querySelector(".o_action_manager");
        actionManagerElement?.style.setProperty("margin-left", "0", "important");
        this.state.isSidebarHidden = true;
        sessionStorage.setItem("isSidebarHidden", "true");
        await this.actionService.doAction({
            type: 'ir.actions.client',
            tag: 'theme_diwy.homemenus',
            params: {
                apps: this._apps,
            },
        });
    }
})
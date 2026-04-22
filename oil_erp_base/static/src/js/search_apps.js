/** @odoo-module */
/**
 * This file adds search and sidebar behavior to the navigation bar.
 */

import { NavBar } from "@web/webclient/navbar/navbar";
import { computeAppsAndMenuItems } from "@web/webclient/menus/menu_helpers";
import { useBus, useService } from "@web/core/utils/hooks";
import { useRef, onMounted, useState } from "@odoo/owl";
import { patch } from "@web/core/utils/patch";

patch(NavBar.prototype, {
    /**
     * Patched setup to include sidebar state management.
     */
    setup() {
        super.setup();
        const isSidebarHidden = sessionStorage.getItem("isSidebarHidden") === "true";
        this.sidebarRef = useRef("sidebar");
        this.menu_sectionsRef = useRef("menu_sections");
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

    /**
     * Applies the sidebar visibility state to the DOM.
     */
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

    /**
     * Handles app selection and ensures sidebar visibility.
     * @param {Object} app - The clicked app object.
     */
    onAppClick(app) {
        const sidebarElement = this.sidebarRef.el;
        const sectionsElement = this.menu_sectionsRef.el;
        sidebarElement?.classList.remove("o_hidden");
        sectionsElement?.classList.remove("o_hidden");
        const actionManagerElement = document.querySelector(".o_action_manager");
        actionManagerElement?.style.setProperty("margin-left", "98px");
        this.state.isSidebarHidden = false;
        sessionStorage.setItem("isSidebarHidden", "false");
        this.state.activeApp = app.id;
        sessionStorage.setItem("activeApp", this.state.activeApp);
        this.onNavBarDropdownItemSelection(app);
    },

    /**
     * Toggles the home menu panel and updates sidebar state.
     */
    async _onClickMenusPanel() {
        const sidebarElement = this.sidebarRef.el;
        const sectionsElement = this.menu_sectionsRef.el;
        sidebarElement?.classList.add("o_hidden");
        sectionsElement?.classList.add("o_hidden");
        const actionManagerElement = document.querySelector(".o_action_manager");
        actionManagerElement?.style.setProperty("margin-left", "0", "important");
        this.state.isSidebarHidden = true;
        sessionStorage.setItem("isSidebarHidden", "true");
        await this.actionService.doAction({
            type: 'ir.actions.client',
            tag: 'oil_erp_base.homemenus',
            params: {
                apps: this._apps,
            },
        });
    }
});

/** @odoo-module */

import { NavBar } from "@web/webclient/navbar/navbar";
import { computeAppsAndMenuItems } from "@web/webclient/menus/menu_helpers";
import { useBus, useService } from "@web/core/utils/hooks";
import { useRef, onMounted, useState } from "@odoo/owl";
import { patch } from "@web/core/utils/patch";

patch(NavBar.prototype, {
    // To modify the Navbar properties and functions.
    setup() {
        super.setup();
        const isSidebarHidden = sessionStorage.getItem("isSidebarHidden") === "true";
        this.sidebarRef = useRef("sidebar");
        this.menu_sectionsRef = useRef("menu_sections");
        this.busService = this.env.services.bus_service;
        this.menuService = useService("menu");
        this.action = useService("action");
        const menuTree = this.menuService.getMenuAsTree("root");
        const { apps } = computeAppsAndMenuItems(menuTree);
        this._apps = apps;
        this.state = useState({
            activeApp: parseInt(sessionStorage.getItem("activeApp")),
            isSidebarHidden: isSidebarHidden,
        });
        useBus(this.env.bus, "app-selected", (event) => {
            this.onAppClick(event.detail.activeApp);
        });
        onMounted(() => {
            this.applySidebarState();
        });
    },

    get currentAppSections() {
        if (this.state.isSidebarHidden || this.action?.currentController?.action?.tag === 'theme_diwy.homemenus') {
            return [];
        }
        return super.currentAppSections || [];
    },

    getAppIcon(app) {
        if (app && app.webIconData) {
            if (app.webIconData.startsWith("data:image")) {
                return app.webIconData;
            }
            const prefix = app.webIconData.startsWith("P")
                ? "data:image/svg+xml;base64,"
                : "data:image/png;base64,";
            return prefix + app.webIconData.replace(/\s/g, "");
        }
        if (app && app.webIcon && typeof app.webIcon === "string" && app.webIcon.includes(",")) {
            const parts = app.webIcon.split(",");
            if (parts.length === 2) {
                return `/${parts[0]}/${parts[1]}`;
            }
        }
        return false;
    },

    getIconClass(name) {
        if (!name) return "grid-fill";
        const iconMap = {
            'Discuss': 'chat-dots-fill',
            'Calendar': 'calendar-event-fill',
            'Contacts': 'person-lines-fill',
            'Sales': 'cart-fill',
            'Dashboards': 'speedometer',
            'Settings': 'gear-wide-connected',
        };
        return iconMap[name] || 'grid-fill';
    },

    applySidebarState() {
        const sidebarElement = this.sidebarRef.el;
        const sectionsElement = this.menu_sectionsRef.el;
        const actionManagerElement = document.querySelector(".o_action_manager");
        if (sidebarElement) {
            if (this.state.isSidebarHidden) {
                sidebarElement.classList.add("o_hidden");
                if (sectionsElement) sectionsElement.classList.add("o_hidden");
                if (actionManagerElement) {
                    actionManagerElement.style.setProperty("margin-left", "0", "important");
                }
            } else {
                sidebarElement.classList.remove("o_hidden");
                if (sectionsElement) sectionsElement.classList.remove("o_hidden");
                if (actionManagerElement) {
                    actionManagerElement.style.removeProperty("margin-left");
                }
            }
        }
    },

    onAppClick(app) {
        const sidebarElement = this.sidebarRef.el;
        const sectionsElement = this.menu_sectionsRef.el;
        const actionManagerElement = document.querySelector(".o_action_manager");
        sidebarElement?.classList.remove("o_hidden");
        sectionsElement?.classList.remove("o_hidden");
        if (actionManagerElement) {
            actionManagerElement.style.removeProperty("margin-left");
        }
        this.state.isSidebarHidden = false;
        sessionStorage.setItem("isSidebarHidden", "false");
        this.state.activeApp = app.id;
        sessionStorage.setItem("activeApp", this.state.activeApp);
        this.onNavBarDropdownItemSelection(app);
    },

    async _onClickMenusPanel() {
        const sidebarElement = this.sidebarRef.el;
        const sectionsElement = this.menu_sectionsRef.el;
        const actionManagerElement = document.querySelector(".o_action_manager");
        sidebarElement?.classList.add("o_hidden");
        sectionsElement?.classList.add("o_hidden");
        if (actionManagerElement) {
            actionManagerElement.style.setProperty("margin-left", "0", "important");
        }
        this.state.isSidebarHidden = true;
        sessionStorage.setItem("isSidebarHidden", "true");
        await this.action.doAction({
            type: 'ir.actions.client',
            tag: 'theme_diwy.homemenus',
            params: {
                apps: this._apps,
            },
        });
    }
});
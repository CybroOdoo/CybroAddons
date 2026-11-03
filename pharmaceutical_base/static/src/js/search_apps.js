/** @odoo-module */

import { BusPlugin } from "@bus/services/bus_plugin";
import { useLayoutEffect } from "@web/owl2/utils";
import { NavBar } from "@web/webclient/navbar/navbar";
import { computeAppsAndMenuItems } from "@web/webclient/menus/menu_helpers";
import { useBus } from "@web/core/utils/hooks";
import { onMounted, proxy, usePlugin } from "@odoo/owl";
import { patch } from "@web/core/utils/patch";
import { sidebarState } from "@pharmaceutical_base/js/sidebar";

patch(NavBar.prototype, {
    setup() {
        super.setup()
        this.busService = usePlugin(BusPlugin);
        const { apps } = computeAppsAndMenuItems(this.menuService.getMenuAsTree("root"));
        this._apps = apps;

        // The rail itself is a separate main component (js/sidebar.js); we
        // only drive the state it shares with us.
        this.sidebarState = proxy(sidebarState);

        // Always start with the rail visible; it is only hidden by the toggle
        // or the home menu.
        const currentAppId = this.currentApp ? this.currentApp.id : null;
        if (currentAppId) {
            this.sidebarState.activeApp = currentAppId;
        }
        this.sidebarState.isHidden = false;
        sessionStorage.setItem("isSidebarHidden", "false");

        useBus(this.env.bus, "app-selected", (event) => {
            this.onAppClick(event.detail.activeApp);
        });

        useBus(this.env.bus, "HOME-MENU:TOGGLED", () => {
            this.applySidebarState();
        });

        // Watch active app changes to update state & sidebar visibility.
        useLayoutEffect(
            () => {
                if (this.currentApp) {
                    this.sidebarState.activeApp = this.currentApp.id;
                    sessionStorage.setItem("activeApp", this.currentApp.id);
                    this.sidebarState.isHidden = false;
                    sessionStorage.setItem("isSidebarHidden", "false");
                }
                this.applySidebarState();
                this.applyNavbarBrand();
            },
            () => [this.currentApp?.id]
        );

        onMounted(() => {
            this.applySidebarState();
            this.applyNavbarBrand();
        });
    },

    /**
     * Tag the navbar only while the Pharmaceutical ERP app is active, so the
     * brand logo can be swapped to icon2.png for THIS app alone (see
     * backend_theme.scss). Other apps keep their own icon; icon.png stays the
     * app icon in the apps menu / home grid / sidebar tray.
     *
     * Applied from here rather than by extending web.NavBar: the Enterprise
     * navbar is a primary fork of that template, so it never sees the
     * extensions declared by modules loading after web_enterprise — and the
     * brand icon it draws is the only one this rule can act on.
     */
    applyNavbarBrand() {
        const navEl = this.root?.()?.querySelector(".o_main_navbar");
        navEl?.classList.toggle(
            "o_pharma_navbar_brand",
            this.currentApp?.xmlid === "pharmaceutical_base.menu_pharma_quality_root"
        );
    },

    applySidebarState() {
        // The rail hides itself from its own state (plus a CSS rule for the
        // home menu); here we only follow along for the navbar sections.
        const sectionsElement = this.appSubMenus?.();
        const isHomeMenu = this.hm?.hasHomeMenu || document.querySelector(".app_container") !== null;
        sectionsElement?.classList.toggle("o_hidden", this.sidebarState.isHidden || isHomeMenu);
    },

    onAppClick(app) {
        const sectionsElement = this.appSubMenus?.();
        sectionsElement?.classList.remove("o_hidden");
        this.sidebarState.isHidden = false;
        sessionStorage.setItem("isSidebarHidden", "false");
        this.sidebarState.activeApp = app.id;
        sessionStorage.setItem("activeApp", this.sidebarState.activeApp);
        this.onNavBarDropdownItemSelection(app);
    },

    async _onClickMenusPanel() {
        if (this.sidebarState.isHidden) {
            const lastAppId = parseInt(sessionStorage.getItem("activeApp"));
            const lastApp = this._apps.find(app => app.id == lastAppId);
            if (lastApp) {
                this.onAppClick(lastApp);
            } else if (this._apps.length > 0) {
                this.onAppClick(this._apps[0]);
            }
            return;
        }
        const sectionsElement = this.appSubMenus?.();
        sectionsElement?.classList.add("o_hidden");
        this.sidebarState.isHidden = true;
        sessionStorage.setItem("isSidebarHidden", "true");
        if (this.hm) {
            await this.hm.toggle(true);
        } else {
            await this.actionService.doAction({
                type: 'ir.actions.client',
                tag: 'pharmaceutical_base.homemenus',
                params: {
                    apps: this._apps,
                },
            });
        }
    }
})

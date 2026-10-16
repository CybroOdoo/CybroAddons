/** @odoo-module **/

import { NavBar } from "@web/webclient/navbar/navbar";
import { patch } from "@web/core/utils/patch";

/**
 * Patch NavBar to add compatibility shims for the liquid glass sidebar
 * template. V20 already manages sidebar state via `this.state` (a proxy
 * with `isAppMenuSidebarOpened`). We expose thin wrappers so the XML
 * template can use the same names as before without duplicating state.
 */
patch(NavBar.prototype, {
    /**
     * Toggle the built-in V20 app-menu sidebar.
     * Called from the sidebar toggle button injected by apps_sidebar.xml.
     */
    toggleSidebar() {
        this._openAppMenuSidebar();
    },

    /**
     * Close the built-in V20 app-menu sidebar.
     * Called from the close button and overlay click in apps_sidebar.xml.
     */
    closeSidebar() {
        this._closeAppMenuSidebar();
    },

    /**
     * Navigate to the selected app and close the sidebar.
     * @param {Object} app
     */
    onNavBarAppClick(app) {
        this.onNavBarDropdownItemSelection(app);
        this._closeAppMenuSidebar();
    },
});

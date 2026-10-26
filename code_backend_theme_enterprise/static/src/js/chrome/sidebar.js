import { NavBar } from "@web/webclient/navbar/navbar";
import { patch } from "@web/core/utils/patch";

import { onWillUnmount, proxy } from "@odoo/owl";

// Body class driving the sidebar layout (see scss/backend/sidebar.scss)
const SIDEBAR_OPEN_CLASS = "o_cbt_sidebar_open";

patch(NavBar.prototype, {
    setup() {
        super.setup();
        this.cbtSidebar = proxy({ isOpen: false });
        onWillUnmount(() => document.body.classList.remove(SIDEBAR_OPEN_CLASS));
    },

    /**
     * @param {boolean} [isOpen] forced state, toggles when omitted
     */
    toggleCbtSidebar(isOpen = !this.cbtSidebar.isOpen) {
        this.cbtSidebar.isOpen = isOpen;
        document.body.classList.toggle(SIDEBAR_OPEN_CLASS, isOpen);
    },

    /**
     * Open the app in the current tab, but let the browser handle
     * ctrl/cmd/middle clicks so apps can still be opened in a new tab.
     *
     * @param {Object} app
     * @param {MouseEvent} ev
     */
    onCbtSidebarAppClick(app, ev) {
        if (ev.ctrlKey || ev.metaKey || ev.shiftKey || ev.button !== 0) {
            return;
        }
        ev.preventDefault();
        this.toggleCbtSidebar(false);
        this.onNavBarDropdownItemSelection(app);
    },
});

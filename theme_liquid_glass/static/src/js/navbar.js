/** @odoo-module **/

import { NavBar } from "@web/webclient/navbar/navbar";
import { patch } from "@web/core/utils/patch";
import { useState } from "@odoo/owl";

patch(NavBar.prototype, {
    setup() {
        super.setup();
        this.sidebarState = useState({ isOpen: false });
    },
    toggleSidebar() {
        this.sidebarState.isOpen = !this.sidebarState.isOpen;
    },
    closeSidebar() {
        this.sidebarState.isOpen = false;
    },
    onNavBarAppClick(app) {
        this.closeSidebar();
        this.menuService.selectMenu(app);
    }
});

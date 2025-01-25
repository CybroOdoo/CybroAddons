/** @odoo-module */

import { Component, useRef } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { computeAppsAndMenuItems } from "@web/webclient/menus/menu_helpers";
import { useService } from "@web/core/utils/hooks";
import { menuService } from "@web/webclient/menus/menu_service";

export class HomeMenus extends Component {
    static template = "theme_diwy.home_menus";
    setup() {
        this.menu = useService("menu");
        this.sidebarRef = useRef("sidebar");
    }
    onAppClick(app) {
       this.env.bus.trigger('app-selected', { activeApp: app });
       this.menu.selectMenu(app);
    }
}
registry.category("actions").add("theme_diwy.homemenus", HomeMenus);
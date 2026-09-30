/** @odoo-module */

import { Component, useRef } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

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
    }
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
    }
}
registry.category("actions").add("theme_diwy.homemenus", HomeMenus);
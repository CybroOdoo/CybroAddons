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

    getIconClass(appName) {
        if (!appName) return 'app';
        const iconMap = {
            'Discuss': 'chat-dots',
            'Calendar': 'calendar3',
            'Contacts': 'person-lines-fill',
            'CRM': 'graph-up-arrow',
            'Sales': 'cart-fill',
            'Website': 'globe',
            'Inventory': 'box-seam',
            'Purchase': 'bag-check-fill',
            'Manufacturing': 'tools',
            'Repair': 'wrench-adjustable',
            'Accounting': 'calculator',
            'Project': 'journal-check',
            'Employees': 'people-fill',
            'Expenses': 'cash-stack',
            'Appraisal': 'star-fill',
            'Time Off': 'sun-fill',
            'Attendance': 'clock-history',
            'Recruitment': 'person-badge',
            'Knowledge': 'book-half',
            'Planning': 'map-fill',
            'Helpdesk': 'headset',
            'Field Service': 'briefcase-fill',
            'Quality': 'patch-check',
            'Fleet': 'truck',
            'Lunch': 'egg-fried',
            'Events': 'calendar-event',
            'Surveys': 'pencil-square',
            'Subscriptions': 'arrow-repeat',
            'Discuss': 'chat-dots',
            'Documents': 'folder-fill',
            'Sign': 'pencil-fill',
            'Studio': 'layers-fill',
            'Settings': 'gear-fill',
            'Dashboards': 'speedometer2',
            'Point of Sale': 'pc-display-horizontal',
            'Subscriptions': 'arrow-repeat',
            'Maintenance': 'tools',
            'Marketing Automation': 'megaphone-fill',
            'Email Marketing': 'envelope-paper-heart-fill',
        };
        return iconMap[appName] || 'app';
    }

    onAppClick(app) {
        this.env.bus.trigger('app-selected', { activeApp: app });
        this.menu.selectMenu(app);
    }
}
registry.category("actions").add("theme_diwy.homemenus", HomeMenus);
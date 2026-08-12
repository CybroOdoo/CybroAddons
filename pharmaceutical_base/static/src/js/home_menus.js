/** @odoo-module */

import { Component, useRef } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { standardActionServiceProps } from "@web/webclient/actions/action_service";
import { useService } from "@web/core/utils/hooks";

/**
 * App grid shown when the menus panel is opened.
 *
 * Community has no home-menu service, so the navbar patch in search_apps.js
 * falls back to this client action to render the app switcher.
 */
export class HomeMenus extends Component {
    static template = "pharmaceutical_base.home_menus";
    static props = { ...standardActionServiceProps };

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
            'Invoicing': 'calculator',
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
            'Documents': 'folder-fill',
            'Sign': 'pencil-fill',
            'Studio': 'layers-fill',
            'Settings': 'gear-fill',
            'Dashboards': 'speedometer2',
            'Point of Sale': 'pc-display-horizontal',
            'Maintenance': 'tools',
            'Marketing Automation': 'megaphone-fill',
            'Email Marketing': 'envelope-paper-heart-fill',
            'Pharmaceutical ERP': 'capsule',
        };
        return iconMap[appName] || 'app';
    }

    onAppClick(app) {
        this.env.bus.trigger('app-selected', { activeApp: app });
        this.menu.selectMenu(app);
    }
}

// Namespaced to this module's own technical name so it can never collide with
// an action tag belonging to another theme / module.
registry.category("actions").add("pharmaceutical_base.homemenus", HomeMenus);

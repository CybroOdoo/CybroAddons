/** @odoo-module */
/**
 * This file defines the home menu component for Oil ERP.
 */

import { Component, useRef } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

export class OilHomeMenus extends Component {
    static template = "oil_erp_base.home_menus";
    /**
     * Initializes the component and its dependencies.
     */
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
            'Documents': 'folder-fill',
            'Sign': 'pencil-fill',
            'Studio': 'layers-fill',
            'Settings': 'gear-fill',
            'Dashboards': 'speedometer2',
            'Point of Sale': 'pc-display-horizontal',
            'Maintenance': 'tools',
            'Marketing Automation': 'megaphone-fill',
            'Email Marketing': 'envelope-paper-heart-fill',
            'SMS Marketing': 'phone-fill',
            'Live Chat': 'chat-left-text-fill',
            'Link Tracker': 'link-45deg',
            'Apps': 'grid-fill',
            'To-do': 'check2-square',
            // Oil ERP specific
            'Oil ERP': 'droplet-fill',
            'oil_base': 'droplet-fill',
            'E&P Operations': 'geo-alt-fill',
            'Pipeline & Transport': 'signpost-split-fill',
            'Downstream': 'arrow-down-circle-fill',
            'HSE': 'shield-check',
            'Configuration': 'gear-fill',
        };
        return iconMap[appName] || 'app';
    }

    /**
     * Navigates to the selected app.
     * @param {Object} app - The app menu object.
     */
    onAppClick(app) {
        this.env.bus.trigger('app-selected', { activeApp: app });
        this.menu.selectMenu(app);
    }
}
registry.category("actions").add("oil_erp_base.homemenus", OilHomeMenus);

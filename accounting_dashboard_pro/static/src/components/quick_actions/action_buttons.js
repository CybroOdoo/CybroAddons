/** @odoo-module **/

import { Component } from "@odoo/owl";

export class QuickActions extends Component {
    static template = "accounting_dashboard_pro.QuickActions";
    static props = {
        userGroups: Object,
        onAction: Function,
    };
}

export class AlertsFeed extends Component {
    static template = "accounting_dashboard_pro.AlertsFeed";
    static props = {
        alerts: Array,
        onAction: Function,
    };
}

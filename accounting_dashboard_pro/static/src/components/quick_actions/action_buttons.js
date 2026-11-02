/** @odoo-module **/

import { Component, useProps } from "@odoo/owl";

export class QuickActions extends Component {
    static template = "accounting_dashboard_pro.QuickActions";
    props = useProps();
}

export class AlertsFeed extends Component {
    static template = "accounting_dashboard_pro.AlertsFeed";
    props = useProps();
}


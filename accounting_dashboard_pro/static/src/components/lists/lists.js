/** @odoo-module **/

import { Component } from "@odoo/owl";

export class OverdueInvoices extends Component {
    static template = "accounting_dashboard_pro.OverdueInvoices";
    static props = {
        data: Array,
        formatCurrency: Function,
        onItemClick: { type: Function, optional: true },
    };

    onClick(id) {
        if (this.props.onItemClick) this.props.onItemClick(id);
    }
}

export class UpcomingBills extends Component {
    static template = "accounting_dashboard_pro.UpcomingBills";
    static props = {
        data: Array,
        formatCurrency: Function,
        onItemClick: { type: Function, optional: true },
    };

    onClick(id) {
        if (this.props.onItemClick) this.props.onItemClick(id);
    }
}

export class RecentPayments extends Component {
    static template = "accounting_dashboard_pro.RecentPayments";
    static props = {
        data: Array,
        formatCurrency: Function,
        onItemClick: { type: Function, optional: true },
    };
    onClick(id) {
        if (this.props.onItemClick) this.props.onItemClick(id);
    }
}

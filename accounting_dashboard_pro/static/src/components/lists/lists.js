/** @odoo-module **/

import { Component, useProps } from "@odoo/owl";

export class OverdueInvoices extends Component {
    static template = "accounting_dashboard_pro.OverdueInvoices";
    props = useProps();

    onClick(id) {
        if (this.props.onItemClick) this.props.onItemClick(id);
    }
}

export class UpcomingBills extends Component {
    static template = "accounting_dashboard_pro.UpcomingBills";
    props = useProps();

    onClick(id) {
        if (this.props.onItemClick) this.props.onItemClick(id);
    }
}

export class RecentPayments extends Component {
    static template = "accounting_dashboard_pro.RecentPayments";
    props = useProps();

    onClick(item) {
        if (this.props.onItemClick) this.props.onItemClick(item);
    }
}

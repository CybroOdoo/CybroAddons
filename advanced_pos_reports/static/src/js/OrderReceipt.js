/** @odoo-module **/
import { Component, useProps } from "@odoo/owl";
import { usePos } from "@point_of_sale/app/hooks/pos_hook";

export class OrderSummaryReceipt extends Component {
    static template = "advanced_pos_reports.OrderSummaryReceipt";
    props = useProps();

    setup() {
        super.setup();
        this.pos = usePos();
    }

    formatCurrency(amount) {
        return this.pos?.formatCurrency ? this.pos.formatCurrency(amount || 0) : (amount || 0).toFixed(2);
    }
}

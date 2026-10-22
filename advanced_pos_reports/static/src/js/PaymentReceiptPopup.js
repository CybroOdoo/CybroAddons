/** @odoo-module **/
import { Component, signal, useProps } from "@odoo/owl";
import { Dialog } from "@web/core/dialog/dialog";
import { usePos } from "@point_of_sale/app/hooks/pos_hook";
import { printReceipt } from "./utils";

export class PaymentSummaryReceiptScreen extends Component {
    static template = "advanced_pos_reports.PaymentSummaryReceiptScreen";
    static components = { Dialog };
    props = useProps();

    setup() {
        super.setup();
        this.pos = usePos();
        this.receiptRef = signal.ref();
    }

    formatCurrency(amount) {
        return this.pos?.formatCurrency ? this.pos.formatCurrency(amount || 0) : (amount || 0).toFixed(2);
    }

    printSummary() {
        printReceipt(this.receiptRef(), this.props.title, this.pos);
    }
}

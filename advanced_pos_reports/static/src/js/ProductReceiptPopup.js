/** @odoo-module **/
import { Component, signal, useProps } from "@odoo/owl";
import { Dialog } from "@web/core/dialog/dialog";
import { usePos } from "@point_of_sale/app/hooks/pos_hook";
import { printReceipt } from "./utils";

export class ProductSummaryReceiptScreen extends Component {
    static template = "advanced_pos_reports.ProductSummaryReceiptScreen";
    static components = { Dialog };
    props = useProps();

    setup() {
        super.setup();
        this.pos = usePos();
        this.receiptRef = signal.ref();
    }

    printSummary() {
        printReceipt(this.receiptRef(), this.props.title, this.pos);
    }
}

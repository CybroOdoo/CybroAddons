/** @odoo-module **/
import { useService } from "@web/core/utils/hooks";
import { Component, useState, useRef } from "@odoo/owl";
import { Dialog } from "@web/core/dialog/dialog";
import { CategorySummaryReceipt } from "./CategoryReceipt";

    export class CategorySummaryReceiptScreen extends Component {
    // Extending AbstractAwaitablePopup And Adding A Popup
        static template = 'CategorySummaryReceiptScreen';
        static components = { Dialog };
        static props = {
            categories:{ type: Object },
            start_date:{ type: String },
            end_date:{ type: String },
            data:{ type: Object },
            close: "Cancel",
        }
        setup() {
            super.setup();
            this.printer = useService("printer");
        }
        async printSummary() {
            //Method to print the receipt
            await this.printer.print(CategorySummaryReceipt , {data: this.props},
                        { webPrintFallback: true });
        }
    }

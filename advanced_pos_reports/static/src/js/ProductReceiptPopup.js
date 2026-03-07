/** @odoo-module **/
import { useService } from "@web/core/utils/hooks";
import { Component, useState, useRef } from "@odoo/owl";
import { Dialog } from "@web/core/dialog/dialog";
import { ProductSummaryReceipt } from "./ProductReceipt";

    export class ProductSummaryReceiptScreen extends Component {
    // Extending AbstractAwaitablePopup And Adding A Popup
        static template = 'ProductSummaryReceiptScreen';
        static components = { Dialog };
        static props = {
            products:{ type: Object },
            start_date: { type: String },
            end_date: { type: String },
            data:{ type: Object },
            close: "Cancel",
        }
            setup() {
                super.setup();
                this.printer = useService("printer");
            }
            async printSummary() {
                //Method to print the receipt
                await this.printer.print(ProductSummaryReceipt , {data: this.props},
                    { webPrintFallback: true });
            }

        }

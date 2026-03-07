/** @odoo-module **/
import { useService } from "@web/core/utils/hooks";
import { Component, useState, useRef } from "@odoo/owl";
import { Dialog } from "@web/core/dialog/dialog";
import { PaymentSummaryReceipt } from "./PaymentReceipt";

    export class PaymentSummaryReceiptScreen extends Component {
    // Extending AbstractAwaitablePopup And Adding A Popup
        static template = 'PaymentSummaryReceiptScreen';
        static components = { Dialog };
            static props = {
                payment_summary:{ type: Object },
                start_date: { type: String },
                end_date: { type: String },
                is_user:{ type: Boolean },
                data:{ type: Object },
                close: "Cancel",
            }
            setup() {
                super.setup();
                this.printer = useService("printer");
            }
            async printSummary() {
                //Method to print the receipt
                await this.printer.print(PaymentSummaryReceipt , {data: this.props},{ webPrintFallback: true }
                     );
            }
        }

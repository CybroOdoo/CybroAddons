/** @odoo-module **/
import { useService } from "@web/core/utils/hooks";
import { Component, useState, useRef } from "@odoo/owl";
import { Dialog } from "@web/core/dialog/dialog";
import { OrderSummaryReceipt } from "./OrderReceipt";

    export class OrderSummaryReceiptScreen extends Component {
    // Extending AbstractAwaitablePopup And Adding A Popup
        static template = 'OrderSummaryReceiptScreen';
            static components = { Dialog };
            static props = {
                start_date:{ type: String },
                end_date:{ type: String },
                orders:{ type: Object },
                data:{ type: Object },
                close: "Cancel",
            }
            setup() {
                super.setup();
                this.printer = useService("printer");
            }
            async printSummary() {
                    await this.printer.print(OrderSummaryReceipt , {data: this.props},
                        { webPrintFallback: true });

            }
        }

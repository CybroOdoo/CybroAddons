/** @odoo-module **/
import { useService } from "@web/core/utils/hooks";
import { Dialog } from "@web/core/dialog/dialog";
import { Component } from "@odoo/owl";
import { LocationSummaryReceipt } from "./LocationReceipt";

export class LocationSummaryReceiptScreen extends Component {
    // Extending AbstractAwaitablePopup And Adding A Popup
    static template = 'LocationSummaryReceiptScreen';
        static components = { Dialog };
        static props = {
            title:{ type: String },
            locations:{ type: Object },
            data:{ type: Object },
            close: "Cancel",
        }
        setup() {
            super.setup();
                this.printer = useService("printer");
        }
        async printSummary() {
            //Method to print the receipt
            await this.printer.print(LocationSummaryReceipt , {data: this.props},
                { webPrintFallback: true });
        }
    }

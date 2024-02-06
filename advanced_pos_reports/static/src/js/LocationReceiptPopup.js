/** @odoo-module **/
import { useService } from "@web/core/utils/hooks";
import { AbstractAwaitablePopup } from "@point_of_sale/app/popup/abstract_awaitable_popup";
import { LocationSummaryReceipt } from "./LocationReceipt";

export class LocationSummaryReceiptScreen extends AbstractAwaitablePopup {
    // Extending AbstractAwaitablePopup And Adding A Popup
    static template = 'LocationSummaryReceiptScreen';
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

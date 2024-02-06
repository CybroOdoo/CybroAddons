/** @odoo-module **/
import { useService } from "@web/core/utils/hooks";
import { AbstractAwaitablePopup } from "@point_of_sale/app/popup/abstract_awaitable_popup";
import { PaymentSummaryReceipt } from "./PaymentReceipt";

    export class PaymentSummaryReceiptScreen extends PaymentSummaryReceipt {
    // Extending AbstractAwaitablePopup And Adding A Popup
        static template = 'PaymentSummaryReceiptScreen';
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

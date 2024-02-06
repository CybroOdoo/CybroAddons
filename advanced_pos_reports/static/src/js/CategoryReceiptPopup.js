/** @odoo-module **/
import { useService } from "@web/core/utils/hooks";
import { CategorySummaryReceipt } from "./CategoryReceipt";
import { AbstractAwaitablePopup } from "@point_of_sale/app/popup/abstract_awaitable_popup";

    export class CategorySummaryReceiptScreen extends AbstractAwaitablePopup {
    // Extending AbstractAwaitablePopup And Adding A Popup
        static template = 'CategorySummaryReceiptScreen';
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

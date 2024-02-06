/** @odoo-module **/
import { useService } from "@web/core/utils/hooks";
import { AbstractAwaitablePopup } from "@point_of_sale/app/popup/abstract_awaitable_popup";
import { ProductSummaryReceipt } from "./ProductReceipt";

    export class ProductSummaryReceiptScreen extends AbstractAwaitablePopup {
    // Extending AbstractAwaitablePopup And Adding A Popup
        static template = 'ProductSummaryReceiptScreen';
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

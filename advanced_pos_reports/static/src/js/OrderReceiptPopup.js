/** @odoo-module **/
import { useService } from "@web/core/utils/hooks";
import { AbstractAwaitablePopup } from "@point_of_sale/app/popup/abstract_awaitable_popup";
import { OrderSummaryReceipt } from "./OrderReceipt";

    export class OrderSummaryReceiptScreen extends AbstractAwaitablePopup {
    // Extending AbstractAwaitablePopup And Adding A Popup
        static template = 'OrderSummaryReceiptScreen';
            setup() {
                super.setup();
                this.printer = useService("printer");
            }
            async printSummary() {
                    await this.printer.print(OrderSummaryReceipt , {data: this.props},
                        { webPrintFallback: true });

            }
        }


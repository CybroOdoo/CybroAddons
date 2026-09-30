/** @odoo-module **/

/**
 * In Odoo 19, a FeedbackScreen was shown after order completion.
 * This patch auto-advanced past it. In Odoo 17, there is no
 * FeedbackScreen — the equivalent is ReceiptScreen.
 *
 * This patch makes the ReceiptScreen auto-advance to the next
 * order after the receipt is printed, skipping the manual
 * "Next Order" button press.
 */

import { patch } from "@web/core/utils/patch";
import { ReceiptScreen } from "@point_of_sale/app/screens/receipt_screen/receipt_screen";
import { onMounted } from "@odoo/owl";

patch(ReceiptScreen.prototype, {
    setup() {
        super.setup();

        // After the receipt screen mounts, check if a system printer
        // is configured. If so, auto-print and auto-advance.
        onMounted(async () => {
            const printerName =
                this.pos?.config?.system_printer_name || '';
            if (printerName) {
                // Give a brief moment for the receipt to render,
                // then auto-print and move to the next order.
                try {
                    await this.printReceipt();
                } catch (e) {
                    console.warn("Auto-print failed:", e);
                }
                // Auto-advance to the next order after a short delay
                setTimeout(() => {
                    this.orderDone();
                }, 500);
            }
        });
    },
});

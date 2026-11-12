/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { rpc } from "@web/core/network/rpc";
import { WarningDialog } from "@web/core/errors/error_dialogs";
import { useService } from "@web/core/utils/hooks";
import { _t } from "@web/core/l10n/translation";
import { ReceiptScreen } from "@point_of_sale/app/screens/receipt_screen/receipt_screen";

patch(ReceiptScreen.prototype, {
    setup() {
        super.setup();
        this.dialogService = useService("dialog");
    },
    async printReceipt() {
        try {
            const order = this.currentOrder;
            if (!order) {
                return;
            }
            if (!order.isSynced || !order.id) {
                this.dialogService.add(WarningDialog, {
                    title: _t("Warning:"),
                    message: _t("This order is not synced yet. Please wait and try again."),
                });
                return;
            }

            const response = await rpc("/pos/print_receipt_custom", {
                order_id: order.id,
            });

            if (!response.success) {
                this.dialogService.add(WarningDialog, {
                    title: _t("Warning:"),
                    message: response.error,
                });
            }
        } catch (err) {
            this.dialogService.add(WarningDialog, {
                title: _t("Warning:"),
                message: _t("The receipt could not be sent to the printer."),
            });
        }
    },
});

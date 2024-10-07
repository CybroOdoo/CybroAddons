import { patch } from "@web/core/utils/patch";
import { PosStore } from "@point_of_sale/app/store/pos_store";
import { _t } from "@web/core/l10n/translation";
import { AlertDialog } from "@web/core/confirmation_dialog/confirmation_dialog";

patch(PosStore.prototype, {
/**
 * Patched version of the pay method.
 * Ensures that no order line has a quantity of 0 before processing the payment.
 * If any order line has a quantity of 0, it displays an error popup.
 */
    async pay() {
    const currentOrder = this.get_order();
    let quantity = currentOrder.lines.map(line => line.qty);
        if (quantity.includes(0)) {
            this.dialog.add(AlertDialog, {
                title: _t("Zero quantity is not allowed"),
                body: _t(
                    "Only a positive quantity is allowed for confirming the order."
                ),
            });
        } else {
            return super.pay(...arguments);
        }
    },
});

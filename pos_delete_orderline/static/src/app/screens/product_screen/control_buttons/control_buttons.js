import { ControlButtons } from "@point_of_sale/app/screens/product_screen/control_buttons/control_buttons";
import { ConfirmationDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { _t } from "@web/core/l10n/translation";
import { patch } from "@web/core/utils/patch";

patch(ControlButtons.prototype, {
    /**
     * Ask for confirmation, then remove every line of the current order.
     */
    onClickClearLines() {
        const order = this.pos.getOrder();
        if (!order?.lines.length) {
            return;
        }
        this.dialog.add(ConfirmationDialog, {
            title: _t("Clear all lines?"),
            body: _t("Are you sure you want to remove all lines from the cart?"),
            confirmLabel: _t("Clear"),
            confirm: () => {
                // Combo items are removed together with their combo.
                for (const line of order.lines.filter((line) => !line.combo_parent_id)) {
                    order.removeOrderline(line);
                }
            },
            cancel: () => {},
        });
    },
});

import { ConfirmationDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { ControlButtons } from "@point_of_sale/app/screens/product_screen/control_buttons/control_buttons";
import { patch } from "@web/core/utils/patch";
import { _t } from "@web/core/l10n/translation";

// Patching ControlButtons
patch(ControlButtons.prototype, {
    async onClearLines() {
        const order = this.pos.selectedOrder;

        if (!order) {
            this.notification.add(_t("No order selected."), { type: "danger" });
            return;
        }

        const lines = order.lines;

        if (lines.length) {
            this.dialog.add(ConfirmationDialog, {
                title: _t("Clear Orders?"),
                body: _t("Are you sure you want to delete all orders from the cart?"),
                confirm: () => {
                    const linesToRemove = [...lines];
                    linesToRemove.forEach(line => {
                        order.removeOrderline(line);
                    });
                },
                confirmLabel: _t("Clear"),
                cancel: () => {},
                cancelLabel: _t("Cancel"),
            });
        } else {
            this.notification.add(_t("No Items to remove."), {
                type: "danger"
            });
        }
    }
});
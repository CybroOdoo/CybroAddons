/** @odoo-module **/
import { ControlButtons } from "@point_of_sale/app/screens/product_screen/control_buttons/control_buttons";
import { patch } from "@web/core/utils/patch";
import { _t } from "@web/core/l10n/translation";
import { ask } from "@point_of_sale/app/store/make_awaitable_dialog";

patch(ControlButtons.prototype, {
    async onClickClearAll() {
        var order = this.pos.get_order();
        var lines = order.get_orderlines();
        if (lines.length) {
            const confirmed = await ask(this.dialog, {
                title: _t('Clear Orders?'),
                body: _t('Are you sure you want to delete all orders from the cart?'),
            });
            if (confirmed) {
                // We need to slice or clone the lines because removeOrderline modifies the array
                [...lines].filter(line => line.get_product())
                    .forEach(line => order.removeOrderline(line));
            }
        } else {
            this.notification.add(_t("No Items to remove."), 3000);
        }
    }
});

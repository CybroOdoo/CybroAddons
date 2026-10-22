/** @odoo-module **/
import { ControlButtons } from "@point_of_sale/app/screens/product_screen/control_buttons/control_buttons";
import { patch } from "@web/core/utils/patch";
import { _t } from "@web/core/l10n/translation";
import { OrderSummaryPopup } from "./OrderPopup";

patch(ControlButtons.prototype, {
    async onClickOrderSummary() {
        await this.dialog.add(OrderSummaryPopup, {
            title: _t("Order Summary"),
        });
    },
});

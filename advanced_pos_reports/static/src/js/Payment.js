/** @odoo-module **/
import { ControlButtons } from "@point_of_sale/app/screens/product_screen/control_buttons/control_buttons";
import { patch } from "@web/core/utils/patch";
import { _t } from "@web/core/l10n/translation";
import { PaymentSummaryPopup } from "./PaymentPopup";

patch(ControlButtons.prototype, {
    async onClickPaymentSummary() {
        await this.dialog.add(PaymentSummaryPopup, {
            title: _t("Payment Summary"),
        });
    },
});

/** @odoo-module **/

import { PaymentScreen } from "@point_of_sale/app/screens/payment_screen/payment_screen";
import { patch } from "@web/core/utils/patch";
import { _t } from "@web/core/l10n/translation";
import { ErrorPopup } from "@point_of_sale/app/errors/error_popup";

patch(PaymentScreen.prototype, {
    /**
     * Override _isOrderValid to enforce customer selection if laundry services are present.
     */
    async _isOrderValid(isForceValidate) {
        const order = this.currentOrder;
        const hasWashing = order.get_orderlines().some(line => line.get_washing_type());

        if (hasWashing && !order.get_partner()) {
            this.dialog.add(ErrorPopup, {
                title: _t("Customer Required"),
                body: _t("Please select a customer before validating an order with laundry services."),
            });
            return false;
        }

        return super._isOrderValid(...arguments);
    }
});

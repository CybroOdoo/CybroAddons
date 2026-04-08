/** @odoo-module */
import { patch } from "@web/core/utils/patch";
import { ActionpadWidget } from "@point_of_sale/app/screens/product_screen/action_pad/action_pad";

/**
 * Patch to extend the ActionpadWidget behavior for POS.
 * Specifically, this adds logic to disable the payment button
 * based on the currently logged-in cashier's configuration.
 */
patch(ActionpadWidget.prototype, {
    /**
     * Determines whether the payment button should be disabled
     * for the current POS cashier.
     *
     * @returns {boolean} True if `disable_payment` is enabled for the current cashier, otherwise false.
     */
    disable_payment() {
        return !!this.pos.cashier?.disable_payment;
    }
});

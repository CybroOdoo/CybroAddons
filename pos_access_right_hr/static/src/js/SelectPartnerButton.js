/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { SelectPartnerButton } from "@point_of_sale/app/screens/product_screen/control_buttons/select_partner_button/select_partner_button";

/**
 * Patch to extend the SelectPartnerButton functionality.
 * Disables the customer selection button based on cashier permissions.
 */
patch(SelectPartnerButton.prototype, {
    /**
     * Determines whether the customer selection button should be disabled.
     *
     * @returns {boolean} True if the cashier is restricted from selecting customers; otherwise, false.
     */
    disable_customer() {
        return !!this.pos.cashier?.disable_customer;
    },
});

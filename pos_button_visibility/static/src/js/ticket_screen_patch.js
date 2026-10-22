/** @odoo-module */
/**
 * Patch: TicketScreen (POS)
 *
 * Restricts the Refund action on TicketScreen based on the logged-in
 * cashier's button visibility settings and POS configuration.
 */
import { TicketScreen } from "@point_of_sale/app/screens/ticket_screen/ticket_screen";
import { patch } from "@web/core/utils/patch";
import { isButtonRestricted } from "@pos_button_visibility/js/utils";

patch(TicketScreen.prototype, {
    get isRefundRestricted() {
        return isButtonRestricted(this.pos, "Refund");
    },
    get buttonClasses() {
        if (this.isRefundRestricted) {
            return "btn-secondary disabled";
        }
        return super.buttonClasses;
    },
    async onClickRefund() {
        if (this.isRefundRestricted) {
            return;
        }
        return super.onClickRefund(...arguments);
    },
});

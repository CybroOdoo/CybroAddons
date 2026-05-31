/** @odoo-module **/

import { AlertDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { patch } from "@web/core/utils/patch";
import { PaymentScreen } from "@point_of_sale/app/screens/payment_screen/payment_screen";
import { _t } from "@web/core/l10n/translation";
import { useRef } from "@odoo/owl";

/**
 * Patch for PaymentScreen to handle partial payment validation and UI logic.
 */
patch(PaymentScreen.prototype, {
    /**
     * @override
     */
    setup() {
        super.setup(...arguments);
        this.root = useRef('PartialPayment');
    },

    /**
     * Toggle the Partial Payment state for the current order.
     * Checks if a partner is selected before enabling.
     */
    PartialPaymentButton() {
        if (!this.currentOrder.get_partner()) {
            this.env.services.dialog.add(AlertDialog, {
                title: _t("No partner selected"),
                body: _t("Please select partner."),
            });
            return false;
        }

        if (this.currentOrder.is_partial_payment === true) {
            this.currentOrder.is_partial_payment = false;
            if (this.root.el) {
                this.root.el.classList.add('disabled');
            }
        } else {
            if (this.currentOrder.get_partner()) {
                this.currentOrder.is_partial_payment = true;
                if (this.root.el) {
                    this.root.el.classList.remove('disabled');
                }
            }
        }
    },

    /**
     * @override
     * Handle the validation logic. If it is a partial payment,
     * bypass the fully paid check while maintaining other standard validations.
     * @param {Boolean} isForceValidate
     */
    async validateOrder(isForceValidate) {
        if (!this.currentOrder.is_partial_payment) {
            await super.validateOrder(isForceValidate);
        } else {
            if (this.currentOrder.get_partner()?.prevent_partial_payment) {
                this.env.services.dialog.add(AlertDialog, {
                    title: _t("Partial Payment Not Allowed"),
                    body: _t("The Customer is not allowed to make Partial Payments."),
                });
                return false;
            }
            if (!this.currentOrder.to_invoice) {
                this.env.services.dialog.add(AlertDialog, {
                    title: _t("Cannot Validate This Order"),
                    body: _t("You need to Set Invoice for Validating Partial Payments."),
                });
                return false;
            }
            if (!this.currentOrder.get_due()) {
                this.env.services.dialog.add(AlertDialog, {
                    title: _t("Cannot Validate This Order"),
                    body: _t("The Amount is Fully Paid. Disable Partial Payment to Validate this Order."),
                });
                return false;
            }

            const originalIsPaid = this.currentOrder.is_paid;
            this.currentOrder.is_paid = () => true;
            try {
                await super.validateOrder(isForceValidate);
            } finally {
                this.currentOrder.is_paid = originalIsPaid;
            }
        }
    }
});

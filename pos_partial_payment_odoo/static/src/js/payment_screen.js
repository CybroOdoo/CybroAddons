/** @odoo-module **/
import OrderPaymentValidation from "@point_of_sale/app/utils/order_payment_validation";
import { AlertDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { patch } from "@web/core/utils/patch";
import { PaymentScreen } from "@point_of_sale/app/screens/payment_screen/payment_screen";
import { _t } from "@web/core/l10n/translation";
import { useRef } from "@odoo/owl";

patch(PaymentScreen.prototype, {
    setup() {
        super.setup(...arguments);
        this.root = useRef('PartialPayment');
    },

    // Toggle Partial Payment flag and enable/disable related UI
    PartialPaymentButton() {
        if (!this.currentOrder.getPartner()) {
            this.env.services.dialog.add(AlertDialog, {
                title: _t("No partner selected"),
                body: _t("Please select partner."),
            });
            return false;
        }
        if (this.currentOrder.remainingDue == 0) {
                this.env.services.dialog.add(AlertDialog, {
                    title: _t("Cannot Validate This Order"),
                    body: _t("The Amount is Fully Paid. Disable Partial Payment to Validate this Order."),
                });
                return false;
            }


        if (this.currentOrder.is_partial_payment === true) {
            this.currentOrder.is_partial_payment = false;
            if (this.root.el) {
                this.root.el.classList.add('disabled');
            }
        } else {
            if (this.currentOrder.getPartner()) {
                this.currentOrder.is_partial_payment = true;
                if (this.root.el) {
                    this.root.el.classList.remove('disabled');
                }
            }
        }
    },
});
    // Override validateOrder to handle partial payment validation logic

patch(OrderPaymentValidation.prototype, {
    async validateOrder(isForceValidate) {
        if (!this.order.is_partial_payment) {
            // Normal flow
            await super.validateOrder(isForceValidate);
        } else {
            // Partial payment validations

            if (this.order.getPartner()?.prevent_partial_payment) {
                this.pos.dialog.add(AlertDialog, {
                    title: _t("Partial Payment Not Allowed"),
                    body: _t("The Customer is not allowed to make Partial Payments."),
                });
                return false;
            }

            if (!this.order.to_invoice) {
                this.pos.dialog.add(AlertDialog, {
                    title: _t("Cannot Validate This Order"),
                    body: _t("You need to Set Invoice for Validating Partial Payments."),
                });
                return false;
            }

            // Mark the order as partial payment and finalize
            this.order.is_paid = () => true;
            this.order.is_partial_payment = true;
            const nextPage = this.nextPage;
            this.pos.navigate(nextPage.page, nextPage.params);
            this.isOrderValid(isForceValidate);
            await this.finalizeValidation();
        }
    }
});

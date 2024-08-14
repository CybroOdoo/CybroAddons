/** @odoo-module **/

import { ErrorPopup } from "@point_of_sale/app/errors/popups/error_popup";
import { patch } from "@web/core/utils/patch";
import { PaymentScreen } from "@point_of_sale/app/screens/payment_screen/payment_screen";
import { _t } from "@web/core/l10n/translation";
import { useRef } from "@odoo/owl";

// patch the PaymentScreen class
patch(PaymentScreen.prototype, {
        setup() {
            super.setup(...arguments);
            this.root = useRef('PartialPayment');
        },
    //Partial Payment Button Functionality
    PartialPaymentButton() {
        if (!this.currentOrder.get_partner()) {
                this.env.services.popup.add(ErrorPopup, {
                        title: _t("No partner selected"),
                        body: _t("Please select partner."),
                });
            return false;
        };
        if (this.currentOrder.partial_payment === true) {
            this.currentOrder.partial_payment = false;
            var validate = this.root.el
            validate.classList.add('disabled');
        } else if(this.currentOrder.get_partner()){
            this.currentOrder.partial_payment = true;
            var validate = this.root.el
            validate.classList.remove('disabled');
        }
    },
    //Validate Payment Button Functionality
    async validateOrder(isForceValidate) {
        if (!this.currentOrder.partial_payment){
        await super.validateOrder(isForceValidate);
            }
        else{
        if (this.currentOrder.get_partner().prevent_partial_payment ) {
                this.env.services.popup.add(ErrorPopup, {
                        title: _t("Partial Payment Not Allowed"),
                        body: _t("The Customer is not allowed to make Partial Payments."),
                });
            return false;
        };
        //If Invoice not Selected Show Error
        if(!this.currentOrder.to_invoice){
            this.env.services.popup.add(ErrorPopup, {
                title: _t("Cannot Validate This Order"),
                body: _t("You need to Set Invoice for Validating Partial Payments."),
            });
        return false;
        };
        //If amount is fully paid show error
        if(!this.currentOrder.get_due()){
            this.env.services.popup.add(ErrorPopup, {
                title: _t("Cannot Validate This Order"),
                body: _t("The Amount is Fully Paid Disable Partial Payment to Validate this Order."),
            });
            return false;
        };
        this.currentOrder.is_partial_payment = true
        this._isOrderValid(isForceValidate)
        await this._finalizeValidation();
        }
    }
});

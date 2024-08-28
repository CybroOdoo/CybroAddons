/** @odoo-module */
import { _t } from "@web/core/l10n/translation";
import paymentForm from '@payment/js/payment_form';
import { Dialog } from "@web/core/dialog/dialog";
import { jsonrpc } from "@web/core/network/rpc_service";

// Payment process with cybersource
paymentForm.include({
    _processRedirectFlow(providerCode, paymentOptionId, paymentMethodCode, processingValues) {
        if (providerCode !== 'cybersource') {
            return this._super(...arguments);
        }
        var customerInputNumber = parseInt($('#customer_input_number').val());
        const customerInputName = $('#customer_input_name').val();
        const expMonth = $('#customer_input_month').val();
        const expYear = $('#customer_input_year').val();
        var self = this;
        // Display error if card number is null
        if(customerInputNumber == "") {
            this._displayErrorDialog(
                _t("Server Error"),
                _t("We are not able to process your payment Card Number not entered")
            );
        }
        // Display error if card is expired
        else if(expYear <= 2022) {
            var self = this;
            self._displayErrorDialog(
                _t("Server Error"),
                _t("We are not able to process your payment. Expiry year is not valid")
            );
        }
        // Display error if card expiry month is not a valid one
        else if(expMonth == 0) {
            var self = this;
            self._displayErrorDialog(
                _t("Server Error"),
                _t("We are not able to process your payment. Expiry month not valid.")
            );
        }
        // If details are correct process the payment
        else {
            return jsonrpc(
                '/payment/cybersource/simulate_payment',
                {
                    'reference': processingValues.reference,
                    'customer_input': {
                        'exp_year': expYear,
                        'exp_month': expMonth,
                        'name':customerInputName,
                        'card_num':customerInputNumber,
                    },
                    'values':{
                        'amount': processingValues.amount,
                        'currency': processingValues.currency_id,
                        'partner': processingValues.partner_id,
                        'order': processingValues.reference
                    },
                },
           ).then(() => window.location = '/payment/status');
        }
    },
})

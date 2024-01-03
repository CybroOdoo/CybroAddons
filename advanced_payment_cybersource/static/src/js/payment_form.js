/** @odoo-module */

import core from "web.core";
import checkoutForm from 'payment.checkout_form';
import manageForm from 'payment.manage_form';
const _t = core._t;
//Payment process with cybersource
const acceptCyberSourceMixin = {
    _processRedirectPayment: function (code, providerId, processingValues) {
        if (code !== 'cybersource') {
            return this._super(...arguments);
        }
        var customerInputNumber = parseInt($('#customer_input_number').val());
        const customerInputName = $('#customer_input_name').val();
        const expMonth = $('#customer_input_month').val();
        const expYear = $('#customer_input_year').val();
        var self = this;
        if(customerInputNumber == "")
        {
            self._displayError(
                _t("Server Error"),
                _t("We are not able to process your payment Card Number not entered")
            );
        }
        else if(expYear <= 2022)
        {
            self._displayError(
                _t("Server Error"),
                _t("We are not able to process your payment Expiry year is not valid")
            );
        }
        else if(expMonth == 0)
        {
            self._displayError(
                _t("Server Error"),
                _t("We are not able to process your payment Expiry month not valid.")
            );
        }
        else {
           return this._rpc({
              route: '/payment/cybersource/simulate_payment',
              params: {
                  'reference': processingValues.reference,
                  'customer_input': {'exp_year': expYear,
                                        'exp_month': expMonth,
                                        'name':customerInputName,
                                        'card_num':customerInputNumber,
                                     },
                  'values':{'amount': processingValues.amount,
                               'currency': processingValues.currency_id,
                               'partner': processingValues.partner_id,
                               'order': processingValues.reference
                  },
              },
           }).then(() => window.location = '/payment/status');
        }
    },
};
checkoutForm.include(acceptCyberSourceMixin);
manageForm.include(acceptCyberSourceMixin);


odoo.define('safer_pay.payment_form', require => {
    'use strict';
    const checkoutForm = require('payment.checkout_form');
    const manageForm = require('payment.manage_form');

    const paymentProvider = {
        /**
           For redirecting the page to corresponding url after processing the
           credentials
        **/
        _processRedirectPayment: function (code, acquirerId, processingValues) {
            if (code !== 'saferpay') {
                return this._super(...arguments);
            }
            var response =  this._rpc({
                route: '/saferpay/payment',
                params: {
                    'reference': processingValues,
                },
            }).then((response) => {
               if(response == false){
                    this._displayError(("Please provide proper credential."));
                    return
                }
                else{
                    window.location = response
                }
            });
        },
    };
    checkoutForm.include(paymentProvider);
    manageForm.include(paymentProvider);
});

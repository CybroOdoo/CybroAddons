odoo.define('safer_pay.payment_form', require => {
    'use strict';
    const checkoutForm = require('payment.checkout_form');
    const manageForm = require('payment.manage_form');
    var Dialog = require('web.Dialog');

    const paymentProvider = {
           /**
           Redirect to url of safer pay page after processing the values
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
                    Dialog.alert(
                       this,
                       "Please provide proper credential",{
                           onForceClose: function(){
                            window.location = '/shop/payment'
                           },
                           confirm_callback: function(){
                                window.location = '/shop/payment'
                           }
                       }
                    );
                    return
                }
                else{
                      window.open(response)
                }
            });
        },
    };
    checkoutForm.include(paymentProvider);
    manageForm.include(paymentProvider);
});

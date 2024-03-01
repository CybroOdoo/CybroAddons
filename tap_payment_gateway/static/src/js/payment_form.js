odoo.define('tap_payment_gateway.payment_form', function (require) {
    "use strict";
     /**
     * Tap Payment Gateway Payment Form Module
     *
     * This module extends the payment checkout form and payment manage form
     * for processing payments with the Tap payment provider.
     */
    const core = require('web.core');
    const ajax = require('web.ajax');
    const _t = core._t;
    const checkoutForm = require('payment.checkout_form');
    const manageForm = require('payment.manage_form');
    const tapMixin = {
    /**
         * Process Redirect Payment for Tap Provider
         *
         * @param {string} provider - The payment provider.
         * @param {string} acquirerId - The acquirer ID.
         * @param {Object} processingValues - The processing values.
         * @returns {Promise} A promise that resolves when the payment is processed.
         */
        _processRedirectPayment: function (provider, acquirerId, processingValues) {
            if (provider !== 'tap') {
                return this._super(...arguments);
            }
            const self = this;
            return ajax.jsonRpc("/tap", 'call', {
                card_number: self.$('#cc_number').val(),
                exp_month: self.$('#cc_expiry_month').val(),
                exp_year: self.$('#cc_expiry_year').val(),
                cvc: self.$('#cc_cvv').val(),
                cardholder_name: self.$('#cc_holder_name').val(),
                total_amount: self.txContext.amount,
                reference: processingValues['reference']
            }).then(token => {
                if (token) {
                    ajax.jsonRpc("/payment/tap/process_payment", 'call', {
                        payload: token,
                        data: processingValues
                    }).then(response => {
                        if (response.success) {
                            const payment_url = response.payment_url;
                            window.location.href = payment_url;
                        } else {
                            const error_message = response.error_message || 'Payment processing failed';
                        }
                    });
                }
            });
        },
         _prepareInlineForm: function (provider, paymentOptionId, flow) {
            if (provider !== 'tap') {
                return this._super(...arguments);
            }
            if (flow === 'token') {
                return Promise.resolve();
            }
        },
    };
    checkoutForm.include(tapMixin);
    manageForm.include(tapMixin);
});

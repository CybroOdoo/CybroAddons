/** @odoo-module */
import paymentForm from '@payment/js/payment_form';
import { jsonrpc } from "@web/core/network/rpc_service";
    const paymentCreditPayMixin = {
        //--------------------------------------------------------------------------
        // Private
        //--------------------------------------------------------------------------

        /**
         * Simulate a feedback from a payment provider and redirect the customer to the status page.
         *
         * @override method from payment.payment_form_mixin
         * @private
         * @param {string} code - The code of the provider
         * @param {number} providerId - The id of the provider handling the transaction
         * @param {object} processingValues - The processing values of the transaction
         * @return {Promise}
         */

        _processRedirectFlow: function (code, providerId, paymentMethodCode, processingValues) {
            if (code !== 'credit_pay') {
                return this._super(...arguments);
            }
            const customerInput = document.getElementById('customer_input').value;
            const simulatedPaymentState = document.getElementById('simulated_payment_state').value;
            jsonrpc('/payment/credit_pay/simulate_payment',{
                args: {
                    'reference': processingValues.reference,
                    'payment_details': customerInput,
                    'simulated_state': simulatedPaymentState,
                },
            }).then(() => {
                window.location = '/payment/status';
            });
        },

        /**
         * Prepare the inline form of Demo for direct payment.
         *
         * @override method from payment.payment_form_mixin
         * @private
         * @param {string} code - The code of the selected payment option's provider
         * @param {integer} paymentOptionId - The id of the selected payment option
         * @param {string} flow - The online payment flow of the selected payment option
         * @return {Promise}
         */
        _prepareInlineForm: function (code, paymentOptionId, flow) {
            if (code !== 'credit_pay') {
                return this._super(...arguments);
            } else if (flow === 'token') {
                return Promise.resolve();
            }
            this._setPaymentFlow('direct');
            return Promise.resolve()
        },
    };
    paymentForm.include(paymentCreditPayMixin);

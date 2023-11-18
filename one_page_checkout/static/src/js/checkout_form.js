odoo.define('one_page_checkout.checkout_form', require => {
    'use strict';

    const publicWidget = require('web.public.widget');
    const paymentFormMixin = require('payment.payment_form_mixin');
    /**
     * OnePagePaymentForm widget. Enhances the payment form by adding a click
     * event listener that submits the extra_info_form along with the payment form.
     *
     * @extends paymentFormMixin
     */
    publicWidget.registry.OnePagePaymentForm = publicWidget.Widget.extend(paymentFormMixin, {
        selector: 'form[name="o_payment_checkout"]',
        events: Object.assign({}, publicWidget.Widget.prototype.events, {
                'click button[name="o_payment_submit_button"]': '_onClickPayment',
            }),
        init: function () {
            this._super(...arguments);
        },
        /**
         * OnePagePaymentForm widget. Enhances the payment form by adding a click
         * event listener that submits the extra_info_form along with the payment form.
         *
         * @extends paymentFormMixin
         */
        _onClickPayment: async function (ev) {
            $('#extra_info_form').submit()

        },
    });
    return publicWidget.registry.OnePagePaymentForm;
});

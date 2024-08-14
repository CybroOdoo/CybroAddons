/** @odoo-module **/
import { _t } from '@web/core/l10n/translation';
import { Component } from '@odoo/owl';
import PaymentForm from '@payment/js/payment_form';


PaymentForm.include({
    events: Object.assign({}, PaymentForm.prototype.events || {}, {
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
        this.$el('#extra_info_form').submit()
    },
});


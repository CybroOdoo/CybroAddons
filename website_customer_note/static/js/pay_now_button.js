odoo.define('website_customer_note.payment_screen', require => {
    'use strict';

    // Import required modules
    const publicWidget = require('web.public.widget');
    const paymentFormMixin = require('payment.payment_form_mixin');

    // Define PaymentFormCustomerNote widget
    publicWidget.registry.PaymentFormCustomerNote = publicWidget.Widget.extend(paymentFormMixin, {
        selector: 'form[name="o_payment_checkout"]',
        events: Object.assign({}, publicWidget.Widget.prototype.events, {
            'click button[name="o_payment_submit_button"]': '_onClickPay',
        }),

        // Initialize widget
        init: function () {
            this._super(...arguments);
        },

        // Handle click event on payment submit button
        _onClickPay: async function (ev) {
            // Get the value of the customer_note field
            const customerNote = $('#customer_note').val();

            // Get the current sale order ID from the form data
            const saleOrderId = $('input[name="sale_order_id"]').val();

            // Check if sale order ID is found
            if (!saleOrderId) {
                console.error("Sale Order ID not found in form data.");
                return;
            }

            // Make a RPC call to the server-side method write_customer_note
            const result = await this._rpc({
                model: 'sale.order',
                method: 'write_customer_note',
                args: [parseInt(saleOrderId), customerNote],
            });

            // Reload the page to reflect changes
            location.reload();
        },
    });

    return publicWidget.registry.PaymentFormCustomerNote;
});

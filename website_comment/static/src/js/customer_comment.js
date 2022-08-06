odoo.define('website_comment.payment_extension', function(require) {
    "use strict";

    var ajax = require('web.ajax');

    var publicWidget = require('web.public.widget');

    const paymentFormMixin = require('payment.payment_form_mixin');


    publicWidget.registry.Paymentclick = publicWidget.Widget.extend({
        selector: 'form[name="o_payment_checkout"]',
        events: {
                'click button[name="o_payment_submit_button"]': '_onClickPay',
        },

        _onClickPay: function(ev) {
            var comment = $('#comment').val();
            ajax.jsonRpc('/shop/customer_comment/', 'call', {
                'comment': comment
            })
        }
        });

        return publicWidget.registry.Paymentclick;
    });
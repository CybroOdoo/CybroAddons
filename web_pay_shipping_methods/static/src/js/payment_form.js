odoo.define('web_pay_shipping_methods.payment_form_inherit', function (require) {
"use strict";

    var PaymentForm = require('payment.payment_form');
    var ajax = require('web.ajax');
    var Dialog = require('web.Dialog');
    var core = require('web.core');
    var qweb = core.qweb;
    var _t = core._t;

    PaymentForm.include({
        /**
        * Function executes when payment provider is clicked and it checks if there are
        * any shipping methods specified inside the payment provider to list them
        * in website after the payment provider.
        *
        * @param {Object} ev Contains details about the payment provider.
        */
        radioClickEvent: async function (ev) {
            await this._super(...arguments);
            var self = this;
            this.dialogShown = false;
            var delivery_method_div = this.$el[0]?.parentElement?.nextElementSibling;
            var check_carrier = false
            const pay_option_input = ev.currentTarget?.childNodes[1]?.children[0];
            await ajax.jsonRpc('/get/shipping/methods', 'call', {
                'args' : pay_option_input.dataset.acquirerId
            })
            .then(function (data) {
                var delivery_select_text = delivery_method_div.children[0];
                var delivery_method_card = delivery_method_div.children[1];
                if(delivery_method_card){
                    var delivery_methods = delivery_method_card.children[0].children;
                    for(var delivery_index = 0; delivery_index < delivery_methods.length; delivery_index++){
                        if(data == false){
                            delivery_methods[delivery_index].style.display = 'none';
                            delivery_select_text.style.display = 'none';
                        }
                        for(let data_index = 0; data_index<data.length; data_index++){
                            if(data[data_index] == delivery_methods[delivery_index].querySelector('input').value){
                                delivery_methods[delivery_index].style.display = '';
                                delivery_select_text.style.display = '';
                                if (check_carrier == false){
                                    delivery_methods[delivery_index].click();
                                    check_carrier = true;
                                }
                                break;
                            }
                            delivery_methods[delivery_index].style.display = 'none';
                        }
                    }
                }
            });
            if(check_carrier == false){
                if (!this.dialogShown) {
                    this.dialogShown = true;
                    var dialog = new Dialog(this, {
                        size: 'medium',
                        title: _t('No Shipping Methods'),
                        $content: "<p>" + "No shipping methods available for this payment option" + "</p>" ,
                        buttons: [
                            {
                                text: _t("Close"),
                                close: true,
                            },
                        ],
                    }).open();
                }
                pay_option_input.checked = false;
            }
        },
    });
});

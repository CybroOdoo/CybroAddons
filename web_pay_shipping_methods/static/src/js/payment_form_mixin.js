/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
const paymentFormMixin = require('payment.payment_form_mixin');
import ajax from 'web.ajax';
import core from 'web.core';
const _t = core._t;
const QWeb = core.qweb;

patch(paymentFormMixin, 'PaymentFormMixinInherit', {
    /**
    * Function executes when payment provider is clicked and it checks if there are
    * any shipping methods specified inside the payment provider to list them
    * in website after the payment provider.
    *
    * @param {Object} ev Contains details about the payment provider.
    */
    async _onClickPaymentOption(ev) {
        await this._super(...arguments);
        var self = this;
        var delivery_method_card = this.$el.find('#delivery_method');
        var check_carrier = false
        const pay_option_input = ev.currentTarget.childNodes[1].children[0];
        await ajax.jsonRpc('/get/shipping/methods', 'call', {
            'args' : pay_option_input.dataset.paymentOptionId
        })
        .then(function (data) {
            var delivery_select_text = self.$el.find("#delivery_text")
            if(delivery_method_card){
                var delivery_methods = delivery_method_card[0].children[0].children;
                for(var delivery_index = 0; delivery_index < delivery_methods.length; delivery_index++){
                    if(data == false){
                        delivery_methods[delivery_index].style.display = 'none';
                        delivery_select_text[0].style.display = 'none';
                    }
                    for(let data_index = 0; data_index<data.length; data_index++){
                        if(data[data_index] == delivery_methods[delivery_index].children[0].value){
                            delivery_methods[delivery_index].style.display = '';
                            delivery_select_text[0].style.display = '';
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
            pay_option_input.checked = false;
            this._displayError(
                    _t("No Shipping Methods"),
                    _t("No shipping methods available for this payment option")
            );
        }
    },
});

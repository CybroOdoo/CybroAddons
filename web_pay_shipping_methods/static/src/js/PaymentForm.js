/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import PaymentForm from '@payment/js/payment_form';
console.log(PaymentForm)
PaymentForm.include({
    /**
    * Function executes when payment provider is clicked and it checks if there are
    * any shipping methods specified inside the payment provider to list them
    * in website after the payment provider.
    *
    * @param {Object} ev Contains details about the payment provider.
    */
    async _selectPaymentOption(ev) {
        this._super(...arguments);
        $('.list-group-item.o_delivery_carrier_select').each(function(key,carrier) {
            $(this).find('input[type="radio"]').prop('checked', false);
            $(this).addClass('d-none');
        });
        let providerId = ev.target.dataset['providerId']
        let carriers = await this.orm.read("payment.provider",[parseInt(providerId)],['delivery_carrier_ids'])
        if(carriers[0].delivery_carrier_ids.length > 0){
            carriers[0].delivery_carrier_ids.forEach((id)=>{
                if(id){
                    let deliveryMethod = '#delivery_method_'+id
                    $(deliveryMethod)[0].classList.remove('d-none')
                    $('#NoShippingMethod')[0].classList.remove('d-none')
                }
            })
        }else{
            $('#NoShippingMethod')[0].classList.remove('d-none')
        }
    },
});

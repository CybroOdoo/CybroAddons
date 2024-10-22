/** @odoo-module **/

import { PaymentScreen } from "@point_of_sale/app/screens/payment_screen/payment_screen";
import { patch } from "@web/core/utils/patch";
import { _t } from "@web/core/l10n/translation";
import { TextInputPopup } from "@point_of_sale/app/utils/input_popups/text_input_popup";
import { useService } from "@web/core/utils/hooks";
import { useState } from "@odoo/owl";
let order_list = []
patch(PaymentScreen.prototype, {
    setup() {
        super.setup();
        this.popup = useService("popup");
        this.state = useState({
            code: false,
        });
    },
   async IsPaymentReferenceButton() {
        let { confirmed, payload: code } = await this.popup.add(TextInputPopup, {
            title: _t("Payment Reference"),
            startingValue: "",
            placeholder: _t('eg:PREF16'),
        });
        if (confirmed) {
            code = code.trim();
            if (code !== '') {
                if (this.env.services.pos.user_payment_reference.length > 0){
                    this.env.services.pos.user_payment_reference[this.env.services.pos.user_payment_reference.length-1].user_payment_reference = code
                    this.state.code = code
                    order_list.push({'name':this.env.services.pos.get_order().name,
                                     'code': code})
                    this.order_list = order_list
                }
                else if (this.env.services.pos.user_payment_reference.length == 0){
                    this.env.services.pos.user_payment_reference.user_payment_reference = code
                    order_list.push({'name':this.env.services.pos.get_order().name,
                                     'code': code})
                    this.order_list = order_list
                }
            }
        }
   },

   async _finalizeValidation() {
        await super._finalizeValidation(...arguments);
        await this.env.services.rpc("/web/dataset/call_kw/pos.payment/get_payment_reference", {
            model: 'pos.payment',
            method: 'get_payment_reference',
            args: [[],order_list],
            kwargs: {}
        });
   }
});

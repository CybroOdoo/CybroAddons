/** @odoo-module **/

import { PaymentScreen } from "@point_of_sale/app/screens/payment_screen/payment_screen";
import { patch } from "@web/core/utils/patch";
import { _t } from "@web/core/l10n/translation";
import { TextInputPopup } from "@point_of_sale/app/utils/input_popups/text_input_popup";
import { useState } from "@odoo/owl";

let order_list = []

patch(PaymentScreen.prototype, {
    setup() {
        super.setup();
        this.state = useState({
            code: false,
        });
    },

    async IsPaymentReferenceButton() {
    // Opens a popup to capture and assign a payment reference to the current POS order.
        let { confirmed, payload: code } = await this.dialog.add(TextInputPopup, {
            title: _t("Payment Reference"),
            startingValue: "",
            placeholder: _t('eg:PREF16'),
            getPayload: async (code) => {
                code = code.trim();
                if (code !== '') {
                    // Store as a temporary reference in state
                    this.state.code = code;
                    const order = this.pos.get_order();
                    order_list.push({ 'name': order.name, 'code': code });
                    order.set_payment_reference(code.trim());
                    this.order_list = order_list;
                }
            },
        });
    },

    async _finalizeValidation() {
    // Finalizes order validation and syncs payment references with the backend.
        await super._finalizeValidation(...arguments);
        // Use Odoo 18's data service call method
        if (order_list.length > 0) {
            await this.pos.data.call('pos.payment', 'get_payment_reference', [[], order_list]);
        }
    }
});

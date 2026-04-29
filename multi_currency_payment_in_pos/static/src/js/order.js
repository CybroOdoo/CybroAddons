/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { Order } from "@point_of_sale/app/models/order";

patch(Order, {
    export_as_JSON() {
        const result = super.export_as_JSON();

        // Inject converted currency into payment lines
        for (const payment of result.payment_lines) {
            const localPayment = this.payments.find(p => p.cid === payment.cid);
            if (localPayment?.converted_currency) {
                payment.converted_currency_amount = localPayment.converted_currency.amount;
                payment.converted_currency_name = localPayment.converted_currency.name;
                payment.converted_currency_symbol = localPayment.converted_currency.symbol;
            }
        }

        return result;
    }
});

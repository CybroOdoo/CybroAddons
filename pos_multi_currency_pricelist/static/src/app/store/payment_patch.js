/** @odoo-module **/

import { PosPayment } from "@point_of_sale/app/models/pos_payment";
import { patch } from "@web/core/utils/patch";
import {
    convertOrderAmountToBaseCurrency,
    isMultiCurrencyPricelistEnabled,
} from "@pos_multi_currency_pricelist/app/utils/currency_helpers";

patch(PosPayment.prototype, {
    serialize(options = {}) {
        const data = super.serialize(...arguments);
        if (!(options.orm && isMultiCurrencyPricelistEnabled(this.pos_order_id))) {
            return data;
        }
        data.amount = convertOrderAmountToBaseCurrency(this.pos_order_id, data.amount);
        return data;
    },
});

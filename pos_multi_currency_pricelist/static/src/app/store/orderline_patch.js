/** @odoo-module **/

import { PosOrderline } from "@point_of_sale/app/models/pos_order_line";
import { patch } from "@web/core/utils/patch";
import {
    convertOrderAmountToBaseCurrency,
    isMultiCurrencyPricelistEnabled,
} from "@pos_multi_currency_pricelist/app/utils/currency_helpers";

patch(PosOrderline.prototype, {
    serialize(options = {}) {
        const data = super.serialize(...arguments);
        if (!(options.orm && isMultiCurrencyPricelistEnabled(this.order_id))) {
            return data;
        }
        data.price_unit = convertOrderAmountToBaseCurrency(this.order_id, data.price_unit);
        data.price_subtotal = convertOrderAmountToBaseCurrency(this.order_id, data.price_subtotal);
        data.price_subtotal_incl = convertOrderAmountToBaseCurrency(
            this.order_id,
            data.price_subtotal_incl
        );
        data.price_extra = convertOrderAmountToBaseCurrency(this.order_id, data.price_extra);
        return data;
    },
});

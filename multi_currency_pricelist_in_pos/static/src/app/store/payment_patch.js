/** @odoo-module **/
import { Payment } from "@point_of_sale/app/store/models";
import { patch } from "@web/core/utils/patch";
import {
    convertOrderAmountToBaseCurrency,
    isMultiCurrencyPricelistEnabled,
} from "@multi_currency_pricelist_in_pos/app/utils/currency_helpers";
/**
 * Extends the POS Payment model to support multi-currency pricelists.
 *
 * This patch converts the payment amount from the active order currency
 * to the company base currency before exporting the payment data to
 * ensure consistent backend processing.
 */

patch(Payment.prototype, {
    export_as_JSON() {
        const json = super.export_as_JSON(...arguments);
        if (!isMultiCurrencyPricelistEnabled(this.pos)) {
            return json;
        }
        json.amount = convertOrderAmountToBaseCurrency(this.order, json.amount);
        return json;
    },
});

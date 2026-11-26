/** @odoo-module **/
import { PosStore } from "@point_of_sale/app/store/pos_store";
import { patch } from "@web/core/utils/patch";

/**
 * Extends the POS Store to manage currencies associated with
 * multi-currency pricelists.
 *
 * This patch stores the currencies loaded during POS initialization
 * and provides a helper method to retrieve a currency by its ID.
 */

patch(PosStore.prototype, {
    async _processData(loadedData) {
        await super._processData(...arguments);
        this.pricelistCurrenciesById = Object.fromEntries(
            (loadedData.multi_currency_pricelist_currencies || []).map((currency) => [
                currency.id,
                currency,
            ])
        );
        if (this.currency) {
            this.pricelistCurrenciesById[this.currency.id] = this.currency;
        }
    },

    getCurrencyById(currencyId) {
        return this.pricelistCurrenciesById?.[currencyId] || null;
    },
});

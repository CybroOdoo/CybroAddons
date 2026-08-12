/** @odoo-module **/

import { PosStore } from "@point_of_sale/app/store/pos_store";
import { patch } from "@web/core/utils/patch";
import { roundPrecision as round_pr } from "@web/core/utils/numbers";
import {
    convertAmount,
    getBaseCurrency,
    getOrderCurrency,
    isMultiCurrencyPricelistEnabled,
} from "@pos_multi_currency_pricelist/app/utils/currency_helpers";

patch(PosStore.prototype, {
    getCurrencyById(currencyId) {
        return this.models["res.currency"]?.get?.(currencyId) || null;
    },

    async selectPricelist(pricelist) {
        await super.selectPricelist(...arguments);
        const order = this.get_order();
        if (order) {
            order.uiState.pricelistManuallySet = true;
        }
    },

    postSyncAllOrders(orders) {
        super.postSyncAllOrders(...arguments);
        for (const order of orders || []) {
            if (!isMultiCurrencyPricelistEnabled(order)) {
                continue;
            }
            const baseCurrency = getBaseCurrency(order);
            const orderCurrency = getOrderCurrency(order);
            if (!baseCurrency || !orderCurrency || baseCurrency.id === orderCurrency.id) {
                continue;
            }

            order.set_pricelist(order.pricelist_id);

            for (const line of order.lines) {
                if (line.price_type === "manual") {
                    line.set_unit_price(
                        convertAmount(line.get_unit_price(), baseCurrency, orderCurrency)
                    );
                    line.price_extra = convertAmount(
                        line.price_extra || 0,
                        baseCurrency,
                        orderCurrency
                    );
                }
            }

            for (const payment of order.payment_ids) {
                payment.amount = round_pr(
                    convertAmount(payment.amount || 0, baseCurrency, orderCurrency),
                    orderCurrency.rounding
                );
            }

            order.recomputeOrderData();
        }
    },
});

/** @odoo-module **/

import { OrderSummary } from "@point_of_sale/app/screens/product_screen/order_summary/order_summary";
import { patch } from "@web/core/utils/patch";
import { isMultiCurrencyPricelistEnabled } from "@pos_multi_currency_pricelist/app/utils/currency_helpers";

patch(OrderSummary.prototype, {
    get orderWidgetTaxTotals() {
        const order = this.currentOrder;
        const taxTotals = order?.taxTotals;
        if (!taxTotals || !isMultiCurrencyPricelistEnabled(order)) {
            return taxTotals;
        }
        const currencyId = order.currency?.id;
        if (!currencyId || taxTotals.currency_id === currencyId) {
            return taxTotals;
        }
        return {
            ...taxTotals,
            currency_id: currencyId,
        };
    },
});

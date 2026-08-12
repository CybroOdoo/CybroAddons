/** @odoo-module **/

import { ProductInfoPopup } from "@point_of_sale/app/screens/product_screen/product_info_popup/product_info_popup";
import { patch } from "@web/core/utils/patch";
import {
    convertAmount,
    getOrderCurrency,
    isMultiCurrencyPricelistEnabled,
} from "@pos_multi_currency_pricelist/app/utils/currency_helpers";

patch(ProductInfoPopup.prototype, {
    getSupplierPrice(supplier) {
        const order = this.pos.get_order();
        const orderCurrency = getOrderCurrency(order) || this.pos.currency;
        if (!isMultiCurrencyPricelistEnabled(this.pos) || !supplier?.currency_id) {
            return supplier?.price ?? 0;
        }
        const supplierCurrency = this.pos.getCurrencyById(supplier.currency_id);
        return convertAmount(supplier.price, supplierCurrency, orderCurrency);
    },
});

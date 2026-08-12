/** @odoo-module **/

import { ProductProduct } from "@point_of_sale/app/models/product_product";
import { patch } from "@web/core/utils/patch";
import { _t } from "@web/core/l10n/translation";
import { roundPrecision as round_pr } from "@web/core/utils/numbers";
import {
    convertAmount,
    getBaseCurrency,
    getPricelistCurrency,
    isMultiCurrencyPricelistEnabled,
} from "@pos_multi_currency_pricelist/app/utils/currency_helpers";

patch(ProductProduct.prototype, {
    get_price(pricelist, quantity, price_extra = 0, recurring = false, list_price = false) {
        if (!isMultiCurrencyPricelistEnabled(this)) {
            return super.get_price(...arguments);
        }

        if (recurring && !pricelist) {
            alert(
                _t(
                    "An error occurred when loading product prices. Make sure all pricelists are available in the POS."
                )
            );
        }

        const baseCurrency = getBaseCurrency(this);
        const targetCurrency = getPricelistCurrency(this, pricelist);
        let price = convertAmount(
            (list_price || this.lst_price) + (price_extra || 0),
            baseCurrency,
            targetCurrency
        );
        const rule = this.getPricelistRule(pricelist, quantity);
        if (!rule) {
            return price;
        }

        if (rule.base === "pricelist") {
            if (rule.base_pricelist_id) {
                price = this.get_price(rule.base_pricelist_id, quantity, 0, true, list_price);
                price = convertAmount(
                    price,
                    getPricelistCurrency(this, rule.base_pricelist_id),
                    targetCurrency
                );
            }
        } else if (rule.base === "standard_price") {
            price = convertAmount(this.standard_price, baseCurrency, targetCurrency);
        }

        if (rule.compute_price === "fixed") {
            price = rule.fixed_price;
        } else if (rule.compute_price === "percentage") {
            price = price - price * (rule.percent_price / 100);
        } else {
            const priceLimit = price;
            price -= price * (rule.price_discount / 100);
            if (rule.price_round) {
                price = round_pr(price, rule.price_round);
            }
            if (rule.price_surcharge) {
                price += rule.price_surcharge;
            }
            if (rule.price_min_margin) {
                price = Math.max(price, priceLimit + rule.price_min_margin);
            }
            if (rule.price_max_margin) {
                price = Math.min(price, priceLimit + rule.price_max_margin);
            }
        }

        return price;
    },
});

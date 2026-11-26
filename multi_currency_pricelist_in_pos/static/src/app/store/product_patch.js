/** @odoo-module **/
import { Product } from "@point_of_sale/app/store/models";
import { patch } from "@web/core/utils/patch";
import { _t } from "@web/core/l10n/translation";
import { roundPrecision as round_pr } from "@web/core/utils/numbers";
import {
    convertAmount,
    getPricelistCurrency,
    isMultiCurrencyPricelistEnabled,
} from "@multi_currency_pricelist_in_pos/app/utils/currency_helpers";

/**
 * Extends the POS Product model to support multi-currency pricelists.
 *
 * This patch customizes product price computation and display by applying
 * currency conversion based on the selected pricelist. It also ensures
 * that tax calculations and pricelist rules are evaluated using the
 * appropriate currency.
 */

const { DateTime } = luxon;

patch(Product.prototype, {
    get_price(pricelist, quantity, price_extra = 0, recurring = false, original_line = false, related_lines = []) {
        if (!isMultiCurrencyPricelistEnabled(this.pos)) {
            return super.get_price(...arguments);
        }

        const date = DateTime.now();
        if (recurring && !pricelist) {
            alert(
                _t(
                    "An error occurred when loading product prices. Make sure all pricelists are available in the POS."
                )
            );
        }

        const rules = !pricelist
            ? []
            : (this.applicablePricelistItems[pricelist.id] || []).filter((item) =>
                  this.isPricelistItemUsable(item, date)
              );

        if (original_line && original_line.is_lot_tracked()) {
            related_lines.push(
                ...original_line.order.orderlines.filter((line) => line.product.id === this.id)
            );
            quantity = related_lines.reduce((sum, line) => sum + line.get_quantity(), 0);
        }

        const rule = rules.find((candidate) => !candidate.min_quantity || quantity >= candidate.min_quantity);
        const baseCurrency = this.pos.currency;
        const targetCurrency = getPricelistCurrency(this.pos, pricelist);
        let price = convertAmount(
            this.pos,
            this.lst_price + (price_extra || 0),
            baseCurrency,
            targetCurrency
        );
        if (!rule) {
            return price;
        }

        if (rule.base === "pricelist") {
            const basePricelist = this.pos.pricelists.find(
                (candidate) => candidate.id === rule.base_pricelist_id[0]
            );
            if (basePricelist) {
                const basePrice = this.get_price(basePricelist, quantity, 0, true);
                price = convertAmount(
                    this.pos,
                    basePrice,
                    getPricelistCurrency(this.pos, basePricelist),
                    targetCurrency
                );
            }
        } else if (rule.base === "standard_price") {
            price = convertAmount(this.pos, this.standard_price, baseCurrency, targetCurrency);
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

    get_display_price({
        pricelist = this.pos.getDefaultPricelist(),
        quantity = 1,
        price = this.get_price(pricelist, quantity),
        iface_tax_included = this.pos.config.iface_tax_included,
    } = {}) {
        if (!isMultiCurrencyPricelistEnabled(this.pos)) {
            return super.get_display_price(...arguments);
        }

        const order = this.pos.get_order();
        const taxes = this.pos.get_taxes_after_fp(this.taxes_id, order && order.fiscal_position);
        const currentTaxes = this.pos.getTaxesByIds(this.taxes_id);
        const priceAfterFp = this.pos.computePriceAfterFp(price, currentTaxes);
        const currency = getPricelistCurrency(this.pos, pricelist);
        const allPrices = this.pos.compute_all(taxes, priceAfterFp, quantity, currency.rounding);
        return iface_tax_included === "total" ? allPrices.total_included : allPrices.total_excluded;
    },
});

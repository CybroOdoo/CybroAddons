/** @odoo-module **/
import { Orderline } from "@point_of_sale/app/store/models";
import { patch } from "@web/core/utils/patch";
import { roundPrecision as round_pr } from "@web/core/utils/numbers";
import {
    convertOrderAmountToBaseCurrency,
    getCurrencyRounding,
    isMultiCurrencyPricelistEnabled,
} from "@multi_currency_pricelist_in_pos/app/utils/currency_helpers";

/**
 * Extends the POS Orderline model to support multi-currency pricelists.
 *
 * This patch overrides price and tax calculations to use the active
 * order currency, applies currency-specific rounding, and converts
 * monetary values to the company base currency during JSON export.
 */

patch(Orderline.prototype, {
    get_base_price() {
        if (!isMultiCurrencyPricelistEnabled(this.pos)) {
            return super.get_base_price(...arguments);
        }
        return round_pr(
            this.get_unit_price() * this.get_quantity() * (1 - this.get_discount() / 100),
            getCurrencyRounding(this.order)
        );
    },

    get_display_price_one() {
        if (!isMultiCurrencyPricelistEnabled(this.pos)) {
            return super.get_display_price_one(...arguments);
        }

        const rounding = getCurrencyRounding(this.order);
        const priceUnit = this.get_unit_price();
        if (this.pos.config.iface_tax_included !== "total") {
            return round_pr(priceUnit * (1.0 - this.get_discount() / 100.0), rounding);
        }

        const product = this.get_product();
        const taxesIds = this.tax_ids || product.taxes_id;
        const productTaxes = this.pos.get_taxes_after_fp(taxesIds, this.order.fiscal_position);
        const allTaxes = this.compute_all(productTaxes, priceUnit, 1, rounding);
        return round_pr(allTaxes.total_included * (1 - this.get_discount() / 100), rounding);
    },

    get_taxed_lst_unit_price() {
        if (!isMultiCurrencyPricelistEnabled(this.pos)) {
            return super.get_taxed_lst_unit_price(...arguments);
        }

        const lstPrice = this.compute_fixed_price(this.get_lst_price());
        const product = this.get_product();
        const taxesIds = product.taxes_id;
        const productTaxes = this.pos.get_taxes_after_fp(taxesIds, this.order.fiscal_position);
        const unitPrices = this.compute_all(
            productTaxes,
            lstPrice,
            1,
            getCurrencyRounding(this.order)
        );
        return this.pos.config.iface_tax_included === "total"
            ? unitPrices.total_included
            : unitPrices.total_excluded;
    },

    get_all_prices(qty = this.get_quantity()) {
        if (!isMultiCurrencyPricelistEnabled(this.pos)) {
            return super.get_all_prices(...arguments);
        }

        const priceUnit = this.get_unit_price() * (1.0 - this.get_discount() / 100.0);
        let taxTotal = 0;
        const product = this.get_product();
        let taxesIds = this.tax_ids || product.taxes_id;
        taxesIds = taxesIds.filter((taxId) => taxId in this.pos.taxes_by_id);
        const taxDetail = {};
        const productTaxes = this.pos.get_taxes_after_fp(taxesIds, this.order?.fiscal_position);
        const rounding = getCurrencyRounding(this.order);
        const allTaxes = this.compute_all(productTaxes, priceUnit, qty, rounding);
        const allTaxesBeforeDiscount = this.compute_all(
            productTaxes,
            this.get_unit_price(),
            qty,
            rounding
        );
        allTaxes.taxes.forEach((tax) => {
            taxTotal += tax.amount;
            taxDetail[tax.id] = {
                amount: tax.amount,
                base: tax.base,
            };
        });

        return {
            priceWithTax: allTaxes.total_included,
            priceWithoutTax: allTaxes.total_excluded,
            priceWithTaxBeforeDiscount: allTaxesBeforeDiscount.total_included,
            priceWithoutTaxBeforeDiscount: allTaxesBeforeDiscount.total_excluded,
            tax: taxTotal,
            taxDetails: taxDetail,
        };
    },

    export_as_JSON() {
        const json = super.export_as_JSON(...arguments);
        if (!isMultiCurrencyPricelistEnabled(this.pos)) {
            return json;
        }
        json.price_unit = convertOrderAmountToBaseCurrency(this.order, json.price_unit);
        json.price_subtotal = convertOrderAmountToBaseCurrency(this.order, json.price_subtotal);
        json.price_subtotal_incl = convertOrderAmountToBaseCurrency(
            this.order,
            json.price_subtotal_incl
        );
        json.price_extra = convertOrderAmountToBaseCurrency(this.order, json.price_extra);
        return json;
    },
});

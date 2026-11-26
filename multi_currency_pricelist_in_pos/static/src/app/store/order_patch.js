/** @odoo-module **/
import { Order } from "@point_of_sale/app/store/models";
import { patch } from "@web/core/utils/patch";
import { roundPrecision as round_pr } from "@web/core/utils/numbers";
import {
    convertOrderAmountToBaseCurrency,
    getCurrencyRounding,
    isMultiCurrencyPricelistEnabled,
} from "@multi_currency_pricelist_in_pos/app/utils/currency_helpers";

/**
 * Extends the POS Order model to support multi-currency pricelists.
 *
 * This patch overrides order total calculations to use the active
 * pricelist currency, applies currency-specific rounding, and converts
 * monetary values to the company base currency when exporting the order.
 */

patch(Order.prototype, {
    get_subtotal() {
        if (!isMultiCurrencyPricelistEnabled(this.pos)) {
            return super.get_subtotal(...arguments);
        }
        return round_pr(
            this.orderlines.reduce((sum, orderLine) => sum + orderLine.get_display_price(), 0),
            getCurrencyRounding(this)
        );
    },

    get_total_without_tax() {
        if (!isMultiCurrencyPricelistEnabled(this.pos)) {
            return super.get_total_without_tax(...arguments);
        }
        return round_pr(
            this.orderlines.reduce((sum, orderLine) => sum + orderLine.get_price_without_tax(), 0),
            getCurrencyRounding(this)
        );
    },

    get_total_discount() {
        if (!isMultiCurrencyPricelistEnabled(this.pos)) {
            return super.get_total_discount(...arguments);
        }

        const ignoredProductIds = this._get_ignored_product_ids_total_discount();
        return round_pr(
            this.orderlines.reduce((sum, orderLine) => {
                if (!ignoredProductIds.includes(orderLine.product.id)) {
                    sum +=
                        orderLine.getUnitDisplayPriceBeforeDiscount() *
                        (orderLine.get_discount() / 100) *
                        orderLine.get_quantity();
                    if (
                        orderLine.display_discount_policy() === "without_discount" &&
                        !(orderLine.price_type === "manual")
                    ) {
                        sum +=
                            (orderLine.get_taxed_lst_unit_price() -
                                orderLine.getUnitDisplayPriceBeforeDiscount()) *
                            orderLine.get_quantity();
                    }
                }
                return sum;
            }, 0),
            getCurrencyRounding(this)
        );
    },

    get_total_tax() {
        if (!isMultiCurrencyPricelistEnabled(this.pos)) {
            return super.get_total_tax(...arguments);
        }

        const rounding = getCurrencyRounding(this);
        if (this.pos.company.tax_calculation_rounding_method === "round_globally") {
            const groupedTaxes = {};
            this.orderlines.forEach((line) => {
                const taxDetails = line.get_tax_details();
                const taxIds = Object.keys(taxDetails);
                for (const taxId of taxIds) {
                    if (!(taxId in groupedTaxes)) {
                        groupedTaxes[taxId] = 0;
                    }
                    groupedTaxes[taxId] += taxDetails[taxId].amount;
                }
            });

            let sum = 0;
            for (const taxAmount of Object.values(groupedTaxes)) {
                sum += round_pr(taxAmount, rounding);
            }
            return sum;
        }

        return round_pr(
            this.orderlines.reduce((sum, orderLine) => sum + orderLine.get_tax(), 0),
            rounding
        );
    },

    get_total_paid() {
        if (!isMultiCurrencyPricelistEnabled(this.pos)) {
            return super.get_total_paid(...arguments);
        }

        return round_pr(
            this.paymentlines.reduce((sum, paymentLine) => {
                if (paymentLine.is_done()) {
                    sum += paymentLine.get_amount();
                }
                return sum;
            }, 0),
            getCurrencyRounding(this)
        );
    },

    get_change(paymentline) {
        if (!isMultiCurrencyPricelistEnabled(this.pos)) {
            return super.get_change(...arguments);
        }

        let change;
        if (!paymentline) {
            change =
                this.get_total_paid() - this.get_total_with_tax() - this.get_rounding_applied();
        } else {
            change = -this.get_total_with_tax();
            for (const line of this.paymentlines) {
                change += line.get_amount();
                if (line === paymentline) {
                    break;
                }
            }
        }
        return round_pr(Math.max(0, change), getCurrencyRounding(this));
    },

    get_due(paymentline) {
        if (!isMultiCurrencyPricelistEnabled(this.pos)) {
            return super.get_due(...arguments);
        }

        let due;
        if (!paymentline) {
            due =
                this.get_total_with_tax() - this.get_total_paid() + this.get_rounding_applied();
        } else {
            due = this.get_total_with_tax();
            for (const line of this.paymentlines) {
                if (line === paymentline) {
                    break;
                }
                due -= line.get_amount();
            }
        }
        return round_pr(due, getCurrencyRounding(this));
    },

    export_as_JSON() {
        const json = super.export_as_JSON(...arguments);
        if (!isMultiCurrencyPricelistEnabled(this.pos)) {
            return json;
        }
        json.amount_paid = convertOrderAmountToBaseCurrency(this, json.amount_paid);
        json.amount_total = convertOrderAmountToBaseCurrency(this, json.amount_total);
        json.amount_tax = convertOrderAmountToBaseCurrency(this, json.amount_tax);
        json.amount_return = convertOrderAmountToBaseCurrency(this, json.amount_return);
        return json;
    },
});

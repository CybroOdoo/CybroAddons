/** @odoo-module **/

import { PosOrder } from "@point_of_sale/app/models/pos_order";
import { patch } from "@web/core/utils/patch";
import { floatIsZero, roundPrecision as round_pr } from "@web/core/utils/numbers";
import { accountTaxHelpers } from "@account/helpers/account_tax";
import { getTaxesAfterFiscalPosition } from "@point_of_sale/app/models/utils/tax_utils";
import {
    convertOrderAmountToBaseCurrency,
    getCurrencyRounding,
    getOrderCurrency,
    isMultiCurrencyPricelistEnabled,
} from "@pos_multi_currency_pricelist/app/utils/currency_helpers";

patch(PosOrder.prototype, {
    get currency() {
        return getOrderCurrency(this) || this.config.currency_id;
    },

    updatePricelistAndFiscalPosition(newPartner) {
        if (!this.uiState.pricelistManuallySet) {
            return super.updatePricelistAndFiscalPosition(...arguments);
        }

        const defaultFiscalPosition = this.models["account.fiscal.position"].find(
            (position) => position.id === this.config.default_fiscal_position_id?.id
        );
        const newPartnerFiscalPosition = newPartner
            ? newPartner.property_account_position_id
                ? this.models["account.fiscal.position"].find(
                      (position) => position.id === newPartner.property_account_position_id?.id
                  )
                : defaultFiscalPosition
            : defaultFiscalPosition;
        this.update({ fiscal_position_id: newPartnerFiscalPosition });
    },

    get taxTotals() {
        if (!isMultiCurrencyPricelistEnabled(this)) {
            return super.taxTotals;
        }

        const currency = this.currency;
        const company = this.company;
        const extraValues = { currency_id: currency };
        const orderLines = this.lines;
        const isRefund = this._isRefundOrder();
        const documentSign = isRefund ? -1 : 1;

        const baseLines = [];
        for (const line of orderLines) {
            let taxes = line.tax_ids;
            if (this.fiscal_position_id) {
                taxes = getTaxesAfterFiscalPosition(taxes, this.fiscal_position_id, this.models);
            }
            baseLines.push(
                accountTaxHelpers.prepare_base_line_for_taxes_computation(line, {
                    ...extraValues,
                    quantity: documentSign * line.qty,
                    tax_ids: taxes,
                })
            );
        }
        accountTaxHelpers.add_tax_details_in_base_lines(baseLines, company);
        accountTaxHelpers.round_base_lines_tax_details(baseLines, company);

        let cashRounding =
            !this.config.only_round_cash_method && this.config.cash_rounding
                ? this.config.rounding_method
                : null;

        const taxTotals = accountTaxHelpers.get_tax_totals_summary(baseLines, currency, company, {
            cash_rounding: cashRounding,
        });

        taxTotals.order_sign = documentSign;
        taxTotals.order_total =
            taxTotals.total_amount_currency - (taxTotals.cash_rounding_base_amount_currency || 0.0);

        let order_rounding = 0;
        let remaining = taxTotals.order_total;
        const validPayments = this.payment_ids.filter((p) => p.is_done() && !p.is_change);
        for (const [payment, isLast] of validPayments.map((p, i) => [
            p,
            i === validPayments.length - 1,
        ])) {
            const paymentAmount = documentSign * payment.get_amount();
            if (isLast) {
                if (this.config.cash_rounding) {
                    const roundedRemaining = this.getRoundedRemaining(
                        this.config.rounding_method,
                        remaining
                    );
                    if (!floatIsZero(paymentAmount - remaining, currency.decimal_places)) {
                        order_rounding = roundedRemaining - remaining;
                    }
                }
            }
            remaining -= paymentAmount;
        }

        taxTotals.order_rounding = order_rounding;
        taxTotals.order_remaining = remaining;

        const remaining_with_rounding = remaining + order_rounding;
        if (floatIsZero(remaining_with_rounding, currency.decimal_places)) {
            taxTotals.order_has_zero_remaining = true;
        } else {
            taxTotals.order_has_zero_remaining = false;
        }

        return taxTotals;
    },

    get_subtotal() {
        if (!isMultiCurrencyPricelistEnabled(this)) {
            return super.get_subtotal(...arguments);
        }
        return round_pr(
            this.lines.reduce((sum, orderLine) => sum + orderLine.get_display_price(), 0),
            getCurrencyRounding(this)
        );
    },

    get_total_with_tax() {
        if (!isMultiCurrencyPricelistEnabled(this)) {
            return super.get_total_with_tax(...arguments);
        }
        return round_pr(
            this.lines.reduce((sum, orderLine) => sum + orderLine.get_price_with_tax(), 0),
            getCurrencyRounding(this)
        );
    },

    get_total_without_tax() {
        if (!isMultiCurrencyPricelistEnabled(this)) {
            return super.get_total_without_tax(...arguments);
        }
        return round_pr(
            this.lines.reduce((sum, orderLine) => sum + orderLine.get_price_without_tax(), 0),
            getCurrencyRounding(this)
        );
    },

    get_total_discount() {
        if (!isMultiCurrencyPricelistEnabled(this)) {
            return super.get_total_discount(...arguments);
        }

        const ignoredProductIds = this._get_ignored_product_ids_total_discount();
        return round_pr(
            this.lines.reduce((sum, orderLine) => {
                if (!ignoredProductIds.includes(orderLine.product_id.id)) {
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
        if (!isMultiCurrencyPricelistEnabled(this)) {
            return super.get_total_tax(...arguments);
        }

        const rounding = getCurrencyRounding(this);
        if (this.company.tax_calculation_rounding_method === "round_globally") {
            const groupedTaxes = {};
            this.lines.forEach((line) => {
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
            this.lines.reduce((sum, orderLine) => sum + orderLine.get_tax(), 0),
            rounding
        );
    },

    get_total_paid() {
        if (!isMultiCurrencyPricelistEnabled(this)) {
            return super.get_total_paid(...arguments);
        }

        return round_pr(
            this.payment_ids.reduce((sum, paymentLine) => {
                if (paymentLine.is_done()) {
                    sum += paymentLine.get_amount();
                }
                return sum;
            }, 0),
            getCurrencyRounding(this)
        );
    },

    get_change(paymentline) {
        if (!isMultiCurrencyPricelistEnabled(this)) {
            return super.get_change(...arguments);
        }

        let change;
        if (!paymentline) {
            change =
                this.get_total_paid() - this.get_total_with_tax() - this.get_rounding_applied();
        } else {
            change = -this.get_total_with_tax();
            for (const line of this.payment_ids) {
                change += line.get_amount();
                if (line === paymentline) {
                    break;
                }
            }
        }
        return round_pr(Math.max(0, change), getCurrencyRounding(this));
    },

    get_due(paymentline) {
        if (!isMultiCurrencyPricelistEnabled(this)) {
            return super.get_due(...arguments);
        }

        let due;
        if (!paymentline) {
            due =
                this.get_total_with_tax() - this.get_total_paid() + this.get_rounding_applied();
        } else {
            due = this.get_total_with_tax();
            for (const line of this.payment_ids) {
                if (line === paymentline) {
                    break;
                }
                due -= line.get_amount();
            }
        }
        return round_pr(due, getCurrencyRounding(this));
    },

    serialize(options = {}) {
        const data = super.serialize(...arguments);
        if (!(options.orm && isMultiCurrencyPricelistEnabled(this))) {
            return data;
        }
        data.amount_paid = convertOrderAmountToBaseCurrency(this, data.amount_paid);
        data.amount_total = convertOrderAmountToBaseCurrency(this, data.amount_total);
        data.amount_tax = convertOrderAmountToBaseCurrency(this, data.amount_tax);
        data.amount_return = convertOrderAmountToBaseCurrency(this, data.amount_return);
        return data;
    },
});

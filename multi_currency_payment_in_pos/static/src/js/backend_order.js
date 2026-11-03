/** @odoo-module **/
import { patch } from "@web/core/utils/patch";
import { PosPayment } from "@point_of_sale/app/models/pos_payment";
import { GeneratePrinterData } from "@point_of_sale/app/utils/printer/generate_printer_data";

/**
 * Patch for PosPayment and GeneratePrinterData to include converted currency
 * information when exporting payment data for receipt printing and serialization.
 */

patch(PosPayment.prototype, {
    /**
     * Initialize PosPayment with foreign currency values if available.
     *
     * @override
     * @param {Object} vals - Raw payment data values.
     */
    setup(vals) {
        super.setup(...arguments);
        if (vals) {
            if (vals.payment_currency) {
                this.payment_currency = vals.payment_currency;
            }
            if (vals.currency_amount) {
                this.currency_amount = vals.currency_amount;
            }
            if (vals.payment_currency && vals.currency_amount && !this.converted_currency) {
                this.converted_currency = {
                    name: vals.payment_currency,
                    amount: vals.currency_amount,
                };
            }
        }
    },
});

patch(GeneratePrinterData.prototype, {
    /**
     * Enrich printer payment data with foreign currency name and amount.
     *
     * @override
     * @returns {Array<Object>}
     */
    generatePaymentData() {
        const payments = super.generatePaymentData(...arguments);
        return this.order.payment_ids.map((line, index) => {
            const data = payments[index] || {};
            const paymentCurrency =
                line.payment_currency ||
                line.raw?.payment_currency ||
                line.converted_currency?.name ||
                false;
            let currencyAmount =
                line.currency_amount ??
                line.raw?.currency_amount ??
                line.converted_currency?.amount;
            if (
                currencyAmount !== undefined &&
                currencyAmount !== false &&
                currencyAmount !== null &&
                !isNaN(currencyAmount)
            ) {
                currencyAmount =
                    typeof currencyAmount === "number"
                        ? currencyAmount.toFixed(2)
                        : currencyAmount;
            } else {
                currencyAmount = false;
            }
            return {
                ...data,
                payment_currency: paymentCurrency,
                currency_amount: currencyAmount,
            };
        });
    },
});

/** @odoo-module **/
import { PaymentScreen } from "@point_of_sale/app/screens/payment_screen/payment_screen";
import { NumberPopup } from "@point_of_sale/app/utils/input_popups/number_popup";
import { _t } from "@web/core/l10n/translation";
import { patch } from "@web/core/utils/patch";
import { parseFloat } from "@web/views/fields/parsers";
import { floatIsZero } from "@web/core/utils/numbers";
import {
    getOrderCurrency,
    isMultiCurrencyPricelistEnabled,
} from "@multi_currency_pricelist_in_pos/app/utils/currency_helpers";

/**
 * Extends the POS Payment Screen to support multi-currency pricelists.
 *
 * This patch customizes:
 * - Tip entry using the order's active currency.
 * - Terminal payment validation based on the selected pricelist currency.
 */
patch(PaymentScreen.prototype, {
    async addTip() {
        if (!isMultiCurrencyPricelistEnabled(this.pos)) {
            return super.addTip(...arguments);
        }

        const tip = this.currentOrder.get_tip();
        const change = this.currentOrder.get_change();
        const value = tip === 0 && change > 0 ? change : tip;
        const currency = getOrderCurrency(this.currentOrder) || this.pos.currency;
        const { confirmed, payload } = await this.popup.add(NumberPopup, {
            title: tip ? _t("Change Tip") : _t("Add Tip"),
            startingValue: value,
            isInputSelected: true,
            nbrDecimal: currency.decimal_places,
            inputSuffix: currency.symbol,
        });

        if (confirmed) {
            this.currentOrder.set_tip(parseFloat(payload ?? ""));
        }
    },

    async sendPaymentRequest(line) {
        if (!isMultiCurrencyPricelistEnabled(this.pos)) {
            return super.sendPaymentRequest(...arguments);
        }

        this.numberBuffer.capture();
        this.paymentLines.forEach((paymentLine) => {
            paymentLine.can_be_reversed = false;
        });

        const isPaymentSuccessful = await line.pay();
        const currentOrder = this.pos.get_order();
        const currency = getOrderCurrency(currentOrder) || this.pos.currency;
        if (
            isPaymentSuccessful &&
            currentOrder.is_paid() &&
            floatIsZero(currentOrder.get_due(), currency.decimal_places) &&
            this.pos.config.auto_validate_terminal_payment
        ) {
            this.validateOrder(false);
        }
    },
});
